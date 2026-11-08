"""Handcrafted-style retro-industrial pixel-art environment renderer for ECHO-7.

Co-designs code-generated 640x360 logical pixel-art backgrounds (upscaled 2x via
nearest-neighbor to 1280x720) with the level's real solid-tile architecture:
1. World-locked under-deck girder trusses and load-bearing stanchions aligned to `self._world_tiles`.
2. Multi-story vertical bay tiling (`_get_upper_chunk`) for tall rooms (`height > 720`) without
   repeating floor seams.
3. Plausible connected machinery (gearbox drive shafts, pump manifolds, busbar insulators,
   observation bays with interior ladders, and local signal-reactive feeder risers).
"""
from __future__ import annotations
import math
import pygame
from src.core.settings import VIRTUAL_WIDTH, VIRTUAL_HEIGHT
from src.visuals.level_effects import draw_level_specific_fx

SCALE = 2
LOGICAL_W = VIRTUAL_WIDTH // SCALE   # 640
LOGICAL_H = VIRTUAL_HEIGHT // SCALE  # 360
CHUNK_W = 160                        # 320 virtual px per modular bay

PALETTES: dict[int, dict[str, tuple[int, int, int]]] = {
    1: {
        "void": (6, 12, 22), "far": (11, 21, 35), "mid": (15, 30, 48),
        "panel": (21, 41, 62), "panel_alt": (17, 34, 52), "recess": (12, 25, 40),
        "seam": (9, 18, 29), "edge": (42, 76, 102), "hi": (66, 114, 146),
        "accent": (75, 212, 225), "warn": (229, 144, 80), "glass": (14, 38, 56),
    },
    2: {
        "void": (12, 9, 8), "far": (22, 16, 13), "mid": (34, 25, 20),
        "panel": (48, 36, 29), "panel_alt": (39, 29, 24), "recess": (27, 20, 16),
        "seam": (16, 12, 10), "edge": (86, 66, 52), "hi": (118, 92, 72),
        "accent": (253, 170, 73), "warn": (235, 110, 52), "glass": (64, 38, 22),
    },
    3: {
        "void": (5, 11, 22), "far": (10, 21, 38), "mid": (15, 33, 55),
        "panel": (21, 44, 70), "panel_alt": (17, 36, 58), "recess": (12, 26, 44),
        "seam": (8, 17, 30), "edge": (46, 90, 128), "hi": (72, 134, 180),
        "accent": (84, 197, 245), "warn": (241, 164, 88), "glass": (18, 52, 82),
    },
    4: {
        "void": (10, 8, 20), "far": (17, 14, 32), "mid": (25, 22, 44),
        "panel": (33, 30, 56), "panel_alt": (27, 24, 46), "recess": (19, 17, 35),
        "seam": (13, 11, 24), "edge": (66, 56, 96), "hi": (96, 84, 136),
        "accent": (209, 106, 244), "warn": (237, 78, 104), "glass": (22, 28, 52),
    },
    5: {
        "void": (5, 14, 18), "far": (10, 25, 31), "mid": (15, 36, 44),
        "panel": (21, 48, 56), "panel_alt": (17, 40, 48), "recess": (12, 29, 36),
        "seam": (8, 19, 24), "edge": (44, 88, 100), "hi": (68, 124, 136),
        "accent": (73, 222, 213), "warn": (239, 162, 85), "glass": (16, 56, 64),
    },
    6: {
        "void": (15, 8, 9), "far": (28, 14, 13), "mid": (42, 21, 19),
        "panel": (56, 29, 25), "panel_alt": (45, 23, 20), "recess": (32, 15, 14),
        "seam": (20, 9, 9), "edge": (100, 54, 42), "hi": (138, 76, 56),
        "accent": (255, 145, 67), "warn": (255, 96, 54), "glass": (92, 38, 22),
    },
    7: {
        "void": (9, 13, 22), "far": (19, 23, 36), "mid": (28, 36, 52),
        "panel": (38, 50, 66), "panel_alt": (30, 41, 56), "recess": (22, 29, 42),
        "seam": (13, 17, 26), "edge": (72, 94, 114), "hi": (102, 128, 150),
        "accent": (255, 110, 124), "warn": (240, 150, 88), "glass": (52, 36, 64),
    },
    8: {
        "void": (6, 10, 18), "far": (12, 19, 32), "mid": (19, 29, 46),
        "panel": (27, 40, 58), "panel_alt": (21, 32, 48), "recess": (15, 23, 36),
        "seam": (9, 15, 24), "edge": (52, 74, 98), "hi": (82, 112, 140),
        "accent": (115, 219, 250), "warn": (246, 91, 112), "glass": (17, 30, 50),
    },
}


def _clamp(value: int | float, low: int | float, high: int | float):
    return max(low, min(high, value))


def screen_x(world_x: float, camera_x: float) -> int:
    """Architectural world-to-screen mapping (factor 1.0). Never depends on player X."""
    return int(round(world_x - camera_x))


def parallax_x(origin_x: float, camera_x: float, factor: float) -> int:
    """Distant scenic world-to-screen mapping with explicit depth factor."""
    return int(round(origin_x - camera_x * factor))


def archetype_for_level(level_num: int) -> str:
    """Selects one of three composition archetypes per chapter from level number."""
    pos_in_chapter = (max(1, int(level_num)) - 1) % 10
    if pos_in_chapter < 3:
        return "opening"
    if pos_in_chapter < 7:
        return "mid_complex"
    return "late_crisis"


def _draw_beveled_panel(
    surf: pygame.Surface,
    rect: pygame.Rect,
    fill: tuple[int, int, int],
    edge: tuple[int, int, int],
    seam: tuple[int, int, int],
    hi: tuple[int, int, int] | None = None,
    rivets: bool = True,
    vertical_ribs: int = 0,
) -> None:
    """Draws an industrial pixel-art beveled plate with top highlight, bottom shadow, ribs, and corner rivets."""
    x, y, w, h = rect
    if w <= 4 or h <= 4:
        return
    pygame.draw.rect(surf, seam, (x, y, w, h))
    pygame.draw.rect(surf, fill, (x + 1, y + 1, w - 2, h - 2))
    if vertical_ribs > 0 and w > vertical_ribs * 2:
        for rx in range(x + vertical_ribs, x + w - 4, vertical_ribs):
            pygame.draw.line(surf, seam, (rx, y + 3), (rx, y + h - 4), 1)
            pygame.draw.line(surf, edge, (rx + 1, y + 3), (rx + 1, y + h - 4), 1)
    pygame.draw.line(surf, hi or edge, (x + 2, y + 1), (x + w - 3, y + 1), 1)
    pygame.draw.line(surf, edge, (x + 1, y + 2), (x + 1, y + h - 3), 1)
    pygame.draw.line(surf, seam, (x + 2, y + h - 2), (x + w - 3, y + h - 2), 1)
    if rivets and w >= 16 and h >= 16:
        for rx in (x + 3, x + w - 5):
            for ry in (y + 3, y + h - 5):
                pygame.draw.rect(surf, seam, (rx + 1, ry + 1, 2, 2))
                pygame.draw.rect(surf, edge, (rx, ry, 2, 2))


