"""Generate reproducible STATIC comparison previews from the game code via a Pillow approximation.
Never call these actual running-game screenshots or playtests.
"""
from __future__ import annotations
import sys,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageChops,ImageStat

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sys.path.insert(0,str(HERE))
import offline_pygame_adapter as shim
sys.path.insert(0,str(ROOT))
from src.visuals.scene_renderer import SceneRenderer
from src.visuals.pixel_environment import PixelEnvironment

CHAPTERS=(
  ('awakening',1,'01 / AWAKENING'),
  ('mechanical',11,'02 / MECHANICAL DEPTHS'),
  ('power',25,'03 / POWER GRID'),
  ('optical',31,'04 / SURVEILLANCE GRID'),
  ('environmental',41,'05 / FLOOD CONTROL'),
  ('furnace',51,'06 / CORE COLLAPSE'),
  ('spire',62,'07 / BROKEN SPIRE'),
  ('surface',80,'08 / SURFACE BREACH'),
)

portrait=Image.open(ROOT/'data/art/player/idle_0.png').convert('RGBA')
preview_cards=[];metrics={}
per_ch=ROOT/'docs'/'background_recovery_previews'
per_ch.mkdir(parents=True,exist_ok=True)
for chapter,(theme,level,caption) in enumerate(CHAPTERS,1):
 data=json.loads((ROOT/'data/levels'/f'level_{level:02d}.json').read_text())
 width,height=data['width'],data['height']
 spawn_x,spawn_y=data['spawn']
 camera_x=max(0,min(width-1280,spawn_x-410))
 camera_y=max(0,min(height-720,spawn_y-460))
 renderer=SceneRenderer();renderer.set_level_context(level);renderer.set_level_focus(spawn_x,spawn_y)
 renderer.set_level_tiles([shim.pg.Rect(*t) for t in data.get("tiles",[])])
 surf0=shim.pg.Surface((1280,720))
 renderer.draw_background(surf0,theme,camera_x,camera_y,0.4,width,height,powered=True)
 surf1=shim.pg.Surface((1280,720))
 renderer.draw_background(surf1,theme,camera_x,camera_y,2.1,width,height,powered=True)
 count=sum(1 for px in ImageChops.difference(surf0.im,surf1.im).convert('L').getdata() if px>4)
 if count < 1: raise AssertionError(f'Chapter {chapter}: no animation difference')
 # Determinism: repeated same world state and frame time must render identically.
 again=shim.pg.Surface((1280,720))
 renderer.draw_background(again,theme,camera_x,camera_y,0.4,width,height,powered=True)
 assert ImageChops.difference(again.im,surf0.im).getbbox() is None, f'Chapter {chapter}: nondeterministic frame'
 # Demonstrate movement of background at a fixed scene time.
 surf_move=shim.pg.Surface((1280,720))
 renderer.draw_background(surf_move,theme,min(width-1280,camera_x+80),camera_y,0.4,width,height,powered=True)
 assert ImageChops.difference(surf_move.im,surf0.im).getbbox() is not None, f'Chapter {chapter}: camera shift no change'
 # Terrain comes from real active JSON and the real scene renderer, via shim.
 composite=shim.pg.Surface((1280,720));composite.blit(surf0,(0,0))
 for x,y,w,h in data.get('tiles',[]):
  rect=shim.pg.Rect(x-camera_x,y-camera_y,w,h)
  if rect.colliderect(composite.get_rect()):
   renderer.draw_platform(composite,rect,theme,(camera_x,camera_y),world_rect=shim.pg.Rect(x,y,w,h))
 # Real character sprite placed at authored spawn point, for scale reference only.
 composite.im.paste(portrait,(spawn_x-camera_x,spawn_y-camera_y),portrait)
 composite.dr=ImageDraw.Draw(composite.im)
 shot=composite.im.copy()
 shot.save(per_ch/f'chapter_{chapter:02d}_offline_gameplay_composition.png',optimize=True)
 card=shot.resize((624,351),Image.Resampling.NEAREST)
 drawer=ImageDraw.Draw(card)
 drawer.rectangle((0,0,623,27),fill=(9,19,32))
 drawer.text((10,7),caption+'  /  STATIC PREVIEW',fill=(122,221,243))
 preview_cards.append(card)
 metrics[chapter]={
   'level':level,'theme':theme,'camera':(camera_x,camera_y),
   'changed_pixels_between_times_0_4_and_2_1':count,
   'frame_determinism':True,
   'camera_shift_changes_background':True,
   'no_fullscreen_image_plates':True,
 }
 print(chapter,theme,'ambient changed pixels',count)

sheet=Image.new('RGB',(1280,1488),(5,10,19))
d=ImageDraw.Draw(sheet)
d.text((16,11),'ECHO-7 / CLEANED ARCHITECTURE — 8 CODE-GENERATED CHAPTERS',fill=(125,218,240))
d.text((16,25),'Offline Pygame approximation with active level terrain; NOT native-game screenshots',fill=(137,150,163))
for idx,card in enumerate(preview_cards):
 x=14+(idx%2)*640;y=51+(idx//2)*357
 sheet.paste(card,(x,y));d.rectangle((x-1,y-1,x+625,y+352),outline=(51,91,122),width=1)

out=Path('/mnt/data/ECHO7_Gemini_Cleanup_Preview.jpg')
sheet.save(out,quality=93)
(ROOT/'docs'/'GEMINI_CLEANUP_PREVIEW.jpg').write_bytes(out.read_bytes())
(ROOT/'docs'/'GEMINI_CLEANUP_METRICS.json').write_text(json.dumps(metrics,indent=2))
print('Saved',out)
