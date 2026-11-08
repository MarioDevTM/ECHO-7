"""Pygame-free contract checks for the ECHO-7 procedural background painter.

Run with: python3 tools/check_pixel_environment_offline.py
Proves data, source, and pure math contracts only; NOT interactive playability.
"""
from __future__ import annotations
import ast
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / 'src/visuals/pixel_environment.py'
SCENE = ROOT / 'src/visuals/scene_renderer.py'
MODULE = ast.parse(PATH.read_text(encoding='utf-8'), filename=str(PATH))

# Reject any background-image load calls in the painting module.
for node in ast.walk(MODULE):
    if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and node.func.attr == 'load'
            and isinstance(node.func.value, ast.Attribute)
            and node.func.value.attr == 'image'):
        raise AssertionError('The procedural painter must not load background images')

# Evaluate only pure constant and helper nodes. Inject game virtual dimensions to
# avoid the NameError in the previous script's isolated execution of assignments.
ns = {'VIRTUAL_WIDTH': 1280, 'VIRTUAL_HEIGHT': 720, 'math': math}
whitelist = {'SCALE', 'LOGICAL_W', 'LOGICAL_H', 'CHUNK_W', 'PALETTES'}
helpers = {'_clamp', 'screen_x', 'parallax_x', 'archetype_for_level'}
for node in MODULE.body:
    if isinstance(node, ast.Assign):
        if any(isinstance(t, ast.Name) and t.id in whitelist for t in node.targets):
            exec(compile(ast.Module(body=[node], type_ignores=[]), str(PATH), 'exec'), ns)
    elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id in whitelist:
        exec(compile(ast.Module(body=[node], type_ignores=[]), str(PATH), 'exec'), ns)
    elif isinstance(node, ast.FunctionDef) and node.name in helpers:
        exec(compile(ast.Module(body=[node], type_ignores=[]), str(PATH), 'exec'), ns)

assert (ns['SCALE'], ns['LOGICAL_W'], ns['LOGICAL_H'], ns['CHUNK_W']) == (2, 640, 360, 160)
for cam in (0, 45, 320, 1280):
    assert ns['screen_x'](960, cam) == 960 - cam
    assert ns['parallax_x'](960, cam, 0.4) == round(960 - 0.4 * cam)
for ch in range(1, 9):
    start = (ch - 1) * 10
    assert [ns['archetype_for_level'](start + i) for i in (1, 5, 9)] == [
        'opening', 'mid_complex', 'late_crisis']

def luma(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]

pals = ns['PALETTES']
assert set(pals) == set(range(1, 9))
for ch, pal in pals.items():
    assert luma(pal['void']) < luma(pal['far']) < luma(pal['mid']) <= luma(pal['panel']), (ch, 'value hierarchy')
    assert luma(pal['panel']) < 60.0, (ch, 'panel brightness')
    assert luma(pal['hi']) < 130.0, (ch, 'highlight brightness')

class_node = next(n for n in MODULE.body if isinstance(n, ast.ClassDef) and n.name == 'PixelEnvironment')
methods = {n.name for n in class_node.body if isinstance(n, ast.FunctionDef)}
assert {'set_focus', 'set_level', 'menu_background', 'draw', '_get_near_chunk',
        '_get_hero_landmark', '_draw_ambient_fx'} <= methods
scene = SCENE.read_text(encoding='utf-8')
assert '_pano_background' not in scene
assert 'pixel_environment.menu_background' in scene
assert 'pixel_environment.set_level' in scene
print('PASS: 8 palettes, 24 progression archetypes, world/parallax transforms, procedural-only painter, and renderer API.')
print('LIMITATION: offline source/math checks do not validate game frame rate, physics, or camera smoothness.')
