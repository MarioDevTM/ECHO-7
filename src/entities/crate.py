from src.visuals import get_env_sprite
import pygame
from src.core.settings import CRATE_SIZE, GRAVITY, MAX_FALL_SPEED, COLORS


class Crate:
    """Pushable physics crate supporting mass variation, water buoyancy, and wind/conveyor forces."""

    def __init__(
        self,
        crate_id: str,
        x: float,
        y: float,
        mass: float = 1.0,
        buoyant: bool = True,
    ) -> None:
        self.crate_id = crate_id
        self.spawn_x = float(x)
        self.spawn_y = float(y)
        self.pos_x = float(x)
        self.pos_y = float(y)
        self.rect = pygame.Rect(int(x), int(y), CRATE_SIZE, CRATE_SIZE)
        self.vx = 0.0
        self.vy = 0.0
        self.mass = float(mass)  # < 0.8 = lightweight (pushed by wind fans)
        self.buoyant = bool(buoyant)
        self.on_ground = False
        self.in_water = False
        self.immersion = 0.0
        self.conveyor_vx = 0.0
        self.wind_vx = 0.0
        self.wind_vy = 0.0

    def apply_gravity_and_friction(self, dt: float) -> None:
        if not self.in_water:
            self.vy = min(MAX_FALL_SPEED, self.vy + (GRAVITY + self.wind_vy) * dt)

        else:
            buoyancy = 1.8 * self.immersion if self.buoyant else 0.0
            self.vy = (self.vy + GRAVITY * (1 - buoyancy) * dt) / (1 + 5 * dt)

        if abs(self.wind_vx) > 1.0 and self.mass < 0.85:
            self.vx = self.wind_vx / max(0.35, self.mass)
        else:
            decay = 2800.0 if self.on_ground else 550.0
            if self.vx > 0:
                self.vx = max(0.0, self.vx - decay * dt)
            elif self.vx < 0:
                self.vx = min(0.0, self.vx + decay * dt)

        self.wind_vx = 0.0
        self.wind_vy = 0.0

    def get_state(self) -> dict:
        return {
            "pos_x": self.pos_x,
            "pos_y": self.pos_y,
            "vx": self.vx,
            "vy": self.vy,
        }

    def set_state(self, state: dict) -> None:
        self.pos_x = float(state["pos_x"])
        self.pos_y = float(state["pos_y"])
        self.vx = float(state.get("vx", 0.0))
        self.vy = float(state.get("vy", 0.0))
        self.rect.topleft = (int(round(self.pos_x)), int(round(self.pos_y)))

    def draw(self, surface: pygame.Surface, camera) -> None:
        """Sprite-backed research cargo (36x36) aligned with physical hitbox."""
        r = camera.apply(self.rect)
        if r.right < 0 or r.left > surface.get_width():
            return
        lightweight = self.mass < 0.85
        sp_name = "crate_energy_core" if lightweight else ("crate_steel" if not self.buoyant else "crate_wood")
        sp = get_env_sprite(sp_name, (r.width, r.height))
        if sp is not None:
            surface.blit(sp, r.topleft)
            border_col = (95, 212, 230) if lightweight else (240, 169, 78)
            pygame.draw.rect(surface, (6, 15, 30), r, 2)
            pygame.draw.rect(surface, border_col, r.inflate(-2, -2), 1)
            return
        edge = (95, 212, 230) if lightweight else (240, 169, 78)
        hi = (175, 245, 255) if lightweight else (255, 215, 130)
        body = (34, 88, 108) if lightweight else (40, 54, 70)
        recess = (18, 34, 48) if lightweight else (24, 34, 46)

        # 2 px dark navy outer silhouette & beveled frame
        pygame.draw.rect(surface, (6, 15, 30), r)
        pygame.draw.rect(surface, edge, r.inflate(-2, -2), 2)
        pygame.draw.line(surface, hi, (r.left + 3, r.top + 2), (r.right - 4, r.top + 2), 1)

        # Recessed dark steel body & diagonal cross-bracing bars
        panel = r.inflate(-8, -8)
        pygame.draw.rect(surface, recess, panel)
        pygame.draw.rect(surface, body, panel.inflate(-2, -2), 1)
        pygame.draw.line(surface, (6, 15, 30), panel.topleft, panel.bottomright, 4)
        pygame.draw.line(surface, (6, 15, 30), panel.topright, panel.bottomleft, 4)
        pygame.draw.line(surface, edge, panel.topleft, panel.bottomright, 2)
        pygame.draw.line(surface, edge, panel.topright, panel.bottomleft, 2)

        # Corner bumper brackets & fastening rivets
        for cx, cy in ((r.left + 4, r.top + 4), (r.right - 5, r.top + 4),
                       (r.left + 4, r.bottom - 5), (r.right - 5, r.bottom - 5)):
            pygame.draw.circle(surface, (6, 15, 30), (cx, cy), 2)
            pygame.draw.circle(surface, hi, (cx, cy), 1)

        # Central status core
        core = pygame.Rect(r.centerx - 5, r.centery - 5, 10, 10)
        pygame.draw.rect(surface, (6, 15, 30), core)
        pygame.draw.rect(surface, edge, core.inflate(-2, -2), 1)
        pygame.draw.rect(surface, (0, 230, 255) if lightweight else hi, core.inflate(-6, -6))
