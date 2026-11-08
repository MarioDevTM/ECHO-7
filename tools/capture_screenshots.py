"""Capture genuine 1280x720 in-engine frames for comparing player art in two chapters.

Run after installing pygame-ce: ./.venv/bin/python tools/capture_screenshots.py
These are snapshots at spawn, not demonstrations of completed puzzle solutions.
"""
import os
import tempfile
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
from src.core.settings import VIRTUAL_WIDTH, VIRTUAL_HEIGHT
from src.core.save_manager import SaveManager
from src.levels.level_manager import LevelManager
from src.levels.level_loader import LevelLoader


def main():
    pygame.init()
    output = ROOT / "docs" / "redesign-captures"
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        manager = LevelManager(LevelLoader(), SaveManager(Path(tmp) / "capture-save.json"), None)
        for chapter, room in ((1, 3), (3, 11)):
            manager.load_level(room)
            canvas = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT))
            manager.draw(canvas)
            filepath = output / f"chapter-{chapter}-level-{room:02d}-spawn.png"
            pygame.image.save(canvas, str(filepath))
            print(f"Captured {filepath}")
    pygame.quit()


if __name__ == "__main__":
    main()
