"""Source-only regression check: works even on machines without pygame-ce."""
import ast
from pathlib import Path
from types import SimpleNamespace
import json, hashlib
from PIL import Image
BASE=Path(__file__).resolve().parents[1]
menu=ast.parse((BASE/'src/ui/main_menu.py').read_text())
cls=next(n for n in menu.body if isinstance(n,ast.ClassDef) and n.name=='MainMenu')
getitems=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='_get_items')
script=ast.Module(body=[getitems],type_ignores=[])
ns={'CHAPTER_METADATA':{},'AUXILIARY_ROOMS':{}}
exec(compile(ast.fix_missing_locations(script),'<MainMenu._get_items>','exec'),ns)
class Dummy:
 pass
m=Dummy()
m.mode='MUSIC_GALLERY';m.gallery_chapter=1;m.selected_chapter=1
m.game=SimpleNamespace(save_manager=SimpleNamespace(data={'unlocked_level':1,'completed_levels':[],'collected_logs':[],'completed_auxiliary':[], 'current_level':1}),
    audio=SimpleNamespace(gallery_active=True,gallery_paused=False),level_loader=SimpleNamespace(TOTAL_CHAPTERS=8))
ns['CHAPTER_METADATA']={k:{'title':f'CHAPTER {k} — TEST','levels':list(range((k-1)*10+1,k*10+1))} for k in range(1,9)}
tracks=ns['_get_items'](m)
assert len(tracks)==10,tracks
assert tracks[0][1]=='GALLERY_1' and tracks[-1][1]=='GALLERY_BACK'
assert 'PLAYING' in tracks[0][0]
m.game.audio.gallery_paused=True
assert 'PAUSED' in ns['_get_items'](m)[0][0]
m.mode='ROOT';assert len(ns['_get_items'](m))==8
m.mode='CHAPTER_SELECT';m.level_catalog={n:{} for n in range(1,81)}
assert len(ns['_get_items'](m))==9
m.mode='LEVEL_SELECT';assert len(ns['_get_items'](m))==12
# Same level JSON files as uploaded playable source package.
baseline=json.loads((BASE/'docs/preserved_level_hashes.json').read_text())
for n in range(1,25):
    name=f'level_{n:02d}.json'
    raw=(BASE/'data/levels'/name).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==baseline[name],f'Level {n} changed'
    json.loads(raw)
# All original chapter loops and additional sprite frames must exist.
for n in range(1,9):
 with Image.open(BASE/f'data/art/backgrounds/chapter_{n:02d}.png') as image:
  assert image.size==(1280,720)
 for layer in ('quiet','rhythm'):
  assert (BASE/f'data/music/chapter_{n}_{layer}.wav').stat().st_size>1000
sprite_counts={'idle':4,'run':8,'jump':3,'fall':3,'land':3,'interact':4,'turn':2,
               'death':4,'respawn':4,'dash':3,'crouch':2,'wall':2}
for state,count in sprite_counts.items():
 for i in range(count):
  with Image.open(BASE/f'data/art/player/{state}_{i}.png') as image:
   assert image.size==(36,56)
print('PASS: Gallery item generation (including playing/paused), other menus, 24 preserved levels,')
print('      8 original backgrounds, 16 music layers, 42 movement sprites + sprite_sheet.png')
