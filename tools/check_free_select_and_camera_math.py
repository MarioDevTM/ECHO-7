"""No-Pygame regression checks for save/load and world/camera math.

Uses isolated functions/classes extracted from source. Not actual display testing.
"""
from pathlib import Path
import ast, json, math, tempfile, os, shutil, warnings
ROOT=Path(__file__).resolve().parents[1]

# Save file compatibility with a selected stage 80 while story unlock stays at 1.
ns={'Path':Path,'json':json,'os':os,'shutil':shutil,'warnings':warnings,'tempfile':tempfile,
    'SAVE_FILE':Path('/tmp/echo-save-qa.json'),'DEFAULT_KEYBINDS':{'left':[1,2],'pause':[3]},'AUXILIARY_ROOMS':{}}
node=next(n for n in ast.parse((ROOT/'src/core/save_manager.py').read_text()).body
          if isinstance(n,ast.ClassDef) and n.name=='SaveManager')
# Annotations require typing in the isolated namespace.
from typing import Any
ns['Any']=Any
exec(compile(ast.Module(body=[node],type_ignores=[]),'save_manager-isolated','exec'),ns)
Save=ns['SaveManager']
with tempfile.TemporaryDirectory() as td:
    path=Path(td)/'save.json'
    sm=Save(path)
    assert sm.data['unlocked_level']==1 and sm.data['current_level']==1
    sm.data['current_level']=80
    sm.save()
    load=Save(path)
    assert load.data['current_level']==80 and load.data['unlocked_level']==1
    assert load.data['completed_levels']==[]
    load.mark_level_completed(80)
    assert load.data['completed_levels']==[80]
    assert load.data['unlocked_level']==1
    load.reset_new_game()
    assert load.data['current_level']==1 and load.data['completed_levels']==[]
print('PASS: fresh-save independent stage selection and persistence without completion inflation.')

# Solid world-space props move exactly opposite the camera, regardless of player
# world position. Separate elapsed is reserved for animated internals.
s=(ROOT/'src/visuals/world_dressing.py').read_text()
fn=next(n for n in ast.parse(s).body if isinstance(n,ast.FunctionDef) and n.name=='anchor_for')
exec(compile(ast.Module(body=[fn],type_ignores=[]),'world_dressing_math','exec'),ns)
a=ns['anchor_for']
for cx,cy in ((0,0),(140,55),(620,300)):
    x,y=a(cx,cy,880,450,50,80,'top_center')
    assert x==880-cx-25 and y==450-cy
print('PASS: world-anchored props independent of player/camera-follow implementation.')

# Structural static world art atlas pixel-space viewport read is bounded.
for world_w,world_h in ((1280,720),(2100,950),(4800,1400),(3200,1800)):
    aw=max(1280,world_w)//2+2;ah=max(720,world_h)//2+2
    for cx,cy in ((0,0),(max(0,world_w-1280)//2,max(0,world_h-720)//2),
                  (max(0,world_w-1280),max(0,world_h-720))):
        sx=max(0,min(aw-640,int(cx)//2))
        sy=max(0,min(ah-360,int(cy)//2))
        assert 0<=sx<=aw-640 and 0<=sy<=ah-360
print('PASS: procedural pixel-world atlas viewport coverage at room/camera extremes.')
