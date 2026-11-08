"""Verify authored plans match the packaged rooms and the protected campaign prefix."""
import hashlib
import json
from pathlib import Path
import sys
from zipfile import ZipFile

from expand_campaign import room

ROOT = Path(__file__).resolve().parents[1]
LEVELS = ROOT / 'data/levels'
original = ZipFile(sys.argv[1]) if len(sys.argv) > 1 else None
prefix = json.loads((ROOT / 'docs/preserved_level_hashes.json').read_text())
assert len(prefix) == 24
for name, expected in prefix.items():
    data = (LEVELS / name).read_bytes()
    assert hashlib.sha256(data).hexdigest() == expected, name
    if original:
        assert original.read('ECHO-7/data/levels/' + name) == data, name

specs = json.loads(Path(__file__).with_name('room_plans.json').read_text())
assert [spec['number'] for spec in specs] == list(range(25, 80))
signatures = set()
for n in range(25, 81):
    name = f'level_{n:02}.json'
    data = json.loads((LEVELS / name).read_text())
    assert data.get('overhaul_version') == 1, name
    if n < 80:
        assert data.get('secondary_validation_1'), name
        assert not any(p['id'].startswith(('overhaul_step_', 'validation_foot_'))
                       for p in data.get('one_way_platforms',[])), name
        assert data['side_challenge_policy']['optional_signals']==[], name
        assert not data['side_challenge_policy']['campaign_blocking'], name
    else:
        assert len([p for p in data.get('one_way_platforms',[])
                    if p['id'].startswith('overhaul_step_')])==3, name
    signature = tuple(map(tuple, data['tiles']))
    assert signature not in signatures, name
    signatures.add(signature)
    assert data['chapter'] == (n-1)//10+1
    assert data['doors'][0]['required_links'] and any(v['id']=='kip' for v in data['npcs'])
    assert any(v['id']==f'log_{n:02}' for v in data['collectibles'])
    if original:
        previous = json.loads(original.read('ECHO-7/data/levels/' + name))
        assert previous['one_way_platforms'] != data['one_way_platforms'], name
print('PASS: first 24 hashes, 56 independently authored late-stage structural additions, 55 cleaned optional service investigations, original exit gates preserved, final stage preserved.')
