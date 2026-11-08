"""Validate new precision-content placement without importing pygame.

This is JSON integrity/placement checking, NOT traversability testing.
"""
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

for level in range(1,25):
    d=json.loads((ROOT/'data/levels'/f'level_{level:02d}.json').read_text())
    assert d['abilities']['wall_jump']==(level>=5),level
    assert d['abilities']['dash']==(level>=9),level
    occupied={}
    for group in ('springs','dash_recharges','one_way_platforms','dash_barriers'):
        for obj in d[group]:
            assert isinstance(obj['id'],str) and obj['id'] not in occupied,(level,obj)
            occupied[obj['id']]=group
            x,y=obj['x'],obj['y']
            w,h=obj.get('w',28),obj.get('h',28)
            assert 40 <= x and x+w <= d['width']-40,(level,obj)
            assert 40 <= y and y+h <= d['height'],(level,obj)
            for tx,ty,tw,th in d['tiles']:
                assert not (x<tx+tw and x+w>tx and y<ty+th and y+h>ty), (level,obj,'terrain overlap')
    if level<9:
        assert not d['dash_recharges'] and not d['dash_barriers']
    if level<5:
        assert not d['springs'] and not d['one_way_platforms']
print('PASS: 24 room ability gates, new object bounds, IDs and terrain clearance')
print('NOTE: geometry integrity does not prove traversal or puzzle correctness')
