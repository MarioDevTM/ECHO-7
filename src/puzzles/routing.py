from src.visuals import get_env_sprite
"""Reusable, checkpoint-safe signal memories and mutually exclusive power routes."""
import pygame
from src.core.settings import COLORS


class LatchingRelay:
    """An operator must store a momentary upstream condition before freeing its source."""

    def __init__(self, link_id, x, y, required_links):
        self.link_id = link_id
        self.rect = pygame.Rect(int(x), int(y) - 43, 38, 43)
        self.interact_rect = self.rect.inflate(24, 18)
        self.required_links = list(required_links)
        self.latched = False
        self.denied_flash = 0.0

    def interact(self, signals):
        if self.latched:
            return False
        if not all(link in signals for link in self.required_links):
            self.denied_flash = 0.5
            return False
        self.latched = True
        return True

    def get_state(self):
        return {"latched": self.latched}

    def set_state(self, state):
        self.latched = bool(state.get("latched", False))
        self.denied_flash = 0.0

    def draw(self, surface, camera, prompted=False, font=None):
        r = camera.apply(self.rect)
        sp = get_env_sprite('lever_switch_red', (r.width, r.height))
        if sp is not None:
            surface.blit(sp, r.topleft)
        col = COLORS['plate_active'] if self.latched else COLORS['ui_warning']
        if self.denied_flash > 0:
            col = COLORS['switch_off']
        pygame.draw.rect(surface, COLORS['tile_dark'], r, border_radius=4)
        pygame.draw.rect(surface, col, r, 2, border_radius=4)
        pygame.draw.circle(surface, col, (r.centerx, r.centery - 6), 7)
        pygame.draw.line(surface, col, (r.centerx - 8, r.bottom - 8),
                         (r.centerx + 8, r.bottom - 8), 3)
        if prompted and font:
            msg = 'MEMORY HELD' if self.latched else '[E] STORE POWER'
            label = font.render(msg, True, COLORS['ui_text'])
            surface.blit(label, label.get_rect(center=(r.centerx, r.top - 18)))


class RoutingConsole:
    """Physical control for a shared, two-output routing bus."""

    def __init__(self, panel_id, route_id, x, y, a_signal, b_signal,
                 required_links=()):
        self.panel_id = panel_id
        self.route_id = route_id
        self.a_signal = a_signal
        self.b_signal = b_signal
        self.required_links = list(required_links)
        self.rect = pygame.Rect(int(x), int(y) - 44, 38, 44)
        self.interact_rect = self.rect.inflate(24, 18)

    def draw(self, surface, camera, mode, prompted=False, font=None):
        r = camera.apply(self.rect)
        sp = get_env_sprite('console_cyan' if mode == 0 else 'console_magenta', (r.width, r.height))
        if sp is not None:
            surface.blit(sp, r.topleft)
        else:
            pygame.draw.rect(surface, COLORS['tile_dark'], r, border_radius=5)
        pygame.draw.rect(surface, COLORS['ui_accent'], r, width=2, border_radius=5)
        for i in (0, 1):
            lamp = (COLORS['plate_active'] if mode == i else COLORS['plate_idle'])
            pygame.draw.circle(surface, lamp, (r.centerx + (i * 16 - 8), r.centery), 5)
        if prompted and font:
            msg = '[E] -> EXIT' if mode == 0 else '[E] -> FERRY'
            label = font.render(msg, True, COLORS['ui_text'])
            surface.blit(label, label.get_rect(center=(r.centerx, r.top - 18)))
