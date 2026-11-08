"""Scripted routes use only key state and key events, starting at the authored spawn."""
import tempfile
import unittest
from collections import defaultdict
from pathlib import Path
from unittest.mock import patch

import pygame

from src.core.save_manager import SaveManager
from src.levels.level_loader import LevelLoader
from src.levels.level_manager import LevelManager


class CampaignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.save = SaveManager(Path(directory.name) / "save.json")
        self.room = LevelManager(LevelLoader(), self.save, None)
        self.keys = defaultdict(bool)
        keyboard = patch("pygame.key.get_pressed", return_value=self.keys)
        keyboard.start()
        self.addCleanup(keyboard.stop)

    def step(self, held=(), press=None):
        self.keys.clear()
        self.keys.update({key: True for key in held})
        events = [] if press is None else [pygame.event.Event(pygame.KEYDOWN, key=press)]
        result = self.room.update(1 / 60, events)
        self.assertTrue(self.room.player.alive, f"Died at {self.room.player.rect}")
        return result

    def move(self, target, *keys):
        start = self.room.player.rect.x
        right = start < target
        direction = pygame.K_d if right else pygame.K_a
        for _ in range(1200):
            if (self.room.player.rect.x >= target) == right:
                return
            self.step((direction, *keys))
        self.fail(f"Could not reach x={target} from {start}, stopped at {self.room.player.rect}")

    def climb(self, x, deck):
        self.move(x)
        for _ in range(120):
            if self.room.player.rect.bottom <= deck:
                break
            self.step((pygame.K_w,))
        self.assertLessEqual(self.room.player.rect.bottom, deck)
        for _ in range(16):
            self.step((pygame.K_w, pygame.K_d))

    def leap(self, frames=36, direction=pygame.K_d):
        keys = (direction, pygame.K_LSHIFT)
        self.step(keys, pygame.K_SPACE)
        for _ in range(frames):
            self.step(keys)

    def finish(self):
        for _ in range(600):
            if self.step((pygame.K_d, pygame.K_LSHIFT)) == "NEXT_LEVEL":
                return
        self.fail(f"Exit not reached: {self.room.player.rect}, signals {self.room.puzzle_manager.active_signals}")

    def test_laser_laboratory_full_route(self):
        self.room.load_level(11)
        self.move(250)
        self.step(press=pygame.K_e)
        self.move(645)
        beam = self.room.puzzle_manager.optical_beams[0]
        self.assertFalse(beam.receiving)
        self.step(press=pygame.K_e)
        self.assertTrue(beam.receiving)
        self.move(887)
        self.leap()
        self.assertIn("plate_11_lens", self.room.puzzle_manager.active_signals)
        self.move(1200, pygame.K_LSHIFT)
        self.leap()
        self.move(1550)
        self.interact_at(1480)  # approach from right so leftward jump has momentum
        self.assertIn("relay_11_bridge", self.room.puzzle_manager.active_signals)
        # Return with the original receiver still feeding the remembered ferry.
        self.leap(44, pygame.K_a)
        self.move(645, pygame.K_LSHIFT)
        self.step(press=pygame.K_e)
        self.assertIn("opt_11_exit", self.room.puzzle_manager.active_signals)
        self.move(1200, pygame.K_LSHIFT)
        self.leap()
        self.move(1790, pygame.K_LSHIFT)
        self.leap()
        self.finish()

    def test_optional_archives(self):
        for number, deck in [(11, 450), (15, 470)]:
            self.room.load_level(number)
            self.climb(190, deck)
            self.move(242)
            self.step(press=pygame.K_e)
            self.move(316)
            self.step(press=pygame.K_e)
            self.move(496)
            self.assertIn(f"archive_log_{number}", self.save.data["collected_logs"])
            self.move(205)
            self.assertEqual(number, self.room.current_level_num)

    def test_assembly_line_full_route(self):
        self.room.load_level(3)
        # Cargo settles on the left staging sensor before we reverse the belt.
        for _ in range(360):
            self.step()
            if "plate_3_staging" in self.room.puzzle_manager.active_signals:
                break
        self.assertIn("plate_3_staging", self.room.puzzle_manager.active_signals)
        self.climb(350, 470)
        self.move(516)
        self.step(press=pygame.K_e)
        self.assertIn("relay_3_staged", self.room.puzzle_manager.active_signals)
        self.move(477)
        self.step(press=pygame.K_e)
        self.move(345)
        for _ in range(48):
            self.step()
        self.move(1049)
        self.leap(16)
        self.assertIn("plate_assembly", self.room.puzzle_manager.active_signals)
        self.move(1162)
        for _ in range(300):
            self.step()
            if self.room.player.on_ground and self.room.moving_platforms[0].rect.x < 1270:
                break
        self.leap(23)
        for _ in range(300):
            p = self.room.moving_platforms[0]
            if self.room.player.on_ground and self.room.player.rect.bottom == p.rect.top and p.rect.x > 1410:
                break
            self.step()
        self.leap()
        self.climb(1850, 480)
        self.move(2010)
        self.step(press=pygame.K_e)
        self.finish()

    def test_heavy_machinery_full_route(self):
        self.room.load_level(6)
        self.move(597)
        self.move(565)
        # Let the crate travel through the press; enter after the piston retracts.
        press = self.room.hazard_manager.crushers[0]
        for _ in range(300):
            self.step()
            if 1.1 <= press.timer < 1.12:
                break
        self.move(1310, pygame.K_LSHIFT)
        self.leap(9)
        self.move(1448)
        self.climb(1450, 460)
        self.move(1610)
        self.step(press=pygame.K_e)
        self.move(2110)
        self.step(press=pygame.K_e)
        self.finish()

    def interact_at(self, x):
        self.move(x)
        for _ in range(75):
            if self.room.player.on_ground:
                break
            self.step()
        self.step(press=pygame.K_e)

    def test_basin_routes(self):
        for level, valve, ladder in [(13, 575, 1570), (19, 515, 1450)]:
            self.room.load_level(level)
            self.interact_at(valve)
            if level == 13:
                self.move(1330)
                self.leap(15)
                self.interact_at(1490)
                self.assertIn("relay_13_sump", self.room.puzzle_manager.active_signals)
                self.interact_at(valve)  # refill; crate is now free to float
                for _ in range(260):
                    self.step()
                    if "sump_refilled" in self.room.puzzle_manager.active_signals:
                        break
                self.assertIn("sump_refilled", self.room.puzzle_manager.active_signals)
            else:
                self.interact_at(1090)
            self.climb(ladder, 580)
            self.interact_at(1950 if level == 13 else 2110)
            if level == 19:
                self.move(2210, pygame.K_LSHIFT)
                self.leap()
            self.finish()

    def test_ventilation_routes(self):
        for level, fan, column, deck, plate in [(14, 630, 1150, 460, 1960), (18, 1070, 1220, 480, 2120)]:
            self.room.load_level(level)
            if level == 18:
                for x in [250, 510, 770]:
                    self.interact_at(x)
            self.interact_at(fan)
            self.move(column)
            for _ in range(180):
                self.step()
                if self.room.player.rect.bottom < deck - 40:
                    break
            self.assertLess(self.room.player.rect.bottom, deck)
            self.move(plate - 30)
            self.leap(14)
            if level == 14:
                self.interact_at(2170)
            else:
                self.move(2190)
                for _ in range(50):
                    self.step()
                self.move(2236, pygame.K_LSHIFT)
                self.leap()
            self.finish()

    def test_final_escape(self):
        self.room.load_level(20)
        self.interact_at(175)
        self.move(1010)
        self.move(489)
        self.climb(490, 510)
        self.interact_at(575)
        self.interact_at(695)
        self.interact_at(915)
        self.move(980)
        self.leap(20)
        self.move(1240)
        self.leap()
        self.move(2040)
        laser = self.room.hazard_manager.lasers[0]
        for _ in range(200):
            self.step()
            if 1.11 < laser.timer % laser.period < 1.14:
                break
        self.move(2330, pygame.K_LSHIFT)
        self.leap(12)
        self.interact_at(2490)
        self.move(2585, pygame.K_LSHIFT)
        self.leap()
        for _ in range(200):
            if self.step((pygame.K_d, pygame.K_LSHIFT)) == "NEXT_LEVEL":
                self.assertIn(20, self.save.data["completed_levels"])
                return
        self.fail(f"Final door: {self.room.puzzle_manager.active_signals}")

    def cross_ferry(self, edge):
        self.move(edge - 62)
        for _ in range(400):
            self.step()
            if self.room.moving_platforms[0].rect.left < edge + 50 and self.room.player.on_ground:
                break
        self.leap(24)
        ferry = self.room.moving_platforms[0]
        for _ in range(400):
            self.step()
            if self.room.player.on_ground and self.room.player.rect.bottom == ferry.rect.top and ferry.pos_x >= ferry.end_x - 35:
                break
        self.leap(22)

    def test_structural_failure(self):
        self.room.load_level(16)
        self.move(639, pygame.K_LSHIFT)
        self.leap(34)
        self.move(997, pygame.K_LSHIFT)
        self.leap(44)
        self.interact_at(1475)
        self.move(1650)
        self.leap(12)
        self.cross_ferry(1820)
        self.interact_at(2230)
        self.finish()

    def test_awakening(self):
        self.room.load_level(1)
        self.move(377, pygame.K_LSHIFT)
        self.leap()
        self.move(765, pygame.K_LSHIFT)
        self.leap()
        self.climb(1130, 460)
        self.interact_at(1275)
        self.move(973)
        for _ in range(60):
            self.step()
        self.move(1530)
        self.step((pygame.K_d,), pygame.K_SPACE)
        for _ in range(18):
            self.step((pygame.K_d,))
        for _ in range(60):
            self.step()
        self.move(1650, pygame.K_LSHIFT)
        self.leap()
        self.finish()

    def test_locked_passage(self):
        self.room.load_level(2)
        self.climb(490, 480)
        self.interact_at(850)
        self.move(930)
        for _ in range(100):
            self.step()
        self.move(1050, pygame.K_LSHIFT)
        self.leap()
        self.climb(1470, 500)
        self.move(1855)
        for _ in range(75):
            self.step()
        self.move(1870)
        for _ in range(75):
            self.step()
        self.move(1852)
        for _ in range(40):
            self.step()
        self.move(1930)
        self.leap(18)
        self.finish()

    def test_emergency_exit(self):
        self.room.load_level(4)
        self.move(595)
        self.leap(24)
        self.interact_at(850)
        self.move(755)
        self.leap(38, pygame.K_a)
        self.move(1150)
        self.leap(10)
        self.cross_ferry(1340)
        self.climb(1690, 470)
        self.interact_at(1810)
        self.move(1975, pygame.K_LSHIFT)
        self.leap()
        self.finish()

    def test_factory_shutdown(self):
        self.room.load_level(8)
        self.interact_at(250)
        self.climb(390, 490)
        self.interact_at(530)
        self.interact_at(835)
        self.cross_ferry(1140)
        self.interact_at(1815)
        self.interact_at(1920)
        self.assertIn("route_20_exit", self.room.puzzle_manager.active_signals)
        self.assertIn("gen_20_independent", self.room.puzzle_manager.active_signals)
        self.move(2210)
        self.leap(18)
        self.finish()

    def test_power_failure(self):
        self.room.load_level(9)
        self.interact_at(550)
        self.cross_ferry(1080)
        self.climb(1590, 480)
        self.interact_at(1770)
        self.move(1420)
        for _ in range(60):
            self.step()
        self.move(2090)
        self.step((pygame.K_d,), pygame.K_SPACE)
        for _ in range(20):
            self.step((pygame.K_d,))
        for _ in range(60):
            self.step()
        self.move(2435, pygame.K_LSHIFT)
        self.leap(18)
        self.finish()

    def test_circuit_breaker(self):
        self.room.load_level(10)
        for x in (295, 575, 855):
            self.interact_at(x)
        self.cross_ferry(1180)
        self.climb(1590, 480)
        self.interact_at(1735)
        self.interact_at(2075)
        self.finish()

    def test_overload(self):
        self.room.load_level(12)
        self.interact_at(235)
        self.move(950)
        self.leap(16)
        self.cross_ferry(1300)
        self.interact_at(2110)
        self.finish()

    def test_system_reboot(self):
        self.room.load_level(17)
        self.interact_at(235)
        self.move(950)
        self.leap(16)
        self.cross_ferry(1260)
        self.climb(1690, 480)
        self.interact_at(1870)
        self.move(2070, pygame.K_LSHIFT)
        self.leap()
        self.finish()

    def test_pressure_system(self):
        self.room.load_level(15)
        self.interact_at(410)
        self.move(1090)
        self.leap(16)
        self.climb(1250, 470)
        self.interact_at(1430)
        self.move(1852)
        vent = self.room.hazard_manager.steam_vents[-1]
        for _ in range(240):
            self.step()
            if 1.32 < vent.timer < 1.35:
                break
        self.finish()

    def board_lift(self, lift, x):
        self.move(x)
        for _ in range(500):
            self.step()
            if lift.rect.y >= lift.start_y - 15 and self.room.player.on_ground:
                break
        self.leap(13)
        for _ in range(600):
            self.step()
            if self.room.player.on_ground and self.room.player.rect.bottom == lift.rect.top and lift.rect.y < lift.end_y + 18:
                return
        self.fail(f"Missed lift: {lift.plat_id}, player {self.room.player.rect}")

    def test_counterbalance(self):
        self.room.load_level(7)
        self.move(730)
        self.leap(12)
        self.board_lift(self.room.moving_platforms[0], 880)
        self.leap(24)
        self.interact_at(1238)
        self.assertIn("relay_7_counter", self.room.puzzle_manager.active_signals)
        self.interact_at(1510)
        self.move(1690)
        self.leap(14)
        self.board_lift(self.room.moving_platforms[1], 1780)
        self.leap()
        self.finish()

    def test_elevator_shaft(self):
        self.room.load_level(5)
        self.interact_at(610)
        self.board_lift(self.room.moving_platforms[0], 665)
        self.leap(28)
        self.move(1390)
        lift = self.room.moving_platforms[1]
        self.move(1180)
        for _ in range(500):
            self.step()
            if lift.rect.y > 626 and not lift.forward:
                break
        self.step((pygame.K_a,), pygame.K_SPACE)
        for _ in range(20):
            self.step((pygame.K_a,))
        for _ in range(650):
            self.step()
            if self.room.player.rect.bottom == lift.rect.top and lift.rect.y < 467:
                break
        self.leap(28, pygame.K_a)
        self.interact_at(410)
        self.move(965)
        for _ in range(600):
            self.step()
            if 465 < lift.rect.y < 495 and lift.forward:
                break
        self.step((pygame.K_d,), pygame.K_SPACE)
        for _ in range(21):
            self.step((pygame.K_d,))
        for _ in range(600):
            self.step()
            if self.room.player.rect.bottom == lift.rect.top and lift.rect.y < 333:
                break
        self.leap(24)
        self.move(1460, pygame.K_LSHIFT)
        self.leap()
        self.finish()

    def finish_auxiliary(self, number):
        for _ in range(400):
            if self.step((pygame.K_d, pygame.K_LSHIFT)) == "NEXT_LEVEL":
                self.assertIn(number, self.save.data["completed_levels"])
                self.assertEqual(self.save.data["current_level"], number + 1)
                self.assertEqual(self.save.data["unlocked_level"], number + 1)
                return
        self.fail(f"Auxiliary exit {number}: {self.room.puzzle_manager.active_signals}")

    def test_freight_dispatch(self):
        self.room.load_level(21)
        self.climb(220, 475)
        self.interact_at(360)
        self.interact_at(550)
        for _ in range(220):
            self.step()
        self.assertIn("cargo", self.room.puzzle_manager.active_signals)
        self.move(1005)
        self.leap(24)
        self.interact_at(1370)
        self.finish_auxiliary(21)

    def test_periscope_relay(self):
        self.room.load_level(22)
        self.interact_at(229)
        self.interact_at(530)
        beam = self.room.puzzle_manager.optical_beams[0]
        self.assertFalse(beam.receiving)
        self.climb(530, 474)
        self.step(press=pygame.K_e)
        self.assertTrue(beam.receiving)
        self.assertEqual(len(beam.segments), 3)
        self.finish_auxiliary(22)

    def test_ballast_sump(self):
        self.room.load_level(23)
        self.interact_at(300)
        for _ in range(170):
            self.step()
        self.move(790)
        self.leap(14)
        self.move(1030)
        for _ in range(180):
            self.step()
            if self.room.player.rect.bottom < 395:
                break
        self.interact_at(1440)
        self.finish_auxiliary(23)

    def test_blackstart(self):
        self.room.load_level(24)
        self.interact_at(225)
        self.interact_at(435)
        self.interact_at(630)
        self.move(692, pygame.K_LSHIFT)
        self.leap(36)
        self.move(982, pygame.K_LSHIFT)
        self.leap(40)
        self.interact_at(1380)
        self.finish_auxiliary(24)
