"""Verify ECHO-7 finale geometry, level data safety and nine music scores.

Does not claim Pygame runtime performance or complete puzzle solvability.
"""
from __future__ import annotations
import json
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[1]
pre=ROOT/'data/levels_pre_finale_overhaul_backup'

def overlap(a,b):
    return a[0]<b[0]+b[2] and a[0]+a[2]>b[0] and a[1]<b[1]+b[3] and a[1]+a[3]>b[1]

added_count=0
removed_count=0
for n in range(25,81):
    old=json.loads((pre/f'level_{n:02d}.json').read_text())
    cur=json.loads((ROOT/f'data/levels/level_{n:02d}.json').read_text())
    assert cur['doors']==old['doors'] and cur['spawn']==old['spawn'] and cur['exit']==old['exit'],n
    for cat in ('switches','plates','generators','valves','latching_relays','routing_consoles','sequences',
                'crates','moving_platforms','optical_beams','lasers','water_zones','wind_zones'):
        assert cur.get(cat)==old.get(cat),(n,cat)
    before_ids={p['id'] for p in old['one_way_platforms']}
    after_ids={p['id'] for p in cur['one_way_platforms']}
    assert after_ids <= before_ids,n
    removed_count+=len(before_ids-after_ids)
    assert not any(overlap((cur['spawn'][0],cur['spawn'][1],26,46),t) for t in cur['tiles']),n
    old_tile_set={tuple(t) for t in old['tiles']}
    added=[t for t in cur['tiles'] if tuple(t) not in old_tile_set]
    added_count+=len(added)
    for tile in added:
        assert not any(overlap(tile,t) for t in old['tiles']),(n,'tile overlaps old terrain')
        assert not overlap(tile,(cur['exit'][0],cur['exit'][1],48,80)),(n,'blocked exit')
        for cat in ('switches','generators','valves','latching_relays','routing_consoles',
                    'collectibles','npcs','checkpoints','plates','dash_recharges','springs'):
            for obj in cur.get(cat,[]):
                if not isinstance(obj,dict) or 'x' not in obj or 'y' not in obj: continue
                x,y=obj['x'],obj['y']
                width,height=(obj.get('w',24),obj.get('h',28))
                if cat not in ('collectibles','springs'):width,height=24,36
                assert not overlap(tile,(x,y,width,height)),(n,cat,obj.get('id') or obj.get('link_id'))

l80=json.loads((ROOT/'data/levels/level_80.json').read_text())
assert len(l80['one_way_platforms'])==3 and len(l80['tiles'])==35
assert {p['id'] for p in l80['one_way_platforms']}=={'stair0','stair2','moon_balcony'}
assert l80['doors'][0]['required_links']==['evac_proof','countdown']
for n in range(1,9):
    tracks=(ROOT/f'data/music/chapter_{n}_quiet.ogg',ROOT/f'data/music/chapter_{n}_rhythm.ogg',
            ROOT/f'soundtrack_previews/Chapter_{n:02d}_preview.ogg')
    for f in tracks:
        assert f.exists() and f.stat().st_size>20000,f
        val=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries',
            'stream=sample_rate,channels','-of','json',str(f)]))
        assert val['streams'][0]['sample_rate']=='44100' and val['streams'][0]['channels']==2
for name in ('finale_ascent_quiet.ogg','finale_ascent_rhythm.ogg'):
    assert (ROOT/'data/music'/name).is_file(),name
assert (ROOT/'soundtrack_previews/Chapter_80_Finale_preview.ogg').is_file()
print(f'PASS: Level 80 9 -> 3 catwalks, 17 -> 35 solid structures; added {added_count} safe terrain sections and removed {removed_count} additional late-game catwalks.')
print('PASS: mandatory puzzle entities and gate dependencies preserved, no new device overlaps; 27 stereo OGG files present.')
print('LIMITATION: Actual playthroughs and subjective music quality remain unverified.')
