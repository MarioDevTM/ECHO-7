import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pygame

from src.core.save_manager import SaveManager
from src.entities.crate import Crate
from src.entities.moving_platform import MovingPlatform
from src.entities.player import Player
from src.levels.level_loader import LevelLoader
from src.levels.level_manager import LevelManager
from src.puzzles.puzzle_manager import OpticalBeam, RotatableMirror
from src.systems.collision import CollisionSystem


class MachineryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.path = Path(temp.name)
        self.save = SaveManager(self.path / "save.json")
        self.room = LevelManager(LevelLoader(), self.save, None)

    def test_belt_contact_speed_and_framerate(self):
        for level in (3, 6):
            for fps in (30, 60, 120):
                with self.subTest(level=level, fps=fps):
                    self.room.load_level(level)
                    pm = self.room.puzzle_manager
                    belt = pm.conveyors[0]
                    self.room.player.set_position(800, belt.rect.top - 46)
                    crate = self.room.crates[0]
                    crate.set_state({"pos_x": 920, "pos_y": belt.rect.top - 36})
                    for _ in range(fps // 2):
                        self.room.update(1 / fps, [])
                    offset = belt.base_speed * 0.5
                    self.assertAlmostEqual(self.room.player.pos_x, 800 + offset)
                    self.assertAlmostEqual(crate.pos_x, 920 + offset)
                    self.assertEqual(self.room.player.vx, 0)
                    if belt.reversed_by:
                        pm.switches_by_id[belt.reversed_by].interact()
                        for _ in range(fps // 2):
                            self.room.update(1 / fps, [])
                        self.assertAlmostEqual(crate.pos_x, 920)
                        self.assertAlmostEqual(self.room.player.pos_x, 800)
                    before = self.room.player.pos_x
                    jump = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE)
                    self.room.update(1 / fps, [jump])
                    self.assertLess(self.room.player.vy, 0)
                    self.assertEqual(self.room.player.pos_x, before)

    def test_fast_crate_stops_at_thin_wall(self):
        box = Crate("cargo", 0, 40)
        box.conveyor_vx = 1000
        wall = pygame.Rect(120, 0, 2, 150)
        CollisionSystem.move_and_collide_crate(box, 0.4, [wall], [box])
        self.assertEqual(box.rect.right, wall.left)

    def test_elevator_carries_both_riders_and_stalls_under_ceiling(self):
        lift = MovingPlatform("lift", 0, 200, 180, 20, 0, 100, 120)
        player, cargo = Player(10, 154), Crate("cargo", 90, 164)
        ceiling = pygame.Rect(0, 90, 180, 10)
        for _ in range(120):
            lift.update(1 / 120)
            CollisionSystem.apply_platform_carry([player, cargo], [lift], [ceiling])
            self.assertEqual(player.rect.bottom, lift.rect.top)
            self.assertEqual(cargo.rect.bottom, lift.rect.top)
        self.assertEqual(player.rect.top, ceiling.bottom)
        self.assertFalse(player.rect.colliderect(ceiling))

    def test_multiple_reflections_obstacles_and_power(self):
        beam = OpticalBeam("r", 10, 80, (1, 0), 180, pygame.Rect(97, 36, 10, 8), "power")
        mirrors = [RotatableMirror("a", 46, 62, 0), RotatableMirror("b", 46, 22, 0)]
        self.assertTrue(beam.update([], {"power"}, mirrors))
        self.assertEqual(len(beam.segments), 3)
        self.assertFalse(beam.update([pygame.Rect(75, 36, 1, 8)], {"power"}, mirrors))
        self.assertEqual(beam.end_point, (75, 40))
        mirrors[1].interact()
        self.assertFalse(beam.update([], {"power"}, mirrors))
        self.assertFalse(beam.update([], set(), mirrors))
        self.assertFalse(beam.segments)

    def test_wind_requires_power_and_lifts_only_light_crates(self):
        self.room.load_level(14)
        pm = self.room.puzzle_manager
        light, heavy = Crate("light", 1100, 600, 0.7), Crate("heavy", 1180, 600, 1.2)
        for active in (False, True):
            pm.switches_by_id["sw_fan_14"].active = active
            for box in (light, heavy):
                box.vy = 0
            pm.update(1 / 60, self.room.player.rect, [light, heavy], [], [])
            for box in (light, heavy):
                box.apply_gravity_and_friction(1 / 60)
            self.assertEqual(light.vy < 0, active)
            self.assertGreater(heavy.vy, 0)

    def test_water_buoyancy_and_restore(self):
        self.room.load_level(13)
        pm = self.room.puzzle_manager
        water = pm.water_zones[0]
        box = self.room.crates[0]
        for _ in range(180):
            self.room.update(1 / 60, [])
        self.assertLess(box.rect.top, water.rect.top)
        self.assertGreater(box.rect.bottom, water.rect.top)
        pm.valves[0].interact()
        for _ in range(60):
            self.room.update(1 / 60, [])
        state = pm.capture_state()
        for _ in range(60):
            self.room.update(1 / 60, [])
        pm.restore_state(state)
        self.assertEqual(water.rect.top, round(state["water"][water.wz_id]["current_y"]))

    def test_checkpoint_restores_platform_timer_through_death(self):
        self.room.load_level(16)
        room = self.room
        cp = room.checkpoint_manager.checkpoints[0]
        platform = room.puzzle_manager.collapsing_platforms[0]
        platform.state, platform.timer = "SHAKING", 0.30
        room.player.set_position(*cp.respawn_pos)
        room.update(1 / 120, [])
        saved = platform.timer
        self.assertEqual(room.checkpoint_manager.active_cp_id, cp.cp_id)
        platform.state, platform.timer = "FALLEN", 2
        room.trigger_manual_restart()
        for _ in range(90):
            room.update(1 / 120, [])
            if room.player.alive:
                break
        self.assertEqual(platform.state, "SHAKING")
        self.assertAlmostEqual(platform.timer, saved)
        self.assertEqual(room.player.rect.topleft, cp.respawn_pos)
        self.assertGreater(room.respawn_grace, 0)

    def test_hint_progression_opt_out_and_expired_timer(self):
        self.room.load_level(20)
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_h)
        clues = []
        for _ in range(3):
            self.room.update(1 / 60, [event])
            clues.append(self.room.log_banner_text)
        self.assertEqual(len(set(clues)), 3)
        self.save.data["settings"]["hints"] = False
        self.room.log_banner_text = ""
        self.room.update(1 / 60, [event])
        self.assertEqual(self.room.log_banner_text, "")
        pm = self.room.puzzle_manager
        switch = pm.switches_by_id["sw_20_final_sprint"]
        pm.try_interact(switch.rect)
        self.assertTrue(switch.active)
        for _ in range(340):
            self.room.update(1 / 60, [])
        self.assertFalse(switch.active)

    def test_validation_reads_the_authored_bytes(self):
        loader = LevelLoader(self.path / "levels")
        self.assertIn("No such file", loader.validate_all_levels()[3][0])
        loader.ensure_default_levels()
        path = loader.levels_dir / "level_03.json"
        for content, expected in [("{bad", "Expecting"), ("null", "level object")]:
            path.write_text(content)
            loader.ensure_default_levels(overwrite_outdated=True)
            self.assertIn(expected, loader.validate_all_levels()[3][0])
            self.assertEqual(path.read_text(), content)
        original = self.room.level_loader.load_level_data(3)
        original["doors"][0]["required_links"] = ["missing"]
        path.write_text(json.dumps(original))
        self.assertIn("unknown signal", loader.validate_all_levels()[3][0])

    def test_migration_backup_and_failed_write_preserve_progress(self):
        path = self.path / "old.json"
        original = {"current_level": 3, "unlocked_level": 3, "completed_levels": [1, 2],
                    "collected_logs": ["log_03"], "settings": {"fullscreen": True}}
        path.write_text(json.dumps(original))
        manager = SaveManager(path)
        self.assertEqual(manager.data["current_level"], 3)
        with patch("src.core.save_manager.os.replace", side_effect=OSError("interrupted")):
            with self.assertWarns(UserWarning):
                manager.mark_log_collected("archive_log_11")
        self.assertEqual(json.loads(path.read_text()), original)
        manager.save()
        self.assertEqual(json.loads(path.with_suffix(".pre-update.bak").read_text()), original)
        self.assertIn("archive_log_11", SaveManager(path).data["collected_logs"])

    def test_reserve_generator_expires_after_checkpoint_restore(self):
        self.room.load_level(24)
        pm = self.room.puzzle_manager
        reserve = pm.generators[0]
        pm.try_interact(reserve.rect)
        pm.update(4.0, self.room.player.rect, [], [], [])
        state = pm.capture_state()
        pm.update(9.0, self.room.player.rect, [], [], [])
        self.assertFalse(reserve.active)
        pm.restore_state(state)
        self.assertTrue(reserve.active)
        self.assertAlmostEqual(pm.timer_mech.timers["reserve"][0], 8.0)
        pm.update(8.01, self.room.player.rect, [], [], [])
        self.assertNotIn("reserve", pm.active_signals)
