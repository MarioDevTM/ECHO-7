"""Repeatable pygame-free tests for the repair release.

These checks verify source behavior contracts, asset integrity and level data.
They DO NOT certify real-time physics, animation or player completion.
"""
from __future__ import annotations
import ast
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageStat

R = Path(__file__).resolve().parents[1]
BASE = json.loads((R / 'docs/BASELINE_ARCHIVE_FINGERPRINTS.json').read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# Protect early campaign and user-approved chapter source paintings.
for n in range(1, 25):
    assert sha(R / f'data/levels/level_{n:02}.json') == BASE['prefix_hashes'][str(n)], n
for ch in (2, 6, 7, 8):
    assert sha(R / f'data/art/backgrounds/chapter_{ch:02}.png') == BASE['protected_art_hashes'][str(ch)], ch

# Old late-game gates must not depend on physically untested new stations.
for n in range(25, 80):
    level = json.loads((R / f'data/levels/level_{n:02}.json').read_text())
    old = BASE['late_game'][str(n)]['doors'][0]['required_links']
    assert level['doors'][0]['required_links'] == old, n
    assert level['side_challenge_policy']['campaign_blocking'] is False
    assert any(c['id'] == f'service_challenge_{n:02}' for c in level['collectibles'])
level_80 = json.loads((R / 'data/levels/level_80.json').read_text())
assert level_80['doors'][0]['required_links'] == BASE['late_game']['80']['doors'][0]['required_links']

# Execute the exact exit gating function, isolated without a Pygame runtime.
source = ast.parse((R/'src/levels/level_manager.py').read_text())
klass = next(n for n in source.body if isinstance(n, ast.ClassDef) and n.name == 'LevelManager')
func = next(n for n in klass.body if isinstance(n, ast.FunctionDef) and n.name == 'exit_is_ready')
code = compile(ast.Module(body=[func], type_ignores=[]), 'exit_is_ready', 'exec')
namespace = {}
exec(code, namespace)
exit_ready = namespace['exit_is_ready']
class Gate:
    def __init__(self, opened, solid):
        self.is_open, self.is_solid = opened, solid
class Level:
    def __init__(self, gate):
        self.exit_gate = gate
assert not exit_ready(Level(Gate(False, True)))  # locked
assert not exit_ready(Level(Gate(True, True)))   # still retracting
assert exit_ready(Level(Gate(True, False)))      # physically open
assert exit_ready(Level(None))                   # stages without gate

# World-space scenery mapping is independent of camera smoothing or player X.
module = ast.parse((R/'src/visuals/pixel_environment.py').read_text())
screen_fn = next(n for n in module.body if isinstance(n, ast.FunctionDef) and n.name == 'screen_x')
contract = {}
exec(compile(ast.Module(body=[screen_fn], type_ignores=[]), 'pixel_space', 'exec'), contract)
fx = contract['screen_x']
for camera in (0, 10, 225, 781):
    assert fx(1040, camera) == 1040 - camera
assert fx(1040, 0) - fx(1040, 200) == 200

# Derived scene modules must be genuinely small, consistent and valid.
for ch in (1, 3, 4, 5):
    pix = R/'data/art/backgrounds/pixel'
    assert Image.open(pix/f'chapter_{ch:02}_hero.png').size == (640, 360)
    for i in range(3):
        assert Image.open(pix/f'chapter_{ch:02}_module_{i}.png').size == (160, 360)
with Image.open(R/'data/art/backgrounds/scenic/chapter_07_pano.png') as image:
    assert image.size == (1920, 960)
    # Old plate had a nearly uniform lower-half magenta filler.
    strip = image.crop((350, 720, 1650, 940)).convert('RGB')
    assert sum(ImageStat.Stat(strip).stddev) > 38, 'chapter 7 still has flat-color padding'

# Every Python module in project parses, independent of installed pygame.
python_files = list(R.rglob('*.py'))
for path in python_files:
    ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
print(f'PASS: protected originals, 55 safe exit gates, active exit guard, world transform,')
print(f'      chapter art assets, Chapter 7 panorama, {len(python_files)} Python files parsed.')
print('LIMITATION: no Pygame live rendering or full level traversal was performed.')
