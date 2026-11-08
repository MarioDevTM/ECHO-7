import unittest
import pygame
from src.puzzles.pressure_plate import PressurePlate
from src.puzzles.switch import Switch
from src.puzzles.door import Door
from src.puzzles.puzzle_manager import PuzzleManager


class TestPuzzleSystem(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()

    def test_pressure_plate_and_switch_open_all_logic_door(self) -> None:
        pm = PuzzleManager()
        plate = PressurePlate("p1", 100, 200)
        sw = Switch("s1", 200, 200, mode="permanent")
        door = Door("d1", 300, 100, 40, 100, ["p1", "s1"], logic="ALL")
        pm.add_plate(plate)
        pm.add_switch(sw)
        pm.add_door(door)

        # Only plate active -> door remains closed
        actor_on_plate = pygame.Rect(105, 160, 26, 46)
        pm.update(0.1, actor_on_plate, [], [], [])
        self.assertFalse(door.is_open)

        # Activate switch too -> door opens
        sw.interact()
        pm.update(0.5, actor_on_plate, [], [], [])
        self.assertTrue(door.is_open)

    def test_sequence_puzzle_resets_on_wrong_order(self) -> None:
        pm = PuzzleManager()
        s1 = Switch("seq_1", 100, 200, mode="sequence")
        s2 = Switch("seq_2", 200, 200, mode="sequence")
        pm.add_switch(s1)
        pm.add_switch(s2)
        pm.timer_mech.register_sequence("grp", ["seq_1", "seq_2"])

        # Press s2 first (wrong order) -> resets
        pm.try_interact(pygame.Rect(200, 170, 26, 46))
        self.assertFalse(s2.active)
        self.assertFalse(pm.timer_mech.is_sequence_complete("grp"))

        # Press s1 then s2 -> completes sequence
        pm.try_interact(pygame.Rect(100, 170, 26, 46))
        pm.try_interact(pygame.Rect(200, 170, 26, 46))
        self.assertTrue(pm.timer_mech.is_sequence_complete("grp"))


if __name__ == "__main__":
    unittest.main()