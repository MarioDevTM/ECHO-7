import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pygame
from src.core.game import Game
from src.core.settings import AUXILIARY_ROOMS
from src.core.save_manager import SaveManager
from src.levels.level_loader import DEFAULT_LEVELS, LevelLoader


class ReleaseTests(unittest.TestCase):
    def test_menu_play_pause_resume_and_quit(self):
        with tempfile.TemporaryDirectory() as tmp:
            save = SaveManager(Path(tmp) / "save.json")
            with patch("src.core.game.SaveManager", return_value=save):
                game = Game()
            frames = iter([
                [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)],
                [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)],
                [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)],
                [pygame.event.Event(pygame.QUIT)],
            ])
            states = []
            def poll():
                states.append(game.state)
                return next(frames)
            with patch("pygame.event.get", side_effect=poll), self.assertRaises(SystemExit):
                game.run()
            self.assertEqual(states, ["MAIN_MENU", "PLAYING", "PAUSED", "PLAYING"])

    def test_all_eighty_rooms_load_draw_and_change_chapter_audio(self):
        with tempfile.TemporaryDirectory() as tmp:
            save = SaveManager(Path(tmp) / "save.json")
            with patch("src.core.game.SaveManager", return_value=save):
                game = Game()
            for number in range(1, 81):
                with self.subTest(number=number):
                    data = LevelLoader().load_level_data(number)
                    self.assertEqual(data["chapter"], (number - 1) // 10 + 1)
                    game.start_level(number)
                    game.level_manager.update(1 / 60, [])
                    game.level_manager.draw(game.canvas)
                    if game.audio.enabled:
                        self.assertEqual(game.audio.current_chapter_track, data["chapter"])
                    self.assertEqual(save.data["current_level"], number)
            pygame.quit()

    def test_eight_chapters_and_21_is_no_longer_auxiliary(self):
        with tempfile.TemporaryDirectory() as tmp:
            save = SaveManager(Path(tmp) / "save.json")
            with patch("src.core.game.SaveManager", return_value=save):
                game = Game()
            self.assertEqual(game.level_loader.TOTAL_LEVELS, 80)
            self.assertEqual(game.level_loader.TOTAL_CHAPTERS, 8)
            self.assertEqual(len(game.main_menu.level_catalog), 80)
            self.assertEqual(AUXILIARY_ROOMS, {})
            game.main_menu._trigger_action("CHAPTER_SELECT")
            self.assertEqual(len(game.main_menu._get_items()), 9)
            game.save_manager.data["unlocked_level"] = 80
            game.main_menu._trigger_action("OPEN_CHAPTER_8")
            self.assertEqual(len(game.main_menu._get_items()), 12)
            game.main_menu._trigger_action("LEVEL_80")
            self.assertEqual(game.level_manager.current_level_num, 80)
            pygame.quit()
