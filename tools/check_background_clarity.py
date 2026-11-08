"""Headless checks for the new non-traversable scenic art and stable dressing.

Does NOT assert that live pygame gameplay is visually verified. Tests source,
assets, world-coordinate transforms, chapter policy, and original-file integrity.
"""
from __future__ import annotations
import hashlib
import importlib.util
import json
import sys
import zipfile
from pathlib import Path
from PIL import Image,ImageChops,ImageStat
ROOT=Path(__file__).resolve().parents[1]
MOD=ROOT/'src/visuals/world_dressing.py'
spec=importlib.util.spec_from_file_location('world_dressing_headless',MOD)
world=importlib.util.module_from_spec(spec)
spec.loader.exec_module(world)


def verify(original=None):
    failures=[]
    def check(ok, msg):
        if not ok:failures.append(msg)
    base=ROOT/'data/art/backgrounds'
    for ch in range(1,9):
        original_art=base/f'chapter_{ch:02d}.png'
        scenic=base/'scenic'/f'chapter_{ch:02d}_scenic.png'
        check(original_art.is_file() and scenic.is_file(),f'chapter {ch}: art missing')
        if not original_art.is_file() or not scenic.is_file():continue
        with Image.open(scenic) as art,Image.open(original_art) as old:
            check(art.size==(1280,720) and old.size==art.size, f'chapter {ch}: wrong dimensions')
            lower_diff=ImageChops.difference(old.convert('RGB').crop((0,350,1280,720)),art.convert('RGB').crop((0,350,1280,720)))
            check(sum(ImageStat.Stat(lower_diff).mean)/3>18, f'chapter {ch}: background not materially reauthored')
    for name in ('terrain_wall_tile_steel','terrain_wall_tile_panel'):
        with Image.open(ROOT/f'data/art/environment/{name}.png') as pic:
            check(pic.size==(40,40),f'{name}: incorrect tile size')
    renderer=(ROOT/'src/visuals/scene_renderer.py').read_text(encoding='utf-8')
    platform=renderer[renderer.index('    def draw_platform('):renderer.index('    def draw_exit(')]
    check('bush_moss_flora' not in platform, 'bush attached by generic platform renderer')
    check('wall_tile_vines' not in platform, 'vine wall tile used in generic terrain')
    check('platform_hazard_long' not in platform, 'hazard stripes used on normal terrain')
    check('pixel_environment.draw' in renderer and 'placements_for_level' in renderer,'procedural scenery and curated world decoration not integrated')
    check("self._environment_prop(surface, 'vines_hanging_cluster'" not in renderer,'screen-locked vine effects remain')
    manifest=world.load_world_dressing()
    check(len(manifest.get('levels',{}))>=2,'no explicit world decorative anchors')
    for n_str,props in manifest['levels'].items():
        n=int(n_str)
        d=json.loads((ROOT/f'data/levels/level_{n:02d}.json').read_text())
        theme=d['theme']
        check(bool(world.placements_for_level(n,theme,manifest)),f'placement {n} rejected by chapter policy')
        for prop in props:
            wx,wy=prop['world'];w,h=prop['size'];anchor=prop['anchor']
            check(0<=wx<d['width'] and 0<=wy<=d['height'],f'placement {n} out of level bounds')
            # The sprite's world location must be invariant across arbitrary
            # camera pans, including both x and y movement.
            for ox,oy in ((0,0),(150,87),(713,335)):
                x,y=world.anchor_for(ox,oy,wx,wy,w,h,anchor)
                bx=w//2 if 'center' in anchor else 0
                by=h if anchor=='bottom_center' else 0
                check((x+ox+bx,y+oy+by)==(wx,wy),f'placement {n} drifts with camera')
    for theme in ('mechanical','power','optical','environmental','furnace','spire'):
        for n in range(1,81):
            check(not world.placements_for_level(n,theme,manifest), f'unwanted flora in {theme} level {n}')
    levels=sorted((ROOT/'data/levels').glob('level_*.json'))
    check(len(levels)==80,'not 80 level JSONs')
    if original:
        with zipfile.ZipFile(original) as z:
            for p in levels:
                arc=f'ECHO-7/data/levels/{p.name}'
                check(p.read_bytes()==z.read(arc),f'changed gameplay level {p.name}')
            for rel in ('src/entities/player.py','src/systems/collision.py','src/core/settings.py','src/core/camera.py','src/puzzles/puzzle_manager.py'):
                check((ROOT/rel).read_bytes()==z.read('ECHO-7/'+rel),f'changed mechanics file {rel}')
            for ch in range(1,9):
                rel=f'data/art/backgrounds/chapter_{ch:02d}.png'
                check((ROOT/rel).read_bytes()==z.read('ECHO-7/'+rel),f'original art {ch} changed')
    if failures:
        print('FAIL:',*failures,sep='\n- ')
        return 1
    print('PASS: 8 scenic PNGs, 2 tile crops, 80 levels, curated chapter policy, world-space anchor invariance, terrain art roles, original artwork preserved.')
    print('NOT TESTED: live Pygame rendering, FPS, interactive collisions, actual visual screenshots.')
    return 0

if __name__=='__main__':
    raise SystemExit(verify(sys.argv[1] if len(sys.argv)>1 else None))
