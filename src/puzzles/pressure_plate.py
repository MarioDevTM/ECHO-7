import pygame
from src.core.settings import COLORS


class PressurePlate:
    """Weight-sensitive floor plate activated by the player or a crate."""

    def __init__(self, link_id: str, x: int, y: int, width: int = 44) -> None:
        self.link_id = link_id
        self.base_rect = pygame.Rect(x, y - 10, width, 10)
        self.sensor_rect = pygame.Rect(x + 2, y - 16, width - 4, 16)
        self.active = False
        self.was_active = False

    def check_activation(self, actors: list[pygame.Rect]) -> bool:
        """Returns True on the frame the plate transitions from inactive to active."""
        self.was_active = self.active
        self.active = any(self.sensor_rect.colliderect(a) for a in actors)
        return self.active and not self.was_active

    def draw(self, surface: pygame.Surface, camera) -> None:
        r = camera.apply(self.base_rect)
        pad_h = 4 if self.active else 8
        pad_rect = pygame.Rect(r.left + 4, r.bottom - pad_h - 2, r.width - 8, pad_h)
        color = COLORS["plate_active"] if self.active else COLORS["plate_idle"]

        # Recessed spring pistons under sensor pad
        for px in (r.left + 10, r.centerx, r.right - 11):
            pygame.draw.line(surface, (45, 58, 78), (px, pad_rect.bottom), (px, r.bottom - 2), 2)

        # Glowing central pressure strip with dark outline
        pygame.draw.rect(surface, (6, 15, 30), pad_rect.inflate(2, 2), border_radius=2)
        pygame.draw.rect(surface, color, pad_rect, border_radius=2)
        pygame.draw.line(surface, (220, 255, 235) if self.active else (255, 160, 160),
                         (pad_rect.left + 2, pad_rect.top + 1), (pad_rect.right - 3, pad_rect.top + 1), 1)

        # Beveled steel approach ramps & bolted base plate
        base_strip = pygame.Rect(r.left, r.bottom - 4, r.width, 4)
        pygame.draw.rect(surface, (6, 15, 30), base_strip.inflate(2, 2))
        pygame.draw.rect(surface, COLORS["tile_border"], base_strip)
        pygame.draw.polygon(surface, (45, 58, 78), [(r.left, r.bottom - 1), (r.left + 5, r.bottom - 4), (r.left + 5, r.bottom - 1)])
        pygame.draw.polygon(surface, (45, 58, 78), [(r.right, r.bottom - 1), (r.right - 5, r.bottom - 4), (r.right - 5, r.bottom - 1)])
