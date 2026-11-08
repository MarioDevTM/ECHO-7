import unittest
import pygame
from src.entities.player import Player
from src.entities.crate import Crate
from src.entities.moving_platform import MovingPlatform
from src.systems.collision import CollisionSystem


class TestCollisionSystem(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()

    def test_player_lands_on_ground_without_tunneling(self) -> None:
        player = Player(100, 100)
        player.vy = 800.0
        floor = pygame.Rect(0, 160, 400, 40)
        CollisionSystem.move_and_collide_player(player, 0.05, [floor], [])
        self.assertTrue(player.on_ground)
        self.assertEqual(player.rect.bottom, floor.top)

    def test_player_pushes_crate_horizontally(self) -> None:
        floor = pygame.Rect(0, 200, 500, 40)
        player = Player(100, 154)
        crate = Crate("c1", 126, 164)
        player.vx = 240.0
        CollisionSystem.move_and_collide_player(player, 0.05, [floor], [crate])
        self.assertGreater(crate.pos_x, 126.0)
        self.assertTrue(player.pushing_crate)

    def test_moving_platform_carries_player(self) -> None:
        mp = MovingPlatform("mp1", 100, 200, 120, 20, 300, 200, speed=200.0)
        player = Player(130, 154)
        player.on_ground = True
        mp.update(0.1)
        CollisionSystem.apply_platform_carry([player], [mp], [])
        self.assertGreater(player.pos_x, 130.0)


if __name__ == "__main__":
    unittest.main()