"""Conservative, deterministic removal of legacy no-purpose one-way catwalks.

This is a *static geometric heuristic*, not a proof of live solvability.
It compares alternate jump-surface connectivity, keeps nearby interactions,
and backs up every original level. Use --dry-run to inspect proposals.
Re-running on the cleaned JSON changes nothing.
"""
from __future__ import annotations
import argparse
import json
import math
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEVELS = ROOT / 'data' / 'levels'
BACKUP = ROOT / 'data' / 'levels_before_platform_pruning'
REPORT = ROOT / 'docs' / 'PLATFORM_PRUNING_AUDIT.json'

# These tiny floating stepping-stones were installed in previous level iterations.
# Exclude original authored deck_, finale stair_ and moon_ structures.
TARGET_PREFIXES = ('walk',)


def candidates(data):
    """Return solid-tile upper surfaces and one-way catwalk upper surfaces."""
    solids = list(data.get('tiles', []))
    result = []
    for i, (x,y,w,h) in enumerate(solids):
        if w < 36 or h <= 0:
            continue
        # A walkable top needs a clear player-sized rectangle. A raised
        # structural rib under a roof is not a path even if it has an upper edge.
        positions = (x+18, x+w//2, x+w-18)
        usable = any(not any(j != i and
                            sx < tx+tw and sx+26 > tx and
                            y-46 < ty+th and y > ty
                            for j,(tx,ty,tw,th) in enumerate(solids)) for sx in positions)
        if usable:
            result.append(dict(id=f'tile:{i}',x=x,y=y,w=w,kind='tile'))
    for p in data.get('one_way_platforms', []):
        result.append(dict(id=p['id'],x=p['x'],y=p['y'],w=p['w'],kind='platform'))
    return result


def horizontal_gap(a,b):
    return max(0, b['x'] - a['x']-a['w'], a['x']-b['x']-b['w'])


def can_jump(a,b):
    if a is b:
        return False
    rise=a['y']-b['y']  # positive when next deck is higher
    if rise > 89 or rise < -215:
        return False
    # Running jump speed 365/s, gravity 1550/s^2, impulse 575/s.
    disc=575**2-2*1550*rise
    if disc < 0:
        return False
    t=(575+math.sqrt(disc))/1550
    max_gap = min(245, max(85, 365*t*0.70))
    return horizontal_gap(a,b) <= max_gap


def reachable(start, nodes):
    if start is None:
        return set()
    todo=[start]; found={start}
    while todo:
        i=todo.pop()
        for j,node in enumerate(nodes):
            if j not in found and can_jump(nodes[i],node):
                found.add(j);todo.append(j)
    return found


def find_spawn_node(data,nodes):
    sx,sy=data['spawn']; feet=sy+46
    scores=[]
    for i,p in enumerate(nodes):
        dx=max(0,p['x']-sx-13,sx+13-(p['x']+p['w']))
        dy=abs(p['y']-feet)
        if dx<90 and dy<160:
            scores.append((dy+dx*0.4,i))
    return min(scores)[1] if scores else None


def touches_interaction(data,p):
    cx=p['x']+p['w']/2; y=p['y']
    for cat in ('switches','generators','valves','latching_relays','routing_consoles',
                'collectibles','checkpoints','plates','crates','mirrors',
                'dash_recharges','springs','npcs','sequence_terminals'):
        for obj in data.get(cat,[]):
            if not isinstance(obj,dict) or 'x' not in obj or 'y' not in obj:
                continue
            if abs(obj['x']-cx)<110 and -135 < obj['y']-y < 85:
                return f'{cat}:{obj.get("id", obj.get("link_id", "object"))}'
    for posname in ('spawn','exit'):
        x0,y0=data[posname]
        if abs(x0-cx)<105 and abs(y0-y)<110:
            return posname
    for lad in data.get('ladders',[]):
        if abs(lad['x']-cx)<65 and lad['y']-70<=y<=lad['y']+lad['h']+70:
            return 'ladder'
    return None


def analyze(data):
    nodes=candidates(data)
    start=find_spawn_node(data,nodes)
    before=reachable(start,nodes)
    # Critical path anchors: any surface directly below all relevant devices.
    critical={nodes[i]['id'] for i in before if nodes[i]['kind']=='tile'}
    critical.add(nodes[start]['id'] if start is not None else '')
    ranked=[]
    for p in data.get('one_way_platforms',[]):
        if not p['id'].startswith(TARGET_PREFIXES):
            continue
        if touches_interaction(data,p):
            continue
        i=next((i for i,n in enumerate(nodes) if n['id']==p['id']),None)
        if i is None:
            continue
        others=[n for n in nodes if n['id']!=p['id']]
        new_start=find_spawn_node(data,others)
        after=reachable(new_start,others)
        still={others[j]['id'] for j in after}
        # Removing this stepping-stone may not remove access to any original
        # solid-ground path. Note: this is an approximation, not a playtest.
        if not critical.issubset(still):
            continue
        # Also keep the path to other original/remaining one-way platforms that
        # the current graph identifies as reachable from the starting position.
        old_platforms={nodes[j]['id'] for j in before if nodes[j]['kind']=='platform' and nodes[j]['id']!=p['id']}
        if not old_platforms.issubset(still):
            continue
        nearby_tiles=[n for n in nodes if n['kind']=='tile' and abs(n['y']-p['y'])<=45 and horizontal_gap(n,p)<=90]
        near_dist=min((horizontal_gap(n,p)+abs(n['y']-p['y']) for n in nearby_tiles),default=999)
        degree=sum(can_jump(n,nodes[i]) or can_jump(nodes[i],n) for n in nodes if n is not nodes[i])
        # Bias toward visually redundant end-of-run pieces nearest real terrain,
        # but allow a few low-importance isolated dead-ends.
        if near_dist<=100:
            score=(0 if near_dist<50 else 1 if near_dist<=100 else 2, near_dist,degree,p['id'])
            ranked.append((score,p))
    ranked.sort(key=lambda it:it[0])
    # Make real but restrained deletions, generally at most one per room.
    return [p for _,p in ranked[:1]]


def apply(dry_run=False, restore=False):
    if restore:
        if not BACKUP.is_dir():
            raise FileNotFoundError(f'No rollback data: {BACKUP}')
        count=0
        for source in sorted(BACKUP.glob('level_*.json')):
            shutil.copy2(source, LEVELS/source.name)
            count+=1
        if REPORT.exists():
            REPORT.unlink()
        print(f'RESTORED {count} original levels; previous pruning undone.')
        return []
    # Idempotence: a report records this release's accepted platform removals.
    # The heuristic can propose extra candidates on a second run; never cascade.
    if REPORT.exists():
        rows=json.loads(REPORT.read_text(encoding='utf-8'))
        for r in rows:
            data=json.loads((LEVELS/f"level_{r['level']:02}.json").read_text(encoding='utf-8'))
            kept={x['id'] for x in data.get('one_way_platforms',[])}
            if any(x['id'] in kept for x in r.get('removed',[])):
                raise RuntimeError(f"Level {r['level']} reverted partially; use --restore before reapplying")
        print('DRY-RUN: ' if dry_run else '', 'ALREADY APPLIED: 0 further removals; previous audit is preserved.', sep='')
        return rows
    rows=[]
    for level in range(1,81):
        path=LEVELS/f'level_{level:02}.json'
        data=json.loads(path.read_text(encoding='utf-8'))
        old_platforms=list(data.get('one_way_platforms',[]))
        # Early tutorial rooms and finale are deliberately preserved.
        selected=analyze(data) if 25<=level<=79 else []
        ids={p['id'] for p in selected}
        if ids and not dry_run:
            BACKUP.mkdir(parents=True,exist_ok=True)
            bak=BACKUP / path.name
            if not bak.exists():
                shutil.copy2(path,bak)
            data['one_way_platforms']=[p for p in old_platforms if p['id'] not in ids]
            path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
        rows.append(dict(level=level,original_count=len(old_platforms),removed=[dict(id=p['id'],x=p['x'],y=p['y'],w=p['w']) for p in selected],remaining=len(old_platforms)-len(ids)))
    if not dry_run:
        REPORT.parent.mkdir(parents=True,exist_ok=True)
        REPORT.write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')
    changed=[r for r in rows if r['removed']]
    print(('DRY-RUN' if dry_run else 'APPLIED'), 'platform removals:',sum(len(r['removed']) for r in rows),'across',len(changed),'levels')
    for row in changed:
        print(f"  Level {row['level']:02}: "+', '.join(p['id'] for p in row['removed']))
    return rows


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dry-run',action='store_true')
    parser.add_argument('--restore',action='store_true',help='Restore backed-up level JSONs')
    args=parser.parse_args()
    apply(args.dry_run,args.restore)
