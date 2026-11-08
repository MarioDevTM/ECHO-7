"""Small, authored precision-platforming elements; no new dependency on the puzzle engine.

Every object is data-driven, reversible on checkpoint reset, and drawn using
pygame primitives. Interactions are resolved in the 120 Hz simulation tick.
"""
from __future__ import annotations
import pygame
from src.core.settings import COLORS, SPRING_IMPULSE


class PrecisionWorld:
    def __init__(self, data: dict):
        self.springs = [dict(s, rect=pygame.Rect(s['x'], s['y'], s['w'], s.get('h', 12)), cooldown=0.0)
                        for s in data.get('springs', [])]
        self.recharges = [dict(c, rect=pygame.Rect(c['x'], c['y'], 28, 28), cooldown=0.0)
                          for c in data.get('dash_recharges', [])]
        self.one_ways = [pygame.Rect(p['x'], p['y'], p['w'], p.get('h', 14))
                         for p in data.get('one_way_platforms', [])]
        self.barriers = [dict(b, rect=pygame.Rect(b['x'], b['y'], b['w'], b['h']), broken=False)
                         for b in data.get('dash_barriers', [])]

    def solid_barriers(self) -> list[pygame.Rect]:
        return [b['rect'] for b in self.barriers if not b['broken']]

    def snapshot(self) -> dict:
        return {
            'springs': [s['cooldown'] for s in self.springs],
            'recharges': [r['cooldown'] for r in self.recharges],
            'barriers': [b['broken'] for b in self.barriers],
        }

    def restore(self, state: dict) -> None:
        for obj, seconds in zip(self.springs, state.get('springs', [])):
            obj['cooldown'] = float(seconds)
        for obj, seconds in zip(self.recharges, state.get('recharges', [])):
            obj['cooldown'] = float(seconds)
        for obj, broken in zip(self.barriers, state.get('barriers', [])):
            obj['broken'] = bool(broken)

    def tick(self, dt, player, landed=False, impact_vy=0.0):
        """Called after world collision, before hazards/checkpoints are tested."""
        sounds = []
        for s in self.springs:
            s['cooldown'] = max(0.0, s['cooldown'] - dt)
            # Trigger only while the feet are on the pad and the player is
            # descending. Avoid touching it from below or the side.
            r = s['rect']
            feet = pygame.Rect(player.rect.x + 3, player.rect.bottom - 7,
                               player.rect.width - 6, 9)
            if (s['cooldown'] <= 0 and player.alive and not player.dashing and
                    landed and impact_vy > 95 and feet.colliderect(r) and
                    player.rect.bottom <= r.bottom + 6):
                player.vy = -abs(float(s.get('impulse', SPRING_IMPULSE)))
                player.on_ground = False
                player.coyote_timer = 0.0
                player.refresh_dash()
                player.squash_x, player.squash_y = 0.80, 1.28
                s['cooldown'] = 0.38
                sounds.append('spring')

        for r in self.recharges:
            r['cooldown'] = max(0.0, r['cooldown'] - dt)
            if (r['cooldown'] <= 0 and player.can_dash and player.dash_charges == 0
                    and player.rect.colliderect(r['rect'])):
                player.refresh_dash()
                r['cooldown'] = float(r.get('respawn', 1.5))
                sounds.append('dash_recharge')
        return sounds

    def break_with_dash(self, player, dt, other_solids: list[pygame.Rect]) -> bool:
        """Break only a barrier directly along the dash's swept movement."""
        if not player.dashing or not player.can_dash:
            return False
        dx = player.vx * dt
        dy = player.vy * dt
        proposed = player.rect.move(round(dx), round(dy))
        swept = player.rect.union(proposed)
        if any(swept.colliderect(solid) for solid in other_solids):
            return False
        result = False
        for b in self.barriers:
            if not b['broken'] and swept.colliderect(b['rect']):
                b['broken'] = True
                result = True
        return result

    def draw(self, surface, camera, phase: float) -> None:
        for p in self.one_ways:
            r = camera.apply(p)
            if not r.colliderect(surface.get_rect()):
                continue
            # Structural suspension cables & end-bracket mounts (visual only; collision unchanged)
            cable_col = (34, 48, 66)
            bracket_col = (58, 76, 98)
            pygame.draw.line(surface, cable_col, (r.left + 6, max(0, r.top - 52)), (r.left + 6, r.top), 2)
            pygame.draw.line(surface, cable_col, (r.right - 7, max(0, r.top - 52)), (r.right - 7, r.top), 2)
            pygame.draw.polygon(surface, bracket_col, [
                (r.left + 2, r.bottom), (r.left + 12, r.bottom), (r.left + 6, r.bottom + 7)
            ])
            pygame.draw.polygon(surface, bracket_col, [
                (r.right - 13, r.bottom), (r.right - 3, r.bottom), (r.right - 7, r.bottom + 7)
            ])
            pygame.draw.rect(surface, (36, 48, 66), r, border_radius=2)
            pygame.draw.rect(surface, COLORS['tile_border'], r, width=2, border_radius=2)
            pygame.draw.line(surface, COLORS['platform_glow'], (r.left + 4, r.top + 2), (r.right - 5, r.top + 2), 2)
            for x in range(r.left + 10, r.right - 8, 16):
                pygame.draw.line(surface, (74, 96, 122), (x, r.bottom - 3), (x + 6, r.top + 5), 1)
        for s in self.springs:
            r = camera.apply(s['rect'])
            pygame.draw.rect(surface, (40, 90, 101), r, border_radius=3)
            pygame.draw.rect(surface, (110, 239, 190) if s['cooldown'] <= 0 else (70, 122, 115),
                             pygame.Rect(r.x + 2, r.y + 1, r.w - 4, 4), border_radius=2)
            for x in range(r.left + 7, r.right - 4, 12):
                pygame.draw.line(surface, COLORS['ui_accent'], (x, r.bottom - 3),
                                 (x + 4, r.top + 5), 1)
        for charge in self.recharges:
            r = camera.apply(charge['rect'])
            color = COLORS['ui_accent'] if charge['cooldown'] <= 0 else COLORS['checkpoint_idle']
            pygame.draw.circle(surface, color, r.center, 13, 2)
            pygame.draw.polygon(surface, color, [
                (r.centerx + 2, r.y + 5), (r.centerx - 6, r.centery + 2),
                (r.centerx + 1, r.centery + 2), (r.centerx - 2, r.bottom - 4),
                (r.centerx + 7, r.centery - 2), (r.centerx, r.centery - 2)])
        for barrier in self.barriers:
            if barrier['broken']:
                continue
            r = camera.apply(barrier['rect'])
            pygame.draw.rect(surface, (60, 80, 99), r)
            pygame.draw.rect(surface, COLORS['ui_warning'], r, 2)
            for y in range(r.top + 7, r.bottom - 4, 16):
                pygame.draw.line(surface, COLORS['ui_warning'],
                                 (r.left + 3, y), (r.right - 3, y + 5), 2)
