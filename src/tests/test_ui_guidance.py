"""Pygame-backed tests for NPC progress and UI overflow. Run with SDL dummy."""
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import tempfile
import unittest
from pathlib import Path
import pygame

from src.core.save_manager import SaveManager
from src.entities.kip_dialogue import KIP_GUIDE, dialogue_for_room
from src.levels.level_loader import LevelLoader
from src.levels.level_manager import LevelManager
from src.ui.text_layout import wrap_text, paginate, draw_fitted, draw_lines


class UIGuidanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    def test_wrapping_respects_actual_glyph_width(self):
        font = pygame.font.SysFont('consolas', 21)
        text = 'An_interminably_long_single_token_' * 20
        rows = wrap_text(text, font, 310)
        self.assertGreater(len(rows), 3)
        self.assertTrue(all(font.size(row)[0] <= 310 for row in rows))
        self.assertEqual(''.join(rows), text)
        self.assertTrue(all(len(page) <= 3 for page in paginate(rows, 3)))

    def test_draw_respects_clip_and_restores_it(self):
        canvas = pygame.Surface((320, 180))
        canvas.fill((3, 7, 11))
        font = pygame.font.SysFont('consolas', 18)
        original_clip = pygame.Rect(30, 20, 230, 125)
        canvas.set_clip(original_clip)
        rows = wrap_text('GUIDE ' * 60, font, 120)
        draw_lines(canvas, font, rows[:3], pygame.Rect(90, 50, 120, 60),
                   (250, 250, 250))
        draw_fitted(canvas, 'Dynamic button label that needs wrapping',
                    pygame.Rect(80, 115, 150, 30), (250, 250, 250), size=20)
        self.assertEqual(canvas.get_clip(), original_clip)
        self.assertEqual(canvas.get_at((25, 10))[:3], (3, 7, 11))
        self.assertEqual(canvas.get_at((270, 155))[:3], (3, 7, 11))

    def test_one_reachable_kip_per_room(self):
        loader = LevelLoader()
        for level in range(1, 25):
            data = loader.load_level_data(level)
            kips = [npc for npc in data['npcs'] if npc['id'] == 'kip']
            with self.subTest(level=level):
                self.assertEqual(len(kips), 1)
                self.assertLess(abs(kips[0]['x'] - data['spawn'][0]), 260)
                self.assertTrue(all(dialogue_for_room(level, i) for i in range(3)))

    def test_initial_introduction_not_replayed_after_reload(self):
        with tempfile.TemporaryDirectory() as tmp:
            save = SaveManager(Path(tmp) / 'test-save.json')
            room = LevelManager(LevelLoader(), save, None)
            room.load_level(3)
            kip = next(n for n in room.npcs if n.npc_id == 'kip')
            room.player.set_position(kip.rect.x, kip.rect.y)
            self.assertTrue(room._talk_to_nearby_npc())
            self.assertIn('kip_room_3', save.data['story_flags'])
            first = room.dialogue_text
            self.assertTrue(room.dialogue_active)
            self.assertNotIn('KIP:', room.dialogue_pages[0][0])
            room._close_dialogue()
            self.assertTrue(room._talk_to_nearby_npc())
            self.assertNotEqual(first, room.dialogue_text)
            room.load_level(3)
            kip = next(n for n in room.npcs if n.npc_id == 'kip')
            room.player.set_position(kip.rect.x, kip.rect.y)
            self.assertTrue(room._talk_to_nearby_npc())
            self.assertNotEqual(first, room.dialogue_text)
            self.assertEqual(save.data['story_flags'].count('kip_room_3'), 1)

    def test_all_room_dialogue_has_progressive_content(self):
        self.assertEqual(set(KIP_GUIDE), set(range(1, 21)))
        self.assertTrue(all(len(set(KIP_GUIDE[n])) == 3 for n in KIP_GUIDE))


if __name__ == '__main__':
    unittest.main()
