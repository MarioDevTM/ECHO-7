from src.visuals import get_env_sprite
import math
import pygame
from src.core.settings import COLORS
from src.puzzles.pressure_plate import PressurePlate
from src.puzzles.switch import Switch
from src.puzzles.door import Door
from src.puzzles.timer_mechanism import TimerMechanism
from src.puzzles.routing import LatchingRelay, RoutingConsole


class Generator:
    """Electrical generator activated with [E] to supply continuous or timed power."""

    def __init__(self, link_id: str, x: int, y: int, duration: float = 0.0) -> None:
        self.link_id = link_id
        self.rect = pygame.Rect(x, y - 48, 44, 48)
        self.interact_rect = self.rect.inflate(28, 16)
        self.duration = float(duration)
        self.active = False
        self.phase = 0.0

    def interact(self) -> bool:
        if not self.active:
            self.active = True
            return True
        return False

    def update(self, dt: float) -> None:
        if self.active:
            self.phase += dt * 10.0

    def get_state(self) -> dict:
        return {"active": self.active}

    def set_state(self, state: dict) -> None:
        self.active = bool(state.get("active", False))

    def draw(
        self,
        surface: pygame.Surface,
        camera,
        show_prompt: bool = False,
        font: pygame.font.Font | None = None,
    ) -> None:
        r = camera.apply(self.rect)
        sp = get_env_sprite('power_cell_blue', (r.width, r.height))
        if sp is not None:
            surface.blit(sp, r.topleft)
        pygame.draw.rect(surface, (6, 15, 30), r.inflate(2, 2), border_radius=5)
        pygame.draw.rect(surface, COLORS["tile_dark"], r, border_radius=5)
        pygame.draw.rect(surface, COLORS["tile_border"], r, width=2, border_radius=5)
        for ex in (r.left + 8, r.right - 14):
            pygame.draw.rect(surface, (45, 58, 78), (ex, r.top - 4, 6, 4))
        for ly in range(r.top + 8, r.bottom - 8, 6):
            pygame.draw.line(surface, (18, 25, 38), (r.left + 4, ly), (r.left + 10, ly), 2)
            pygame.draw.line(surface, (18, 25, 38), (r.right - 10, ly), (r.right - 4, ly), 2)

        core_col = COLORS["switch_on"] if self.active else COLORS["switch_off"]
        core = r.inflate(-14, -14)
        pygame.draw.rect(surface, (6, 15, 30), core.inflate(2, 2), border_radius=4)
        pygame.draw.rect(surface, core_col, core, border_radius=4)
        # Rotating armature cross inside core
        ang = self.phase if self.active else 0.0
        dx = int(math.cos(ang) * 6)
        dy = int(math.sin(ang) * 6)
        pygame.draw.line(surface, (235, 255, 250), (core.centerx - dx, core.centery - dy), (core.centerx + dx, core.centery + dy), 2)

        if show_prompt and font is not None:
            label = font.render("[E] Power", True, COLORS["ui_text"])
            lrect = label.get_rect(center=(r.centerx, r.top - 16))
            bg = lrect.inflate(8, 4)
            pygame.draw.rect(surface, COLORS["ui_bg"], bg, border_radius=3)
            pygame.draw.rect(surface, COLORS["ui_accent"], bg, width=1, border_radius=3)
            surface.blit(label, lrect)


