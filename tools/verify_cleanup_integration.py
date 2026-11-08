"""Static invariants for ECHO-7's Gemini architectural cleanup.

Note: this does NOT prove puzzle solvability, player physics, or live rendering.
"""
from pathlib import Path
import json, hashlib, ast, subprocess, sys

R=Path(__file__).resolve().parents[1]
PRE=R/'data/levels_pre_cleanup_backup'
BACK=R/'data/levels_backup'
PRUNE_AUDIT=json.loads((R/'docs/PLATFORM_PRUNING_AUDIT.json').read_text())
PRUNED={row['level']:{p['id'] for p in row['removed']} for row in PRUNE_AUDIT}


def overlap(a,b):
    return a[0]<b[0]+b[2] and a[0]+a[2]>b[0] and a[1]<b[1]+b[3] and a[1]+a[3]>b[1]


removed_plats=removed_devices=added_walls=0
for n in range(1,81):
    before_path=PRE/f'level_{n:02d}.json'
    after_path=R/f'data/levels/level_{n:02d}.json'
    assert before_path.exists() and after_path.exists(),n
    before=json.loads(before_path.read_text())
    after=json.loads(after_path.read_text())
    if n<=24:
        assert before_path.read_bytes()==after_path.read_bytes(),f'Level {n}: early level changed'
        continue
    for k in ('spawn','exit','width','height','chapter','theme','doors','abilities',
              'moving_platforms','crates','plates','hazards','checkpoints',
              'optical_beams','wind_zones','water_zones','laser','lasers',
              'springs','dash_barriers','dash_recharges','npcs'):
        assert before.get(k)==after.get(k),f'Level {n}: protected {k} altered'
    original_platforms=[p for p in before.get('one_way_platforms',[])
                        if not p['id'].startswith(('overhaul_step_','validation_foot_'))
                        and p['id'] not in PRUNED.get(n,set())]
    if n<80:
        assert original_platforms==after.get('one_way_platforms',[]),f'Level {n}: unexpected platform alteration beyond audited pruning'
        bonus=[c for c in after['collectibles'] if c['id']==f'service_challenge_{n:02d}']
        assert len(bonus)==1 and bonus[0].get('required_links')==[],f'Level {n}: optional record dependency'
        c=bonus[0]
        assert 0<=c['x']<after['width']-24 and 0<=c['y']<after['height']-28,n
        assert not any(overlap((c['x'],c['y'],24,28),t) for t in after['tiles']),f'Level {n}: optional record inside terrain'
        assert after.get('side_challenge_policy',{}).get('optional_signals')==[],n
    remaining={k:after.get(k,[]) for k in ('switches','generators','valves','latching_relays','routing_consoles','sequences')}
    removed_plats+=len(before.get('one_way_platforms',[]))-len(after.get('one_way_platforms',[]))
    removed_devices+=sum(len(before.get(k,[]))-len(v) for k,v in remaining.items())
    # Original (non-generated) puzzle objects are preserved exactly.
    for k,v in remaining.items():
        must_keep=[x for x in before.get(k,[]) if not
                   (str(x.get('id') or x.get('link_id') or x.get('group_id') or '').startswith(f'overhaul_{n:02d}_')
                    or str(x.get('id') or x.get('link_id') or x.get('group_id') or '')==f'sector_{n:02d}_validated')]
        assert all(x in v for x in must_keep),f'Level {n}: original puzzle device {k} lost'
    new_tiles=after['tiles'][len(before['tiles']):]
    assert all(a==b for a,b in zip(after['tiles'][:len(before['tiles'])],before['tiles'])),f'Level {n}: pre-clean terrain changed'
    for new in new_tiles:
        assert not any(overlap(new,old) for old in before['tiles']),f'Level {n}: added wall overlaps old terrain'
        sx,sy=after['spawn'];ex,ey=after['exit']
        assert not overlap(new,(sx,sy,26,46)) and not overlap(new,(ex,ey,48,80)),f'Level {n}: blocked spawn/exit'
    added_walls+=len(new_tiles)
    assert not any(overlap((after['spawn'][0],after['spawn'][1],26,46), t) for t in after['tiles']),f'Level {n}: spawn blocked'
    assert not any(overlap((after['exit'][0],after['exit'][1],48,80), t) for t in after['tiles']),f'Level {n}: exit blocked'
    assert after.get('cleanup_v3_audit',{}).get('level')==n,n

assert removed_plats>=200 and removed_devices>=100,(removed_plats,removed_devices)
assert added_walls>=1,added_walls
renderer=ast.parse((R/'src/visuals/pixel_environment.py').read_text())
cls=next(x for x in renderer.body if isinstance(x,ast.ClassDef) and x.name=='PixelEnvironment')
methods={x.name for x in cls.body if isinstance(x,ast.FunctionDef)}
assert {'set_level','set_focus','menu_background','set_world_tiles','set_local_signal_nodes',
        '_get_upper_chunk','_draw_tile_linked_architecture','draw'} <= methods
for script in ('check_level_schema_offline.py','check_level_dependencies_static.py',
               'check_field_traces.py','check_remodel_integrity.py','check_pixel_environment_offline.py'):
    result=subprocess.run([sys.executable,str(R/'tools'/script)],cwd=R,text=True,capture_output=True,timeout=45)
    assert result.returncode==0,f'{script}: {result.stdout} {result.stderr}'
print(f'PASS: 1-24 unchanged, {removed_plats} redundant steps and {removed_devices} side devices removed; {added_walls} solid tiles added')
print('PASS: original exit gates and mandatory puzzle objects preserved; optional reward ungated and non-colliding; 5 additional checks pass')
print('NOT VERIFIED: live Pygame playthrough or reachability of every optional collectible.')
