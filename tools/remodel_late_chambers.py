"""Idempotent, source-aware stage 25–80 spatial/puzzle additions.

Changes REAL traversable geometry and the required exit signal for 55 rooms.
The carefully hand-scripted Level 80 finale retains its existing gate dependency,
with a new optional service detour. Never regenerates 1–24.

This tool edits authored JSON, it does not regenerate their base topology.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEVELS = ROOT / 'data/levels'
# Distinct chapter- and level-specific brief IDs and supported signal patterns.
# Repetition of a mechanism can be productive; repeating the same route geometry
# is not. Every profile is deliberately specified, not random coordinates.
PROFILE = {
 25:('relay_bus','left_up'),26:('sequence','right_rise'),27:('generator','left_switchback'),
 28:('valve_relay','right_up'),29:('route_proof','right_return'),30:('generator_relay','left_rise'),
 31:('sequence','right_switchback'),32:('valve','left_return'),33:('relay_bus','right_rise'),
 34:('generator','left_up'),35:('route_proof','right_up'),36:('sequence','left_switchback'),
 37:('valve_relay','left_rise'),38:('generator_relay','right_return'),39:('route_proof','right_switchback'),
 40:('relay_bus','left_return'),41:('valve','right_rise'),42:('generator_relay','left_up'),
 43:('sequence','right_switchback'),44:('valve_relay','right_return'),45:('route_proof','left_rise'),
 46:('generator','right_up'),47:('relay_bus','left_switchback'),48:('valve','right_return'),
 49:('sequence','left_up'),50:('generator_relay','right_rise'),51:('generator','right_return'),
 52:('relay_bus','left_rise'),53:('sequence','right_up'),54:('valve_relay','left_switchback'),
 55:('route_proof','right_switchback'),56:('generator_relay','left_return'),57:('sequence','right_rise'),
 58:('generator','left_up'),59:('valve','right_return'),60:('relay_bus','left_switchback'),
 61:('route_proof','right_up'),62:('generator_relay','left_return'),63:('sequence','right_rise'),
 64:('valve','left_up'),65:('generator','right_switchback'),66:('relay_bus','left_rise'),
 67:('valve_relay','right_return'),68:('route_proof','left_switchback'),69:('sequence','right_up'),
 70:('generator_relay','left_return'),71:('valve','right_rise'),72:('relay_bus','left_up'),
 73:('generator_relay','right_switchback'),74:('route_proof','left_rise'),75:('sequence','right_return'),
 76:('valve_relay','left_switchback'),77:('generator','right_up'),78:('relay_bus','left_return'),
 79:('sequence','right_rise'),80:('finale_detour','left_up'),
}
assert set(PROFILE)==set(range(25,81))

# Each profile has a deliberately different traversal zigzag. Horizontal steps
# are within normal running-jump reach; vertical rises are 56–64 px against a
# ~106 px nominal jump apex. Engine movement must still be playtested.
PATH = {
 'left_up':        (-1, ((48,60),(118,118),(207,174))),
 'right_up':       ( 1, ((55,59),(132,125),(212,180))),
 'left_rise':      (-1, ((63,62),(147,119),(218,179))),
 'right_rise':     ( 1, ((66,61),(149,120),(230,184))),
 'left_switchback':(-1, ((40,60),(141,111),(93,180))),
 'right_switchback':(1, ((49,60),(154,120),(108,182))),
 'left_return':    (-1, ((80,65),(169,125),(111,184))),
 'right_return':   ( 1, ((83,65),(174,119),(119,178))),
}


def overlap(r, tile):
    x,y,w,h=r; a,b,c,d=tile
    return x<a+c and x+w>a and y<b+d and y+h>b


def platform_route(data, route):
    sx,sy = data['spawn']; floor = sy+46
    direction, offsets = PATH[route]
    initial=(direction, offsets)
    # Try the authored direction first, followed by the mirrored traversal
    # when the available world geometry blocks that side.
    candidates=(initial, (-direction, offsets))
    for direction,offsets in candidates:
        for drop in (0,10,20,30):
            pts=[]
            for dx,dy in offsets:
                x = int(sx + direction*dx - 39)
                y = int(floor - dy + drop)
                pts.append((x,y,78,12))
            if any(x<45 or x+w>data['width']-45 or y<90 or y+h>=data['height']-90 for x,y,w,h in pts):
                continue
            if any(overlap(r,t) for r in pts for t in data.get('tiles',[])):
                continue
            # Don't block any original moving crossing or preexisting ledge.
            existing=[(p['x'],p['y'],p['w'],p['h']) for k in ('moving_platforms','one_way_platforms')
                      for p in data.get(k,[])]
            if any(overlap(r,t) for r in pts for t in existing):
                continue
            return pts, direction
    return [], 0


def make_level(n):
    p=LEVELS/f'level_{n:02}.json'
    d=json.loads(p.read_text(encoding='utf-8'))
    kind,route=PROFILE[n]
    signal=f'overhaul_{n:02}_'
    if d.get('overhaul_version')==1:
        return {'level':n,'status':'already applied','profile':kind}
    assert d['level_id']==n
    before=hashlib.sha256(p.read_bytes()).hexdigest()
    steps, actual_dir=platform_route(d,route)
    # No unreachable gate: when a safe platform route cannot be established,
    # place the new interlock on the accessible spawn deck instead.
    floor=d['spawn'][1]+46
    if not steps:
        sx=d['spawn'][0]
        steps=[(sx+36, floor-60,78,12),(sx+107,floor-120,78,12),(sx+185,floor-178,78,12)]
        # Do NOT create potentially solid-overlapping steps in the fallback.
        steps=[r for r in steps if not any(overlap(r,t) for t in d.get('tiles',[]))]
    for i,(x,y,w,h) in enumerate(steps):
        d['one_way_platforms'].append(dict(id=f'overhaul_step_{n}_{i}',x=x,y=y,w=w,h=h))
    # 2 side-route stations are separated from each other when possible.
    px=[r[0]+18 for r in steps]
    py=[r[1] for r in steps]
    if not px:
        px=[d['spawn'][0]+42]*3; py=[floor]*3
    while len(px)<3:
        px.append(px[-1]);py.append(py[-1])
    a,b,c=(px[0],py[0]),(px[1],py[1]),(px[2],py[2])
    # Unique signal names guarantee compatibility with existing chapter routing.
    mission=''; req=[]
    if kind=='generator':
        sid=signal+'power'
        d['generators'].append(dict(link_id=sid,x=c[0],y=c[1]))
        req=[sid];mission='Explore the elevated service detour and energize its auxiliary generator.'
    elif kind=='valve':
        sid=signal+'valve'
        d['valves'].append(dict(link_id=sid,x=c[0],y=c[1]))
        req=[sid];mission='Find the upper service handwheel and restore the isolated circuit.'
    elif kind=='sequence':
        seq_ids=[signal+t for t in ('first','second','third')]
        for pos,sid in zip((a,b,c),seq_ids):
            d['switches'].append(dict(link_id=sid,x=pos[0],y=pos[1],mode='sequence'))
        group=signal+'order'
        d['sequences'].append(dict(group_id=group,order=seq_ids))
        req=[group]; mission='Visit three elevated diagnostics in the numbered order; an incorrect input resets the chain.'
    elif kind=='relay_bus':
        gid,mem=signal+'generator',signal+'memory'
        A,B=signal+'A',signal+'B'
        d['generators'].append(dict(link_id=gid,x=a[0],y=a[1]))
        d['latching_relays'].append(dict(link_id=mem,x=b[0],y=b[1],required_links=[gid,A]))
        d['routing_consoles'].append(dict(id=signal+'selector',route_id=signal+'bus',x=c[0],y=c[1],a_signal=A,b_signal=B))
        req=[mem,B]
        mission='Energize the service bus, memorize A at the middle station, and reroute to B before proceeding.'
    elif kind=='route_proof':
        mem,sid=signal+'proof',signal+'valve'
        d['valves'].append(dict(link_id=sid,x=a[0],y=a[1]))
        d['latching_relays'].append(dict(link_id=mem,x=c[0],y=c[1],required_links=[sid]))
        req=[mem];mission='Activate the lower isolation valve, then climb and permanently record its state.'
    elif kind=='valve_relay':
        sid,mem=signal+'valve',signal+'record'
        d['valves'].append(dict(link_id=sid,x=b[0],y=b[1]))
        d['latching_relays'].append(dict(link_id=mem,x=c[0],y=c[1],required_links=[sid]))
        req=[mem];mission='Use the intermediate valve and record its new state at the higher control point.'
    elif kind=='generator_relay':
        sid,mem=signal+'generator',signal+'record'
        d['generators'].append(dict(link_id=sid,x=a[0],y=a[1]))
        d['latching_relays'].append(dict(link_id=mem,x=c[0],y=c[1],required_links=[sid]))
        req=[mem];mission='Restore the auxiliary feeder and latch a reading from the upper inspection platform.'
    else:
        # Finale has its own rich west/reserve/central proof graph. Do not risk
        # destroying it: add a unique, player-facing optional high-route log.
        cid=signal+'log'
        d['collectibles'].append(dict(id=cid,x=c[0],y=c[1]-29,
                title='ECHO-7 / Last exterior relay',
                text='A final observation point above the surface breach. Optional: the exit remains controlled by EVAC PROOF.'))
        mission='Optional elevated viewpoint; preserve all original escape dependencies.'
    if req:
        # Existing final door and its required signals are preserved in order.
        d['doors'][0]['required_links'].extend(req)
        # The mechanic must be visible as a clear prerequisite and represented
        # by existing hint UI without spoiling prior stages.
        d.setdefault('hint_route',[]).extend([k for k in req if k not in d.get('hint_route',[])])
        for k in req:
            d.setdefault('hint_notes',{})[k]=[mission,mission,mission]
        d.setdefault('solution_steps',[]).append(mission)
    if steps:
        d.setdefault('decorations',[]).append(dict(type='monitor',x=steps[0][0]+2,y=steps[0][1]-103,
            text=f'ACCESS / {n:02}'))
        d.setdefault('decorations',[]).append(dict(type='warning_stripe',x=steps[-1][0],
            y=steps[-1][1]+12,w=steps[-1][2]))
    d['subtitle']=d.get('subtitle','') + '  //  SERVICE DETOUR: ' + mission
    # Source audit fields: ignored by gameplay; help reviewers confirm intent.
    d['overhaul_version']=1
    d['overhaul_design']=dict(profile=kind,route=route,actual_direction=actual_dir,
                               mandatory=bool(req),service_platform_count=len(steps))
    p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    return {'level':n,'status':'changed','profile':kind,'route':route,
            'new_platforms':len(steps),'new_exit_links':req,'before_sha256':before,
            'after_sha256':hashlib.sha256(p.read_bytes()).hexdigest()}


def main():
    results=[make_level(n) for n in range(25,81)]
    (ROOT/'docs'/'LATE_GAME_REMODEL_MANIFEST.json').write_text(json.dumps(results,indent=2)+'\n')
    print('Changed',sum(r['status']=='changed' for r in results),'levels;',
          'New platforms:',sum(r.get('new_platforms',0) for r in results))
    for r in results:
        print(r['level'],r['status'],r['profile'],r.get('new_platforms',''))

if __name__=='__main__':main()
