import math
import pygame
from src.core.settings import COLORS


class SpikeHazard:
    """Static metallic floor/ceiling spikes."""

    def __init__(
        self, x: int, y: int, width: int, height: int, orientation: str = "up"
    ) -> None:
        self.rect = pygame.Rect(x, y, width, height)
        self.hitbox = self.rect.inflate(-6, -6)
        self.orientation = orientation

    def check_player_hit(self, player_rect: pygame.Rect) -> bool:
        return self.hitbox.colliderect(player_rect)

    def draw(self, surface: pygame.Surface, camera) -> None:
        r = camera.apply(self.rect)
        step = 16
        for sx in range(r.left, r.right, step):
            w = min(step, r.right - sx)
            if self.orientation == "up":
                pts = [(sx, r.bottom), (sx + w // 2, r.top), (sx + w, r.bottom)]
                hi_pts = [(sx + 2, r.bottom - 1), (sx + w // 2, r.top + 2)]
            else:
                pts = [(sx, r.top), (sx + w // 2, r.bottom), (sx + w, r.top)]
                hi_pts = [(sx + 2, r.top + 1), (sx + w // 2, r.bottom - 2)]
            pygame.draw.polygon(surface, (90, 110, 133), pts)
            pygame.draw.polygon(surface, COLORS["spike"], [pts[0], pts[1], (sx + w // 2, pts[0][1])])
            pygame.draw.polygon(surface, (6, 15, 30), pts, 2)
            pygame.draw.line(surface, (220, 235, 250), hi_pts[0], hi_pts[1], 1)


class AcidHazard:
    """Hazardous chemical coolant pool with animated surface waves."""

    def __init__(self, x: int, y: int, width: int, height: int) -> None:
        self.rect = pygame.Rect(x, y, width, height)
        self.hitbox = pygame.Rect(x + 4, y + 6, width - 8, height - 6)
        self.phase = 0.0

    def update(self, dt: float) -> None:
        self.phase += dt * 5.0

    def check_player_hit(self, player_rect: pygame.Rect) -> bool:
        return self.hitbox.colliderect(player_rect)

    def draw(self, surface: pygame.Surface, camera) -> None:
        r = camera.apply(self.rect)
        pygame.draw.rect(surface, (28, 125, 58), r)
        if r.height > 14:
            pygame.draw.rect(surface, COLORS["acid"], (r.left, r.top + 4, r.width, max(4, r.height // 2)))
        top_strip = pygame.Rect(r.left, r.top, r.width, 5)
        pygame.draw.rect(surface, COLORS["acid_glow"], top_strip)
        for bx in range(r.left + 12, r.right - 8, 28):
            by = r.top + 8 + int(4 * math.sin(self.phase + bx * 0.1))
            pygame.draw.circle(surface, (185, 255, 200), (bx, min(r.bottom - 4, by)), 2)


class LaserHazard:
    """Lethal laser emitter that can be disabled by puzzle signals or blocked by crates."""

    def __init__(
        self,
        x: int,
        y: int,
        direction: tuple[int, int],
        max_length: int,
        disabled_by: list[str] | None = None,
        logic: str = "ANY",
        period: float = 0.0,
        duty_cycle: float = 0.55,
    ) -> None:
        self.origin = (x, y)
        self.direction = direction
        self.max_length = max_length
        self.disabled_by = disabled_by or []
        self.logic = logic.upper()
        self.period = float(period)
        self.duty_cycle = float(duty_cycle)
        self.timer = 0.0
        self.active = True
        self.beam_rect = pygame.Rect(x, y, 4, 4)

    def update(
        self,
        dt: float,
        solids: list[pygame.Rect],
        active_signals: set[str],
    ) -> None:
        self.timer += dt
        if self.disabled_by:
            if self.logic == "ALL":
                disabled = all(s in active_signals for s in self.disabled_by)
            else:
                disabled = any(s in active_signals for s in self.disabled_by)
            if disabled:
                self.active = False
                return

        if self.period > 0.0:
            cycle_pos = (self.timer % self.period) / self.period
            self.active = cycle_pos < self.duty_cycle
        else:
            self.active = True

        if not self.active:
            return

        dx, dy = self.direction
        step = 6
        cx, cy = self.origin
        for _ in range(0, self.max_length, step):
            cx += dx * step
            cy += dy * step
            test = pygame.Rect(cx - 2, cy - 2, 4, 4)
            if any(s.colliderect(test) for s in solids):
                break

        x1, y1 = min(self.origin[0], cx), min(self.origin[1], cy)
        w = max(6, abs(cx - self.origin[0]))
        h = max(6, abs(cy - self.origin[1]))
        self.beam_rect = pygame.Rect(x1, y1, w, h)

    def check_player_hit(self, player_rect: pygame.Rect) -> bool:
        return self.active and self.beam_rect.colliderect(player_rect)

    def draw(self, surface: pygame.Surface, camera) -> None:
        ox, oy = camera.apply_point(self.origin)
        pygame.draw.rect(surface, (6, 15, 30), (ox - 8, oy - 8, 16, 16), border_radius=3)
        pygame.draw.rect(surface, COLORS["tile_border"], (ox - 7, oy - 7, 14, 14), width=2, border_radius=3)
        pygame.draw.circle(surface, COLORS["laser"] if self.active else (90, 45, 55), (ox, oy), 3)
        if not self.active:
            return
        r = camera.apply(self.beam_rect)
        pygame.draw.rect(surface, (140, 20, 40), r.inflate(2, 2))
        pygame.draw.rect(surface, COLORS["laser"], r)
        core = r.inflate(-2, -2) if r.width > 6 or r.height > 6 else r
        pygame.draw.rect(surface, COLORS["laser_core"], core)


class CrusherHazard:
    """Reciprocating industrial hydraulic stamping press."""

    def __init__(
        self,
        crusher_id: str,
        x: int,
        y: int,
        w: int,
        h: int,
        travel: int,
        period: float = 2.2,
        disabled_by: list[str] | None = None,
    ) -> None:
        self.crusher_id = crusher_id
        self.base_x = x
        self.base_y = y
        self.width = w
        self.height = h
        self.travel = travel
        self.period = max(0.5, float(period))
        self.disabled_by = disabled_by or []
        self.timer = 0.0
        self.active = True
        self.rect = pygame.Rect(x, y, w, h)

    def update(self, dt: float, active_signals: set[str]) -> None:
        if self.disabled_by and any(s in active_signals for s in self.disabled_by):
            self.active = False
            self.rect.y = self.base_y
            return

        self.active = True
        self.timer = (self.timer + dt) % self.period
        phase = self.timer / self.period
        # Fast downward slam, slower hydraulic retraction
        if phase < 0.35:
            ext = (phase / 0.35) ** 2
        else:
            ext = max(0.0, 1.0 - (phase - 0.35) / 0.65)
        self.rect.y = int(round(self.base_y + ext * self.travel))

    def check_player_hit(self, player_rect: pygame.Rect) -> bool:
        return self.active and self.rect.inflate(-4, -2).colliderect(player_rect)

    def draw(self, surface: pygame.Surface, camera) -> None:
        r = camera.apply(self.rect)
        base_top = camera.apply_point((self.base_x + self.width // 2, self.base_y))
        # Dual telescoping chrome hydraulic rams
        for offset in (-12, 12):
            pygame.draw.line(surface, (6, 15, 30), (base_top[0] + offset, base_top[1]), (r.centerx + offset, r.top), 8)
            pygame.draw.line(surface, COLORS["tile_border"], (base_top[0] + offset, base_top[1]), (r.centerx + offset, r.top), 4)
        # Heavy ribbed stamping block with hazard collar
        pygame.draw.rect(surface, (6, 15, 30), r.inflate(2, 2), border_radius=3)
        pygame.draw.rect(surface, COLORS["door_closed"], r, border_radius=3)
        col = COLORS["door_accent"] if self.active else COLORS["plate_active"]
        pygame.draw.rect(surface, col, r, width=2, border_radius=3)
        for sx in range(r.left + 6, r.right - 8, 14):
            pygame.draw.line(surface, (255, 180, 55), (sx, r.top + 4), (sx + 5, r.top + 10), 2)


class SteamVentHazard:
    """Periodic high-pressure steam jet controlled by isolation valves."""

    def __init__(
        self,
        vent_id: str,
        x: int,
        y: int,
        w: int,
        h: int,
        period: float = 2.4,
        duty_cycle: float = 0.5,
        disabled_by: list[str] | None = None,
    ) -> None:
        self.vent_id = vent_id
        self.rect = pygame.Rect(x, y, w, h)
        self.period = max(0.5, float(period))
        self.duty_cycle = float(duty_cycle)
        self.disabled_by = disabled_by or []
        self.timer = 0.0
        self.active = False

    def update(self, dt: float, active_signals: set[str]) -> None:
        if self.disabled_by and any(s in active_signals for s in self.disabled_by):
            self.active = False
            return
        self.timer = (self.timer + dt) % self.period
        self.active = (self.timer / self.period) < self.duty_cycle

    def check_player_hit(self, player_rect: pygame.Rect) -> bool:
        return self.active and self.rect.inflate(-6, -4).colliderect(player_rect)

    def draw(self, surface: pygame.Surface, camera) -> None:
        r = camera.apply(self.rect)
        nozzle = pygame.Rect(r.left - 2, r.bottom - 8, r.width + 4, 8)
        pygame.draw.rect(surface, COLORS["tile_border"], nozzle, border_radius=2)
        if not self.active:
            return
        steam_surf = pygame.Surface((r.width, r.height), pygame.SRCALPHA)
        steam_surf.fill((225, 238, 250, 165))
        surface.blit(steam_surf, r.topleft)


class HazardManager:
    """Aggregates spikes, acid pools, lasers, crushers, steam vents, and pit boundaries."""

    def __init__(self, level_height: int) -> None:
        self.level_height = level_height
        self.spikes: list[SpikeHazard] = []
        self.acids: list[AcidHazard] = []
        self.lasers: list[LaserHazard] = []
        self.crushers: list[CrusherHazard] = []
        self.steam_vents: list[SteamVentHazard] = []

    def update(
        self,
        dt: float,
        solids_and_crates: list[pygame.Rect],
        active_signals: set[str],
    ) -> None:
        for acid in self.acids:
            acid.update(dt)
        for laser in self.lasers:
            laser.update(dt, solids_and_crates, active_signals)
        for crusher in self.crushers:
            crusher.update(dt, active_signals)
        for vent in self.steam_vents:
            vent.update(dt, active_signals)

    def is_player_killed(self, player_rect: pygame.Rect) -> bool:
        if player_rect.top > self.level_height + 60:
            return True
        for sp in self.spikes:
            if sp.check_player_hit(player_rect):
                return True
        for ac in self.acids:
            if ac.check_player_hit(player_rect):
                return True
        for ls in self.lasers:
            if ls.check_player_hit(player_rect):
                return True
        for cr in self.crushers:
            if cr.check_player_hit(player_rect):
                return True
        for sv in self.steam_vents:
            if sv.check_player_hit(player_rect):
                return True
        return False

    def draw(self, surface: pygame.Surface, camera) -> None:
        for ac in self.acids:
            ac.draw(surface, camera)
        for sp in self.spikes:
            sp.draw(surface, camera)
        for ls in self.lasers:
            ls.draw(surface, camera)
        for cr in self.crushers:
            cr.draw(surface, camera)
        for sv in self.steam_vents:
            sv.draw(surface, camera)