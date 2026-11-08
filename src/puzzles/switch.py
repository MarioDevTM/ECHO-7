from src.visuals import get_env_sprite
import pygame
from src.core.settings import COLORS


class Switch:
    """Interactive facility terminal/lever/valve supporting toggle, permanent, timed, and sequence modes."""

    def __init__(
        self,
        link_id: str,
        x: int,
        y: int,
        mode: str = "toggle",
        duration: float = 0.0,
        seq_order: int = 0,
        focus_target: list[int] | None = None,
    ) -> None:
        self.link_id = link_id
        self.rect = pygame.Rect(x, y - 36, 28, 36)
        self.interact_rect = self.rect.inflate(28, 16)
        self.mode = mode  # "toggle", "permanent", "timed", "sequence"
        self.duration = float(duration)
        self.seq_order = int(seq_order)
        self.focus_target = focus_target
        self.active = False

    def interact(self) -> bool:
        if self.mode == "permanent":
            if not self.active:
                self.active = True
                return True
            return False
        elif self.mode == "toggle":
            self.active = not self.active
            return True
        elif self.mode in ("timed", "sequence"):
            self.active = True
            return True
        return False

    def get_state(self) -> dict:
        return {"active": self.active}

    def set_state(self, state: dict) -> None:
        self.active = bool(state.get("active", False))

    def draw(
        self,
        surface: pygame.Surface,
        camera,
        timer_ratio: float = 0.0,
        show_prompt: bool = False,
        font: pygame.font.Font | None = None,
    ) -> None:
        r = camera.apply(self.rect)
        sp = get_env_sprite("console_cyan" if self.active else "console_magenta", (r.width + 6, r.height + 4))
        if sp is not None:
            surface.blit(sp, (r.left - 3, r.top - 2))
        # Bolted dark pedestal base & console body
        pygame.draw.rect(surface, (6, 15, 30), r.inflate(2, 2), border_radius=4)
        pygame.draw.rect(surface, COLORS["tile_dark"], r, border_radius=4)
        pygame.draw.rect(surface, COLORS["tile_border"], r, width=2, border_radius=4)
        pygame.draw.rect(surface, (45, 58, 78), (r.left - 2, r.bottom - 5, r.width + 4, 5), border_radius=2)

        # Angled CRT monitor hood & glowing telemetry screen
        screen_col = COLORS["switch_on"] if self.active else COLORS["switch_off"]
        screen_rect = pygame.Rect(r.left + 4, r.top + 5, r.width - 8, 13)
        pygame.draw.rect(surface, (6, 15, 30), screen_rect.inflate(2, 2), border_radius=2)
        pygame.draw.rect(surface, screen_col, screen_rect, border_radius=2)
        # Telemetry scanlines inside screen
        pygame.draw.line(surface, (235, 255, 245) if self.active else (255, 190, 180),
                         (screen_rect.left + 2, screen_rect.top + 3), (screen_rect.right - 3, screen_rect.top + 3), 1)
        pygame.draw.line(surface, (20, 45, 55),
                         (screen_rect.left + 2, screen_rect.top + 7), (screen_rect.right - 5, screen_rect.top + 7), 1)
        # Lower keypad detail
        pygame.draw.rect(surface, (18, 26, 38), (r.left + 6, r.top + 21, r.width - 12, 8))
        pygame.draw.circle(surface, screen_col, (r.centerx, r.top + 25), 2)

        if self.mode == "timed" and self.active and timer_ratio > 0.0:
            bar_bg = pygame.Rect(r.left - 4, r.top - 10, r.width + 8, 5)
            bar_fg = pygame.Rect(
                bar_bg.left,
                bar_bg.top,
                int(bar_bg.width * max(0.0, min(1.0, timer_ratio))),
                5,
            )
            pygame.draw.rect(surface, COLORS["bg_deep"], bar_bg)
            pygame.draw.rect(surface, COLORS["ui_warning"], bar_fg)

        if show_prompt and font is not None:
            label = font.render("[E]", True, COLORS["ui_text"])
            lrect = label.get_rect(center=(r.centerx, r.top - 18))
            bg = lrect.inflate(8, 4)
            pygame.draw.rect(surface, COLORS["ui_bg"], bg, border_radius=3)
            pygame.draw.rect(surface, COLORS["ui_accent"], bg, width=1, border_radius=3)
            surface.blit(label, lrect)
