import math
import pygame
from src.core.settings import (
    PLAYER_WIDTH,
    PLAYER_HEIGHT,
    PLAYER_CROUCH_HEIGHT,
    GRAVITY,
    MAX_FALL_SPEED,
    WALK_SPEED,
    RUN_SPEED,
    CROUCH_SPEED,
    LADDER_SPEED,
    GROUND_ACCEL,
    GROUND_DECEL,
    AIR_ACCEL,
    AIR_DECEL,
    JUMP_VELOCITY,
    JUMP_CUT_MULTIPLIER,
    COYOTE_TIME,
    JUMP_BUFFER_TIME,
    COLORS,
    WALL_SLIDE_SPEED,
    WALL_JUMP_HORIZONTAL,
    WALL_JUMP_VERTICAL,
    WALL_JUMP_CONTROL_LOCK,
    DASH_SPEED,
    DASH_DURATION,
    DASH_EXIT_SPEED,
    DASH_RECOVERY,
)


class Player:
    """Responsive 2D platformer controller with ladders, crouching, wind, water, and coyote time."""

    def __init__(self, x: float, y: float) -> None:
        self.rect = pygame.Rect(int(x), int(y), PLAYER_WIDTH, PLAYER_HEIGHT)
        self.pos_x = float(self.rect.x)
        self.pos_y = float(self.rect.y)
        self.vx = 0.0
        self.vy = 0.0

        self.on_ground = False
        self.was_on_ground = False
        self.on_ladder = False
        self.crouching = False
        self.in_water = False
        self.facing = 1
        self.is_running = False
        self.pushing_crate = False

        self.interact_flash = 0.0

        # Surface speed, horizontal air velocity, and vertical air acceleration.
        self.conveyor_vx = 0.0
        self.external_vx = 0.0
        self.external_vy = 0.0

        # Jump timers
        self.coyote_timer = 0.0
        self.jump_buffer_timer = 0.0
        self.jump_held = False

        # Animation & visual feedback
        self.anim_timer = 0.0
        self.death_anim_clock = 0.0  # rendering only
        self.respawn_visual_timer = 0.0  # rendering only
        self.turn_visual_timer = 0.0  # rendering only
        self.squash_x = 1.0
        self.squash_y = 1.0
        self.alive = True

        # Explicitly unlocked by the room: old stages retain their original routes.
        self.can_wall_jump = False
        self.can_dash = False
        self.wall_side = 0  # -1 left wall, +1 right wall
        self.wall_sliding = False
        self.wall_jump_lock = 0.0
        self.dash_charges = 1
        self.dash_timer = 0.0
        self.dash_recovery = 0.0
        self.dash_vector = (0.0, 0.0)
        self.dash_blocked = False
        self.dash_trail = []
        self.drop_through_timer = 0.0

    def set_position(self, x: float, y: float) -> None:
        self.rect.height = PLAYER_HEIGHT
        self.crouching = False
        self.on_ladder = False
        self.pos_x = float(x)
        self.pos_y = float(y)
        self.rect.topleft = (int(round(self.pos_x)), int(round(self.pos_y)))
        self.vx = 0.0
        self.vy = 0.0
        self.conveyor_vx = 0.0
        self.external_vx = 0.0
        self.external_vy = 0.0
        self.coyote_timer = 0.0
        self.jump_buffer_timer = 0.0
        self.on_ground = False
        self.wall_side = 0
        self.wall_sliding = False
        self.wall_jump_lock = 0.0
        self.dash_charges = 1
        self.dash_timer = 0.0
        self.dash_recovery = 0.0
        self.dash_blocked = False
        self.dash_trail.clear()
        self.drop_through_timer = 0.0

    @property
    def dashing(self) -> bool:
        return self.dash_timer > 0.0

    def begin_dash(self, horizontal: int, vertical: int) -> bool:
        if (not self.can_dash or self.dash_charges <= 0 or self.dashing or
                self.dash_recovery > 0 or self.on_ladder):
            return False
        if horizontal == 0 and vertical == 0:
            horizontal = self.facing
        length = math.hypot(horizontal, vertical)
        self.dash_vector = (horizontal / length, vertical / length)
        self.dash_charges -= 1
        self.dash_timer = DASH_DURATION
        self.dash_recovery = DASH_RECOVERY
        self.on_ground = False
        self.on_ladder = False
        self.coyote_timer = 0.0
        self.jump_buffer_timer = 0.0
        self.wall_sliding = False
        self.dash_blocked = False
        self.vx = self.dash_vector[0] * DASH_SPEED
        self.vy = self.dash_vector[1] * DASH_SPEED
        if horizontal:
            self.facing = 1 if horizontal > 0 else -1
        return True

    def end_dash(self) -> None:
        if self.dash_timer <= 0.0:
            return
        self.dash_timer = 0.0
        self.vx = max(-DASH_EXIT_SPEED, min(DASH_EXIT_SPEED, self.vx))
        self.vy = max(-DASH_EXIT_SPEED, min(DASH_EXIT_SPEED, self.vy))

    def refresh_dash(self) -> None:
        self.dash_charges = 1

    def check_wall(self, climbable: list[pygame.Rect]) -> None:
        self.wall_side = 0
        if not self.can_wall_jump or self.on_ground or self.on_ladder:
            self.wall_sliding = False
            return
        # Ignore ground edges: wall contact must extend alongside the torso.
        core_top = self.rect.top + 6
        core_height = max(3, self.rect.height - 12)
        for direction in (-1, 1):
            probe = pygame.Rect(
                self.rect.left - 2 if direction < 0 else self.rect.right,
                core_top, 2, core_height)
            if any(probe.colliderect(wall) for wall in climbable):
                self.wall_side = direction
                break

    def after_collision(self, climbable: list[pygame.Rect]) -> None:
        if self.dashing and self.dash_blocked:
            self.end_dash()
        if self.on_ground:
            self.refresh_dash()
            self.wall_sliding = False
        self.check_wall(climbable)
        if self.dash_timer <= 0.0:
            self.dash_blocked = False

    def try_drop_through(self, one_ways: list[pygame.Rect]) -> bool:
        """Down + jump descends through a ledge only when standing on it."""
        if not self.on_ground:
            return False
        feet = pygame.Rect(self.rect.x + 3, self.rect.bottom, self.rect.width - 6, 2)
        on_ledge = any(feet.colliderect(platform) and
                       self.rect.bottom <= platform.top + 1 for platform in one_ways)
        if not on_ledge:
            return False
        self.drop_through_timer = 0.23
        self.on_ground = False
        self.coyote_timer = 0.0
        self.vy = 100.0
        self.pos_y += 3.0
        self.rect.y = round(self.pos_y)
        return True

    def queue_jump(self) -> None:
        self.jump_buffer_timer = JUMP_BUFFER_TIME
        self.jump_held = True

    def release_jump(self) -> None:
        self.jump_held = False
        if self.vy < 0.0 and not self.on_ladder and not self.dashing:
            self.vy *= JUMP_CUT_MULTIPLIER

    def _set_crouch_state(self, want_crouch: bool, solids: list[pygame.Rect]) -> None:
        if want_crouch and not self.crouching:
            diff = PLAYER_HEIGHT - PLAYER_CROUCH_HEIGHT
            self.rect.height = PLAYER_CROUCH_HEIGHT
            self.pos_y += diff
            self.rect.y = int(round(self.pos_y))
            self.crouching = True
        elif not want_crouch and self.crouching:
            diff = PLAYER_HEIGHT - PLAYER_CROUCH_HEIGHT
            test_rect = pygame.Rect(
                self.rect.x, self.rect.bottom - PLAYER_HEIGHT, PLAYER_WIDTH, PLAYER_HEIGHT
            )
            if not any(test_rect.colliderect(s) for s in solids):
                self.pos_y = float(test_rect.y)
                self.rect.height = PLAYER_HEIGHT
                self.rect.y = test_rect.y
                self.crouching = False

    def update_timers_and_input(
        self,
        dt: float,
        keys: pygame.key.ScancodeWrapper,
        keybinds: dict[str, list[int]],
        ladders: list[pygame.Rect] | None = None,
        solids: list[pygame.Rect] | None = None,
    ) -> bool:
        """Updates horizontal/vertical velocity, ladders, crouching, and jump states."""
        ladders = ladders or []
        solids = solids or []
        self.anim_timer += dt
        self.respawn_visual_timer = max(0.0, self.respawn_visual_timer - dt)
        self.turn_visual_timer = max(0.0, self.turn_visual_timer - dt)
        self.interact_flash = max(0, self.interact_flash - dt)
        self.wall_jump_lock = max(0.0, self.wall_jump_lock - dt)
        self.drop_through_timer = max(0.0, self.drop_through_timer - dt)
        self.dash_recovery = max(0.0, self.dash_recovery - dt)
        self.dash_trail = [t for t in self.dash_trail if t[2] > 0.0]
        for trail in self.dash_trail:
            trail[2] -= dt
        self.check_wall(getattr(self, 'wall_surfaces', solids))

        self.squash_x += (1.0 - self.squash_x) * min(1.0, dt * 14.0)
        self.squash_y += (1.0 - self.squash_y) * min(1.0, dt * 14.0)

        move_left = any(keys[k] for k in keybinds["left"])
        move_right = any(keys[k] for k in keybinds["right"])
        move_up = any(keys[k] for k in keybinds.get("up", [pygame.K_w, pygame.K_UP]))
        move_down = any(keys[k] for k in keybinds.get("down", [pygame.K_s, pygame.K_DOWN]))
        self.is_running = any(keys[k] for k in keybinds["run"])

        # Dashes have an authored fixed velocity and no gravity/steering.
        # The collision solver still substeps against every solid obstacle.
        if self.dashing:
            self.dash_timer = max(0.0, self.dash_timer - dt)
            if self.dash_timer <= 0:
                self.vx = self.dash_vector[0] * DASH_EXIT_SPEED
                self.vy = self.dash_vector[1] * DASH_EXIT_SPEED
            else:
                self.vx = self.dash_vector[0] * DASH_SPEED
                self.vy = self.dash_vector[1] * DASH_SPEED
                self.dash_trail.append([self.rect.centerx, self.rect.centery, 0.18])
                return False

        # Check ladder attachment
        touching_ladder = any(self.rect.colliderect(lad) for lad in ladders)
        if not touching_ladder:
            self.on_ladder = False
        elif (move_up or move_down) and not self.on_ladder:
            self.on_ladder = True
            self.vy = 0.0

        # Handle crouching on ground when not on a ladder
        want_crouch = move_down and self.on_ground and not self.on_ladder
        self._set_crouch_state(want_crouch, solids)

        direction = (1 if move_right else 0) - (1 if move_left else 0)
        if self.on_ladder and direction == 0:
            self.vx = 0.0
        if direction != 0:
            if direction != self.facing and self.on_ground:
                self.turn_visual_timer = 0.14
            self.facing = direction

        if self.crouching:
            max_speed = CROUCH_SPEED
        elif self.is_running:
            max_speed = RUN_SPEED
        else:
            max_speed = WALK_SPEED

        if self.pushing_crate:
            max_speed *= 0.65
        if self.in_water:
            max_speed *= 0.72

        accel = GROUND_ACCEL if self.on_ground else AIR_ACCEL
        decel = GROUND_DECEL if self.on_ground else AIR_DECEL

        if self.wall_jump_lock > 0.0 and not self.on_ground:
            direction = 0  # preserve the initial outward wall-jump impulse
            decel = 0.0
        if direction != 0:
            target_vx = direction * max_speed
            if self.vx < target_vx:
                self.vx = min(target_vx, self.vx + accel * dt)
            elif self.vx > target_vx:
                self.vx = max(target_vx, self.vx - accel * dt)
        else:
            if self.vx > 0:
                self.vx = max(0.0, self.vx - decel * dt)
            elif self.vx < 0:
                self.vx = min(0.0, self.vx + decel * dt)


        # Ladder vertical movement vs standard gravity
        if self.on_ladder:
            self.coyote_timer = COYOTE_TIME
            climb_dir = (1 if move_down else 0) - (1 if move_up else 0)
            self.vy = climb_dir * LADDER_SPEED
        else:
            if self.on_ground:
                self.coyote_timer = COYOTE_TIME
            else:
                self.coyote_timer = max(0.0, self.coyote_timer - dt)

            grav = GRAVITY * (0.45 if self.in_water else 1.0)
            max_fall = MAX_FALL_SPEED * (0.5 if self.in_water else 1.0)
            self.vy = min(max_fall, self.vy + (grav + self.external_vy) * dt)
            self.wall_sliding = (self.can_wall_jump and self.wall_side != 0 and
                                 self.vy > 0 and not self.in_water and
                                 ((self.wall_side < 0 and move_left) or
                                  (self.wall_side > 0 and move_right)))
            if self.wall_sliding:
                self.vy = min(self.vy, WALL_SLIDE_SPEED)

        if self.jump_buffer_timer > 0.0:
            self.jump_buffer_timer = max(0.0, self.jump_buffer_timer - dt)

        jumped = False
        # Wall-jumps take precedence over a buffered ground jump only when
        # airborne and no coyote jump remains. Wall sides exclude puzzle doors.
        if (self.jump_buffer_timer > 0.0 and self.can_wall_jump and
                self.wall_side != 0 and not self.on_ground and
                self.coyote_timer <= 0 and not self.in_water):
            self.vx = -self.wall_side * WALL_JUMP_HORIZONTAL
            self.vy = WALL_JUMP_VERTICAL
            self.wall_jump_lock = WALL_JUMP_CONTROL_LOCK
            self.facing = -self.wall_side
            self.wall_side = 0
            self.wall_sliding = False
            self.jump_buffer_timer = 0.0
            self.coyote_timer = 0.0
            self.squash_x, self.squash_y = 0.80, 1.18
            jumped = True
        if not jumped and self.jump_buffer_timer > 0.0 and (self.coyote_timer > 0.0 or self.in_water):
            self.vy = JUMP_VELOCITY * (0.82 if self.in_water else 1.0)
            self.on_ground = False
            self.on_ladder = False
            self.coyote_timer = 0.0
            self.jump_buffer_timer = 0.0
            self.squash_x = 0.78
            self.squash_y = 1.24
            jumped = True

        if jumped or self.on_ladder:
            self.conveyor_vx = 0.0
        return jumped

    def notify_landed(self, impact_vy: float) -> None:
        if not self.was_on_ground and impact_vy > 180.0:
            self.squash_x = 1.22
            self.squash_y = 0.80

    def draw(self, surface: pygame.Surface, camera) -> None:
        """Sprite-only redesign; physics and collision footprint are unchanged."""
        from src.visuals.robot_sprite import draw_robot
        draw_robot(surface, camera, self)
