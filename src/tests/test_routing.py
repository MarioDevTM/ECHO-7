"""Signal-level regressions for the redesign (requires pygame-ce)."""
import tempfile
import unittest
from pathlib import Path
import pygame
from src.core.save_manager import SaveManager
from src.levels.level_loader import LevelLoader
from src.levels.level_manager import LevelManager
from src.puzzles.puzzle_manager import PuzzleManager
from src.puzzles.routing import LatchingRelay, RoutingConsole


class RoutingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    def test_mutually_exclusive_reserve_and_independent_supply(self):
        pm = PuzzleManager()
        a = RoutingConsole('west', 'reserve', 100, 200, 'ferry', 'exit', ['laser'])
        b = RoutingConsole('east', 'reserve', 300, 200, 'ferry', 'exit', ['laser'])
        pm.routing_consoles.extend((a, b))
        pm.route_modes['reserve'] = 0
        self.assertEqual(pm.preview_routing(set()), set())
        self.assertEqual(pm.preview_routing({'laser'}), {'ferry'})
        pm.route_modes['reserve'] = 1
        self.assertEqual(pm.preview_routing({'laser'}), {'exit'})
        self.assertNotIn('ferry', pm.preview_routing({'laser'}))
        pm.route_modes['reserve'] = 0
        self.assertEqual(pm.preview_routing({'laser', 'backup'}), {'ferry'})

    def test_latch_requires_earlier_state_and_survives_snapshot(self):
        pm = PuzzleManager()
        relay = LatchingRelay('stored', 100, 200, ['loaded', 'valve'])
        pm.latching_relays.append(relay)
        self.assertFalse(relay.interact({'loaded'}))
        self.assertFalse(relay.latched)
        self.assertTrue(relay.interact({'loaded', 'valve'}))
        snapshot = pm.capture_state()
        self.assertTrue(relay.latched)
        relay.latched = False
        pm.restore_state(snapshot)
        self.assertTrue(relay.latched)

    def test_checkpoint_restores_routing_and_latch(self):
        with tempfile.TemporaryDirectory() as tmp:
            room = LevelManager(LevelLoader(), SaveManager(Path(tmp)/'test.json'), None)
            room.load_level(20)
            room.puzzle_manager.route_modes['reserve_20'] = 1
            room.puzzle_manager.generators[-1].active = True
            room.checkpoint_manager.save_snapshot(room.crates, room.moving_platforms, room.puzzle_manager)
            room.puzzle_manager.route_modes['reserve_20'] = 0
            room.puzzle_manager.generators[-1].active = False
            room.checkpoint_manager.restore_snapshot(room.player, room.crates, room.moving_platforms,
                                                     room.puzzle_manager)
            self.assertEqual(room.puzzle_manager.route_modes['reserve_20'], 1)
            self.assertTrue(room.puzzle_manager.generators[-1].active)

    def test_wrong_route_can_be_undone_from_each_side(self):
        with tempfile.TemporaryDirectory() as tmp:
            room = LevelManager(LevelLoader(), SaveManager(Path(tmp)/'test.json'), None)
            room.load_level(20)
            pm = room.puzzle_manager
            self.assertEqual(len([p for p in pm.routing_consoles if p.route_id == 'reserve_20']), 2)
            pm.route_modes['reserve_20'] = 1
            self.assertNotIn('route_20_ferry', pm.preview_routing({'opt_20_final'}))
            # Both panels control the same route mode: no remote-only softlock.
            pm.route_modes[[p for p in pm.routing_consoles if p.route_id == 'reserve_20'][1].route_id] = 0
            self.assertIn('route_20_ferry', pm.preview_routing({'opt_20_final'}))

    def test_relay_persists_through_checkpoint_and_new_game_clears_story(self):
        with tempfile.TemporaryDirectory() as tmp:
            save = SaveManager(Path(tmp)/'save.json')
            room = LevelManager(LevelLoader(), save, None)
            room.load_level(3)
            relay = room.puzzle_manager.latching_relays[0]
            relay.latched = True
            room.checkpoint_manager.save_snapshot(room.crates,room.moving_platforms,room.puzzle_manager)
            relay.latched = False
            room.checkpoint_manager.restore_snapshot(room.player,room.crates,room.moving_platforms,room.puzzle_manager)
            self.assertTrue(relay.latched)
            save.data['story_flags'].append('kip_met')
            save.save()
            self.assertIn('kip_met', SaveManager(save.save_path).data['story_flags'])
            save.reset_new_game()
            self.assertEqual(save.data['story_flags'], [])
