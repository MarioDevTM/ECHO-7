"""Curate deterministic, world-anchored environmental dressing.

This offline tool examines the existing authored static tiles, but only selects
small decorative anchors for a shortlist of levels where the chapter setting
actually justifies vegetation. Nothing is added to level JSON or physics.
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
LEVELS=ROOT/'data/levels'
OUTPUT=ROOT/'data/art/environment/world_dressing.json'
# Chapter 1: overgrown lab; Chapter 8: regained natural world. No plants in
# furnace, industrial, optical, electrical or collapsing structure chapters.
SELECTED = {
    1:('vine',0),3:('vine',0),5:('vine',0),7:('vine',0),9:('vine',0),
    71:('bush',0),73:('vine',0),75:('bush',0),78:('vine',0),80:('bush',0),
}


def near_critical(x,y,data,radius=130):
    objects = [dict(x=data['spawn'][0],y=data['spawn'][1]),dict(x=data['exit'][0],y=data['exit'][1])]
    for label in ('crates','switches','plates','generators','valves','doors','mirrors','checkpoints','ladders','moving_platforms','conveyors'):
        objects += data.get(label,[])
    return any(abs(float(o['x'])-x) < radius and abs(float(o['y'])-y) < 100 for o in objects)


def build():
    placement={}
    for level_num,(kind,_) in SELECTED.items():
        data=json.loads((LEVELS/f'level_{level_num:02d}.json').read_text())
        world_tiles=[(x,y,w,h) for x,y,w,h in data['tiles'] if w>=160 and 12<=h<=175 and y>=200 and x>0 and y>0]
        # Stay away from the 40px world boundary. Prefer architectural undersides
        # for vines and solid wide floor panels for very small bushes.
        if kind=='vine':
            candidates=[(x+w//2,y+h+2,w) for x,y,w,h in world_tiles if h<=36]
            name='vines_hanging_cluster';size=[33,35]
        else:
            candidates=[(x+w//2,y,w) for x,y,w,h in world_tiles if h>=60]
            name='bush_moss_flora';size=[40,17]
        if not candidates:
            continue
        # No global loop over platforms: one hand-picked candidate is authored
        # as a fixed world coordinate, stored in the JSON.
        ordered=sorted(candidates,key=lambda t:(abs(t[0]-data['width']*.62),t[1]))
        chosen=None
        for x,y,w in ordered:
            if not near_critical(x,y,data):
                chosen=(x,y);break
        if chosen is None:continue
        x,y=chosen
        placement[str(level_num)]=[dict(sprite=name,world=[int(x),int(y)],size=size,anchor='top_center' if kind=='vine' else 'bottom_center',layer='back_terrain',role='decorative')]
    OUTPUT.write_text(json.dumps({'coordinate_system':'world_pixels','chapter_policy':{'awakening':['vines_hanging_cluster','bush_moss_flora'],'surface':['vines_hanging_cluster','bush_moss_flora']},'levels':placement},indent=2)+'\n')
    print('World-anchored decorative placements:', {k:len(v) for k,v in placement.items()})

if __name__=='__main__':build()