class Valve:
    """Rotatable wheel valve [E] used to drain flooded chambers or shut off steam vents."""

    def __init__(self, link_id: str, x: int, y: int) -> None:
        self.link_id = link_id
        self.rect = pygame.Rect(x - 16, y - 36, 32, 36)
        self.interact_rect = self.rect.inflate(28, 16)
        self.active = False
        self.angle = 0.0

    def interact(self) -> bool:
        self.active = not self.active
        return True

    def update(self, dt: float) -> None:
        if self.active:
            self.angle = (self.angle + 180.0 * dt) % 360.0

    def get_state(self) -> dict:
        return {"active": self.active}

    def set_state(self, state: dict) -> None:
        self.active = bool(state.get("active", False))

    def draw(
        self,
        surface: pygame.Surface,
        camera,
        show_prompt: bool = False,
        font: pygame.font.Font | None = None,
    ) -> None:
        r = camera.apply(self.rect)
        col = COLORS["plate_active"] if self.active else COLORS["ui_warning"]
        sp = get_env_sprite('valve_wheel_station', (r.width, r.height))
        if sp is not None:
            surface.blit(sp, r.topleft)
        pygame.draw.rect(surface, (6, 15, 30), (r.centerx - 5, r.centery, 10, r.height // 2))
        pygame.draw.rect(surface, (45, 58, 78), (r.centerx - 3, r.centery, 6, r.height // 2))
        pygame.draw.rect(surface, (72, 92, 120), (r.centerx - 8, r.bottom - 4, 16, 4))
        # 4-spoke industrial handwheel
        pygame.draw.circle(surface, (6, 15, 30), r.center, 15)
        pygame.draw.circle(surface, COLORS["tile_dark"], r.center, 13)
        pygame.draw.circle(surface, col, r.center, 13, 3)
        for offset in (0.0, 90.0):
            rad = math.radians(self.angle + offset)
            dx = int(math.cos(rad) * 11)
            dy = int(math.sin(rad) * 11)
            pygame.draw.line(
                surface, col, (r.centerx - dx, r.centery - dy), (r.centerx + dx, r.centery + dy), 2
            )
        pygame.draw.circle(surface, (235, 245, 255), r.center, 3)

        if show_prompt and font is not None:
            label = font.render("[E] Valve", True, COLORS["ui_text"])
            lrect = label.get_rect(center=(r.centerx, r.top - 16))
            bg = lrect.inflate(8, 4)
            pygame.draw.rect(surface, COLORS["ui_bg"], bg, border_radius=3)
            pygame.draw.rect(surface, COLORS["ui_accent"], bg, width=1, border_radius=3)
            surface.blit(label, lrect)


class PowerCable:
    """Visual conductive line showing puzzle signal connections across the environment."""

    def __init__(self, points: list[list[int]], link_id: str) -> None:
        self.points = [(int(p[0]), int(p[1])) for p in points]
        self.link_id = link_id

    def draw(self, surface: pygame.Surface, camera, active_signals: set[str]) -> None:
        if len(self.points) < 2:
            return
        screen_pts = [camera.apply_point(pt) for pt in self.points]
        active = self.link_id in active_signals
        col = COLORS["plate_active"] if active else (42, 56, 74)
        pygame.draw.lines(surface, (6, 15, 30), False, screen_pts, 5)
        pygame.draw.lines(surface, col, False, screen_pts, 3)
        if active:
            pygame.draw.lines(surface, (200, 255, 230), False, screen_pts, 1)
        for pt in screen_pts:
            pygame.draw.circle(surface, (6, 15, 30), pt, 4)
            pygame.draw.circle(surface, col, pt, 2)


class RotatableMirror:
    """Interactive optical reflector [E] that toggles orientation."""

    def __init__(self, mirror_id: str, x: int, y: int, orientation: int = 0) -> None:
        self.mirror_id = mirror_id
        self.rect = pygame.Rect(x, y, 28, 36)
        self.interact_rect = self.rect.inflate(28, 16)
        self.orientation = int(orientation) % 2

    def interact(self) -> bool:
        self.orientation = (self.orientation + 1) % 2
        return True

    def get_state(self) -> dict:
        return {"orientation": self.orientation}

    def set_state(self, state: dict) -> None:
        self.orientation = int(state.get("orientation", 0))

    def draw(
        self,
        surface: pygame.Surface,
        camera,
        show_prompt: bool = False,
        font: pygame.font.Font | None = None,
    ) -> None:
        r = camera.apply(self.rect)
        sp = get_env_sprite('mirror_rotatable_frame', (r.width, r.height))
        if sp is not None:
            surface.blit(sp, r.topleft)
        pygame.draw.rect(surface, (6, 15, 30), r.inflate(2, 2), width=2, border_radius=4)
        pygame.draw.rect(surface, COLORS["tile_dark"], r, border_radius=4)
        pygame.draw.rect(surface, COLORS["optical_beam"], r, width=2, border_radius=4)
        pygame.draw.rect(surface, (72, 92, 120), (r.left + 2, r.bottom - 4, r.width - 4, 4))
        if self.orientation == 0:
            p1, p2 = (r.left + 5, r.bottom - 6), (r.right - 5, r.top + 6)
        else:
            p1, p2 = (r.left + 5, r.top + 6), (r.right - 5, r.bottom - 6)
        pygame.draw.line(surface, (209, 106, 244), (p1[0], p1[1] + 2), (p2[0], p2[1] + 2), 4)
        pygame.draw.line(surface, (70, 220, 255), p1, p2, 3)
        pygame.draw.line(surface, (245, 252, 255), p1, p2, 1)

        if show_prompt and font is not None:
            label = font.render("[E] Rotate", True, COLORS["ui_text"])
            lrect = label.get_rect(center=(r.centerx, r.top - 16))
            bg = lrect.inflate(8, 4)
            pygame.draw.rect(surface, COLORS["ui_bg"], bg, border_radius=3)
            pygame.draw.rect(surface, COLORS["ui_accent"], bg, width=1, border_radius=3)
            surface.blit(label, lrect)


class ConveyorBelt:
    """Solid mechanical belt that pushes grounded players and crates horizontally."""

    def __init__(
        self,
        conv_id: str,
        x: int,
        y: int,
        w: int,
        h: int,
        speed: float,
        reversed_by: str | None = None,
        powered_by: str | None = None,
    ) -> None:
        self.conv_id = conv_id
        self.rect = pygame.Rect(x, y, w, h)
        self.base_speed = float(speed)
        self.reversed_by = reversed_by
        self.powered_by = powered_by
        self.current_speed = float(speed)
        self.phase = 0.0

    def update(
        self,
        dt: float,
        active_signals: set[str],
        player,
        crates: list,
    ) -> None:
        if self.reversed_by and self.reversed_by in active_signals:
            self.current_speed = -self.base_speed
        else:
            self.current_speed = self.base_speed

        if self.powered_by and self.powered_by not in active_signals:
            self.current_speed = 0
        self.phase = (self.phase + self.current_speed * dt * 0.4) % 24.0

        for actor in ([player] if player is not None else []) + list(crates):
            feet = actor.rect
            if (actor.vy >= 0 and abs(feet.bottom - self.rect.top) <= 1
                    and feet.right > self.rect.left and feet.left < self.rect.right):
                actor.conveyor_vx = self.current_speed

    def draw(self, surface: pygame.Surface, camera) -> None:
        r = camera.apply(self.rect)
        pygame.draw.rect(surface, (6, 15, 30), r.inflate(2, 2), border_radius=4)
        pygame.draw.rect(surface, COLORS["tile_dark"], r, border_radius=4)
        pygame.draw.rect(surface, COLORS["ui_warning"], r, width=2, border_radius=4)
        # End drive-sprocket rollers & internal support rollers
        for rx in (r.left + 6, r.right - 6):
            pygame.draw.circle(surface, (72, 92, 120), (rx, r.centery), max(3, r.height // 2 - 2))
            pygame.draw.circle(surface, (6, 15, 30), (rx, r.centery), 2)
        direction = 1 if self.current_speed >= 0 else -1
        for x in range(r.left + 18, r.right - 12, 24):
            pygame.draw.circle(surface, COLORS["tile_border"], (x, r.bottom - 4), 3)
        for sx in range(r.left + 12, r.right - 12, 28):
            cx = sx + int(self.phase) % 14
            pts = [
                (cx - 4 * direction, r.top + 3),
                (cx + 4 * direction, r.centery),
                (cx - 4 * direction, r.bottom - 3),
            ]
            pygame.draw.lines(surface, COLORS["ui_warning"] if self.current_speed else COLORS["tile_border"], False, pts, 2)


class WindZone:
    """Directional ventilation current that propels the player and crates."""

    def __init__(
        self,
        wind_id: str,
        x: int,
        y: int,
        w: int,
        h: int,
        vx: float,
        vy: float,
        controlled_by: str | None = None,
        active_by_default: bool = True,
    ) -> None:
        self.wind_id = wind_id
        self.rect = pygame.Rect(x, y, w, h)
        self.vx = float(vx)
        self.vy = float(vy)
        self.controlled_by = controlled_by
        self.active_by_default = active_by_default
        self.active = active_by_default
        self.phase = 0.0

    def update(self, dt: float, active_signals: set[str], player) -> None:
        if self.controlled_by:
            sig = self.controlled_by in active_signals
            self.active = sig if not self.active_by_default else (not sig)
        else:
            self.active = self.active_by_default

        if not self.active:
            return

        self.phase = (self.phase + dt * 90.0) % 40.0
        if player is not None and self.rect.colliderect(player.rect):
            player.external_vx += self.vx
            player.external_vy += self.vy

    def draw(self, surface: pygame.Surface, camera) -> None:
        r = camera.apply(self.rect)
        pygame.draw.rect(surface, COLORS["tile_border"], (r.left, r.bottom - 8, r.width, 8))
        hub = (r.centerx, r.bottom - 16)
        fan_sp = get_env_sprite("fan_turbine_blue", (32, 32))
        if fan_sp is not None:
            deg = (int(self.phase * 9.0) // 15 * 15) % 360 if self.active else 0
            rot_fan = pygame.transform.rotate(fan_sp, deg)
            surface.blit(rot_fan, (hub[0] - rot_fan.get_width() // 2, hub[1] - rot_fan.get_height() // 2))
        else:
            pygame.draw.circle(surface, COLORS["bg_near"], hub, 16)
            for blade in range(4):
                angle = blade * math.pi / 2 + self.phase * math.tau / 40
                tip = hub[0] + round(12 * math.cos(angle)), hub[1] + round(12 * math.sin(angle))
                pygame.draw.line(surface, COLORS["tile_border"], hub, tip, 4)
        if not self.active:
            return
        for lx in range(r.left + 20, r.right - 10, 36):
            for ly in range(r.top + 20, r.bottom - 20, 48):
                # ly already includes the screen-space top; subtract it before
                # wrapping to prevent camera-height-dependent drifting.
                oy = int((ly - r.top - self.phase) % max(1, r.height - 16)) + r.top
                if r.top <= oy < r.bottom - 14:
                    pygame.draw.line(
                        surface, COLORS["optical_beam"], (lx, oy), (lx, oy + 14), 2
                    )


class WaterZone:
    """Flooded chamber basin whose water level rises or drains via valve signals."""

    def __init__(
        self,
        wz_id: str,
        x: int,
        y: int,
        w: int,
        h: int,
        drained_y: int,
        controlled_by: str | None = None,
        toxic: bool = False,
    ) -> None:
        self.wz_id = wz_id
        self.base_x = x
        self.full_y = float(y)
        self.bottom_y = float(y + h)
        self.width = w
        self.drained_y = float(drained_y)
        self.current_y = float(y)
        self.phase = 0.0
        self.water_fill = None
        self.controlled_by = controlled_by
        self.toxic = toxic
        self.rect = pygame.Rect(x, y, w, h)

    def update(self, dt: float, active_signals: set[str], player) -> None:
        self.phase = (self.phase + 2 * dt) % math.tau
        drained = bool(self.controlled_by and self.controlled_by in active_signals)
        target_y = self.drained_y if drained else self.full_y
        speed = 55.0
        if self.current_y < target_y:
            self.current_y = min(target_y, self.current_y + speed * dt)
        elif self.current_y > target_y:
            self.current_y = max(target_y, self.current_y - speed * dt)

        self._sync_rect()

        if player is not None and self.rect.colliderect(player.rect):
            player.in_water = True

    def _sync_rect(self) -> None:
        cur_top = int(round(self.current_y))
        cur_h = max(0, int(round(self.bottom_y - cur_top)))
        self.rect = pygame.Rect(self.base_x, cur_top, self.width, cur_h)


    def get_state(self) -> dict:
        return {"current_y": self.current_y}

    def set_state(self, state: dict) -> None:
        self.current_y = float(state.get("current_y", self.full_y))
        self._sync_rect()

    def draw(self, surface: pygame.Surface, camera) -> None:
        if self.rect.height <= 6:
            return
        r = camera.apply(self.rect)
        visible = r.clip(surface.get_rect())
        if not visible:
            return
        if self.water_fill is None:
            self.water_fill = pygame.Surface((self.width, max(1, int(self.bottom_y - self.full_y))), pygame.SRCALPHA)
            self.water_fill.fill((*COLORS["water"], 125))
        # Source texture must use the clipped *world-zone* coordinates,
        # not the viewport origin (otherwise it follows the camera).
        source = pygame.Rect(visible.left - r.left, visible.top - r.top,
                             visible.width, visible.height)
        surface.blit(self.water_fill, visible.topleft, source)
        points = [(x, r.top + round(2 * math.sin((x - r.left) / 28 + self.phase)))
                  for x in range(visible.left - 8, visible.right + 9, 8)]
        ws_tile = get_env_sprite('water_surface_tile', (64, 14))
        if ws_tile is not None:
            first = r.left + ((visible.left - r.left) // 64) * 64
            for wx in range(first, visible.right, 64):
                surface.blit(ws_tile, (wx, max(0, r.top - 6)))
        pygame.draw.lines(surface, COLORS["water_surface"], False, points, 2)



class CollapsingPlatform:
    """Unstable structural catwalk that shakes and drops shortly after the player steps on it."""

    def __init__(
        self,
        plat_id: str,
        x: int,
        y: int,
        w: int,
        h: int,
        delay: float = 0.45,
        respawn: float = 2.5,
    ) -> None:
        self.plat_id = plat_id
        self.rect = pygame.Rect(x, y, w, h)
        self.delay = float(delay)
        self.respawn = float(respawn)
        self.state = "IDLE"  # IDLE, SHAKING, FALLEN
        self.timer = 0.0

    @property
    def is_solid(self) -> bool:
        return self.state != "FALLEN"

    def update(self, dt: float, player_rect: pygame.Rect) -> None:
        if self.state == "IDLE":
            feet = pygame.Rect(
                player_rect.left + 2, player_rect.bottom - 2, player_rect.width - 4, 6
            )
            top_sensor = pygame.Rect(self.rect.left, self.rect.top - 4, self.rect.width, 8)
            if top_sensor.colliderect(feet):
                self.state = "SHAKING"
                self.timer = self.delay
        elif self.state == "SHAKING":
            self.timer -= dt
            if self.timer <= 0.0:
                self.state = "FALLEN"
                self.timer = self.respawn
        elif self.state == "FALLEN":
            self.timer -= dt
            if self.timer <= 0.0:
                self.state = "IDLE"
                self.timer = 0.0

    def reset(self) -> None:
        self.state = "IDLE"
        self.timer = 0.0

    def get_state(self) -> dict:
        return {"state": self.state, "timer": self.timer}

    def set_state(self, state: dict | tuple | list) -> None:
        if isinstance(state, (tuple, list)) and len(state) == 2:
            self.state = str(state[0])
            self.timer = float(state[1])
        elif isinstance(state, dict):
            self.state = str(state.get("state", "IDLE"))
            self.timer = float(state.get("timer", 0.0))

    def draw(self, surface: pygame.Surface, camera) -> None:
        r = camera.apply(self.rect)
        if self.state == "FALLEN":
            pygame.draw.rect(surface, COLORS["tile_dark"], r, width=1, border_radius=3)
            return
        if self.state == "SHAKING":
            r.x += int(math.sin(self.timer * 70.0) * 3)
        col = COLORS["ui_warning"] if self.state == "SHAKING" else COLORS["platform"]
        pygame.draw.rect(surface, col, r, border_radius=3)
        pygame.draw.rect(surface, COLORS["tile_border"], r, width=2, border_radius=3)


class OpticalBeam:
    """Non-lethal calibration light beam that activates a receiver unless blocked by a crate/door."""

    def __init__(
        self,
        link_id: str,
        x: int,
        y: int,
        direction: tuple[int, int],
        max_length: int,
        receiver_rect: pygame.Rect,
        enabled_by: str | None = None,
    ) -> None:
        self.link_id = link_id
        self.origin = (x, y)
        self.direction = direction
        self.max_length = max_length
        self.receiver_rect = receiver_rect
        self.enabled_by = enabled_by
        self.segments = []
        self.end_point = (x, y)
        self.receiving = False

    def update(
        self,
        solids: list[pygame.Rect],
        active_signals: set[str],
        mirrors=(),
    ) -> bool:
        self.segments.clear()
        self.receiving = False
        self.end_point = self.origin
        if self.enabled_by and self.enabled_by not in active_signals:
            return False

        point = self.origin
        direction = self.direction
        remaining = self.max_length
        last_mirror = None
        visited = set()
        while remaining > 0:
            dx, dy = direction
            end = (point[0] + dx * remaining, point[1] + dy * remaining)
            distance = remaining + 1
            hit = None

            def consider(rect, target):
                nonlocal distance, end_hit, hit
                clipped = rect.clipline(point, end)
                if clipped:
                    x, y = clipped[0]
                    travel = abs(x - point[0]) + abs(y - point[1])
                    if travel < distance:
                        distance, end_hit, hit = travel, (x, y), target

            end_hit = end
            for solid in solids:
                consider(solid, None)
            consider(self.receiver_rect, self.receiver_rect)
            for mirror in mirrors:
                if mirror is last_mirror:
                    continue
                # Intersect the actual 45-degree reflective face.
                mx, my = mirror.rect.center
                slope = 1 if mirror.orientation else -1
                if dx:
                    x, y = mx + slope * (point[1] - my), point[1]
                else:
                    x, y = point[0], my + slope * (point[0] - mx)
                if mirror.rect.collidepoint(x, y):
                    consider(pygame.Rect(x, y, 1, 1), mirror)

            self.segments.append((point, end_hit))
            self.end_point = end_hit
            if hit is self.receiver_rect:
                self.receiving = True
                break
            if hit is None or (hit, direction) in visited:
                break
            visited.add((hit, direction))
            last_mirror = hit
            sign = 1 if hit.orientation else -1
            direction = (sign * dy, sign * dx)
            remaining -= distance
            point = end_hit
        return self.receiving

    def draw(self, surface: pygame.Surface, camera) -> None:
        housing = pygame.Rect(0, 0, 20, 20)
        housing.center = camera.apply_point(self.origin)
        em_sp = get_env_sprite("laser_emitter_unit", (22, 24))
        if em_sp is not None:
            surface.blit(em_sp, (housing.centerx - 11, housing.centery - 12))
        pygame.draw.rect(surface, (6, 15, 30), housing.inflate(2, 2), width=2, border_radius=3)
        pygame.draw.rect(surface, (6, 15, 30), housing.inflate(2, 2), border_radius=3)
        pygame.draw.rect(surface, COLORS["tile_dark"], housing, border_radius=3)
        pygame.draw.rect(surface, COLORS["tile_border"], housing, width=2, border_radius=3)
        lens_col = COLORS["optical_beam"] if self.segments else COLORS["plate_idle"]
        pygame.draw.circle(surface, lens_col, housing.center, 5)
        pygame.draw.circle(surface, (235, 252, 255), housing.center, 2)
        for start, end in self.segments:
            p1, p2 = camera.apply_point(start), camera.apply_point(end)
            pygame.draw.line(surface, (35, 130, 185), p1, p2, 6)
            pygame.draw.line(surface, COLORS["optical_beam"], p1, p2, 4)
            pygame.draw.line(surface, (230, 252, 255), p1, p2, 2)

        rec = camera.apply(self.receiver_rect)
        col = COLORS["plate_active"] if self.receiving else COLORS["plate_idle"]
        pygame.draw.rect(surface, (6, 15, 30), rec.inflate(2, 2), border_radius=3)
        pygame.draw.rect(surface, COLORS["tile_dark"], rec, border_radius=3)
        pygame.draw.rect(surface, col, rec, width=2, border_radius=3)
        pygame.draw.circle(surface, col, rec.center, 4)


class PuzzleManager:
    """Coordinates switches, plates, generators, valves, beams, conveyors, wind, water, and doors."""

    def __init__(self, audio=None) -> None:
        self.audio = audio
        self.plates: list[PressurePlate] = []
        self.switches: list[Switch] = []
        self.switches_by_id: dict[str, Switch] = {}
        self.generators: list[Generator] = []
        self.valves: list[Valve] = []
        self.cables: list[PowerCable] = []
        self.latching_relays: list[LatchingRelay] = []
        self.routing_consoles: list[RoutingConsole] = []
        self.route_modes: dict[str, int] = {}
        self.signal_inverters: dict[str, tuple[str, str | None]] = {}
        self.mirrors: list[RotatableMirror] = []
        self.conveyors: list[ConveyorBelt] = []
        self.wind_zones: list[WindZone] = []
        self.water_zones: list[WaterZone] = []
        self.collapsing_platforms: list[CollapsingPlatform] = []
        self.doors: list[Door] = []
        self.optical_beams: list[OpticalBeam] = []
        self.timer_mech = TimerMechanism()
        self.active_signals: set[str] = set()
        self.nearby_interactable = None

    def add_plate(self, plate: PressurePlate) -> None:
        self.plates.append(plate)

    def add_switch(self, switch: Switch) -> None:
        self.switches.append(switch)
        self.switches_by_id[switch.link_id] = switch

    def add_door(self, door: Door) -> None:
        self.doors.append(door)

    def add_optical_beam(self, beam: OpticalBeam) -> None:
        self.optical_beams.append(beam)

    def order_optical_beams(self):
        from graphlib import TopologicalSorter
        by_id = {b.link_id: b for b in self.optical_beams}
        graph = {b.link_id: [b.enabled_by] if b.enabled_by in by_id else [] for b in self.optical_beams}
        self.optical_beams = [by_id[key] for key in TopologicalSorter(graph).static_order()]

    def preview_routing(self, signals: set[str]) -> set[str]:
        """Outputs are exclusive per bus, unless an independent supply bridges them."""
        outputs = set()
        for console in self.routing_consoles:
            if all(link in signals for link in console.required_links):
                outputs.add(console.a_signal if self.route_modes[console.route_id] == 0
                            else console.b_signal)
        return outputs

    def try_interact(self, player_rect: pygame.Rect) -> bool:
        for relay in self.latching_relays:
            if relay.interact_rect.colliderect(player_rect):
                success = relay.interact(self.active_signals)
                if success and self.audio:
                    self.audio.play("checkpoint")
                return success

        for panel in self.routing_consoles:
            if panel.interact_rect.colliderect(player_rect):
                self.route_modes[panel.route_id] = 1 - self.route_modes[panel.route_id]
                if self.audio:
                    self.audio.play("switch")
                return True

        for sw in self.switches:
            if sw.interact_rect.colliderect(player_rect):
                changed = sw.interact()
                if changed:
                    if sw.mode == "timed" and sw.active:
                        self.timer_mech.start_timer(sw.link_id, sw.duration)
                    elif sw.mode == "sequence":
                        _, reset = self.timer_mech.notify_sequence_step(
                            sw.link_id, self.switches_by_id
                        )
                        if reset and self.audio:
                            self.audio.play("death")
                            return True
                    if self.audio:
                        self.audio.play("switch")
                return changed

        for gen in self.generators:
            if gen.interact_rect.colliderect(player_rect):
                if gen.interact():
                    if gen.duration > 0.0:
                        self.timer_mech.start_timer(gen.link_id, gen.duration)
                    if self.audio:
                        self.audio.play("switch")
                    return True

        for valve in self.valves:
            if valve.interact_rect.colliderect(player_rect):
                if valve.interact():
                    if self.audio:
                        self.audio.play("door")
                    return True

        for mirror in self.mirrors:
            if mirror.interact_rect.colliderect(player_rect):
                if mirror.interact():
                    if self.audio:
                        self.audio.play("switch")
                    return True

        return False

    def update(
        self,
        dt: float,
        player_rect: pygame.Rect,
        crates: list,
        tiles: list[pygame.Rect],
        moving_platforms: list,
        player=None,
    ) -> None:
        if player is not None:
            player.in_water = False
            player.conveyor_vx = player.external_vx = player.external_vy = 0.0
        for crate in crates:
            crate.in_water = False
            crate.conveyor_vx = crate.wind_vx = crate.wind_vy = 0.0

        # 1. Update timers
        if self.timer_mech.timers:
            devices = {**self.switches_by_id, **{g.link_id: g for g in self.generators}}
            self.timer_mech.update(dt, devices)

        # 2. Check pressure plates
        actors = [player_rect] + [c.rect for c in crates]
        for plate in self.plates:
            if plate.check_activation(actors) and self.audio:
                self.audio.play("plate")

        # 3. Collect active link signals
        signals: set[str] = set()
        for plate in self.plates:
            if plate.active:
                signals.add(plate.link_id)
        for sw in self.switches:
            if sw.active:
                signals.add(sw.link_id)
        for gen in self.generators:
            gen.update(dt)
            if gen.active:
                signals.add(gen.link_id)
        for valve in self.valves:
            valve.update(dt)
            if valve.active:
                signals.add(valve.link_id)
        for seq_id in self.timer_mech.sequences:
            if self.timer_mech.is_sequence_complete(seq_id):
                signals.add(seq_id)

        # Inverted signals can require both an OFF valve and a physically refilled basin.
        for output, (upstream, water_id) in self.signal_inverters.items():
            if upstream in signals:
                continue
            if water_id is not None:
                basin = next((w for w in self.water_zones if w.wz_id == water_id), None)
                if basin is None or basin.current_y > basin.full_y + 1.0:
                    continue
            signals.add(output)
        # Latches are deliberately manual: standing on a plate alone is not enough.
        for relay in self.latching_relays:
            relay.denied_flash = max(0.0, relay.denied_flash - dt)
            if relay.latched:
                signals.add(relay.link_id)

        # Route output only after the panel's power prerequisites are satisfied.
        signals.update(self.preview_routing(signals))

        # 4. Update optical beams
        beam_solids = tiles + [c.rect for c in crates] + [
            d.rect for d in self.doors if d.is_solid
        ]
        beam_solids.extend(mp.rect for mp in moving_platforms)
        beam_solids.extend(c.rect for c in self.conveyors)
        beam_solids.extend(c.rect for c in self.collapsing_platforms if c.is_solid)
        for beam in self.optical_beams:
            if beam.update(beam_solids, signals, self.mirrors):
                signals.add(beam.link_id)

        # Receivers can be prerequisites for a routing bus (final-escape reserve).
        signals.update(self.preview_routing(signals))
        self.active_signals = signals

        # 5. Update environmental zones & collapsing platforms
        for conv in self.conveyors:
            conv.update(dt, signals, player, crates)
        for wz in self.wind_zones:
            wz.update(dt, signals, player)
            if wz.active:
                for crate in crates:
                    if crate.mass < 0.85 and wz.rect.colliderect(crate.rect):
                        crate.wind_vx += wz.vx
                        crate.wind_vy += wz.vy
        for water in self.water_zones:
            water.update(dt, signals, player)
            for crate in crates:
                if water.rect.colliderect(crate.rect):
                    crate.in_water = True
                    crate.immersion = water.rect.clip(crate.rect).height / crate.rect.height
        for cp_plat in self.collapsing_platforms:
            cp_plat.update(dt, player_rect)

        # 6. Update doors & linked moving platforms
        for door in self.doors:
            was_open = door.is_open
            door.evaluate_signals(signals)
            if door.is_open != was_open and self.audio:
                self.audio.play("door")
            door.update(dt)

        for mp in moving_platforms:
            if mp.required_links:
                if mp.logic.upper() == "ANY":
                    matched = any(l in signals for l in mp.required_links)
                else:
                    matched = all(l in signals for l in mp.required_links)
                mp.active = matched if not mp.active_by_default else (not matched)

        # 7. Identify nearby interactable for HUD prompt
        self.nearby_interactable = None
        for obj in (*self.latching_relays, *self.routing_consoles,
                    *self.switches, *self.generators, *self.valves, *self.mirrors):
            if obj.interact_rect.colliderect(player_rect):
                self.nearby_interactable = obj
                break

    def get_solid_door_rects(self) -> list[pygame.Rect]:
        solids = [d.rect for d in self.doors if d.is_solid]
        solids.extend(c.rect for c in self.conveyors)
        solids.extend(cp.rect for cp in self.collapsing_platforms if cp.is_solid)
        return solids

    def capture_state(self) -> dict:
        return {
            "switches": {sw.link_id: sw.get_state() for sw in self.switches},
            "latches": {r.link_id: r.get_state() for r in self.latching_relays},
            "routes": dict(self.route_modes),
            "generators": {g.link_id: g.get_state() for g in self.generators},
            "valves": {v.link_id: v.get_state() for v in self.valves},
            "mirrors": {m.mirror_id: m.get_state() for m in self.mirrors},
            "water": {w.wz_id: w.get_state() for w in self.water_zones},
            "doors": {d.door_id: d.get_state() for d in self.doors},
            "collapsing": {c.plat_id: (c.state, c.timer) for c in self.collapsing_platforms},
            "timers": self.timer_mech.get_state(),
        }

    def restore_state(self, state: dict) -> None:
        for r in self.latching_relays:
            r.set_state(state.get("latches", {}).get(r.link_id, {}))
        for route_id in self.route_modes:
            self.route_modes[route_id] = int(state.get("routes", {}).get(route_id, 0)) % 2
        sw_states = state.get("switches", {})
        for sw in self.switches:
            if sw.link_id in sw_states:
                sw.set_state(sw_states[sw.link_id])
        gen_states = state.get("generators", {})
        for g in self.generators:
            if g.link_id in gen_states:
                g.set_state(gen_states[g.link_id])
        valve_states = state.get("valves", {})
        for v in self.valves:
            if v.link_id in valve_states:
                v.set_state(valve_states[v.link_id])
        mirror_states = state.get("mirrors", {})
        for m in self.mirrors:
            if m.mirror_id in mirror_states:
                m.set_state(mirror_states[m.mirror_id])
        water_states = state.get("water", {})
        for w in self.water_zones:
            if w.wz_id in water_states:
                w.set_state(water_states[w.wz_id])
        for cp in self.collapsing_platforms:
            cp.state, cp.timer = state.get("collapsing", {}).get(cp.plat_id, ("IDLE", 0.0))
        door_states = state.get("doors", {})
        for d in self.doors:
            if d.door_id in door_states:
                d.set_state(door_states[d.door_id])
        if "timers" in state:
            self.timer_mech.set_state(state["timers"])

    def draw(
        self, surface: pygame.Surface, camera, font: pygame.font.Font | None = None
    ) -> None:
        for cable in self.cables:
            cable.draw(surface, camera, self.active_signals)
        for wz in self.wind_zones:
            wz.draw(surface, camera)
        for beam in self.optical_beams:
            beam.draw(surface, camera)
        for conv in self.conveyors:
            conv.draw(surface, camera)
        for cp in self.collapsing_platforms:
            cp.draw(surface, camera)
        for plate in self.plates:
            plate.draw(surface, camera)
        for relay in self.latching_relays:
            relay.draw(surface, camera, relay is self.nearby_interactable, font)
        for panel in self.routing_consoles:
            panel.draw(surface, camera, self.route_modes[panel.route_id],
                       panel is self.nearby_interactable, font)
        for sw in self.switches:
            ratio = self.timer_mech.get_ratio(sw.link_id)
            sw.draw(
                surface,
                camera,
                timer_ratio=ratio,
                show_prompt=(sw is self.nearby_interactable),
                font=font,
            )
        for gen in self.generators:
            gen.draw(
                surface,
                camera,
                show_prompt=(gen is self.nearby_interactable),
                font=font,
            )
        for valve in self.valves:
            valve.draw(
                surface,
                camera,
                show_prompt=(valve is self.nearby_interactable),
                font=font,
            )
        for mirror in self.mirrors:
            mirror.draw(
                surface,
                camera,
                show_prompt=(mirror is self.nearby_interactable),
                font=font,
            )
        for door in self.doors:
            door.draw(surface, camera)
        for water in self.water_zones:
            water.draw(surface, camera)