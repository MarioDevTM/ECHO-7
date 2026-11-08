"""Event-sensitive visual-only robot animation with phase-continuous frame integration.

Frames remain 36x56 and retain their original approved rounded-helmet design.
Incremental phase accumulation prevents frame-skipping jitter during acceleration
or deceleration, and velocity hysteresis prevents idle/run flicker on platforms.
"""
from pathlib import Path
import pygame

ART = Path(__file__).resolve().parents[2] / 'data' / 'art' / 'player'
_CACHE = {}
_TRAIL_CACHE = {}
FRAMES = {
    'idle': 4, 'run': 8, 'jump': 3, 'fall': 3, 'land': 3,
    'interact': 4, 'turn': 2, 'death': 4, 'respawn': 4,
    'dash': 3, 'crouch': 2, 'wall': 2, 'climb': 4,
}
SPEEDS = {
    'idle': 3.2, 'run': 12.0, 'jump': 8.5, 'fall': 8.5,
    'land': 16.0, 'interact': 10.0, 'turn': 14.0,
    'death': 10.0, 'respawn': 12.0, 'crouch': 4.0,
    'dash': 16.0, 'wall': 5.0, 'climb': 7.5,
}
ONESHOT = {'land', 'interact', 'turn', 'death', 'respawn'}
PRIORITY = {
    'death': 100, 'respawn': 90, 'dash': 70, 'wall': 65,
    'jump': 60, 'fall': 60, 'land': 53, 'climb': 52,
    'interact': 46, 'crouch': 42, 'turn': 35,
    'run': 20, 'idle': 10,
}


class AnimationController:
    """Pure sprite timeline state with incremental phase integration (zero speed-change jitter)."""
    def __init__(self):
        self.state = 'idle'
        self.entered_at = 0.0
        self.last_now = 0.0
        self.phase_accum = 0.0
        self.last_ground = None
        self.last_facing = None
        self.last_flash = False
        self._land_once = False

    def _desired(self, p):
        if not p.alive:
            return 'death'
        if getattr(p, 'respawn_visual_timer', 0.0) > 0:
            return 'respawn'
        if p.dashing:
            return 'dash'
        if p.wall_sliding:
            return 'wall'
        if p.on_ladder:
            return 'climb'
        if not p.on_ground:
            return 'jump' if p.vy < -25 else 'fall'
        if self.last_ground is False and p.on_ground:
            self._land_once = True
        if self._land_once:
            return 'land'
        flash = p.interact_flash > 0
        if flash and not self.last_flash:
            return 'interact'
        if p.pushing_crate:
            return 'interact'
        if p.crouching:
            return 'crouch'
        if self.last_facing is not None and self.last_facing != p.facing:
            return 'turn'
        # Hysteresis prevents micro-velocity jitter between run and idle
        speed_threshold = 16.0 if self.state == 'run' else 25.0
        return 'run' if abs(p.vx) > speed_threshold else 'idle'

    def frame(self, p):
        now = float(getattr(p, 'anim_timer', 0.0))
        if not p.alive:
            now += float(getattr(p, 'death_anim_clock', 0.0))
        dt = max(0.0, min(0.25, now - self.last_now)) if self.last_now > 0.0 else max(0.0, now - self.entered_at)
        self.last_now = now

        desired = self._desired(p)
        old = self.state
        elapsed = max(0.0, now - self.entered_at)
        length = FRAMES[old] / SPEEDS[old]
        active_one_shot = old in ONESHOT and elapsed < length
        retain = active_one_shot and PRIORITY[desired] <= PRIORITY[old]
        if old == 'land' and not p.on_ground:
            retain = False
        if old == 'death' and p.alive:
            retain = False
        if old == 'interact' and p.dashing:
            retain = False
        if old == 'land' and elapsed >= length:
            self._land_once = False
            if desired == 'land':
                desired = 'run' if abs(p.vx) > 25 else 'idle'
        if not retain and desired != old:
            self.state = desired
            self.entered_at = now
            self.phase_accum = 0.0
            elapsed = 0.0
        elif retain:
            desired = old

        fps = SPEEDS[self.state]
        if self.state == 'run':
            fps *= max(0.50, min(1.45, abs(p.vx) / 240.0))
            self.phase_accum += dt * fps
            index = int(self.phase_accum) % FRAMES[self.state]
        elif self.state == 'climb':
            if abs(p.vy) > 10:
                self.phase_accum += dt * fps
            index = int(self.phase_accum) % FRAMES[self.state]
        elif self.state in ONESHOT:
            index = min(FRAMES[self.state] - 1, int(elapsed * fps))
        else:
            self.phase_accum += dt * fps
            index = int(self.phase_accum) % FRAMES[self.state]

        self.last_ground = bool(p.on_ground)
        self.last_facing = p.facing
        self.last_flash = p.interact_flash > 0
        return self.state, index


def frame_for(player):
    controller = getattr(player, '_sprite_controller', None)
    if controller is None:
        controller = AnimationController()
        player._sprite_controller = controller
    return controller.frame(player)


def _get_frame(state, index, facing):
    key = (state, index, facing)
    if key not in _CACHE:
        original = (state, index, 1)
        if original not in _CACHE:
            pic = pygame.image.load(str(ART / f'{state}_{index}.png'))
            if pygame.display.get_init() and pygame.display.get_surface() is not None:
                pic = pic.convert_alpha()
            _CACHE[original] = pic
        base = _CACHE[original]
        _CACHE[key] = pygame.transform.flip(base, True, False) if facing < 0 else base
    return _CACHE[key]


def _get_trail_silhouette(state, index, facing, alpha_step: int):
    key = (state, index, facing, alpha_step)
    if key not in _TRAIL_CACHE:
        base = _get_frame(state, index, facing).copy()
        tint = pygame.Surface(base.get_size(), pygame.SRCALPHA)
        tint.fill((40, 215, 250, max(24, min(140, alpha_step * 36))))
        base.blit(tint, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        _TRAIL_CACHE[key] = base
    return _TRAIL_CACHE[key]


def draw_robot(surface, camera, player):
    state, index = frame_for(player)
    pic = _get_frame(state, index, player.facing)
    rect = camera.apply(player.rect)
    x = rect.centerx - pic.get_width() // 2
    y = rect.bottom - pic.get_height() + 4
    # Render pixel-art dash afterimages instead of raw circles
    for px, py, life in player.dash_trail[-4:]:
        sx, sy = camera.apply_point((px, py))
        step = max(1, min(3, int(round(3 * life / 0.18))))
        ghost = _get_trail_silhouette('dash', 0, player.facing, step)
        surface.blit(ghost, (sx - ghost.get_width() // 2, sy - ghost.get_height() // 2))
    surface.blit(pic, (x, y))
