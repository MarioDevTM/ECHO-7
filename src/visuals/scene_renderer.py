"""World-anchored procedural pixel-art scene & neighbor-aware auto-tiled terrain renderer for ECHO-7.

Implements:
1. Neighbor-aware interval auto-tiling for solid `tiles` (distinguishes exposed top walkable
   decks, underside ceiling soffits, left/right vertical wall faces, convex/concave corners,
   and embedded load-bearing interiors without false internal deck seams).
2. Chapter-specific structural surface treatments across all 8 chapters.
3. Full integration with `PixelEnvironment` including local puzzle signal feedback.
"""
from __future__ import annotations
from pathlib import Path
import math
import pygame
from src.visuals.pixel_environment import PixelEnvironment
from src.visuals.world_dressing import load_world_dressing, placements_for_level, anchor_for
from src.core.settings import VIRTUAL_WIDTH, VIRTUAL_HEIGHT, CHAPTER_THEMES
from src.visuals import get_env_sprite

THEME_NUM = {
    "awakening": 1,
    "mechanical": 2,
    "power": 3,
    "optical": 4,
    "environmental": 5,
    "furnace": 6,
    "spire": 7,
    "surface": 8,
    "core": 4,
}
ACCENT = {
    "awakening": (75, 212, 225),
    "mechanical": (253, 170, 73),
    "power": (78, 192, 255),
    "optical": (209, 106, 244),
    "environmental": (73, 222, 213),
    "furnace": (255, 145, 67),
    "spire": (255, 110, 124),
    "surface": (115, 219, 250),
    "core": (209, 106, 244),
}
INK = (6, 15, 30)


def _subtract_intervals(
    base_start: int, base_end: int, covers: list[tuple[int, int]]
) -> list[tuple[int, int]]:
    """Returns uncovered 1D sub-segments of [base_start, base_end] after subtracting `covers`."""
    segs = [(base_start, base_end)]
    for c0, c1 in covers:
        if c1 <= c0:
            continue
        next_segs: list[tuple[int, int]] = []
        for s0, s1 in segs:
            if c1 <= s0 or c0 >= s1:
                next_segs.append((s0, s1))
            else:
                if c0 > s0:
                    next_segs.append((s0, c0))
                if c1 < s1:
                    next_segs.append((c1, s1))
        segs = next_segs
        if not segs:
            break
    return [(a, b) for a, b in segs if b - a >= 2]


