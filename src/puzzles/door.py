from src.visuals import get_env_sprite
import pygame
from src.core.settings import COLORS


class Door:
    """Mechanical bulkhead door or retractable bridge controlled by puzzle link IDs."""

    def __init__(
        self,
        door_id: str,
        x: int,
        y: int,
        width: int,
        height: int,
        required_links: list[str],
        logic: str = "ALL",
        inverted: bool = False,
    ) -> None:
        self.door_id = door_id
        self.closed_rect = pygame.Rect(x, y, width, height)
        self.rect = self.closed_rect.copy()
        self.required_links = list(required_links)
        self.logic = logic.upper()
        self.inverted = inverted
        self.live_links = set()
        self.is_open = False
        self.open_progress = 0.0

    def evaluate_signals(self, active_signals: set[str]) -> None:
        self.live_links = active_signals
        if not self.required_links:
            matched = False
        elif self.logic == "ANY":
            matched = any(link in active_signals for link in self.required_links)
        else:
            matched = all(link in active_signals for link in self.required_links)

        self.is_open = (not matched) if self.inverted else matched

    def update(self, dt: float) -> None:
        speed = 3.2
        if self.is_open:
            self.open_progress = min(1.0, self.open_progress + speed * dt)
        else:
            self.open_progress = max(0.0, self.open_progress - speed * dt)

        current_h = int(round(self.closed_rect.height * (1.0 - self.open_progress)))
        self.rect = pygame.Rect(
            self.closed_rect.x,
            self.closed_rect.y,
            self.closed_rect.width,
            current_h,
        )

    @property
    def is_solid(self) -> bool:
        return self.open_progress < 0.88 and self.rect.height > 4

    def get_state(self) -> dict:
        return {
            "is_open": self.is_open,
            "open_progress": self.open_progress,
        }

    def set_state(self, state: dict) -> None:
        self.is_open = bool(state["is_open"])
        self.open_progress = float(state["open_progress"])
        self.update(0.0)

    def draw(self, surface: pygame.Surface, camera) -> None:
        frame = camera.apply(self.closed_rect)
        # 3 px steel bulkhead frame & vertical hydraulic guide rails
        pygame.draw.rect(surface, (6, 15, 30), frame.inflate(2, 2), width=2)
        pygame.draw.rect(surface, (99, 128, 153), frame, width=3)
        pygame.draw.line(surface, (42, 58, 76), (frame.left + 4, frame.top + 3), (frame.left + 4, frame.bottom - 3), 2)
        pygame.draw.line(surface, (42, 58, 76), (frame.right - 5, frame.top + 3), (frame.right - 5, frame.bottom - 3), 2)

        # Side-mounted signal status box displaying individual red/green LEDs per required link
        panel_h = max(14, 8 + len(self.required_links) * 7)
        panel = pygame.Rect(frame.left - 12, frame.centery - panel_h // 2, 10, panel_h)
        pygame.draw.rect(surface, (6, 15, 30), panel)
        pygame.draw.rect(surface, (72, 92, 120), panel, 1)
        for row, link in enumerate(self.required_links):
            lamp = COLORS["switch_on"] if link in self.live_links else COLORS["switch_off"]
            ly = panel.y + 5 + row * 7
            pygame.draw.circle(surface, lamp, (panel.centerx, ly), 2)

        if self.rect.height > 2:
            r = camera.apply(self.rect)
            sp = get_env_sprite("door_narrow_active" if self.is_open else "door_hazard_shutter", (max(8, r.width), max(8, r.height)))
            if sp is not None:
                surface.blit(sp, r.topleft)
                pygame.draw.rect(surface, (175, 94, 86) if not self.is_open else (65, 205, 140), r, width=2)
                return
            pygame.draw.rect(surface, (42, 50, 66), r)
            pygame.draw.rect(surface, (6, 15, 30), r, width=2)
            pygame.draw.rect(surface, (175, 94, 86) if not self.is_open else (65, 205, 140), r.inflate(-2, -2), width=2)
            # Horizontal reinforcement ribs every 22 px
            for y in range(r.top + 8, r.bottom - 8, 22):
                pygame.draw.line(surface, (18, 26, 38), (r.left + 4, y + 2), (r.right - 5, y + 2), 2)
                pygame.draw.line(surface, (95, 114, 138), (r.left + 4, y), (r.right - 5, y), 2)
            # Central hydraulic locking spine
            if r.height > 16:
                pygame.draw.rect(surface, (11, 21, 34), (r.centerx - 4, r.top + 5, 8, max(2, r.h - 12)))
                pygame.draw.line(surface, (235, 119, 101), (r.left + 4, r.centery), (r.right - 4, r.centery), 2)
            # Hazard chevrons along the bottom door seal
            if r.height >= 12:
                seal_y = r.bottom - 6
                pygame.draw.rect(surface, (20, 24, 32), (r.left + 3, seal_y, max(2, r.width - 6), 4))
                for sx in range(r.left + 5, r.right - 6, 10):
                    pygame.draw.line(surface, (255, 180, 55), (sx, seal_y + 3), (sx + 4, seal_y), 2)
