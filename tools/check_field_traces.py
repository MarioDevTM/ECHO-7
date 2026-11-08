"""Dependency-free validation of 56 new optional forensic field traces."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def check():
    errors=[]
    for n in range(25,81):
        data=json.loads((ROOT/f'data/levels/level_{n:02d}.json').read_text())
        fields=[c for c in data.get('collectibles',[])
                if c.get('optional_investigation') and c['id'].startswith('field_trace_')]
        if len(fields)!=1:
            errors.append(f'level {n}: expected exactly one forensic trace, got {len(fields)}');continue
        f=fields[0]
        if n < 80:
            bonus=[c for c in data.get('collectibles',[]) if c['id']==f'service_challenge_{n:02d}']
            if len(bonus)!=1 or bonus[0].get('required_links')!=[] or not bonus[0].get('optional_investigation',False):
                errors.append(f'level {n}: missing or invalid cleaned non-blocking service record')
        if f['id']!=f'field_trace_{n:02d}' or not (40<=f['x']<data['width']-40 and 50<=f['y']<data['height']-60):
            errors.append(f'level {n}: invalid trace id/position')
        producers=set()
        for kind in ('latching_relays','switches','generators','valves','plates','optical_beams'):
            producers.update(x['link_id'] for x in data.get(kind,[]) if 'link_id' in x)
        for link in f.get('required_links',[]):
            if link not in producers:errors.append(f'level {n}: unknown trace signal {link}')
        if not any(t[0]-1<=f['x']<=t[0]+t[2] and t[1] > f['y']+27 and t[1]-f['y']<=130
                   for t in data['tiles']):
            errors.append(f'level {n}: no nearby ground')
    if errors:
        for e in errors:print('FAIL:',e)
        raise SystemExit(1)
    print('PASS: 56 optional traces — ID, signal producers, grounded staging positions.')
    print('NOTE: Live Pygame reachability and signal acquisition not proven.')

if __name__=='__main__':check()
