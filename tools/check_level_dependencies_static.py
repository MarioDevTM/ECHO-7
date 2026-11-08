"""Static, pygame-free signal graph checks for all 80 levels.

This is necessary but NOT sufficient to establish player traversal or solvability.
"""
from pathlib import Path
import json
from graphlib import TopologicalSorter, CycleError
ROOT=Path(__file__).resolve().parents[1]

def check(n,d):
    errors=[]
    producers={}
    for category in ('plates','switches','generators','valves','optical_beams','latching_relays','signal_inverters'):
        for entry in d.get(category,[]):
            link=entry.get('link_id')
            if not link:continue
            if link in producers:errors.append(f'{link} emitted by both {producers[link]} and {category}')
            producers[link]=category
    for p in d.get('routing_consoles',[]):
        for link in (p['a_signal'],p['b_signal']):
            # Multiple control stations can share one route_id/output pair
            # (e.g. levels 20 & 24 intentionally expose both ends).
            if link in producers and producers[link]!='routing_console':
                errors.append(f'{link} collides with a different signal source')
            producers[link]='routing_console'
    for seq in d.get('sequences',[]):
        producers[seq['group_id']]='sequence'
    for category in ('doors','latching_relays','moving_platforms','routing_consoles'):
        for obj in d.get(category,[]):
            req=obj.get('required_links',[])
            for link in req:
                if link not in producers:errors.append(f'{category}: unknown {link}')
            for a,b in [('A','B'),('reserve_A','reserve_B'),('up','down'),('east_up','east_down'),('dry','full')]:
                if a in req and b in req:errors.append(f'{category}: mutually exclusive {a}+{b} simultaneously')
    graph={v['link_id']:[s for s in v.get('required_links',[]) if producers.get(s)=='latching_relays']
           for v in d.get('latching_relays',[])}
    try:list(TopologicalSorter(graph).static_order())
    except CycleError as exc:errors.append(f'cyclic latched relays: {exc.args[1]}')
    return errors

def run():
    failures={}
    for n in range(1,81):
        d=json.loads((ROOT/f'data/levels/level_{n:02}.json').read_text())
        errs=check(n,d)
        if errs:failures[n]=errs
    if failures:
        for n,v in failures.items():print('FAIL',n,v)
        raise SystemExit(1)
    print('PASS: 80 levels — signal producers, gate dependencies, relay acyclicity, exclusivity checks.')
    print('NOTE: physical reachability, solve state-space, and actual game play remain unverified.')

if __name__=='__main__':run()
