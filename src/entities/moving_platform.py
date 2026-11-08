from src.visuals import get_env_sprite
import math
import pygame
from src.core.settings import COLORS


class MovingPlatform:
    """Configurable moving platform / elevator that carries the player and crates smoothly."""

    def __init__(
        self,
        plat_id: str,
        x: float,
        y: float,
        width: int,
        height: int,
        end_x: float,
        end_y: float,
        speed: float = 95.0,
        required_links: list[str] | None = None,
        logic: str = "ALL",
        active_by_default: bool = True,
    ) -> None:
        self.plat_id = plat_id
        self.start_x = float(x)
        self.start_y = float(y)
        self.end_x = float(end_x)
        self.end_y = float(end_y)
        self.pos_x = float(x)
        self.pos_y = float(y)
        self.rect = pygame.Rect(int(x), int(y), width, height)
        self.speed = float(speed)
        self.required_links = required_links or []
        self.logic = logic
        self.active_by_default = active_by_default
        self.active = active_by_default

        self.forward = True
        self.dx = 0.0
        self.dy = 0.0

    def update(self, dt: float) -> None:
        self.previous_state = self.get_state()
        old_rx, old_ry = self.rect.x, self.rect.y
        if not self.active:
            self.dx = 0.0
            self.dy = 0.0
            return

        target_x = self.end_x if self.forward else self.start_x
        target_y = self.end_y if self.forward else self.start_y

        vec_x = target_x - self.pos_x
        vec_y = target_y - self.pos_y
        dist = math.hypot(vec_x, vec_y)

        step = self.speed * dt
        if dist <= step or dist < 0.5:
            self.pos_x = target_x
            self.pos_y = target_y
            self.forward = not self.forward
        else:
            self.pos_x += (vec_x / dist) * step
            self.pos_y += (vec_y / dist) * step

        self.rect.x = int(round(self.pos_x))
        self.rect.y = int(round(self.pos_y))
        self.dx = float(self.rect.x - old_rx)
        self.dy = float(self.rect.y - old_ry)

    def get_state(self) -> dict:
        return {
            "pos_x": self.pos_x,
            "pos_y": self.pos_y,
            "forward": self.forward,
            "active": self.active,
        }

    def set_state(self, state: dict) -> None:
        self.pos_x = float(state["pos_x"])
        self.pos_y = float(state["pos_y"])
        self.forward = bool(state["forward"])
        self.active = bool(state["active"])
        self.rect.topleft = (int(round(self.pos_x)), int(round(self.pos_y)))
        self.dx = 0.0
        self.dy = 0.0

    def draw(self, surface: pygame.Surface, camera) -> None:
        p1 = camera.apply_point((self.start_x + self.rect.width / 2,
                                 self.start_y + self.rect.height / 2))
        p2 = camera.apply_point((self.end_x + self.rect.width / 2,
                                 self.end_y + self.rect.height / 2))
        pygame.draw.line(surface, (52, 75, 100), p1, p2, 3)
        r = camera.apply(self.rect)
        if r.right < 0 or r.left > surface.get_width():
            return
        pygame.draw.rect(surface, (25, 39, 55), r)
        sp = get_env_sprite("platform_solid_long" if self.active else "platform_hazard_long", (max(12, r.width), max(8, r.height)))
        if sp is not None:
            surface.blit(sp, r.topleft)
        pygame.draw.rect(surface, (96, 121, 147), r, 2)
        pygame.draw.rect(surface, (49, 69, 88), (r.left+2, r.top+8, max(0, r.width-4), max(0, r.height-10)))
        glow = (53, 230, 255) if self.active else (204, 83, 90)
        if r.width > 12:
            pygame.draw.line(surface, glow, (r.left+5,r.top+3), (r.right-5,r.top+3), 3)
        for x in range(max(0,r.left+10), min(surface.get_width(),r.right-8), 24):
            pygame.draw.circle(surface,(156,179,192),(x,min(r.bottom-2,r.top+10)),2)
        if r.width > 40:
            pygame.draw.rect(surface,(9,23,35),(r.centerx-8,r.top+4,16,min(7,max(1,r.h-5))))
