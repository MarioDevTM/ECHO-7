"""Offline first-frame smoke test for all 80 ECHO-7 levels.

Exercises LevelManager.load_level(), a real game update tick, and its full draw()
with the project's PIL-backed pygame stand-in. It deliberately does *not*
claim that pygame/SDL runtime, optical line collisions, or gameplay solvability
were tested. Use `python3 tools/check_level_entry_offline.py` from the root.
"""
from __future__ import annotations

import collections
import sys
import tempfile
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
import offline_pygame_adapter as adapter

pygame = adapter.pg

# The existing drawing adapter lacks several real Pygame APIs exercised by
# LevelManager. Extend only the *test stub*, never alter the game's API usage.
pygame.Rect.copy = lambda rect: pygame.Rect(rect)
pygame.Rect.center = property(
    lambda rect: (rect.x + rect.w // 2, rect.y + rect.h // 2),
    lambda rect, xy: (setattr(rect, "x", int(xy[0] - rect.w // 2)),
                      setattr(rect, "y", int(xy[1] - rect.h // 2))),
)
pygame.Rect.midtop = property(lambda rect: (rect.centerx, rect.top))
pygame.Rect.bottomright = property(lambda rect: (rect.right, rect.bottom))
pygame.Rect.topright = property(lambda rect: (rect.right, rect.top))
pygame.Rect.midbottom = property(lambda rect: (rect.centerx, rect.bottom))
pygame.Rect.clipline = lambda self, *args: ()  # not a physics/optical beam test
pygame.Rect.collidepoint = lambda rect, *xy: (
    rect.left <= (xy[0][0] if len(xy) == 1 else xy[0]) < rect.right
    and rect.top <= (xy[0][1] if len(xy) == 1 else xy[1]) < rect.bottom
)
pygame.register_quit = lambda callback: None
pygame.BLEND_RGBA_MULT = 0
pygame.draw.ellipse = staticmethod(
    lambda surface, color, rect, width=0: pygame.draw.rect(surface, color, rect, width)
)

class _Font:
    def render(self, text, *args, **kwargs):
        return pygame.Surface((max(1, len(str(text)) * 8), 19))

    def size(self, text):
        return len(str(text)) * 8, 19

    def get_height(self):
        return 19

    def get_linesize(self):
        return 19

pygame.font = types.SimpleNamespace(SysFont=lambda *args, **kwargs: _Font(), Font=_Font)
pygame.key = types.SimpleNamespace(
    ScancodeWrapper=type("ScancodeWrapper", (), {}),
    get_pressed=lambda: collections.defaultdict(bool),
)
pygame.event = types.SimpleNamespace(Event=type("Event", (), {}))
pygame.mixer = types.SimpleNamespace(Sound=lambda *args: None)
pygame.math = types.SimpleNamespace(Vector2=lambda *args: None)

from src.core.save_manager import SaveManager
from src.levels.level_loader import LevelLoader
from src.levels.level_manager import LevelManager

with tempfile.TemporaryDirectory(prefix="echo7-entry-smoke-") as folder:
    save = SaveManager(Path(folder) / "save.json")
    manager = LevelManager(LevelLoader(), save, None)
    for level in range(1, 81):
        manager.load_level(level)
        assert manager.current_level_num == level
        assert manager.scenery._room_num == level, (level, manager.scenery._room_num)
        assert manager.scenery.pixel_environment.level_num == level
        status = manager.update(1 / 60, [])
        assert status == "PLAYING", (level, status)
        manager.draw(pygame.Surface((1280, 720)))
        # Different effect phases, puzzle power states and reduced motion must
        # remain safe during the first frame in every room.
        manager.scenery._reduced_motion = (level % 2 == 0)
        manager.scenery.draw_background(
            pygame.Surface((1280, 720)), manager.theme_name,
            *manager.camera.get_offset(), 2.5, manager.width, manager.height,
            powered=True, signals=manager.puzzle_manager.active_signals,
        )

print("PASS: 80 levels loaded, ticked, drew and retained the correct level-FX context.")
print("LIMITATION: PIL pygame adapter; actual SDL/Pygame, game physics and 80-level completion not tested.")