def _draw_cog(
    surf: pygame.Surface,
    cx: int,
    cy: int,
    radius: int,
    teeth: int,
    angle_rad: float,
    body_col: tuple[int, int, int],
    rim_col: tuple[int, int, int],
    hole_col: tuple[int, int, int],
) -> None:
    """Draws a stepped pixel-art toothed gear wheel."""
    for t in range(teeth):
        a = angle_rad + t * (math.tau / teeth)
        tx = int(round(cx + (radius + 3) * math.cos(a)))
        ty = int(round(cy + (radius + 3) * math.sin(a)))
        pygame.draw.rect(surf, rim_col, (tx - 2, ty - 2, 4, 4))
    pygame.draw.circle(surf, body_col, (cx, cy), radius)
    pygame.draw.circle(surf, rim_col, (cx, cy), radius, 2)
    if radius >= 14:
        for s in range(4):
            sa = angle_rad + s * (math.pi / 2)
            sx = int(round(cx + (radius - 3) * math.cos(sa)))
            sy = int(round(cy + (radius - 3) * math.sin(sa)))
            pygame.draw.line(surf, rim_col, (cx, cy), (sx, sy), 2)
    pygame.draw.circle(surf, hole_col, (cx, cy), max(3, radius // 3))
    pygame.draw.circle(surf, rim_col, (cx, cy), max(3, radius // 3), 1)


def _draw_segmented_pipe(
    surf: pygame.Surface,
    x: int,
    y: int,
    w: int,
    h: int,
    body_col: tuple[int, int, int],
    hi_col: tuple[int, int, int],
    seam_col: tuple[int, int, int],
    flange_step: int = 40,
) -> None:
    """Draws a shaded horizontal industrial pipe with specular highlight, shadow belly, and bolted flanges."""
    pygame.draw.rect(surf, seam_col, (x, y, w, h))
    pygame.draw.rect(surf, body_col, (x, y + 1, w, max(1, h - 2)))
    pygame.draw.line(surf, hi_col, (x, y + 2), (x + w - 1, y + 2), 1)
    for fx in range(x + 16, x + w - 8, flange_step):
        pygame.draw.rect(surf, seam_col, (fx - 1, y - 1, 5, h + 2))
        pygame.draw.rect(surf, hi_col, (fx, y, 3, h))


def _draw_vertical_pipe(
    surf: pygame.Surface,
    x: int,
    y: int,
    w: int,
    h: int,
    body_col: tuple[int, int, int],
    hi_col: tuple[int, int, int],
    seam_col: tuple[int, int, int],
    flange_step: int = 36,
) -> None:
    """Draws a shaded vertical industrial riser pipe with bolted collar joints."""
    pygame.draw.rect(surf, seam_col, (x, y, w, h))
    pygame.draw.rect(surf, body_col, (x + 1, y, max(1, w - 2), h))
    pygame.draw.line(surf, hi_col, (x + 2, y), (x + 2, y + h - 1), 1)
    for fy in range(y + 12, y + h - 8, flange_step):
        pygame.draw.rect(surf, seam_col, (x - 1, fy - 1, w + 2, 4))
        pygame.draw.rect(surf, hi_col, (x, fy, w, 2))


def _draw_echo7_pixel_text(surf: pygame.Surface, x: int, y: int, col: tuple[int, int, int]) -> None:
    """Draws crisp 3x5 pixel-font 'ECHO-7' lettering on a nameplate."""
    glyphs = [
        [(0, 0, 3, 1), (0, 0, 1, 5), (0, 2, 2, 1), (0, 4, 3, 1)],  # E
        [(0, 0, 3, 1), (0, 0, 1, 5), (0, 4, 3, 1)],                # C
        [(0, 0, 1, 5), (2, 0, 1, 5), (0, 2, 3, 1)],                # H
        [(0, 0, 3, 1), (0, 0, 1, 5), (2, 0, 1, 5), (0, 4, 3, 1)],  # O
        [(0, 2, 2, 1)],                                            # -
        [(0, 0, 3, 1), (2, 0, 1, 3), (1, 3, 1, 2)],                # 7
    ]
    gx = x
    for g in glyphs:
        for rx, ry, rw, rh in g:
            pygame.draw.rect(surf, col, (gx + rx * 2, y + ry * 2, rw * 2, rh * 2))
        gx += 9


class PixelEnvironment:
    """Code-drawn, cached multi-plane pixel-art environment for all 8 chapters."""

    def __init__(self) -> None:
        self.focus = (VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT // 2)
        self.level_num = 1
        self._chunk_cache: dict[tuple, pygame.Surface] = {}
        self._upper_chunk_cache: dict[tuple, pygame.Surface] = {}
        self._hero_cache: dict[tuple, pygame.Surface] = {}
        self._far_cache: dict[tuple, pygame.Surface] = {}
        self._work_surface: pygame.Surface | None = None
        self._world_tiles: list = []
        self._local_nodes: list[tuple[int, int, bool, str]] = []
        self._active_signals: set[str] = set()

    def set_world_tiles(self, tiles: list) -> None:
        self._world_tiles = list(tiles)
        self._local_nodes = []
        self._active_signals.clear()

    def set_local_signal_nodes(self, nodes: list[tuple[int, int, bool, str]]) -> None:
        """Registers (world_x, world_y, is_active, kind) of real puzzle devices in the room."""
        self._local_nodes = list(nodes)

    def set_active_signals(self, signals) -> None:
        """Track active puzzle links for the appropriate world-anchored effects."""
        self._active_signals = set(signals) if signals else set()

    def _rect_hits_foreground_tiles(self, world_x: int, world_y: int,
                                    world_w: int, world_h: int, pad: int = 8) -> bool:
        """Reject dressing that crosses thin solid boundaries or interactive equipment."""
        box = pygame.Rect(int(world_x)-pad, int(world_y)-pad,
                          int(world_w)+2*pad, int(world_h)+2*pad)
        for r in self._world_tiles:
            if box.colliderect(r):
                if (r.h <= 120 or r.w <= 96 or
                        box.top < r.top < box.bottom or box.top < r.bottom < box.bottom or
                        box.left < r.left < box.right or box.left < r.right < box.right):
                    return True
        # Shield active/puzzle devices and their immediate interaction space.
        for nx, ny, _on, _kind in self._local_nodes:
            if box.left - 12 <= nx <= box.right + 12 and box.top - 12 <= ny <= box.bottom + 12:
                return True
        return False

    def _is_bay_locally_powered(self, world_x: int, world_y: int, default_powered: bool) -> bool:
        """Returns whether the nearest puzzle device within 480 virtual px is active."""
        if not self._local_nodes:
            return default_powered
        best_dist = 480 * 480
        best_state = None
        for nx, ny, active, _kind in self._local_nodes:
            d2 = (nx - world_x) ** 2 + (ny - world_y) ** 2
            if d2 < best_dist:
                best_dist = d2
                best_state = active
        return default_powered if best_state is None else bool(best_state)

    def set_focus(self, x: int, y: int, level_num: int = 1) -> None:
        self.focus = (int(x), int(y))
        self.level_num = max(1, int(level_num))

    def set_level(self, level_num: int) -> None:
        """Set a deterministic composition without following player movement."""
        self.level_num = max(1, int(level_num))

    def menu_background(
        self, target: pygame.Surface, chapter: int, elapsed: float = 0.0
    ) -> None:
        """Draw an original procedural preview (never a chapter PNG)."""
        old_level, old_focus = self.level_num, self.focus
        old_tiles, old_nodes, old_signals = self._world_tiles, self._local_nodes, self._active_signals
        try:
            # Chapter thumbnails should not inherit foreground occlusion from the last loaded level.
            self._world_tiles, self._local_nodes, self._active_signals = [], [], set()
            chapter = max(1, min(8, int(chapter)))
            self.set_focus(
                VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT // 2, level_num=(chapter - 1) * 10 + 1
            )
            self.draw(
                target, chapter, 0, 0, elapsed, VIRTUAL_WIDTH, VIRTUAL_HEIGHT,
                reduced_motion=True, powered=False,
            )
        finally:
            self.level_num, self.focus = old_level, old_focus
            self._world_tiles, self._local_nodes, self._active_signals = old_tiles, old_nodes, old_signals

    def _get_work_surface(self) -> pygame.Surface:
        if self._work_surface is None:
            self._work_surface = pygame.Surface((LOGICAL_W, LOGICAL_H))
        return self._work_surface

    # ------------------------------------------------------------------
    # LAYER 1 & 2: FAR SKY / DEEP VOID & FAR SILHOUETTE (Parallax 0.16x)
    # ------------------------------------------------------------------
    def _build_far_strip(self, chapter: int, archetype: str) -> pygame.Surface:
        key = (chapter, archetype)
        if key in self._far_cache:
            return self._far_cache[key]
        pal = PALETTES.get(chapter, PALETTES[1])
        surf = pygame.Surface((LOGICAL_W * 2, LOGICAL_H))
        surf.fill(pal["void"])

        for band in range(8):
            by = band * 45
            shade = tuple(
                _clamp(pal["void"][i] + (band * 2 if chapter == 8 else (7 - band)), 0, 255)
                for i in range(3)
            )
            pygame.draw.rect(surf, shade, (0, by, LOGICAL_W * 2, 45))

        if chapter == 1:
            # Ch 1: Cleanroom cryo-stasis cylinder array & overhead sterile light-wells
            for x in range(0, LOGICAL_W * 2, 96):
                pygame.draw.rect(surf, pal["far"], (x + 18, 0, 60, LOGICAL_H))
                pygame.draw.rect(surf, pal["seam"], (x + 26, 28, 44, LOGICAL_H - 56))
                pygame.draw.rect(surf, pal["glass"], (x + 32, 44, 32, 160))
                for y in range(56, 196, 28):
                    pygame.draw.line(surf, pal["mid"], (x + 32, y), (x + 63, y), 2)
        elif chapter == 2:
            # Ch 2: Heavy foundry blast-furnace hearth, overhead crane bridge & drive-cog train
            pygame.draw.rect(surf, (38, 20, 12), (0, LOGICAL_H - 84, LOGICAL_W * 2, 84))
            for x in range(0, LOGICAL_W * 2, 144):
                idx = x // 144
                cx, cy = x + 72, 168 + (idx % 2) * 34
                pygame.draw.rect(surf, pal["far"], (cx - 6, 0, 12, cy + 56))
                pygame.draw.line(surf, pal["mid"], (0, cy), (LOGICAL_W * 2, cy), 4)
                _draw_cog(surf, cx, cy, 48, 12, 0.2 * idx, pal["far"], pal["mid"], pal["void"])
                _draw_cog(surf, cx + 44, cy - 38, 24, 8, -0.3 * idx, pal["far"], pal["mid"], pal["void"])
                pygame.draw.rect(surf, pal["far"], (x + 14, 0, 18, LOGICAL_H))
        elif chapter == 3:
            # Ch 3: High-voltage ceramic insulator towers & catenary transmission lines
            for x in range(0, LOGICAL_W * 2, 88):
                idx = x // 88
                h = 220 + (idx % 3) * 28
                top = LOGICAL_H - h
                pygame.draw.rect(surf, pal["far"], (x + 12, top, 44, h))
                pygame.draw.rect(surf, pal["seam"], (x + 18, top + 8, 32, h - 16))
                for y in range(top + 14, LOGICAL_H - 24, 14):
                    pygame.draw.rect(surf, pal["mid"], (x + 8, y, 52, 4))
                    pygame.draw.line(surf, pal["edge"], (x + 10, y), (x + 58, y), 1)
                pygame.draw.line(surf, pal["mid"], (x + 34, top + 6), (x + 78, top + 20), 1)
                pygame.draw.line(surf, pal["mid"], (x + 78, top + 20), (x + 122, top + 6), 1)
        elif chapter == 4:
            # Ch 4: Panopticon data-vault monoliths & geometric hexagonal security lattice
            for x in range(0, LOGICAL_W * 2, 112):
                pygame.draw.polygon(surf, pal["far"], [
                    (x + 16, LOGICAL_H), (x + 28, 34), (x + 84, 34), (x + 96, LOGICAL_H)
                ])
                pygame.draw.rect(surf, pal["seam"], (x + 38, 52, 36, LOGICAL_H - 72))
                for y in range(64, LOGICAL_H - 40, 18):
                    pygame.draw.line(surf, pal["mid"], (x + 42, y), (x + 70, y), 2)
                pygame.draw.circle(surf, pal["mid"], (x + 56, 86), 14, 1)
        elif chapter == 5:
            # Ch 5: Deep-submerged cylindrical caisson rings, ballast tanks & sluice gates
            for y in (68, 148, 228):
                _draw_segmented_pipe(surf, 0, y, LOGICAL_W * 2, 18, pal["far"], pal["mid"], pal["seam"], 64)
            for x in range(0, LOGICAL_W * 2, 128):
                pygame.draw.rect(surf, pal["far"], (x + 34, 0, 56, LOGICAL_H))
                pygame.draw.circle(surf, pal["seam"], (x + 62, 110), 16)
                pygame.draw.circle(surf, pal["mid"], (x + 62, 110), 16, 2)
                pygame.draw.circle(surf, pal["seam"], (x + 62, 194), 16)
                pygame.draw.circle(surf, pal["mid"], (x + 62, 194), 16, 2)
        elif chapter == 6:
            # Ch 6: Reactor core containment columns & incandescent slag conduits
            for x in range(0, LOGICAL_W * 2, 120):
                pygame.draw.rect(surf, pal["far"], (x + 20, 16, 64, LOGICAL_H - 16))
                pygame.draw.rect(surf, pal["glass"], (x + 36, 40, 32, LOGICAL_H - 72))
                pygame.draw.rect(surf, (124, 48, 26), (x + 44, 48, 16, LOGICAL_H - 88))
                for y in range(52, LOGICAL_H - 40, 24):
                    pygame.draw.rect(surf, pal["mid"], (x + 14, y, 76, 7))
                    pygame.draw.line(surf, pal["edge"], (x + 16, y + 1), (x + 88, y + 1), 1)
        elif chapter == 7:
            # Ch 7: Fractured upper-spire sky-breaches & diagonal shear trusses
            for x in range(0, LOGICAL_W * 2, 160):
                pygame.draw.polygon(surf, (44, 28, 56), [
                    (x + 24, 28), (x + 118, 18), (x + 138, 152), (x + 42, 184),
                ])
                pygame.draw.polygon(surf, (64, 38, 74), [
                    (x + 42, 48), (x + 102, 40), (x + 114, 128), (x + 56, 144),
                ])
                pygame.draw.line(surf, pal["far"], (x + 16, 0), (x + 144, LOGICAL_H), 9)
                pygame.draw.line(surf, pal["mid"], (x + 144, 0), (x + 22, LOGICAL_H), 6)
        elif chapter == 8:
            # Ch 8: Crescent moon, starfield, ruined radar dish & jagged mountain horizon
            pygame.draw.circle(surf, (32, 54, 82), (960, 62), 28)
            pygame.draw.circle(surf, (185, 218, 240), (960, 62), 19)
            pygame.draw.circle(surf, (12, 20, 34), (967, 56), 16)
            for idx in range(56):
                sx = (idx * 67 + 23) % (LOGICAL_W * 2)
                sy = (idx * 31 + 9) % 148
                col = (155, 192, 220) if idx % 3 == 0 else (92, 124, 154)
                pygame.draw.rect(surf, col, (sx, sy, 1, 1))
            pygame.draw.circle(surf, pal["far"], (410, LOGICAL_H - 98), 68, 7)
            pygame.draw.circle(surf, pal["mid"], (410, LOGICAL_H - 98), 54, 2)
            pygame.draw.rect(surf, pal["far"], (378, LOGICAL_H - 78, 64, 78))
            for x in range(0, LOGICAL_W * 2, 20):
                ridge_h = 70 + ((x * 17 + (x // 60) * 31) % 46)
                pygame.draw.rect(surf, pal["far"], (x, LOGICAL_H - ridge_h, 20, ridge_h))
                pygame.draw.line(surf, pal["mid"], (x, LOGICAL_H - ridge_h), (x + 19, LOGICAL_H - ridge_h), 1)

        self._far_cache[key] = surf
        return surf

    # ------------------------------------------------------------------
    # LAYER 3: MID-DISTANCE PARALLAX INFRASTRUCTURE (Parallax 0.40x)
    # ------------------------------------------------------------------
    def _draw_mid_plane(
        self, surf: pygame.Surface, chapter: int, archetype: str, cam_lx: int, cam_ly: int, elapsed: float
    ) -> None:
        pal = PALETTES.get(chapter, PALETTES[1])
        shift_x = int(round(cam_lx * 0.40))
        shift_y = int(round(cam_ly * 0.20))
        spacing = 128 if chapter != 8 else 168
        first_x = -(shift_x % spacing) - spacing

        if chapter != 8:
            truss_y = _clamp(24 - (shift_y % 20), 6, 44)
            pygame.draw.rect(surf, pal["mid"], (0, truss_y, LOGICAL_W, 12))
            pygame.draw.line(surf, pal["edge"], (0, truss_y + 11), (LOGICAL_W, truss_y + 11), 1)
            for tx in range(-(shift_x % 24), LOGICAL_W, 24):
                pygame.draw.line(surf, pal["seam"], (tx, truss_y + 1), (tx + 12, truss_y + 10), 1)
                pygame.draw.line(surf, pal["seam"], (tx + 12, truss_y + 10), (tx + 24, truss_y + 1), 1)

        for sx in range(first_x, LOGICAL_W + spacing, spacing):
            idx = (sx + shift_x) // spacing
            if chapter == 1:
                # Ch 1: Cleanroom buttressed lab stanchions with overhead glass cable trays
                pygame.draw.rect(surf, pal["mid"], (sx, 34, 22, LOGICAL_H - 34))
                pygame.draw.rect(surf, pal["seam"], (sx + 6, 48, 10, LOGICAL_H - 64))
                pygame.draw.line(surf, pal["edge"], (sx + 2, 34), (sx + 2, LOGICAL_H - 34), 1)
                pygame.draw.rect(surf, pal["panel_alt"], (sx + 22, 86, spacing - 22, 8))
            elif chapter == 2:
                # Ch 2: Arched cast-iron foundry ribs & horizontal drive-rod linkages
                pygame.draw.rect(surf, pal["mid"], (sx, 32, 24, LOGICAL_H - 32))
                pygame.draw.polygon(surf, pal["mid"], [
                    (sx + 24, 72), (sx + 56, 36), (sx + 24, 36)
                ])
                pygame.draw.line(surf, pal["edge"], (sx + 24, 72), (sx + 56, 36), 2)
                _draw_segmented_pipe(surf, sx + 24, 134, spacing - 24, 9, pal["panel_alt"], pal["edge"], pal["seam"], 32)
            elif chapter == 3:
                # Ch 3: Porcelain insulator columns & twin HV feeder rails
                pygame.draw.rect(surf, pal["mid"], (sx, 34, 18, LOGICAL_H - 34))
                for iy in range(62, 268, 34):
                    pygame.draw.rect(surf, pal["panel"], (sx - 10, iy, 38, 7))
                    pygame.draw.line(surf, pal["hi"], (sx - 8, iy + 1), (sx + 26, iy + 1), 1)
                if idx % 2 == 0:
                    _draw_segmented_pipe(surf, sx + 18, 118, spacing - 18, 6, pal["mid"], pal["edge"], pal["seam"], 32)
            elif chapter == 4:
                # Ch 4: Angled Panopticon security pylons & suspended camera gantries
                pygame.draw.polygon(surf, pal["mid"], [
                    (sx, 34), (sx + 26, 34), (sx + 18, LOGICAL_H), (sx + 6, LOGICAL_H)
                ])
                pygame.draw.line(surf, pal["edge"], (sx + 2, 34), (sx + 7, LOGICAL_H), 1)
                pygame.draw.rect(surf, pal["recess"], (sx - 8, 96, 42, 14))
                pygame.draw.rect(surf, pal["edge"], (sx - 8, 96, 42, 14), 1)
            elif chapter == 5:
                # Ch 5: Submarine bulkhead ribs with circular pressure-relief valves
                pygame.draw.rect(surf, pal["mid"], (sx, 32, 24, LOGICAL_H - 32))
                pygame.draw.circle(surf, pal["panel"], (sx + 12, 132), 14)
                pygame.draw.circle(surf, pal["edge"], (sx + 12, 132), 14, 2)
                _draw_segmented_pipe(surf, sx + 24, 184, spacing - 24, 12, pal["panel_alt"], pal["edge"], pal["seam"], 36)
            elif chapter == 6:
                # Ch 6: Heavy thermal-baffle columns with chevron brace struts
                pygame.draw.rect(surf, pal["mid"], (sx, 32, 22, LOGICAL_H - 32))
                for cy in range(64, 260, 48):
                    pygame.draw.line(surf, pal["edge"], (sx + 22, cy), (sx + 48, cy + 24), 3)
                    pygame.draw.line(surf, pal["edge"], (sx + 22, cy + 48), (sx + 48, cy + 24), 3)
            elif chapter == 7:
                # Ch 7: Sheared lattice girder columns & diagonal cross-bracing
                pygame.draw.rect(surf, pal["mid"], (sx, 32, 14, LOGICAL_H - 32))
                pygame.draw.line(surf, pal["edge"], (sx + 14, 48), (sx + spacing, 168), 2)
                pygame.draw.line(surf, pal["mid"], (sx + 14, 168), (sx + spacing, 48), 2)
            elif chapter == 8:
                # Ch 8: Exterior ruined transmission towers & catenary cables
                h = 104 + (idx * 29) % 58
                top_y = LOGICAL_H - h
                pygame.draw.rect(surf, pal["mid"], (sx, top_y, 16, h))
                pygame.draw.line(surf, pal["edge"], (sx + 2, top_y), (sx + 2, LOGICAL_H), 1)
                pygame.draw.rect(surf, pal["panel_alt"], (sx - 12, top_y + 14, 40, 5))
                if idx % 2 == 0:
                    pygame.draw.line(surf, pal["mid"], (sx + 8, top_y + 16), (sx + spacing + 8, top_y + 38), 1)

    @staticmethod
    def _draw_progression_detail(
        chunk: pygame.Surface, chapter: int, archetype: str, pal: dict, variant: int
    ) -> None:
        """Restrained pixel-scale wear, corrosion, cracks, and act-specific fixture detail."""
        # Subtle pixel-scale grime/rivet weathering on all acts
        wx = 18 + (variant * 23) % 110
        pygame.draw.rect(chunk, pal["seam"], (wx, 172, 12, 3))
        if archetype == "opening":
            return
        if chapter == 8:
            if archetype == "mid_complex":
                pygame.draw.line(chunk, pal["edge"], (36, 282), (36, 233), 2)
                pygame.draw.line(chunk, pal["mid"], (28, 247), (60, 247), 3)
                pygame.draw.rect(chunk, pal["hi"], (33, 230, 5, 3))
            else:
                pygame.draw.polygon(chunk, pal["seam"], [(74, 303), (90, 265), (111, 271), (118, 303)])
                pygame.draw.line(chunk, pal["edge"], (74, 302), (90, 265), 1)
            return
        if archetype == "mid_complex":
            pygame.draw.rect(chunk, pal["recess"], (66, 18, 51, 12))
            pygame.draw.rect(chunk, pal["edge"], (66, 18, 51, 12), 1)
            for x in (72, 85, 98, 111):
                pygame.draw.rect(chunk, pal["hi"], (x, 22, 3, 3))
            if chapter in (2, 6):
                pygame.draw.line(chunk, pal["edge"], (48, 90), (120, 90), 2)
                pygame.draw.rect(chunk, pal["recess"], (72, 86, 26, 9))
        elif archetype == "late_crisis":
            pygame.draw.lines(chunk, pal["seam"], False, [(89, 42), (82, 57), (96, 70), (85, 86)], 2)
            pygame.draw.lines(chunk, pal["edge"], False, [(90, 42), (83, 57), (97, 70)], 1)
            if chapter in (2, 6):
                pygame.draw.rect(chunk, pal["recess"], (52, 117, 48, 15))
                for y in (120, 124, 128):
                    pygame.draw.line(chunk, pal["edge"], (57, y), (96, y), 1)

    # ------------------------------------------------------------------
    # LAYER 4A: NEAR WORLD-LOCKED MODULAR ARCHITECTURE (Factor 1.00x)
    # ------------------------------------------------------------------
    def _get_near_chunk(self, chapter: int, variant: int, archetype: str) -> pygame.Surface:
        v = variant % 6
        key = (chapter, v, archetype)
        if key in self._chunk_cache:
            return self._chunk_cache[key]

        pal = PALETTES.get(chapter, PALETTES[1])
        chunk = pygame.Surface((CHUNK_W, LOGICAL_H), pygame.SRCALPHA)

        if chapter == 8:
            base_y = 302
            _draw_beveled_panel(
                chunk, pygame.Rect(0, base_y, CHUNK_W, LOGICAL_H - base_y),
                pal["panel"], pal["edge"], pal["seam"], pal["hi"], rivets=True, vertical_ribs=20,
            )
            for bx in range(10, CHUNK_W - 20, 38):
                _draw_beveled_panel(
                    chunk, pygame.Rect(bx, base_y + 10, 30, 26),
                    pal["recess"], pal["edge"], pal["seam"], rivets=False,
                )
            if v in (1, 4):
                pygame.draw.rect(chunk, pal["panel_alt"], (44, base_y - 54, 16, 54))
                pygame.draw.line(chunk, pal["edge"], (45, base_y - 54), (45, base_y), 1)
                pygame.draw.line(chunk, pal["edge"], (52, base_y - 76), (52, base_y - 54), 2)
            elif v in (2, 5):
                pygame.draw.polygon(chunk, pal["panel_alt"], [
                    (88, base_y), (96, base_y - 38), (128, base_y - 26), (138, base_y),
                ])
                pygame.draw.line(chunk, pal["edge"], (88, base_y), (96, base_y - 38), 1)
            self._draw_progression_detail(chunk, chapter, archetype, pal, v)
            self._chunk_cache[key] = chunk
            return chunk

        if chapter == 3:
            _draw_beveled_panel(
                chunk, pygame.Rect(0, 0, CHUNK_W, 42),
                pal["panel"], pal["edge"], pal["seam"], pal["hi"], vertical_ribs=32,
            )
            _draw_beveled_panel(
                chunk, pygame.Rect(0, 306, CHUNK_W, 54),
                pal["panel"], pal["edge"], pal["seam"], pal["hi"], vertical_ribs=32,
            )
            _draw_segmented_pipe(chunk, 0, 32, CHUNK_W, 7, pal["panel_alt"], pal["hi"], pal["seam"], 40)
            _draw_beveled_panel(
                chunk, pygame.Rect(0, 42, 24, 264),
                pal["panel_alt"], pal["edge"], pal["seam"], rivets=True,
            )
            for ly in range(50, 294, 20):
                pygame.draw.line(chunk, pal["seam"], (4, ly), (19, ly + 10), 2)
                pygame.draw.line(chunk, pal["edge"], (4, ly + 1), (19, ly + 11), 1)

            if v in (0, 3):
                # Connected capacitor stack tied into overhead busbar via vertical feeder conduits
                for cx in (42, 82, 122):
                    _draw_vertical_pipe(chunk, cx + 10, 42, 6, 162, pal["mid"], pal["edge"], pal["seam"], 32)
                    _draw_beveled_panel(
                        chunk, pygame.Rect(cx, 204, 26, 102),
                        pal["panel_alt"], pal["edge"], pal["seam"], pal["hi"],
                    )
                    for cy in range(214, 294, 10):
                        pygame.draw.rect(chunk, pal["recess"], (cx + 4, cy, 18, 5))
                        pygame.draw.line(chunk, pal["hi"], (cx + 5, cy + 1), (cx + 20, cy + 1), 1)
            elif v in (1, 4):
                for cx in (48, 104):
                    _draw_beveled_panel(
                        chunk, pygame.Rect(cx, 42, 36, 82),
                        pal["panel_alt"], pal["edge"], pal["seam"], pal["hi"],
                    )
                    pygame.draw.rect(chunk, pal["glass"], (cx + 8, 56, 20, 48))
                    pygame.draw.rect(chunk, pal["edge"], (cx + 8, 56, 20, 48), 1)
                    # Busbar cable drop to floor junction box
                    _draw_vertical_pipe(chunk, cx + 15, 124, 6, 182, pal["recess"], pal["edge"], pal["seam"], 40)
            else:
                _draw_beveled_panel(
                    chunk, pygame.Rect(58, 256, 56, 50),
                    pal["recess"], pal["edge"], pal["seam"],
                )
            self._draw_progression_detail(chunk, chapter, archetype, pal, v)
            self._chunk_cache[key] = chunk
            return chunk

        wall_top = 36
        floor_seam = 308

        if chapter in (1, 4, 5):
            _draw_beveled_panel(
                chunk, pygame.Rect(0, wall_top, CHUNK_W, 114),
                pal["panel"], pal["edge"], pal["seam"], pal["hi"], rivets=True, vertical_ribs=32,
            )
            _draw_beveled_panel(
                chunk, pygame.Rect(0, 164, CHUNK_W, floor_seam - 164),
                pal["panel_alt"], pal["edge"], pal["seam"], pal["edge"], rivets=True, vertical_ribs=32,
            )
        else:
            _draw_beveled_panel(
                chunk, pygame.Rect(0, wall_top, CHUNK_W, 46),
                pal["panel"], pal["edge"], pal["seam"], pal["hi"], vertical_ribs=32,
            )
            _draw_beveled_panel(
                chunk, pygame.Rect(0, floor_seam - 46, CHUNK_W, 46),
                pal["panel_alt"], pal["edge"], pal["seam"], pal["edge"], vertical_ribs=32,
            )
            _draw_beveled_panel(
                chunk, pygame.Rect(0, wall_top + 46, 28, floor_seam - wall_top - 92),
                pal["panel"], pal["edge"], pal["seam"],
            )
            _draw_beveled_panel(
                chunk, pygame.Rect(CHUNK_W - 28, wall_top + 46, 28, floor_seam - wall_top - 92),
                pal["panel"], pal["edge"], pal["seam"],
            )

        _draw_beveled_panel(
            chunk, pygame.Rect(0, 0, CHUNK_W, wall_top),
            pal["recess"], pal["edge"], pal["seam"], pal["hi"], rivets=False,
        )
        _draw_segmented_pipe(chunk, 0, 150, CHUNK_W, 14, pal["recess"], pal["edge"], pal["seam"], 40)
        _draw_beveled_panel(
            chunk, pygame.Rect(0, floor_seam, CHUNK_W, LOGICAL_H - floor_seam),
            pal["recess"], pal["edge"], pal["seam"], pal["hi"], rivets=False,
        )
        for wx in range(8, CHUNK_W - 8, 16):
            pygame.draw.line(chunk, pal["edge"], (wx, floor_seam + 6), (wx + 6, floor_seam + 2), 2)

        if chapter == 1:
            if v in (0, 3):
                win = pygame.Rect(24, 62, 112, 72)
                _draw_beveled_panel(chunk, win, pal["glass"], pal["hi"], pal["seam"], rivets=False)
                # Interior service ladder behind observation glass + silhouetted instruments
                for ly in range(68, 130, 6):
                    pygame.draw.line(chunk, pal["mid"], (116, ly), (126, ly), 1)
                pygame.draw.line(chunk, pal["edge"], (116, 66), (116, 130), 1)
                pygame.draw.line(chunk, pal["edge"], (126, 66), (126, 130), 1)
                pygame.draw.rect(chunk, pal["mid"], (38, 82, 20, 50))
                pygame.draw.line(chunk, pal["edge"], (40, 84), (40, 130), 1)
                pygame.draw.rect(chunk, pal["mid"], (68, 94, 28, 38))
                pygame.draw.rect(chunk, pal["edge"], (72, 98, 20, 12), 1)
                pygame.draw.line(chunk, pal["hi"], (30, 68), (48, 68), 1)
                pygame.draw.line(chunk, pal["hi"], (30, 72), (38, 72), 1)
            elif v in (1, 4):
                _draw_beveled_panel(
                    chunk, pygame.Rect(30, 180, 46, 112),
                    pal["recess"], pal["edge"], pal["seam"],
                )
                # Vertical cable riser connecting server rack to mid-wall raceway
                _draw_vertical_pipe(chunk, 50, 164, 6, 16, pal["panel"], pal["hi"], pal["seam"], 12)
                for ry in range(190, 280, 14):
                    pygame.draw.rect(chunk, pal["panel"], (36, ry, 34, 8))
                    pygame.draw.line(chunk, pal["hi"], (38, ry + 2), (56, ry + 2), 1)
                _draw_beveled_panel(
                    chunk, pygame.Rect(86, 196, 46, 96),
                    pal["panel"], pal["edge"], pal["seam"],
                )
            else:
                _draw_beveled_panel(
                    chunk, pygame.Rect(44, 60, 72, 34),
                    pal["recess"], pal["edge"], pal["seam"], rivets=False,
                )
                for gy in range(66, 90, 5):
                    pygame.draw.line(chunk, pal["edge"], (50, gy), (110, gy), 1)
            if archetype == "late_crisis" and v in (1, 4):
                pygame.draw.line(chunk, pal["seam"], (88, 202), (118, 256), 2)
        elif chapter == 2:
            if v in (0, 2, 4):
                _draw_beveled_panel(
                    chunk, pygame.Rect(36, 82, 88, 30),
                    pal["recess"], pal["edge"], pal["seam"], pal["hi"],
                )
                # Twin vertical drive-shaft housings & lower gearbox plinth (grounded, never floating)
                _draw_vertical_pipe(chunk, 48, 112, 16, 150, pal["panel_alt"], pal["hi"], pal["seam"], 32)
                _draw_vertical_pipe(chunk, 96, 112, 16, 150, pal["panel_alt"], pal["hi"], pal["seam"], 32)
                _draw_beveled_panel(
                    chunk, pygame.Rect(38, 240, 84, 24),
                    pal["recess"], pal["edge"], pal["seam"],
                )
        elif chapter == 4:
            if v in (0, 2, 4):
                win = pygame.Rect(20, 72, 120, 56)
                _draw_beveled_panel(chunk, win, pal["glass"], pal["hi"], pal["seam"], rivets=False)
                for mullion_x in (60, 100):
                    pygame.draw.rect(chunk, pal["seam"], (mullion_x - 2, 72, 4, 56))
                pygame.draw.rect(chunk, pal["mid"], (30, 104, 24, 22))
                pygame.draw.rect(chunk, pal["mid"], (68, 98, 24, 28))
            if v in (1, 3, 5):
                for lx in (24, 64, 104):
                    _draw_beveled_panel(
                        chunk, pygame.Rect(lx, 180, 32, 112),
                        pal["recess"], pal["edge"], pal["seam"],
                    )
                    for slot_y in (192, 198, 204):
                        pygame.draw.line(chunk, pal["edge"], (lx + 6, slot_y), (lx + 25, slot_y), 1)
        elif chapter == 5:
            _draw_segmented_pipe(chunk, 8, 56, CHUNK_W - 16, 16, pal["panel_alt"], pal["hi"], pal["seam"], 36)
            _draw_segmented_pipe(chunk, 8, 82, CHUNK_W - 16, 12, pal["recess"], pal["edge"], pal["seam"], 48)
            if v in (0, 3):
                # Pump housing connected via vertical intake riser to upper pipe manifold
                _draw_vertical_pipe(chunk, 74, 94, 12, 84, pal["panel_alt"], pal["hi"], pal["seam"], 28)
                _draw_beveled_panel(
                    chunk, pygame.Rect(42, 178, 76, 116),
                    pal["recess"], pal["edge"], pal["seam"],
                )
                pygame.draw.circle(chunk, pal["panel"], (80, 224), 20)
                pygame.draw.circle(chunk, pal["hi"], (80, 224), 20, 2)
                pygame.draw.circle(chunk, pal["seam"], (80, 224), 7)
            elif v in (1, 4):
                for px in (46, 98):
                    _draw_vertical_pipe(chunk, px, 94, 18, 214, pal["panel"], pal["hi"], pal["seam"], 36)
        elif chapter == 6:
            if v in (0, 2, 4):
                _draw_beveled_panel(
                    chunk, pygame.Rect(34, 82, 92, 68),
                    pal["recess"], pal["edge"], pal["seam"],
                )
                for ly in range(92, 142, 8):
                    pygame.draw.rect(chunk, pal["glass"], (42, ly, 76, 4))
                # Coolant pipe risers anchoring heat shield to lower bulkhead
                _draw_vertical_pipe(chunk, 44, 150, 10, 112, pal["panel_alt"], pal["hi"], pal["seam"], 28)
                _draw_vertical_pipe(chunk, 106, 150, 10, 112, pal["panel_alt"], pal["hi"], pal["seam"], 28)
        elif chapter == 7:
            if v in (0, 3) or archetype == "late_crisis":
                pygame.draw.line(chunk, pal["seam"], (30, 48), (54, 116), 4)
                pygame.draw.line(chunk, pal["edge"], (31, 48), (55, 116), 1)
                for ry in (64, 84, 102):
                    pygame.draw.line(chunk, pal["hi"], (34, ry), (52, ry + 2), 1)

        self._draw_progression_detail(chunk, chapter, archetype, pal, v)
        self._chunk_cache[key] = chunk
        return chunk

    # ------------------------------------------------------------------
    # LAYER 4B: UPPER-STORY MODULAR BAYS FOR TALL ROOMS (No Floor Seam)
    # ------------------------------------------------------------------
    def _get_upper_chunk(self, chapter: int, variant: int, archetype: str) -> pygame.Surface:
        v = variant % 4
        key = (chapter, v, archetype)
        if key in self._upper_chunk_cache:
            return self._upper_chunk_cache[key]

        pal = PALETTES.get(chapter, PALETTES[1])
        chunk = pygame.Surface((CHUNK_W, LOGICAL_H), pygame.SRCALPHA)

        if chapter == 8:
            # Exterior upper sky bay: ruined vertical radio mast & mountain air
            if v == 1:
                pygame.draw.line(chunk, pal["mid"], (52, 0), (52, LOGICAL_H), 2)
                for y in range(24, LOGICAL_H, 36):
                    pygame.draw.line(chunk, pal["edge"], (46, y), (58, y + 12), 1)
            self._upper_chunk_cache[key] = chunk
            return chunk

        # Interior upper-story structural bay (seamless vertical continuation, no floor curb)
        _draw_beveled_panel(
            chunk, pygame.Rect(0, 0, 22, LOGICAL_H),
            pal["panel_alt"], pal["edge"], pal["seam"], rivets=True,
        )
        _draw_beveled_panel(
            chunk, pygame.Rect(CHUNK_W - 22, 0, 22, LOGICAL_H),
            pal["panel_alt"], pal["edge"], pal["seam"], rivets=True,
        )
        for gy in (72, 192, 312):
            _draw_beveled_panel(
                chunk, pygame.Rect(22, gy, CHUNK_W - 44, 24),
                pal["recess"], pal["edge"], pal["seam"], pal["hi"], vertical_ribs=28,
            )
            _draw_segmented_pipe(chunk, 0, gy + 24, CHUNK_W, 8, pal["panel"], pal["hi"], pal["seam"], 40)

        if chapter in (1, 4, 5) and v in (0, 2):
            _draw_beveled_panel(
                chunk, pygame.Rect(22, 96, CHUNK_W - 44, 96),
                pal["panel"], pal["edge"], pal["seam"], vertical_ribs=32,
            )
            _draw_beveled_panel(
                chunk, pygame.Rect(42, 114, CHUNK_W - 84, 60),
                pal["glass"], pal["hi"], pal["seam"], rivets=False,
            )
        elif chapter == 2 and v in (1, 3):
            _draw_vertical_pipe(chunk, 74, 0, 12, LOGICAL_H, pal["panel_alt"], pal["hi"], pal["seam"], 40)
            _draw_cog(chunk, 80, 144, 24, 8, 0.2, pal["panel"], pal["hi"], pal["seam"])

        self._upper_chunk_cache[key] = chunk
        return chunk

    # ------------------------------------------------------------------
    # LAYER 4C: CO-DESIGNED WORLD-TILE STRUCTURAL SUPPORTS
    # ------------------------------------------------------------------
    def _draw_tile_linked_architecture(
        self, surf: pygame.Surface, chapter: int, cam_lx: int, cam_ly: int
    ) -> None:
        """World-space under-deck trusses, clipped at neighboring terrain below."""
        if not self._world_tiles or chapter == 8:
            return
        pal = PALETTES.get(chapter, PALETTES[1])
        for r in self._world_tiles:
            lw, lh = r.w // SCALE, r.h // SCALE
            if lw < 70 or lh > 90 or r.y < 90:
                continue
            sx, sy = r.x // SCALE - cam_lx, (r.y + r.h) // SCALE - cam_ly
            if sx + lw < -20 or sx > LOGICAL_W + 20 or sy < -40 or sy > LOGICAL_H + 40:
                continue
            clearance_px = 48
            for other in self._world_tiles:
                if other is r:
                    continue
                if other.top >= r.bottom and other.right > r.left + 12 and other.left < r.right - 12:
                    clearance_px = min(clearance_px, other.top - r.bottom)
            if clearance_px < 20:
                continue
            brace_h = min(20, max(0, (clearance_px // SCALE) - 2))
            # This decoration is painted BEHIND actual collision geometry.
            pygame.draw.rect(surf, pal['recess'], (sx + 6, sy, lw - 12, 6))
            pygame.draw.line(surf, pal['edge'], (sx + 6, sy + 5), (sx + lw - 7, sy + 5), 1)
            if brace_h >= 8:
                pygame.draw.line(surf, pal['edge'],
                                 (sx + 10, sy + 6), (sx + 10 + brace_h, sy + 6 + brace_h), 2)
                pygame.draw.line(surf, pal['edge'],
                                 (sx + lw - 10, sy + 6), (sx + lw - 10 - brace_h, sy + 6 + brace_h), 2)

    def _draw_room_dressing(self, surf, chapter, cam_lx, cam_ly, base_ly, world_lw, world_lh):
        """Sparse, world-locked functional silhouette assemblies; entirely Pygame drawn.

        A room's level number and world coordinates choose motifs deterministically.
        No interactive-looking platforms/switches are created here.
        """
        pal = PALETTES[chapter]
        first = max(0, cam_lx // CHUNK_W - 2)
        last = min(world_lw // CHUNK_W + 2, (cam_lx + LOGICAL_W) // CHUNK_W + 2)
        floors = max(1, (world_lh + LOGICAL_H - 1) // LOGICAL_H)
        for tier in range(floors):
            by = base_ly - cam_ly - tier * LOGICAL_H
            if by > LOGICAL_H or by < -LOGICAL_H:
                continue
            for col in range(first, last + 1):
                signature = (col * 17 + self.level_num * 11 + chapter * 29 + tier * 7) % 11
                if signature not in (0, 3, 7):
                    continue  # Preserve most of each room for gameplay readability.
                x = col * CHUNK_W - cam_lx + 27
                y = by + 89
                if x < -120 or x >= LOGICAL_W + 100:
                    continue
                wx_virt = (col * CHUNK_W + 27) * SCALE
                wy_virt = (base_ly - tier * LOGICAL_H + 89) * SCALE
                if self._rect_hits_foreground_tiles(wx_virt, wy_virt,
                                                    100 * SCALE, 129 * SCALE, pad=12):
                    continue
                if chapter == 8:
                    # Sparse ruin shafts stay grounded, not fake floating platforms.
                    ground = by + 303
                    pygame.draw.polygon(surf, pal['mid'], [(x + 13, ground), (x + 20, ground - 87),
                        (x + 38, ground - 84), (x + 40, ground)])
                    pygame.draw.polygon(surf, pal['panel_alt'], [(x + 55, ground), (x + 59, ground - 62),
                        (x + 75, ground - 78), (x + 83, ground)])
                    pygame.draw.line(surf, pal['edge'], (x + 20, ground - 87), (x + 38, ground - 84), 1)
                    pygame.draw.line(surf, pal['edge'], (x + 59, ground - 62), (x + 75, ground - 78), 1)
                    pygame.draw.line(surf, pal['mid'], (x + 29, ground - 89), (x + 29, ground - 125), 2)
                    continue
                # Framed architectural cavity: subdued relative to playable terrain.
                pygame.draw.rect(surf, pal['seam'], (x, y, 100, 129))
                pygame.draw.rect(surf, pal['recess'], (x + 3, y + 3, 94, 123))
                pygame.draw.line(surf, pal['edge'], (x + 5, y + 3), (x + 94, y + 3), 1)
                pygame.draw.rect(surf, pal['panel_alt'], (x + 7, y + 108, 86, 9))
                if chapter == 1:  # Lab observation panel + protected service trunk
                    pygame.draw.rect(surf, pal['glass'], (x + 14, y + 12, 68, 44))
                    pygame.draw.rect(surf, pal['edge'], (x + 14, y + 12, 68, 44), 2)
                    pygame.draw.line(surf, pal['mid'], (x + 48, y + 13), (x + 48, y + 55), 2)
                    for iy in (71, 81, 91):
                        pygame.draw.rect(surf, pal['mid'], (x + 19, y + iy, 57, 4))
                elif chapter == 2:  # Caged drive shaft with axial support
                    pygame.draw.rect(surf, pal['panel'], (x + 45, y + 11, 11, 99))
                    for iy, rad in ((40, 17), (79, 12)):
                        _draw_cog(surf, x + 50, y + iy, rad, 8, 0, pal['panel_alt'], pal['edge'], pal['seam'])
                    pygame.draw.line(surf, pal['edge'], (x + 11, y + 104), (x + 89, y + 104), 2)
                elif chapter == 3:  # Supported transformer and overhead busbar
                    pygame.draw.rect(surf, pal['edge'], (x + 12, y + 13, 76, 6))
                    for ix in (22, 48, 74):
                        pygame.draw.rect(surf, pal['panel'], (x + ix - 8, y + 28, 16, 63))
                        for iy in range(37, 84, 9):
                            pygame.draw.line(surf, pal['edge'], (x + ix - 7, y + iy), (x + ix + 7, y + iy), 1)
                elif chapter == 4:  # Observation grille on mechanical mounts
                    pygame.draw.rect(surf, pal['glass'], (x + 10, y + 17, 80, 66))
                    for ix in (26, 46, 66):
                        pygame.draw.line(surf, pal['mid'], (x + ix, y + 17), (x + ix, y + 83), 3)
                    pygame.draw.rect(surf, pal['edge'], (x + 10, y + 17, 80, 66), 2)
                elif chapter == 5:  # Realistic manifold: header feeds two risers
                    _draw_segmented_pipe(surf, x + 8, y + 24, 84, 11, pal['panel'], pal['edge'], pal['seam'], 33)
                    for ix in (27, 72):
                        pygame.draw.rect(surf, pal['panel'], (x + ix - 5, y + 35, 10, 61))
                        pygame.draw.line(surf, pal['edge'], (x + ix - 3, y + 37), (x + ix - 3, y + 93), 1)
                    pygame.draw.rect(surf, pal['mid'], (x + 12, y + 94, 76, 9))
                elif chapter == 6:  # Containment radiator, insulated vertical tubes
                    pygame.draw.rect(surf, pal['panel'], (x + 12, y + 15, 76, 90))
                    for ix in (23, 36, 49, 62, 75):
                        pygame.draw.rect(surf, pal['glass'], (x + ix, y + 24, 7, 70))
                        pygame.draw.line(surf, pal['edge'], (x + ix, y + 24), (x + ix, y + 94), 1)
                elif chapter == 7:  # Broken bracing, torn upper interior
                    pygame.draw.polygon(surf, pal['mid'], [(x + 8, y + 105), (x + 40, y + 16),
                                       (x + 52, y + 23), (x + 25, y + 106)])
                    pygame.draw.line(surf, pal['edge'], (x + 40, y + 16), (x + 52, y + 23), 2)
                    pygame.draw.line(surf, pal['edge'], (x + 63, y + 7), (x + 83, y + 56), 2)
                else:  # Exterior night ruin: no false walkable platforms
                    pygame.draw.rect(surf, pal['mid'], (x + 14, y + 23, 17, 81))
                    pygame.draw.rect(surf, pal['mid'], (x + 59, y + 14, 20, 91))
                    pygame.draw.line(surf, pal['edge'], (x + 14, y + 23), (x + 31, y + 23), 1)
                    pygame.draw.line(surf, pal['edge'], (x + 59, y + 14), (x + 79, y + 14), 1)

    # ------------------------------------------------------------------
    # HERO LANDMARK: APPEARS ONCE PER ROOM AT FOCUS ANCHOR (320x360)
    # ------------------------------------------------------------------
    def _get_hero_landmark(self, chapter: int, archetype: str) -> pygame.Surface:
        key = (chapter, archetype)
        if key in self._hero_cache:
            return self._hero_cache[key]

        pal = PALETTES.get(chapter, PALETTES[1])
        hero = pygame.Surface((CHUNK_W * 2, LOGICAL_H), pygame.SRCALPHA)
        hero.blit(self._get_near_chunk(chapter, 0, archetype), (0, 0))
        hero.blit(self._get_near_chunk(chapter, 1, archetype), (CHUNK_W, 0))

        cx = CHUNK_W
        if chapter == 1:
            bay = pygame.Rect(cx - 96, 56, 192, 88)
            _draw_beveled_panel(hero, bay, pal["glass"], pal["hi"], pal["seam"], pal["hi"])
            _draw_beveled_panel(
                hero, pygame.Rect(cx - 24, 68, 48, 68),
                pal["mid"], pal["edge"], pal["seam"],
            )
            pygame.draw.rect(hero, pal["accent"], (cx - 12, 82, 24, 32), 1)
            for sx in (cx - 76, cx + 44):
                pygame.draw.rect(hero, pal["mid"], (sx, 80, 32, 56))
                pygame.draw.line(hero, pal["edge"], (sx + 4, 88), (sx + 28, 88), 1)
            _draw_beveled_panel(
                hero, pygame.Rect(cx - 34, 38, 68, 16),
                pal["recess"], pal["hi"], pal["seam"], rivets=False,
            )
            _draw_echo7_pixel_text(hero, cx - 26, 41, pal["accent"])
        elif chapter == 2:
            _draw_beveled_panel(
                hero, pygame.Rect(cx - 76, 64, 152, 210),
                pal["recess"], pal["hi"], pal["seam"],
            )
            # Horizontal axle beam & vertical drive column supporting the triple-cog press
            pygame.draw.rect(hero, pal["panel_alt"], (cx - 70, 148, 140, 12))
            pygame.draw.rect(hero, pal["panel_alt"], (cx - 8, 68, 16, 200))
            _draw_cog(hero, cx, 154, 46, 12, 0.0, pal["panel"], pal["hi"], pal["seam"])
            _draw_cog(hero, cx - 42, 212, 26, 8, 0.4, pal["panel_alt"], pal["edge"], pal["seam"])
            _draw_cog(hero, cx + 42, 212, 26, 8, -0.4, pal["panel_alt"], pal["edge"], pal["seam"])
        elif chapter == 3:
            _draw_beveled_panel(
                hero, pygame.Rect(cx - 68, 58, 136, 224),
                pal["recess"], pal["hi"], pal["seam"],
            )
            for col_x in (cx - 50, cx + 14):
                _draw_beveled_panel(
                    hero, pygame.Rect(col_x, 74, 36, 192),
                    pal["panel"], pal["edge"], pal["seam"],
                )
                for ry in range(86, 250, 18):
                    pygame.draw.rect(hero, pal["glass"], (col_x + 6, ry, 24, 8))
                    pygame.draw.line(hero, pal["hi"], (col_x + 7, ry + 1), (col_x + 28, ry + 1), 1)
        elif chapter == 4:
            _draw_beveled_panel(
                hero, pygame.Rect(cx - 88, 60, 176, 84),
                pal["recess"], pal["hi"], pal["seam"],
            )
            pygame.draw.circle(hero, pal["glass"], (cx, 102), 30)
            pygame.draw.circle(hero, pal["hi"], (cx, 102), 30, 2)
            pygame.draw.circle(hero, pal["seam"], (cx, 102), 14)
            pygame.draw.circle(hero, pal["edge"], (cx, 102), 14, 1)
        elif chapter == 5:
            _draw_beveled_panel(
                hero, pygame.Rect(cx - 84, 104, 168, 168),
                pal["recess"], pal["hi"], pal["seam"],
            )
            pygame.draw.circle(hero, pal["panel"], (cx, 188), 52)
            pygame.draw.circle(hero, pal["hi"], (cx, 188), 52, 3)
            _draw_cog(hero, cx, 188, 32, 8, 0.0, pal["panel_alt"], pal["edge"], pal["seam"])
        elif chapter == 6:
            _draw_beveled_panel(
                hero, pygame.Rect(cx - 64, 42, 128, 264),
                pal["recess"], pal["hi"], pal["seam"],
            )
            pygame.draw.rect(hero, pal["glass"], (cx - 36, 58, 72, 232))
            pygame.draw.rect(hero, (132, 52, 28), (cx - 18, 62, 36, 224))
            for ry in range(72, 276, 28):
                _draw_beveled_panel(
                    hero, pygame.Rect(cx - 52, ry, 104, 12),
                    pal["panel"], pal["hi"], pal["seam"],
                )
        elif chapter == 7:
            _draw_beveled_panel(
                hero, pygame.Rect(cx - 82, 52, 164, 214),
                pal["recess"], pal["edge"], pal["seam"],
            )
            pygame.draw.polygon(hero, (48, 30, 62), [
                (cx - 66, 62), (cx + 68, 62), (cx + 48, 252), (cx - 52, 242),
            ])
            pygame.draw.line(hero, pal["hi"], (cx - 66, 62), (cx - 52, 242), 2)
            pygame.draw.line(hero, pal["hi"], (cx + 68, 62), (cx + 48, 252), 2)
            _draw_beveled_panel(
                hero, pygame.Rect(cx - 14, 52, 28, 86),
                pal["panel"], pal["hi"], pal["seam"],
            )
            _draw_beveled_panel(
                hero, pygame.Rect(cx - 14, 186, 28, 80),
                pal["panel"], pal["hi"], pal["seam"],
            )
            for ry in range(140, 184, 8):
                pygame.draw.line(hero, pal["edge"], (cx - 8, ry), (cx + 8, ry + 4), 1)
        elif chapter == 8:
            pygame.draw.polygon(hero, pal["panel"], [
                (cx - 52, 302), (cx - 18, 198), (cx + 18, 198), (cx + 52, 302),
            ])
            pygame.draw.line(hero, pal["hi"], (cx - 52, 302), (cx - 18, 198), 2)
            pygame.draw.arc(hero, pal["hi"], (cx - 68, 138, 136, 84), 0.25, math.pi - 0.25, 3)
            pygame.draw.line(hero, pal["edge"], (cx, 180), (cx, 132), 2)

        self._hero_cache[key] = hero
        return hero

    # ------------------------------------------------------------------
    # LAYER 5: STEPPED PIXEL LIGHTING & LOCAL SIGNAL AMBIENT ANIMATION
    # ------------------------------------------------------------------
    def _draw_ambient_fx(
        self,
        surf: pygame.Surface,
        chapter: int,
        cam_lx: int,
        cam_ly: int,
        base_ly: int,
        world_lw: int,
        elapsed: float,
        reduced_motion: bool,
        powered: bool,
    ) -> None:
        pal = PALETTES.get(chapter, PALETTES[1])
        first_col = max(0, (cam_lx // CHUNK_W) - 1)
        last_col = min(world_lw // CHUNK_W + 1, (cam_lx + LOGICAL_W) // CHUNK_W + 1)

        for col in range(first_col, last_col + 1):
            if col % 2 == 1:
                continue
            wx = col * CHUNK_W + 80
            wy = base_ly + (114 if chapter != 8 else 242)
            local_on = self._is_bay_locally_powered(wx * SCALE, wy * SCALE, powered)
            active_col = pal["accent"] if local_on else pal["warn"]

            # Draw vertical feeder riser connecting background raceway to any puzzle node in this column
            for nx, ny, node_on, _kind in self._local_nodes:
                nlx, nly = nx // SCALE, ny // SCALE
                if col * CHUNK_W <= nlx < (col + 1) * CHUNK_W:
                    nsx, nsy = nlx - cam_lx, nly - cam_ly
                    raceway_sy = base_ly - cam_ly + 156
                    if -20 <= nsx < LOGICAL_W + 20:
                        riser_col = pal["accent"] if node_on else pal["edge"]
                        pygame.draw.line(surf, pal["seam"], (nsx, nsy), (nsx, raceway_sy), 4)
                        pygame.draw.line(surf, riser_col, (nsx, nsy), (nsx, raceway_sy), 2)

            sx = wx - cam_lx
            sy = wy - cam_ly
            if not (-40 <= sx < LOGICAL_W + 40 and -40 <= sy < LOGICAL_H + 40):
                continue

            pulse = True if reduced_motion else (math.sin(elapsed * 2.0 + col * 1.1) > -0.25)

            if chapter == 1:
                pygame.draw.circle(surf, pal["seam"], (sx, sy - 34), 10)
                pygame.draw.circle(surf, pal["edge"], (sx, sy - 34), 10, 1)
                step_ang = 0.0 if reduced_motion else (int(elapsed * 3.5 + col) % 8) * (math.pi / 4)
                for b in range(2):
                    a = step_ang + b * (math.pi / 2)
                    dx, dy = int(8 * math.cos(a)), int(8 * math.sin(a))
                    pygame.draw.line(surf, pal["hi"], (sx - dx, sy - 34 - dy), (sx + dx, sy - 34 + dy), 2)
                pygame.draw.rect(surf, pal["seam"], (sx - 14, sy + 12, 28, 12))
                pygame.draw.rect(surf, pal["edge"], (sx - 14, sy + 12, 28, 12), 1)
                wave_x = 0 if reduced_motion else int(elapsed * 12 + col * 5) % 20
                pygame.draw.line(surf, active_col, (sx - 12, sy + 18), (sx + 11, sy + 18), 1)
                pygame.draw.rect(surf, active_col, (sx - 10 + wave_x, sy + 15, 2, 6))
            elif chapter == 2:
                step_ang = 0.0 if reduced_motion else (int(elapsed * 4.0 + col) % 12) * (math.pi / 6)
                _draw_cog(surf, sx, sy, 14, 8, step_ang, pal["panel"], pal["hi"], pal["seam"])
                stroke = 0 if reduced_motion else int(7 * math.sin(elapsed * 2.6 + col))
                pygame.draw.rect(surf, pal["seam"], (sx + 22, sy - 14, 10, 28))
                pygame.draw.rect(surf, active_col, (sx + 23, sy - 6 + stroke, 8, 12))
            elif chapter == 3:
                pygame.draw.rect(surf, pal["edge"], (sx - 16, sy - 12, 32, 24), 1)
                if pulse:
                    rise = 0 if reduced_motion else int((elapsed * 18 + col * 7) % 16)
                    ay = sy + 6 - rise
                    jit = 0 if reduced_motion else int(2 * math.sin(elapsed * 11.0 + col))
                    pygame.draw.lines(surf, active_col, False, [
                        (sx - 12, ay), (sx - 4, ay - 2 + jit), (sx + 4, ay + 2 - jit), (sx + 12, ay),
                    ], 1)
                px_off = 0 if reduced_motion else int((elapsed * 45 + col * 23) % CHUNK_W) - 80
                pygame.draw.rect(surf, active_col, (sx + px_off, base_ly - cam_ly + 155, 8, 3))
            elif chapter == 4:
                pan = 0 if reduced_motion else int(4 * math.sin(elapsed * 1.2 + col))
                _draw_beveled_panel(
                    surf, pygame.Rect(sx - 10 + pan, sy - 6, 20, 10),
                    pal["recess"], pal["edge"], pal["seam"], rivets=False,
                )
                pygame.draw.rect(surf, active_col if pulse else pal["edge"], (sx + 5 + pan, sy - 3, 3, 4))
            elif chapter == 5:
                pygame.draw.circle(surf, pal["seam"], (sx, sy - 18), 8)
                pygame.draw.circle(surf, pal["hi"], (sx, sy - 18), 8, 1)
                ang = -0.8 if not local_on else 0.8
                if not reduced_motion:
                    ang += 0.25 * math.sin(elapsed * 2.2 + col)
                pygame.draw.line(
                    surf, active_col, (sx, sy - 18),
                    (sx + int(6 * math.cos(ang)), sy - 18 + int(6 * math.sin(ang))), 1,
                )
                if not reduced_motion:
                    drop_y = int((elapsed * 26 + col * 19) % 46)
                    pygame.draw.rect(surf, pal["accent"], (sx, sy + drop_y, 2, 3))
            elif chapter == 6:
                col_heat = pal["accent"] if pulse else pal["warn"]
                pygame.draw.rect(surf, col_heat, (sx - 10, sy - 14, 20, 26), 1)
                if not reduced_motion:
                    for e_idx in range(3):
                        ey = int((elapsed * (20 + e_idx * 5) + col * 17 + e_idx * 13) % 52)
                        pygame.draw.rect(surf, pal["accent"], (sx - 5 + e_idx * 5, sy + 14 - ey, 2, 2))
            elif chapter == 7:
                sway = 0 if reduced_motion else int(5 * math.sin(elapsed * 1.8 + col))
                pygame.draw.lines(surf, pal["edge"], False, [
                    (sx, sy - 42), (sx + sway // 2, sy - 24), (sx + sway, sy - 6),
                ], 2)
                if pulse:
                    pygame.draw.rect(surf, active_col, (sx + sway - 1, sy - 6, 3, 3))
            elif chapter == 8:
                pygame.draw.rect(surf, active_col if pulse else pal["edge"], (sx, sy - 38, 3, 3))
                if not reduced_motion:
                    cloud_x = int((elapsed * 6 + col * 37) % 120) - 60
                    pygame.draw.rect(surf, pal["mid"], (sx + cloud_x, 42 + (col % 3) * 14, 28, 3))

    def _draw_chapter_signature_fx(
        self, surf: pygame.Surface, chapter: int, cam_lx: int, cam_ly: int,
        world_lw: int, world_lh: int, elapsed: float, reduced_motion: bool,
    ) -> None:
        """Distinctive world-anchored atmospheric pixels for each chapter.

        Sparse, low-brightness and non-colliding by construction. The main player,
        hazards, doors and switches are rendered AFTER this background layer.
        Reduced-motion mode freezes every moving effect.
        """
        pal = PALETTES[chapter]
        t = 0.0 if reduced_motion else elapsed
        spacing = CHUNK_W * 3
        first = max(0, cam_lx // spacing - 1)
        last = min(world_lw // spacing + 1, (cam_lx + LOGICAL_W) // spacing + 1)
        y_base = max(0, world_lh - LOGICAL_H) - cam_ly
        for cell in range(first, last + 1):
            # Fully deterministic positions derived from the current world cell.
            x = cell * spacing + (113 + chapter * 23) % 202 - cam_lx
            y = y_base + 88 + (cell * 37 + chapter * 17) % 97
            if not (-60 < x < LOGICAL_W + 60 and -50 < y < LOGICAL_H + 50):
                continue
            phase = int(t * (10 + chapter * 2) + cell * 7) % 30
            if chapter == 1:
                # Diagnostic waveform on wall glass, bounded to one tiny panel.
                pygame.draw.rect(surf, pal["recess"], (x - 19, y - 8, 38, 14))
                pygame.draw.line(surf, pal["edge"], (x - 18, y + 5), (x + 18, y + 5), 1)
                for i in range(7):
                    px = x - 15 + i * 5
                    py = y - 1 + int(3 * math.sin(i + phase * 0.2))
                    pygame.draw.rect(surf, pal["accent"], (px, py, 2, 2))
            elif chapter == 2:
                # Heat haze and slow mechanical piston pressure strokes.
                for i in range(3):
                    py = y - 6 - ((phase + i * 9) % 22)
                    pygame.draw.line(surf, pal["edge"], (x - 6 + i * 6, py), (x - 3 + i * 6, py - 3), 1)
                pygame.draw.rect(surf, pal["warn"], (x - 11, y + 4, 22, 2))
            elif chapter == 3:
                # Compact electrical corona between two fixed insulators.
                pygame.draw.circle(surf, pal["edge"], (x - 14, y), 3, 1)
                pygame.draw.circle(surf, pal["edge"], (x + 14, y), 3, 1)
                if phase < 21:
                    pygame.draw.lines(surf, pal["accent"], False,
                                      [(x - 11, y), (x - 4, y - 4 + phase % 3),
                                       (x + 3, y + 3 - phase % 4), (x + 11, y)], 1)
            elif chapter == 4:
                # Short surveillance scanner sweep inside a dark viewport.
                pygame.draw.rect(surf, pal["seam"], (x - 18, y - 8, 36, 15))
                pygame.draw.rect(surf, pal["edge"], (x - 18, y - 8, 36, 15), 1)
                pygame.draw.line(surf, pal["accent"], (x - 15 + phase, y - 6),
                                 (x - 15 + phase, y + 4), 1)
            elif chapter == 5:
                # Pressure gauge needle and isolated condensation, not fake pools.
                pygame.draw.circle(surf, pal["edge"], (x, y), 9, 1)
                angle = (phase - 15) * 0.05
                pygame.draw.line(surf, pal["accent"], (x, y),
                                 (x + int(math.sin(angle) * 7), y - int(math.cos(angle) * 7)), 1)
                pygame.draw.rect(surf, pal["mid"], (x + 16, y - phase, 2, 3))
            elif chapter == 6:
                # Suspended hot embers and periodic radiator flicker.
                for i in range(4):
                    ex = x - 14 + i * 9
                    ey = y - ((phase * 2 + i * 11) % 38)
                    pygame.draw.rect(surf, pal["warn"] if i % 2 else pal["accent"], (ex, ey, 2, 2))
                pygame.draw.rect(surf, pal["edge"], (x - 13, y + 7, 26, 2))
            elif chapter == 7:
                # Tiny drifting dust from exposed cracked interior trusses.
                for i in range(4):
                    dx = ((phase // 2 + i * 11) % 27) - 13
                    dy = ((phase + i * 7) % 29) - 18
                    pygame.draw.rect(surf, pal["hi"] if i == 0 else pal["edge"],
                                     (x + dx, y + dy, 1, 2))
            else:
                # Moonlit night wind carrying isolated motes, no false platforms.
                for i in range(4):
                    dx = (phase + i * 27) % 76 - 38
                    dy = -26 + i * 11
                    pygame.draw.line(surf, pal["edge"], (x + dx, y + dy),
                                     (x + dx + 5, y + dy), 1)
                if cell % 2 == 0:
                    pygame.draw.rect(surf, pal["accent"], (x + 20, y - 38, 1, 1))

    # ------------------------------------------------------------------
    # COMPOSITE DRAW ENTRY POINT
    # ------------------------------------------------------------------
    def draw(
        self,
        target: pygame.Surface,
        chapter: int,
        camera_x: float,
        camera_y: float,
        elapsed: float,
        level_width: int,
        level_height: int,
        reduced_motion: bool = False,
        powered: bool = False,
    ) -> None:
        ch = max(1, min(8, int(chapter)))
        archetype = archetype_for_level(self.level_num)
        work = self._get_work_surface()

        cam_lx = int(round(camera_x / SCALE))
        cam_ly = int(round(camera_y / SCALE))
        world_lw = max(LOGICAL_W, int(level_width) // SCALE)
        world_lh = max(LOGICAL_H, int(level_height) // SCALE)
        base_ly = max(0, world_lh - LOGICAL_H)

        far_strip = self._build_far_strip(ch, archetype)
        far_ox = -(int(round(cam_lx * 0.16)) % LOGICAL_W)
        work.blit(far_strip, (far_ox, 0))

        self._draw_mid_plane(work, ch, archetype, cam_lx, cam_ly, elapsed)

        first_col = max(0, (cam_lx // CHUNK_W) - 1)
        last_col = min(world_lw // CHUNK_W + 1, (cam_lx + LOGICAL_W) // CHUNK_W + 1)
        hero_col = max(0, (self.focus[0] // SCALE) // CHUNK_W)

        for col in range(first_col, last_col + 1):
            wx = col * CHUNK_W
            sx = wx - cam_lx
            sy = base_ly - cam_ly
            variant = (col * 5 + ch * 3 + (self.level_num % 3)) % 6
            chunk = self._get_near_chunk(ch, variant, archetype)
            work.blit(chunk, (sx, sy))

            # Multi-story vertical bay tiling above `base_ly` in tall rooms (never repeats floor curb)
            upper_y = sy - LOGICAL_H
            tier = 1
            while upper_y + LOGICAL_H > 0:
                u_chunk = self._get_upper_chunk(ch, variant + tier, archetype)
                work.blit(u_chunk, (sx, upper_y))
                upper_y -= LOGICAL_H
                tier += 1

        hero_sx = hero_col * CHUNK_W - cam_lx
        hero_sy = base_ly - cam_ly
        if -CHUNK_W * 2 <= hero_sx <= LOGICAL_W:
            work.blit(self._get_hero_landmark(ch, archetype), (hero_sx, hero_sy))

        # Co-designed world-tile under-deck trusses & supports
        self._draw_room_dressing(work, ch, cam_lx, cam_ly, base_ly, world_lw, world_lh)
        self._draw_tile_linked_architecture(work, ch, cam_lx, cam_ly)

        self._draw_ambient_fx(
            work, ch, cam_lx, cam_ly, base_ly, world_lw, elapsed, reduced_motion, powered
        )
        self._draw_chapter_signature_fx(
            work, ch, cam_lx, cam_ly, world_lw, world_lh, elapsed, reduced_motion
        )
        draw_level_specific_fx(
            work, self.level_num, ch, PALETTES.get(ch, PALETTES[1]),
            cam_lx, cam_ly, base_ly, world_lw, world_lh,
            elapsed, reduced_motion, powered, self._world_tiles,
            self._active_signals,
        )

        pygame.transform.scale(work, (VIRTUAL_WIDTH, VIRTUAL_HEIGHT), target)
