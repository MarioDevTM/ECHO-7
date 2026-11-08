"""Reproducible, pygame-free QA of the ECHO-7 focused polish release.

Checks assets, synced HiFi loops, HUD/menu source contracts and all level hashes.
Not a substitute for actual gameplay/interactive audio tests.
"""
from __future__ import annotations
import ast,hashlib,json,subprocess,sys
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
QA=ROOT/'docs/polish_qa'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

baseline=json.loads((QA/'level_baseline_hashes.json').read_text())
pruned=json.loads((ROOT/'docs/PLATFORM_PRUNING_AUDIT.json').read_text())
for i in range(1,81):
    file=ROOT/f'data/levels/level_{i:02d}.json'
    new=json.loads(file.read_text())
    assert new['level_id']==i
    if i<=24:
        assert sha(file)==baseline[str(i)], f'Unexpected early level mutation: {i}'
    else:
        authored=json.loads((ROOT/f'data/levels_pre_cleanup_backup/level_{i:02d}.json').read_text())
        before=json.loads((ROOT/f'data/levels_pre_finale_overhaul_backup/level_{i:02d}.json').read_text())
        assert new['spawn']==before['spawn'] and new['exit']==before['exit'],i
        assert new['doors']==before['doors'] and new['abilities']==before['abilities'],i
        assert new['tiles'][:len(authored['tiles'])]==authored['tiles'],f'Authored terrain mutated: {i}'
        assert len(new['tiles'])>=len(authored['tiles'])
        new_ids={p['id'] for p in new['one_way_platforms']}
        assert new_ids <= {p['id'] for p in before['one_way_platforms']},i
        for k in ('switches','generators','valves','latching_relays','routing_consoles',
                  'moving_platforms','optical_beams','checkpoints','crates'):
            assert new[k]==before[k],f'Unexpected puzzle object mutation: {i}.{k}'

icon=ROOT/'data/art/ui/echo7_icon.png'
assert Image.open(icon).size==(256,256)
for size in (32,48,64,128,256):
    assert Image.open(ROOT/f'data/art/ui/echo7_head_{size}.png').size==(size,size)
assert (ROOT/'data/art/ui/echo7_icon.ico').exists()

main=(ROOT/'src/ui/main_menu.py').read_text()
assert '_draw_gallery_detail' in main and '_draw_root_hero' in main
assert 'player/idle_0.png' in main and 'echo7_icon.png' not in main
assert 'self.button_rects.append((rect,action))' in main
assert 'gallery_paused' in main
core=(ROOT/'src/core/game.py').read_text()
assert 'display.set_icon' in core and '_create_display' in core and 'mixer.pre_init(44100, -16, 2' in core
sound=(ROOT/'src/systems/audio.py').read_text()
assert 'chapter}_{layer}.ogg' in sound and '44100' in sound
assert 'chapter}_{layer}.wav' in sound
painter=(ROOT/'src/visuals/pixel_environment.py').read_text()
assert 'def _draw_room_dressing' in painter and 'self._draw_room_dressing(' in painter

metrics=json.loads((QA/'audio_metrics.json').read_text())
assert len(metrics)==8
for i in range(1,9):
    durations=[]
    for role,path in (
        ('quiet',ROOT/f'data/music/chapter_{i}_quiet.ogg'),
        ('rhythm',ROOT/f'data/music/chapter_{i}_rhythm.ogg'),
        ('preview',ROOT/f'soundtrack_previews/Chapter_{i:02d}_preview.ogg')):
        assert path.stat().st_size>10_000, path
        val=json.loads(subprocess.check_output(['ffprobe','-v','error',
            '-show_entries','stream=sample_rate,channels:format=duration',
            '-of','json',str(path)]))
        stream=val['streams'][0]
        assert int(stream['sample_rate'])==44100 and stream['channels']==2,(i,role)
        durations.append(float(val['format']['duration']))
    assert max(durations)-min(durations)<1/44100,(i,durations)
    data=metrics[i-1]
    assert data['mix_peak']<0.98 and data['quiet_seam']<0.02 and data['rhythm_seam']<0.02
print('PASS: protected early stages, audited late-stage architecture, app icon, menu and rendering contracts; 24 synchronized chapter OGGs.')
print('LIMITATION: Pygame gameplay, UI clicking, frame rate, and subjective audio audition untested.')
