import math
import pygame
from src.core.settings import COLORS, PLAYER_HEIGHT, PLAYER_WIDTH


class Checkpoint:
    """Respawn beacon that records player position and deep puzzle/crate/platform state."""

    def __init__(self, cp_id: str, x: int, y: int) -> None:
        self.cp_id = cp_id
        self.rect = pygame.Rect(x, y - 56, 28, 56)
        self.respawn_pos = (float(x), float(y - 48))
        self.activated = False
        self.anim_phase = 0.0

    def update(self, dt: float) -> None:
        self.anim_phase += dt * 4.5

    def draw(self, surface: pygame.Surface, camera, is_current: bool) -> None:
        r = camera.apply(self.rect)
        pole = pygame.Rect(r.centerx - 3, r.top + 10, 6, r.height - 10)
        pygame.draw.rect(surface, COLORS["tile_border"], pole, border_radius=2)

        beacon_col = (
            COLORS["checkpoint_active"]
            if is_current
            else (
                COLORS["platform_glow"]
                if self.activated
                else COLORS["checkpoint_idle"]
            )
        )
        head = pygame.Rect(r.centerx - 9, r.top, 18, 14)
        pygame.draw.rect(surface, beacon_col, head, border_radius=4)

        if is_current:
            pulse = int(4 + math.sin(self.anim_phase) * 3)
            glow_rect = head.inflate(pulse * 2, pulse * 2)
            pygame.draw.rect(
                surface,
                COLORS["checkpoint_active"],
                glow_rect,
                width=1,
                border_radius=6,
            )


class CheckpointManager:
    """Manages level checkpoints and stores deep state snapshots for deterministic respawning."""

    def __init__(self, initial_spawn: tuple[float, float], audio=None) -> None:
        self.audio = audio
        self.checkpoints: list[Checkpoint] = []
        self.active_cp_id: str | None = None
        self.respawn_pos = initial_spawn
        self.saved_snapshot: dict | None = None

    def add_checkpoint(self, cp: Checkpoint) -> None:
        self.checkpoints.append(cp)

    def save_snapshot(
        self,
        crates: list,
        moving_platforms: list,
        puzzle_manager,
        collapsing_platforms: list | None = None,
    ) -> None:
        collapsing_platforms = collapsing_platforms or []
        self.saved_snapshot = {
            "crates": {c.crate_id: c.get_state() for c in crates},
            "platforms": {mp.plat_id: mp.get_state() for mp in moving_platforms},
            "collapsing": {
                cp.plat_id: cp.get_state() for cp in collapsing_platforms
            },
            "puzzles": puzzle_manager.capture_state(),
        }

    def restore_snapshot(
        self,
        player,
        crates: list,
        moving_platforms: list,
        puzzle_manager,
        collapsing_platforms: list | None = None,
    ) -> None:
        collapsing_platforms = collapsing_platforms or []
        player.set_position(self.respawn_pos[0], self.respawn_pos[1])
        if not self.saved_snapshot:
            return

        crate_states = self.saved_snapshot.get("crates", {})
        for c in crates:
            if c.crate_id in crate_states:
                c.set_state(crate_states[c.crate_id])

        plat_states = self.saved_snapshot.get("platforms", {})
        for mp in moving_platforms:
            if mp.plat_id in plat_states:
                mp.set_state(plat_states[mp.plat_id])

        col_states = self.saved_snapshot.get("collapsing", {})
        for cp in collapsing_platforms:
            if cp.plat_id in col_states:
                cp.set_state(col_states[cp.plat_id])

        if "puzzles" in self.saved_snapshot:
            puzzle_manager.restore_state(self.saved_snapshot["puzzles"])

    def update(
        self,
        dt: float,
        player_rect: pygame.Rect,
        crates: list,
        moving_platforms: list,
        puzzle_manager,
        collapsing_platforms: list | None = None,
        unsafe_spawn=None,
    ) -> bool:
        activated_new = False
        for cp in self.checkpoints:
            cp.update(dt)
            if cp.rect.colliderect(player_rect) and self.active_cp_id != cp.cp_id:
                spawn_box = pygame.Rect(*cp.respawn_pos, PLAYER_WIDTH, PLAYER_HEIGHT)
                if unsafe_spawn and unsafe_spawn(spawn_box):
                    continue
                cp.activated = True
                self.active_cp_id = cp.cp_id
                self.respawn_pos = cp.respawn_pos
                self.save_snapshot(
                    crates, moving_platforms, puzzle_manager, collapsing_platforms
                )
                if self.audio:
                    self.audio.play("checkpoint")
                activated_new = True
        return activated_new

    def draw(self, surface: pygame.Surface, camera) -> None:
        for cp in self.checkpoints:
            cp.draw(surface, camera, is_current=(cp.cp_id == self.active_cp_id))