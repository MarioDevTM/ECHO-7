"""Pygame-free structural checks for the five redesigned levels and audio deliverables.

This is NOT input-driven playtesting. Run alongside the actual pygame test suite.
"""
import json
from pathlib import Path
import wave

root = Path(__file__).resolve().parents[1]

def room(num):
    return json.loads((root / f'data/levels/level_{num:02}.json').read_text())

def by_id(items, key='id'):
    return {item[key]: item for item in items}

freight = room(3)
assert by_id(freight['latching_relays'], 'link_id')['relay_3_staged']['required_links'] == ['plate_3_staging']
assert {'relay_3_staged', 'plate_assembly'}.issubset(set(freight['moving_platforms'][0]['required_links']))
assert 'relay_3_staged' in by_id(freight['doors'])['d3_exit']['required_links']
print('03: staging memory must be set before cargo leaves its first plate')

counter = room(7)
assert counter['moving_platforms'][0]['logic'] == 'ANY'
assert set(counter['moving_platforms'][0]['required_links']) == {'plate_counter_1', 'relay_7_counter'}
assert 'relay_7_counter' in by_id(counter['doors'])['d7_exit']['required_links']
print('07: remembered counterweight supports continued ferry use')

laser = room(11)
assert set(x['link_id'] for x in laser['optical_beams']) == {'opt_11_main', 'opt_11_exit'}
assert laser['optical_beams'][0]['receiver'][1] < laser['optical_beams'][1]['receiver'][1]
assert laser['latching_relays'][0]['required_links'] == ['opt_11_main']
assert set(by_id(laser['doors'])['d11_exit']['required_links']) >= {'relay_11_bridge','opt_11_exit'}
print('11: upper and lower receiver states mutually demand a mirror change')

sump = room(13)
assert sump['signal_inverters'] == [{'link_id':'sump_refilled','input':'valve_13_drain', 'water_zone':'wz_13_1'}]
assert set(sump['latching_relays'][0]['required_links']) == {'valve_13_drain','plate_13_dry'}
assert set(by_id(sump['doors'])['d13_exit']['required_links']) >= {'relay_13_sump', 'sump_refilled'}
print('13: dry-state proof must survive return to refilled-state exit')

escape = room(20)
consoles = [p for p in escape['routing_consoles'] if p['route_id'] == 'reserve_20']
assert len(consoles)==2
assert consoles[0]['route_id'] == consoles[1]['route_id']
assert (consoles[0]['a_signal'],consoles[0]['b_signal']) == (consoles[1]['a_signal'],consoles[1]['b_signal'])
assert escape['moving_platforms'][0]['logic'] == 'ANY'
assert set(escape['moving_platforms'][0]['required_links']) == {'route_20_ferry','gen_20_independent'}
assert {'gen_20_independent','route_20_exit'}.issubset(set(by_id(escape['doors'])['d20_exit']['required_links']))
print('20: transfer without backup disables ferry; backup allows evacuation transfer')

music = root / 'data/music'
for chapter in range(1, 9):
    lengths = []
    for layer in ('quiet', 'rhythm'):
        with wave.open(str(music / f'chapter_{chapter}_{layer}.wav')) as sound:
            assert (sound.getnchannels(), sound.getframerate(), sound.getsampwidth()) == (1, 22050, 2)
            lengths.append(sound.getnframes())
    assert lengths[0] == lengths[1] > 0
assert (music / 'surface_resolution.wav').is_file()
for n in range(1,81):
    assert room(n)['level_id'] == n
    assert room(n)['chapter'] == (n-1)//10+1
print('PASS: eight synchronized music pairs, finale cue, 80 ordered levels.')