class SceneRenderer:
    def __init__(self):
        self.pixel_environment = PixelEnvironment()
        self._backgrounds = {}
        self._chapter_thumbs = {}
        self._rotor_frames = {}
        self._menu_tint = None
        self._glow_cache = {}
        self._active_variation = 0
        self._room_num = 1
        self._reduced_motion = False
        self._world_dressing = load_world_dressing()
        self._original_menu_backgrounds = {}
        self._terrain_sprite_sets = {}
        self._solid_deck_sprite = None
        self._world_tiles: list[pygame.Rect] = []
        self._edge_cache: dict[tuple[int, int, int, int], dict[str, list[tuple[int, int]]]] = {}

    def set_level_context(self, level_num: int) -> None:
        """Compatibility with LevelManager: set current room before focus/preview."""
        self._room_num = max(1, int(level_num))
        self.pixel_environment.set_level(self._room_num)

    def set_level_focus(self, world_x: int, world_y: int, level_num: int | None = None) -> None:
        """Set the camera's visual focus without resetting the active room to Level 1.

        LevelManager first calls set_level_context(actual_level), then set_level_focus(x, y).
        The default here must preserve that level; earlier default level_num=1 caused
        all of the level-specific effects to use the wrong profile on game entry.
        """
        if level_num is not None:
            self._room_num = max(1, int(level_num))
        self.pixel_environment.set_focus(world_x, world_y, level_num=self._room_num)

    def set_level_tiles(self, tiles: list[pygame.Rect]) -> None:
        """Caches world-space solid tiles and precomputes exposed edge intervals for auto-tiling."""
        self._world_tiles = list(tiles)
        self._edge_cache.clear()
        self.pixel_environment.set_world_tiles(self._world_tiles)
        tol = 2
        for r in self._world_tiles:
            key = (r.x, r.y, r.w, r.h)
            top_cov: list[tuple[int, int]] = []
            bot_cov: list[tuple[int, int]] = []
            left_cov: list[tuple[int, int]] = []
            right_cov: list[tuple[int, int]] = []
            for o in self._world_tiles:
                if o is r:
                    continue
                # Top edge covered if `o` touches or overlaps `r.top` from above
                if o.top < r.top + tol and o.bottom >= r.top - tol and o.right > r.left and o.left < r.right:
                    top_cov.append((max(r.left, o.left), min(r.right, o.right)))
                # Bottom edge covered if `o` touches or overlaps `r.bottom` from below
                if o.bottom > r.bottom - tol and o.top <= r.bottom + tol and o.right > r.left and o.left < r.right:
                    bot_cov.append((max(r.left, o.left), min(r.right, o.right)))
                # Left edge covered if `o` touches or overlaps `r.left` from the left
                if o.left < r.left + tol and o.right >= r.left - tol and o.bottom > r.top and o.top < r.bottom:
                    left_cov.append((max(r.top, o.top), min(r.bottom, o.bottom)))
                # Right edge covered if `o` touches or overlaps `r.right` from the right
                if o.right > r.right - tol and o.left <= r.right + tol and o.bottom > r.top and o.top < r.bottom:
                    right_cov.append((max(r.top, o.top), min(r.bottom, o.bottom)))

            self._edge_cache[key] = {
                "top": _subtract_intervals(r.left, r.right, top_cov),
                "bottom": _subtract_intervals(r.left, r.right, bot_cov),
                "left": _subtract_intervals(r.top, r.bottom, left_cov),
                "right": _subtract_intervals(r.top, r.bottom, right_cov),
            }

    def get_env_sprite(self, name: str, scale_size=None):
        return get_env_sprite(name, scale_size)

    def _get_rotor_frame(self, name: str, angle_deg: float):
        step_deg = (int(angle_deg // 15) * 15) % 360
        key = (name, step_deg)
        if key not in self._rotor_frames:
            base = get_env_sprite(name)
            self._rotor_frames[key] = None if base is None else pygame.transform.rotate(base, step_deg)
        return self._rotor_frames[key]

    def _background(self, theme: str, variation: int = 0):
        theme = theme if theme in THEME_NUM else "awakening"
        if theme not in self._backgrounds:
            ch = THEME_NUM[theme]
            surf = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT))
            prev_focus = self.pixel_environment.focus
            prev_lvl = self.pixel_environment.level_num
            self.pixel_environment.set_focus(
                VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT // 2, level_num=(ch - 1) * 10 + 1
            )
            self.pixel_environment.menu_background(surf, ch, elapsed=0.0)
            self.pixel_environment.set_focus(prev_focus[0], prev_focus[1], level_num=prev_lvl)
            self._backgrounds[theme] = surf
        return self._backgrounds[theme]

    def get_chapter_preview(self, chapter: int, size: tuple[int, int] = (220, 124)):
        ch = max(1, min(8, int(chapter)))
        key = (ch, size)
        if key not in self._chapter_thumbs:
            themes = [
                "awakening", "mechanical", "power", "optical",
                "environmental", "furnace", "spire", "surface",
            ]
            base = self._background(themes[ch - 1])
            self._chapter_thumbs[key] = pygame.transform.scale(base, size)
        return self._chapter_thumbs[key]

    def _draw_quantized_glow(self, surface, cx, cy, radius, color, max_alpha=48):
        key = (int(radius), tuple(color), int(max_alpha))
        if key not in self._glow_cache:
            size = radius * 2 + 4
            glow_surf = pygame.Surface((size, size), pygame.SRCALPHA)
            center = (size // 2, size // 2)
            for frac, a_scale in ((1.0, 0.25), (0.68, 0.52), (0.38, 1.0)):
                r = max(2, int(radius * frac))
                a = max(4, min(255, int(max_alpha * a_scale)))
                pygame.draw.circle(glow_surf, (*color, a), center, r)
            self._glow_cache[key] = glow_surf
        g = self._glow_cache[key]
        surface.blit(g, (int(cx) - g.get_width() // 2, int(cy) - g.get_height() // 2))

    def draw_background(
        self,
        surface,
        theme,
        camera_x=0,
        camera_y=0,
        elapsed=0.0,
        level_width=VIRTUAL_WIDTH,
        level_height=VIRTUAL_HEIGHT,
        powered=False,
        signals=None,
    ):
        ch = THEME_NUM.get(theme, 1)
        self.pixel_environment.level_num = self._room_num
        self.pixel_environment.draw(
            surface, ch, camera_x, camera_y,
            elapsed, level_width, level_height,
            self._reduced_motion, powered=powered or bool(signals),
        )

    def draw_menu_background(self, surface, chapter=1):
        themes = [
            "awakening", "mechanical", "power", "optical",
            "environmental", "furnace", "spire", "surface",
        ]
        theme = themes[max(0, min(7, chapter - 1))]
        self._active_variation = 0
        if theme not in self._original_menu_backgrounds:
            self._original_menu_backgrounds[theme] = self._background(theme)
        surface.blit(self._original_menu_backgrounds[theme], (0, 0))
        if self._menu_tint is None:
            self._menu_tint = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.SRCALPHA)
            self._menu_tint.fill((4, 9, 20, 148))
        surface.blit(self._menu_tint, (0, 0))
        c = ACCENT[theme]
        pygame.draw.line(surface, c, (20, 10), (VIRTUAL_WIDTH - 20, 10), 2)
        pygame.draw.line(surface, c, (20, VIRTUAL_HEIGHT - 10), (VIRTUAL_WIDTH - 20, VIRTUAL_HEIGHT - 10), 1)

    def draw_platform(self, surface, rect, theme, camera_offset=(0, 0), world_rect=None):
        """Neighbor-aware auto-tiling for solid ground, walls, piers, ceilings, and corbels."""
        if rect.width <= 0 or rect.height <= 0 or not rect.colliderect(surface.get_rect()):
            return
        t = CHAPTER_THEMES.get(theme, CHAPTER_THEMES["awakening"])
        col, edge = t["tile_main"], t["tile_border"]
        a = ACCENT.get(theme, ACCENT["awakening"])
        cx, cy = int(camera_offset[0]), int(camera_offset[1])

        if world_rect is None:
            world_rect = pygame.Rect(rect.x + cx, rect.y + cy, rect.w, rect.h)
        wkey = (world_rect.x, world_rect.y, world_rect.w, world_rect.h)
        edges = self._edge_cache.get(wkey)
        if edges is None:
            edges = {
                "top": [(world_rect.left, world_rect.right)],
                "bottom": [(world_rect.left, world_rect.right)],
                "left": [(world_rect.top, world_rect.bottom)],
                "right": [(world_rect.top, world_rect.bottom)],
            }

        # 1. Base structural fill
        pygame.draw.rect(surface, col, rect)
        prev = surface.get_clip()
        visible = rect.clip(surface.get_rect())
        if visible.width > 0 and visible.height > 0:
            surface.set_clip(prev.clip(visible))
            wall_name = (
                "terrain_wall_tile_panel"
                if theme in ("optical", "power")
                else "terrain_wall_tile_steel"
            )
            wall_variants = self._terrain_sprite_sets.get(wall_name)
            if wall_variants is None:
                wall_variants = tuple(
                    get_env_sprite(wall_name + suffix) for suffix in ("", "_v1", "_v2")
                )
                self._terrain_sprite_sets[wall_name] = wall_variants
            if wall_variants[0] is not None and rect.height >= 16:
                for ty in range(((visible.top + cy) // 40) * 40 - cy, visible.bottom, 40):
                    for tx in range(((visible.left + cx) // 40) * 40 - cx, visible.right, 40):
                        wx, wy = (tx + cx) // 40, (ty + cy) // 40
                        signature = (wx * 71 + wy * 43 + wx * wy * 3) % 29
                        variant = 1 if signature in (3, 11, 23) else (2 if signature in (9, 18) else 0)
                        surface.blit(wall_variants[variant] or wall_variants[0], (tx, ty))

            # Chapter-specific large-scale structural ribs / rock strata inside thick solid masses
            if theme == "surface" and rect.height >= 28:
                strata_col = (max(0, col[0] - 10), max(0, col[1] - 10), max(0, col[2] - 8))
                for sy in range(((visible.top + cy) // 24) * 24 - cy, visible.bottom, 24):
                    pygame.draw.line(surface, strata_col, (visible.left, sy), (visible.right, sy), 2)
            elif rect.width >= 32 and rect.height >= 48 and not edges["top"]:
                # Load-bearing vertical pier / support column cross-bracing
                rib_col = (max(0, col[0] - 12), max(0, col[1] - 12), max(0, col[2] - 12))
                for sy in range(((visible.top + cy) // 40) * 40 - cy, visible.bottom, 40):
                    pygame.draw.line(surface, rib_col, (rect.left + 4, sy), (rect.right - 5, sy), 2)
                    pygame.draw.line(surface, edge, (rect.left + 4, sy + 2), (rect.right - 5, sy + 2), 1)

            # 2. Walkable top deck cap ONLY on exposed top intervals (never inside wall/pier seams!)
            if self._solid_deck_sprite is None:
                self._solid_deck_sprite = get_env_sprite("platform_solid_long")
            deck = self._solid_deck_sprite
            for wx0, wx1 in edges["top"]:
                sx0, sx1 = wx0 - cx, wx1 - cx
                seg_w = sx1 - sx0
                if seg_w < 6:
                    continue
                if deck is not None and rect.height >= 14:
                    depth = min(rect.height, 20, deck.get_height())
                    cap = min(14, seg_w // 3, deck.get_width() // 5)
                    if cap > 0 and depth > 0:
                        y = rect.top
                        surface.blit(deck, (sx0, y), pygame.Rect(0, 0, cap, depth))
                        surface.blit(
                            deck,
                            (sx1 - cap, y),
                            pygame.Rect(deck.get_width() - cap, 0, cap, depth),
                        )
                        center_w = min(42, deck.get_width() - cap * 2)
                        center_start = sx0 + cap
                        x = max(center_start, 0)
                        end = min(sx1 - cap, VIRTUAL_WIDTH)
                        while center_w > 0 and x < end:
                            phase = (x - center_start) % center_w
                            n = min(center_w - phase, end - x)
                            source_x = (deck.get_width() - center_w) // 2 + phase
                            surface.blit(deck, (x, y), pygame.Rect(source_x, 0, n, depth))
                            x += n
                # Crisp walkable top border + chapter accent line only on exposed walkable segments
                pygame.draw.line(surface, INK, (sx0, rect.top), (sx1 - 1, rect.top), 2)
                if rect.height >= 8 and seg_w >= 8:
                    pygame.draw.line(surface, a, (sx0 + 2, rect.top + 2), (sx1 - 3, rect.top + 2), 1)

            # 3. Exposed underside ceiling / overhang soffit trim
            soffit_col = (max(0, col[0] - 16), max(0, col[1] - 16), max(0, col[2] - 16))
            for wx0, wx1 in edges["bottom"]:
                sx0, sx1 = wx0 - cx, wx1 - cx
                if sx1 - sx0 < 4:
                    continue
                if rect.height >= 12:
                    pygame.draw.rect(surface, soffit_col, (sx0, rect.bottom - 5, sx1 - sx0, 4))
                    pygame.draw.line(surface, edge, (sx0 + 2, rect.bottom - 3), (sx1 - 3, rect.bottom - 3), 1)
                pygame.draw.line(surface, INK, (sx0, rect.bottom - 1), (sx1 - 1, rect.bottom - 1), 2)

            # 4. Exposed vertical left and right wall faces
            for wy0, wy1 in edges["left"]:
                sy0, sy1 = wy0 - cy, wy1 - cy
                if sy1 - sy0 < 4:
                    continue
                pygame.draw.line(surface, edge, (rect.left + 2, sy0 + 2), (rect.left + 2, sy1 - 3), 1)
                pygame.draw.line(surface, INK, (rect.left, sy0), (rect.left, sy1 - 1), 2)

            for wy0, wy1 in edges["right"]:
                sy0, sy1 = wy0 - cy, wy1 - cy
                if sy1 - sy0 < 4:
                    continue
                pygame.draw.line(surface, edge, (rect.right - 3, sy0 + 2), (rect.right - 3, sy1 - 3), 1)
                pygame.draw.line(surface, INK, (rect.right - 1, sy0), (rect.right - 1, sy1 - 1), 2)

        surface.set_clip(prev)

    def draw_exit(self, surface, rect, theme, clock, *, locked=False):
        c = ACCENT.get(theme, (80, 220, 255))
        x, y, w, h = rect
        if w <= 5 or h <= 5:
            return
        self._draw_quantized_glow(
            surface, rect.centerx, rect.centery, 48,
            (100, 125, 145) if locked else c,
            12 if locked else 36,
        )
        door_sprite = get_env_sprite("door_airlock_double", (w + 8, h + 4))
        if door_sprite is not None:
            surface.blit(door_sprite, (rect.left - 4, rect.top - 2))
        else:
            pygame.draw.rect(surface, INK, rect, border_radius=5)
            pygame.draw.rect(surface, (100, 134, 159), rect.inflate(-2, -2), 3, border_radius=4)
        inner = rect.inflate(-16, -16)
        shimmer = int(30 + 20 * (0.5 + 0.5 * math.sin(clock * 2.4)))
        scan_offset = int(clock * 14) % 8
        if locked:
            pygame.draw.rect(surface, (29, 40, 53), inner)
            pygame.draw.line(
                surface, (228, 130, 75),
                (inner.left + 4, inner.centery),
                (inner.right - 4, inner.centery), 3,
            )
            return
        for sy in range(inner.top + 3 + scan_offset, inner.bottom - 3, 8):
            pygame.draw.line(
                surface,
                (45, min(255, shimmer + 115), min(255, shimmer + 175)),
                (inner.left + 3, sy),
                (inner.right - 3, sy),
                2,
            )

    def draw_landmark(self, surface, camera, room):
        self._room_num = room.current_level_num
        self._active_variation = (room.current_level_num - 1) % 3

    def draw_room_scenery(self, surface, camera, level_manager):
        """World-anchored decoration & local puzzle signal state forwarding."""
        theme = level_manager.theme_name
        n = level_manager.current_level_num
        self._room_num = n
        self._reduced_motion = level_manager.save_manager.data.get("settings", {}).get("reduced_motion", False)

        # Forward local puzzle emitters & active signals so background machinery reacts locally
        pm = level_manager.puzzle_manager
        local_nodes = []
        for g in pm.generators:
            local_nodes.append((g.rect.centerx, g.rect.centery, g.active, "generator"))
        for v in pm.valves:
            local_nodes.append((v.rect.centerx, v.rect.centery, v.link_id in pm.active_signals, "valve"))
        for rel in pm.latching_relays:
            local_nodes.append((rel.rect.centerx, rel.rect.centery, rel.latched, "relay"))
        self.pixel_environment.set_local_signal_nodes(local_nodes)
        self.pixel_environment.set_active_signals(pm.active_signals)

        # PressurePlate has ``base_rect`` and ``sensor_rect``, not ``rect``.
        # Asking for ``pl.rect`` crashed on the first gameplay frame in all
        # chambers with plates. Use each object's *real* collision/interaction
        # bounds instead of assuming every device shares a ``rect`` attribute.
        device_rects = [
            *(g.rect for g in pm.generators),
            *(v.rect for v in pm.valves),
            *(rel.rect for rel in pm.latching_relays),
            *(rc.rect for rc in pm.routing_consoles),
            *(sw.rect for sw in pm.switches),
            *(pl.base_rect for pl in pm.plates),
            *(pl.sensor_rect for pl in pm.plates),
            *(d.rect for d in pm.doors),
        ]
        ox, oy = camera.get_offset()
        for prop in placements_for_level(n, theme, self._world_dressing):
            sprite = get_env_sprite(prop["sprite"], tuple(prop["size"]))
            if sprite is None:
                continue
            px, py = anchor_for(
                ox, oy, *prop["world"], sprite.get_width(), sprite.get_height(),
                prop.get("anchor", "top_center"),
            )
            world_rect = pygame.Rect(int(px + ox), int(py + oy), sprite.get_width(), sprite.get_height())
            # Eliminate nonessential prop overlap with puzzle nodes and playfield edges.
            if any(world_rect.colliderect(dr.inflate(12, 12)) for dr in device_rects):
                continue
            if any(world_rect.colliderect(tile) and
                   (tile.h <= 100 or tile.w <= 96 or
                    world_rect.top < tile.top < world_rect.bottom)
                   for tile in self._world_tiles):
                continue
            if (
                px + sprite.get_width() < 0
                or py + sprite.get_height() < 0
                or px >= VIRTUAL_WIDTH
                or py >= VIRTUAL_HEIGHT
            ):
                continue
            surface.blit(sprite, (px, py))

        for gen in pm.generators:
            gr = camera.apply(gen.rect)
            if -60 <= gr.centerx <= VIRTUAL_WIDTH + 60:
                glow_col = (65, 235, 165) if gen.active else (225, 85, 95)
                self._draw_quantized_glow(
                    surface, gr.centerx, gr.centery, 36 if gen.active else 22, glow_col, 32 if gen.active else 18
                )
        for rel in pm.latching_relays:
            rr = camera.apply(rel.rect)
            if -60 <= rr.centerx <= VIRTUAL_WIDTH + 60 and rel.latched:
                self._draw_quantized_glow(surface, rr.centerx, rr.centery, 32, (65, 235, 165), 28)
