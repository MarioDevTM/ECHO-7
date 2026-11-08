import math
import pygame
from src.core.settings import SUBSTEP_MAX_DISP


class CollisionSystem:
    """Axis-separated sub-stepped AABB collision solver with crate pushing, platform carry, and conveyor integration."""

    @staticmethod
    def move_and_collide_crate(
        crate,
        dt: float,
        solids: list[pygame.Rect],
        other_crates: list,
    ) -> None:
        all_obstacles = solids + [c.rect for c in other_crates if c is not crate]

        dx = (crate.vx + crate.conveyor_vx) * dt
        dy = crate.vy * dt
        steps = max(1, math.ceil(max(abs(dx), abs(dy)) / SUBSTEP_MAX_DISP))
        for _ in range(steps):
            CollisionSystem.move_crate_x(crate, dx / steps, all_obstacles)
            step_y = crate.vy * dt / steps
            crate.pos_y += step_y
            crate.rect.y = round(crate.pos_y)
            for obs in all_obstacles:
                if crate.rect.colliderect(obs) and step_y:
                    if step_y > 0:
                        crate.rect.bottom = obs.top
                    else:
                        crate.rect.top = obs.bottom
                    crate.pos_y = float(crate.rect.y)
                    crate.vy = 0.0
        probe = crate.rect.move(0, 1)
        crate.on_ground = crate.vy >= 0 and probe.collidelist(all_obstacles) >= 0

    @staticmethod
    def move_crate_x(crate, dx, obstacles):
        crate.pos_x += dx
        crate.rect.x = round(crate.pos_x)
        for obs in obstacles:
            if dx and crate.rect.colliderect(obs):
                if dx > 0:
                    crate.rect.right = obs.left
                else:
                    crate.rect.left = obs.right
                crate.pos_x = float(crate.rect.x)
                crate.vx = 0.0

    @staticmethod
    def apply_platform_carry(
        entities: list, moving_platforms: list, solids: list[pygame.Rect]
    ) -> None:
        """Carries any grounded entity resting on top of a moving platform."""
        for mp in moving_platforms:
            if mp.dx == 0.0 and mp.dy == 0.0:
                continue
            previous = mp.rect.move(-mp.dx, -mp.dy)
            moves = []
            for ent in entities:
                if (ent.vy >= 0 and abs(ent.rect.bottom - previous.top) <= 1
                        and ent.rect.right > previous.left and ent.rect.left < previous.right):
                    moves.append((ent, mp.dx, mp.dy))
                elif mp.rect.colliderect(ent.rect):
                    if mp.dx > 0 and ent.rect.left >= previous.right:
                        moves.append((ent, mp.rect.right - ent.rect.left, 0))
                    elif mp.dx < 0 and ent.rect.right <= previous.left:
                        moves.append((ent, mp.rect.left - ent.rect.right, 0))
                    elif mp.dy > 0 and ent.rect.top >= previous.bottom:
                        moves.append((ent, 0, mp.rect.bottom - ent.rect.top))
                    elif mp.dy < 0 and ent.rect.bottom <= previous.top:
                        moves.append((ent, 0, mp.rect.top - ent.rect.bottom))
            # Stop the motor before pinning a rider against another solid.
            destinations = {e: e.rect.move(dx, dy) for e, dx, dy in moves}
            obstacles = solids + [p.rect for p in moving_platforms if p is not mp]
            if any(rect.collidelist(obstacles) >= 0 or any(
                    other is not ent and rect.colliderect(destinations.get(other, other.rect))
                    for other in entities) for ent, rect in destinations.items()):
                mp.set_state(mp.previous_state)
                continue
            for ent, dx, dy in moves:
                ent.pos_x += dx
                ent.pos_y += dy
                ent.rect.topleft = round(ent.pos_x), round(ent.pos_y)

    @staticmethod
    def move_and_collide_player(
        player,
        dt: float,
        solids: list[pygame.Rect],
        crates: list,
        one_ways: list[pygame.Rect] | None = None,
    ) -> tuple[bool, float]:
        """Sub-stepped player movement resolving tiles, pushing crates, conveyors, and detecting landing."""
        one_ways = one_ways or []
        player.was_on_ground = player.on_ground
        player.pushing_crate = False
        impact_vy = player.vy
        player.dash_blocked = False

        eff_vx = (player.vx if player.dashing else
                  player.vx + player.external_vx + player.conveyor_vx)
        total_dx = eff_vx * dt
        total_dy = player.vy * dt
        max_disp = max(abs(total_dx), abs(total_dy))
        steps = max(1, int(math.ceil(max_disp / SUBSTEP_MAX_DISP)))
        step_dt = dt / steps

        for _ in range(steps):
            # --- Horizontal Step ---
            dx = eff_vx * step_dt
            player.pos_x += dx
            player.rect.x = int(round(player.pos_x))

            # Check crates first so player can push them
            for crate in crates:
                if player.rect.colliderect(crate.rect):
                    overlap_y = min(player.rect.bottom, crate.rect.bottom) - max(
                        player.rect.top, crate.rect.top
                    )
                    if overlap_y > 0 and dx:
                        player.pushing_crate = not player.dashing
                        obstacles = solids + [c.rect for c in crates if c is not crate]
                        if not player.dashing:
                            CollisionSystem.move_crate_x(crate, dx * 0.78, obstacles)
                        else:
                            player.dash_blocked = True
                        if dx > 0:
                            player.rect.right = crate.rect.left
                        elif dx < 0:
                            player.rect.left = crate.rect.right
                        player.pos_x = float(player.rect.x)
                        if player.dashing:
                            player.vx = 0.0

            # Check solid world geometry
            for obs in solids:
                if player.rect.colliderect(obs):
                    if dx > 0:
                        player.rect.right = obs.left
                    elif dx < 0:
                        player.rect.left = obs.right
                    player.pos_x = float(player.rect.x)
                    player.vx = 0.0
                    if player.dashing:
                        player.dash_blocked = True

            # --- Vertical Step ---
            previous_bottom = player.rect.bottom
            dy = player.vy * step_dt
            player.pos_y += dy
            player.rect.y = int(round(player.pos_y))
            player.on_ground = False

            all_vertical_solids = solids + [c.rect for c in crates]
            # One-way ledges only exist when falling across their top face.
            if dy > 0:
                all_vertical_solids += [ledge for ledge in one_ways
                                        if previous_bottom <= ledge.top + 1]
            for obs in all_vertical_solids:
                if player.rect.colliderect(obs):
                    if dy > 0:
                        player.rect.bottom = obs.top
                        player.on_ground = True
                    elif dy < 0:
                        player.rect.top = obs.bottom
                    player.pos_y = float(player.rect.y)
                    player.vy = 0.0
                    if player.dashing:
                        player.dash_blocked = True

        # Ground probe (1px below feet) for stable platform tracking
        if not player.on_ground and player.vy >= 0.0:
            probe = pygame.Rect(
                player.rect.left + 2, player.rect.bottom, player.rect.width - 4, 2
            )
            all_vertical_solids = solids + [c.rect for c in crates]
            all_vertical_solids += [ledge for ledge in one_ways
                                    if player.rect.bottom <= ledge.top + 1]
            if any(probe.colliderect(obs) for obs in all_vertical_solids):
                player.on_ground = True

        landed_this_frame = player.on_ground and not player.was_on_ground
        if landed_this_frame:
            player.notify_landed(impact_vy)

        return landed_this_frame, impact_vy

    @staticmethod
    def is_crushed(player_rect: pygame.Rect, solids: list[pygame.Rect]) -> bool:
        """Detects if a closing door or moving platform has squeezed the player into solid geometry."""
        inner_core = player_rect.inflate(-10, -12)
        return any(inner_core.colliderect(obs) for obs in solids)