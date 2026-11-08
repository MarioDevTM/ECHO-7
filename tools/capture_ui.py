"""Screenshot dialogue and menu screens for human visual QA (requires pygame-ce).

Usage: SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 tools/capture_ui.py
"""
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import pygame
from src.core.save_manager import SaveManager
from src.levels.level_loader import LevelLoader
from src.levels.level_manager import LevelManager
from src.core.settings import VIRTUAL_WIDTH, VIRTUAL_HEIGHT


def main():
    pygame.init()
    output = ROOT / 'docs' / 'ui-captures'
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as temp:
        manager = LevelManager(LevelLoader(), SaveManager(Path(temp) / 'save.json'), None)
        for level in (1, 3, 11, 13, 20):
            manager.load_level(level)
            kip = next(n for n in manager.npcs if n.npc_id == 'kip')
            manager.player.set_position(kip.rect.x, kip.rect.y)
            manager._talk_to_nearby_npc()
            surface = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT))
            manager.draw(surface)
            path = output / f'level-{level:02d}-kip-dialogue.png'
            pygame.image.save(surface, str(path))
            print(path)
    pygame.quit()


if __name__ == '__main__':
    main()
