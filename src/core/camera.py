import math
import pygame
from src.core.settings import VIRTUAL_WIDTH, VIRTUAL_HEIGHT


class Camera:
    """Smooth 2D camera with dead-zone, directional look-ahead, POI focus panning, and culling."""

    def __init__(self, level_width: int, level_height: int) -> None:
        self.level_width = max(level_width, VIRTUAL_WIDTH)
        self.level_height = max(level_height, VIRTUAL_HEIGHT)
        self.x = 0.0
        self.y = 0.0
        self.target_x = 0.0
        self.target_y = 0.0
        self.lerp_speed_x = 6.5
        self.lerp_speed_y = 5.5

        # Deadzone dimensions around screen center
        self.deadzone_w = 90.0
        self.deadzone_h = 65.0

        # Screen shake & POI focus state
        self.effects_enabled = True  # master cinematic toggle, not the shake option
        self.shake_enabled = True
        self.look_ahead_enabled = True
        self.focus_enabled = True
        self.shake_timer = 0.0
        self.shake_magnitude = 0.0
        self.focus_target: tuple[float, float] | None = None
        self.focus_timer = 0.0

    def resize_bounds(self, level_width: int, level_height: int) -> None:
        self.level_width = max(level_width, VIRTUAL_WIDTH)
        self.level_height = max(level_height, VIRTUAL_HEIGHT)

    def snap_to(self, center_x: float, center_y: float) -> None:
        self.x = self._clamp_x(center_x - VIRTUAL_WIDTH * 0.5)
        self.y = self._clamp_y(center_y - VIRTUAL_HEIGHT * 0.5)
        self.target_x = self.x
        self.target_y = self.y
        self.focus_target = None
        self.focus_timer = 0.0

    def add_shake(self, duration: float = 0.18, magnitude: float = 5.0) -> None:
        if not self.effects_enabled or not self.shake_enabled:
            return
        self.shake_timer = max(self.shake_timer, duration)
        self.shake_magnitude = max(self.shake_magnitude, magnitude)

    def trigger_focus(
        self, world_x: float, world_y: float, duration: float = 1.15
    ) -> None:
        """Briefly pans camera toward an activated distant mechanism."""
        if not self.effects_enabled or not self.focus_enabled:
            return
        dist = math.hypot(
            world_x - (self.x + VIRTUAL_WIDTH * 0.5),
            world_y - (self.y + VIRTUAL_HEIGHT * 0.5),
        )
        if dist > 260.0:
            self.focus_target = (world_x, world_y)
            self.focus_timer = duration

    def update(self, target_rect: pygame.Rect, velocity_x: float, dt: float) -> None:
        if self.focus_timer > 0.0 and self.focus_target is not None:
            self.focus_timer = max(0.0, self.focus_timer - dt)
            fx, fy = self.focus_target
            self.target_x = self._clamp_x(fx - VIRTUAL_WIDTH * 0.5)
            self.target_y = self._clamp_y(fy - VIRTUAL_HEIGHT * 0.5)
            if self.focus_timer <= 0.0:
                self.focus_target = None
        else:
            look_ahead = (
                max(-105.0, min(105.0, velocity_x * 0.28))
                if self.effects_enabled and self.look_ahead_enabled
                else 0.0
            )
            cam_cx = self.x + VIRTUAL_WIDTH * 0.5
            cam_cy = self.y + VIRTUAL_HEIGHT * 0.54

            desired_cx = cam_cx
            dx = (target_rect.centerx + look_ahead) - cam_cx
            if abs(dx) > self.deadzone_w * 0.5:
                desired_cx += dx - math.copysign(self.deadzone_w * 0.5, dx)

            desired_cy = cam_cy
            dy = target_rect.centery - cam_cy
            if abs(dy) > self.deadzone_h * 0.5:
                desired_cy += dy - math.copysign(self.deadzone_h * 0.5, dy)

            self.target_x = self._clamp_x(desired_cx - VIRTUAL_WIDTH * 0.5)
            self.target_y = self._clamp_y(desired_cy - VIRTUAL_HEIGHT * 0.54)

        alpha_x = 1.0 - math.exp(-self.lerp_speed_x * dt)
        alpha_y = 1.0 - math.exp(-self.lerp_speed_y * dt)
        self.x += (self.target_x - self.x) * alpha_x
        self.y += (self.target_y - self.y) * alpha_y

        if self.shake_timer > 0.0:
            self.shake_timer = max(0.0, self.shake_timer - dt)

    def get_offset(self) -> tuple[int, int]:
        ox = int(round(self.x))
        oy = int(round(self.y))
        if self.effects_enabled and self.shake_enabled and self.shake_timer > 0.0:
            phase = self.shake_timer * 60.0
            ox += int(math.sin(phase * 2.3) * self.shake_magnitude)
            oy += int(math.cos(phase * 3.1) * self.shake_magnitude)
        return ox, oy

    def get_viewport_rect(self, margin: int = 120) -> pygame.Rect:
        ox, oy = self.get_offset()
        return pygame.Rect(
            ox - margin,
            oy - margin,
            VIRTUAL_WIDTH + margin * 2,
            VIRTUAL_HEIGHT + margin * 2,
        )

    def apply(self, rect: pygame.Rect) -> pygame.Rect:
        ox, oy = self.get_offset()
        return rect.move(-ox, -oy)

    def apply_point(self, pt: tuple[float, float]) -> tuple[int, int]:
        ox, oy = self.get_offset()
        return int(pt[0] - ox), int(pt[1] - oy)

    def _clamp_x(self, val: float) -> float:
        return max(0.0, min(val, float(self.level_width - VIRTUAL_WIDTH)))

    def _clamp_y(self, val: float) -> float:
        return max(0.0, min(val, float(self.level_height - VIRTUAL_HEIGHT)))