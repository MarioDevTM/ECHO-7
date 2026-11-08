"""New pygame-ce regression checks for the precision expansion.

Run: SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 -m unittest src.tests.test_precision
"""
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
import pygame

from src.core.settings import DASH_SPEED, WALL_SLIDE_SPEED
from src.core.save_manager import SaveManager
from src.entities.player import Player
from src.levels.level_loader import LevelLoader
from src.levels.level_manager import LevelManager
from src.systems.collision import CollisionSystem
from src.systems.precision import PrecisionWorld


class MovementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    def test_dash_is_disallowed_until_unlocked(self):
        player = Player(40, 100)
        self.assertFalse(player.begin_dash(1, 0))
        player.can_dash = True
        self.assertTrue(player.begin_dash(1, 0))
        self.assertAlmostEqual(player.vx, DASH_SPEED)
        self.assertEqual(player.dash_charges, 0)
        self.assertFalse(player.begin_dash(1, 0))

    def test_directional_dashes_have_normalized_velocity(self):
        player = Player(30, 30)
        player.can_dash = True
        self.assertTrue(player.begin_dash(1, -1))
        self.assertAlmostEqual((player.vx**2 + player.vy**2)**0.5, DASH_SPEED, places=5)

    def test_dash_does_not_cross_solid_wall(self):
        player = Player(70, 100)
        player.can_dash = True
        self.assertTrue(player.begin_dash(1, 0))
        wall = pygame.Rect(100, 50, 40, 250)
        CollisionSystem.move_and_collide_player(player, 0.15, [wall], [])
        self.assertLessEqual(player.rect.right, wall.left)
        self.assertTrue(player.dash_blocked)
        player.after_collision([wall])
        self.assertFalse(player.dashing)

    def test_wall_jump_has_outward_impulse(self):
        player = Player(74, 90)
        wall = pygame.Rect(100, 50, 40, 200)
        player.can_wall_jump = True
        player.wall_surfaces = [wall]
        player.queue_jump()
        player.coyote_timer = 0.0
        from collections import defaultdict
        keys = defaultdict(bool, {pygame.K_d: True})
        mapping = {'left':[pygame.K_a], 'right':[pygame.K_d],
                   'up':[pygame.K_w], 'down':[pygame.K_s],
                   'jump':[pygame.K_SPACE], 'run':[pygame.K_LSHIFT]}
        jumped = player.update_timers_and_input(1/120, keys, mapping, solids=[wall])
        self.assertTrue(jumped)
        self.assertLess(player.vx, 0)
        self.assertLess(player.vy, 0)

    def test_one_way_ledge_can_be_crossed_from_below_and_landed_on(self):
        platform = pygame.Rect(100, 120, 120, 12)
        upward = Player(120, 144)
        upward.vy = -500
        CollisionSystem.move_and_collide_player(upward, .08, [], [], [platform])
        self.assertLess(upward.rect.top, 144)
        falling = Player(120, 45)
        falling.vy = 650
        CollisionSystem.move_and_collide_player(falling, .06, [], [], [platform])
        self.assertTrue(falling.on_ground)
        self.assertEqual(falling.rect.bottom, platform.top)

    def test_recharge_and_spring(self):
        world = PrecisionWorld({'dash_recharges':[{'id':'r','x':100,'y':100}],
                                'springs':[{'id':'s','x':40,'y':188,'w':70}]})
        player = Player(100, 90)
        player.can_dash = True
        player.dash_charges = 0
        world.tick(1/120, player)
        self.assertEqual(player.dash_charges, 1)
        self.assertGreater(world.recharges[0]['cooldown'], 0)
        player.set_position(55, 154)  # feet at spring top after a small descent
        player.vy = 60
        CollisionSystem.move_and_collide_player(player, .04, [], [])
        world.tick(1/120, player, landed=True, impact_vy=290)
        self.assertLess(player.vy, -800)

    def test_dash_breaks_service_barrier_and_state_restores(self):
        world = PrecisionWorld({'dash_barriers':[{'id':'b','x':100,'y':100,'w':30,'h':60}]})
        player = Player(72, 110)
        player.can_dash = True
        self.assertTrue(player.begin_dash(1, 0))
        initial = world.snapshot()
        self.assertTrue(world.break_with_dash(player, 1/120, []))
        self.assertFalse(world.solid_barriers())
        world.restore(initial)
        self.assertEqual(len(world.solid_barriers()), 1)

    def test_all_levels_unlock_movement_in_sequence_and_have_valid_data(self):
        loader = LevelLoader()
        for num in range(1, 25):
            data = loader.load_level_data(num)
            self.assertEqual(data['abilities']['wall_jump'], num >= 5)
            self.assertEqual(data['abilities']['dash'], num >= 9)

    def test_checkpoint_restores_precision_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            room = LevelManager(LevelLoader(), SaveManager(Path(tmp)/'save.json'), None)
            room.load_level(24)
            self.assertTrue(room.precision.barriers)
            room.precision.barriers[0]['broken'] = True
            room.precision.restore(room.precision_at_checkpoint)
            self.assertFalse(room.precision.barriers[0]['broken'])

if __name__ == '__main__':
    unittest.main()
