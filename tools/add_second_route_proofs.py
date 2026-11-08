"""Add secondary, physically distant validation climbs to remodeled rooms.

Runs after remodel_late_chambers.py. Preserves original puzzle graph and
Stage 80's authored final escape. Does not claim dynamic solvability.
"""
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def collides(r,t):
    x,y,w,h=r;a,b,c,d=t
    return x<a+c and x+w>a and y<b+d and y+h>b


results=[]
for n in range(25,80):
    p=ROOT/f'data/levels/level_{n:02}.json';d=json.loads(p.read_text())
    if d.get('secondary_validation_1'):
        continue
    current=d.get('overhaul_design',{});assert current.get('mandatory')
    cps=d.get('checkpoints',[])
    if not cps:
        results.append((n,'no checkpoint'));continue
    cp=cps[0];x=cp['x'];y=cp['y']
    valid=None
    for sign in (-1 if n%2 else 1,1 if n%2 else -1):
        steps=[(int(x+sign*80-39),int(y-63),78,12),
               (int(x+sign*165-39),int(y-125),78,12)]
        if any(a<42 or a+w>d['width']-42 or b<92 or b+h>d['height']-92 for a,b,w,h in steps):continue
        if any(collides(r,t) for r in steps for t in d['tiles']):continue
        valid=(steps,sign);break
    if valid is None:
        results.append((n,'secondary route blocked'));continue
    steps,sign=valid
    for i,(sx,sy,w,h) in enumerate(steps):
        d['one_way_platforms'].append(dict(id=f'validation_foot_{n}_{i}',x=sx,y=sy,w=w,h=h))
    original_req=d['doors'][0]['required_links']
    base_sig=[r for r in original_req if r.startswith(f'overhaul_{n:02}_')]
    assert base_sig, n
    # Final inspector requires one of the newly authored branch readings.
    sig=f'sector_{n:02}_validated'
    sx,sy,w,h=steps[-1]
    d['latching_relays'].append(dict(link_id=sig,x=sx+18,y=sy,required_links=[base_sig[-1]]))
    d['doors'][0]['required_links'].append(sig)
    d.setdefault('hint_route',[]).append(sig)
    msg='After the service climb, return to the final beacon and record the remote upper validation before exiting.'
    d.setdefault('hint_notes',{})[sig]=[msg,msg,msg]
    d.setdefault('solution_steps',[]).append(msg)
    d['secondary_validation_1']=dict(checkpoint=cp['id'],extra_platforms=2,signal=sig)
    p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    results.append((n,'added'))

added=[n for n,status in results if status=='added']
print('Secondary route added',len(added),'of 55; skipped',[n for n,status in results if status!='added'])
(ROOT/'docs'/'SECONDARY_ROUTE_REPORT.md').write_text(
    '# Secondary exploration routes\n\n'
    f'Added mechanically required validation climbs to {len(added)}/55 stages. '
    'The other stages retain their first mandatory upper-route task. '
    'These changes are structural but have not been playtested.\n\n'
    + '\n'.join(f'- Level {n}: {status}' for n,status in results)+'\n',encoding='utf-8')
