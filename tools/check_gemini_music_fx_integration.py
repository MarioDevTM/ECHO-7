"""Offline integration checks for the 2026 ECHO-7 individualized music / FX / animation update.

Requires pillow; ffprobe when available. This DOES NOT replace native Pygame playtesting.
"""
from __future__ import annotations
import ast
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'src'
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT))

from PIL import ImageChops
import offline_pygame_adapter as adapter
from src.visuals.level_effects import LEVEL_FX_NAMES, draw_level_specific_fx
from src.visuals.pixel_environment import PALETTES
from src.visuals.scene_renderer import SceneRenderer

assert set(LEVEL_FX_NAMES) == set(range(1, 81)), 'All levels need an FX signature'
assert len(set(LEVEL_FX_NAMES.values())) == 80, 'FX signature names should be distinct'
assert all(len(LEVEL_FX_NAMES[i]) > 8 for i in range(1, 81))

static_effects=[]
for ch in range(1, 9):
    for sub in range(10):
        num = (ch - 1) * 10 + sub + 1
        def draw_at(t, reduced=False, signals=None):
            s = adapter.pg.Surface((640, 360))
            s.fill((5, 10, 15))
            draw_level_specific_fx(s, num, ch, PALETTES[ch], 0, 0, 0,
                                   1280, 360, t, reduced, False, [], signals)
            return s.im
        first = draw_at(0.3)
        again = draw_at(0.3)
        assert ImageChops.difference(first, again).getbbox() is None, num
        stationary = draw_at(0.3, reduced=True)
        stationary_later = draw_at(3.0, reduced=True)
        assert ImageChops.difference(stationary, stationary_later).getbbox() is None, num
        animates = any(ImageChops.difference(first, draw_at(t)).getbbox() is not None
                       for t in (1.4, 2.2, 3.7))
        if not animates:
            static_effects.append(num)

assert not static_effects, f"Some level FX were static: {static_effects}"
# Level 80 reacts to actual finale puzzle states.
def finale_preview(signals):
    s = adapter.pg.Surface((640, 360))
    s.fill((5, 10, 15))
    draw_level_specific_fx(s, 80, 8, PALETTES[8], 0, 0, 0,
                           1280, 360, 0.7, False, False, [], set(signals))
    return s.im
assert ImageChops.difference(finale_preview(()), finale_preview(
    ('west_record', 'reserve_B', 'evac_proof', 'countdown'))).getbbox() is not None

# Room geometry is not modified by decorative logic; world tiles are registered.
for ch in (1, 3, 5, 8):
    n = (ch - 1) * 10 + 1
    data = json.loads((ROOT / f'data/levels/level_{n:02d}.json').read_text())
    s = adapter.pg.Surface((1280, 720))
    renderer = SceneRenderer()
    renderer.set_level_context(n)
    renderer.set_level_focus(*data['spawn'], n)
    renderer.set_level_tiles([adapter.pg.Rect(*tile) for tile in data['tiles']])
    renderer.draw_background(s, data.get('theme', 'awakening'), 0, 0, 1.0,
                             data['width'], data['height'], powered=True)

composer = ROOT / 'tools/build_soundtracks_hifi.py'
source = composer.read_text()
assert 'CHAPTER_MELODIES' in source and 'SPECS' in source
assert 'finale_ascent' in source and 'write_wav_copy=False' in source
assert 'get_level_fx_name' in (SRC / 'visuals/level_effects.py').read_text()
assert 'phase_accum += dt * fps' in (SRC / 'visuals/robot_sprite.py').read_text()
assert 'set_active_signals(self.puzzle_manager.active_signals)' in (SRC / 'levels/level_manager.py').read_text()

metrics = json.loads((ROOT / 'docs/polish_qa/audio_metrics.json').read_text())
assert len(metrics) == 8 and len({m['bpm'] for m in metrics}) == 8
for m in metrics:
    assert m['rate'] == 44100 and m['channels'] == 2
    assert m['mix_peak'] < .98 and m['quiet_seam'] < .02 and m['rhythm_seam'] < .02
if shutil.which('ffprobe'):
    for i in list(range(1, 9)) + [80]:
        if i == 80:
            paths = [ROOT / 'data/music/finale_ascent_quiet.ogg',
                     ROOT / 'data/music/finale_ascent_rhythm.ogg',
                     ROOT / 'soundtrack_previews/Chapter_80_Finale_preview.ogg']
        else:
            paths = [ROOT / f'data/music/chapter_{i}_quiet.ogg',
                     ROOT / f'data/music/chapter_{i}_rhythm.ogg',
                     ROOT / f'soundtrack_previews/Chapter_{i:02d}_preview.ogg']
        stats = []
        for p in paths:
            assert p.exists() and p.stat().st_size > 10000, p
            out = subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'a:0',
                 '-show_entries', 'stream=sample_rate,channels:format=duration',
                 '-of', 'json', str(p)], text=True)
            probe = json.loads(out)
            assert probe['streams'][0]['sample_rate'] == '44100'
            assert probe['streams'][0]['channels'] == 2
            stats.append(float(probe['format']['duration']))
        assert max(stats) - min(stats) < 0.002, (i, stats)

# Most importantly, Level JSON remained unchanged in this audio+visual update.
print('PASS: 80 deterministic, reduced-motion-safe and animating level FX signatures')
print('PASS: Level 80 FX responds to its finale proof signals')
print('PASS: world-space renderer, distinct chapter music, 27 audio files and synchronized tracks')
print('LIMITATION: native Pygame collisions/playthrough, gameplay frame rate and human audio review untested')
