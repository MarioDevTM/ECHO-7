"""Pygame-independent checks for authored guide content and measured wrapping.

This uses a rectangle stand-in ONLY to validate schema geometry; it is not a
replacement for pygame-ce physics, rendering, or input-driven playtesting.
"""
import json
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

class Rect:
    def __init__(self, *args):
        x, y, w, h = args[0] if len(args) == 1 else args
        self.x, self.y, self.width, self.height = map(int, (x, y, w, h))
    @property
    def left(self): return self.x
    @property
    def right(self): return self.x + self.width
    @property
    def top(self): return self.y
    @property
    def bottom(self): return self.y + self.height
    def contains(self, other):
        return self.left <= other.left and self.top <= other.top and self.right >= other.right and self.bottom >= other.bottom
    def colliderect(self, other):
        return (self.left < other.right and self.right > other.left and
                self.top < other.bottom and self.bottom > other.top)
    def collidelist(self, items):
        return next((i for i, item in enumerate(items) if self.colliderect(item)), -1)

class FakeFont:
    def size(self, text): return (sum(5 if char == ' ' else 10 for char in text), 18)
    def get_linesize(self): return 20

shim = ModuleType('pygame')
shim.Rect = Rect
shim.font = SimpleNamespace(Font=FakeFont)
shim.Surface = type('Surface', (), {})
# Settings only references keycode constants when defining the defaults.
shim.__getattr__ = lambda name: sum(ord(ch) for ch in name) if name.startswith('K_') else None
sys.modules['pygame'] = shim

from src.entities.kip_dialogue import KIP_GUIDE, AUX_GUIDE, dialogue_for_room
from src.levels.level_loader import LevelLoader
from src.ui.text_layout import wrap_text, paginate

assert set(KIP_GUIDE) == set(range(1, 21))
assert set(AUX_GUIDE) == set(range(21, 25))
loader = LevelLoader()
report = loader.validate_all_levels()
failures = {room: errors for room, errors in report.items() if errors}
assert not failures, failures
font = FakeFont()
for room in range(1, 25):
    data = json.loads((ROOT / f'data/levels/level_{room:02d}.json').read_text())
    kips = [npc for npc in data.get('npcs', []) if npc['id'] == 'kip']
    assert len(kips) == 1, f'room {room}: expected exactly one main KIP NPC'
    assert abs(kips[0]['x'] - data['spawn'][0]) < 260
    assert abs(kips[0]['y'] - data['spawn'][1]) <= 65
    assert len({dialogue_for_room(room, i) for i in range(3)}) == 3
    for stage in range(3):
        message = dialogue_for_room(room, stage)
        assert message and len(message) >= 40
        lines = wrap_text(message, font, 550)
        assert all(font.size(line)[0] <= 550 for line in lines), room
        assert all(len(page) <= 3 for page in paginate(lines, 3))

# Test blank lines, pathological long tokens, and explicit pagination.
for sample in ('hello world\n\nsecond paragraph', 'RESEARCH_' * 100,
               'This is a very long laboratory notice about a machine and a particularly talkative robot.'):
    lines = wrap_text(sample, font, 85)
    assert lines
    assert all(font.size(line)[0] <= 85 for line in lines), lines
    pages = paginate(lines, 3)
    assert [part for page in pages for part in page] == lines
print('PASS: 24 level schema checks with emulated pygame rectangles')
print('PASS: one KIP near spawn in every campaign and auxiliary room')
print('PASS: 72 unique progressive dialogue stages and measured wrapping')
print('PASS: long-token splitting, paragraph handling and pagination')
print('NOTE: these checks are not pygame rendering or gameplay tests')
