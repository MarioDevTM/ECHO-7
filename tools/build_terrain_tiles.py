"""Compile opaque, seamless-sized terrain texture primitives (Pillow offline).

The original environment sheet is preserved. These crops avoid letterbox gaps
when an odd-aspect-ratio asset is fitted into the game's 40x40 collision grid.
"""
from pathlib import Path
from PIL import Image
BASE=Path(__file__).resolve().parents[1]/'data/art/environment'
for name,base_color in [('wall_tile_steel',(40,56,73)),('wall_tile_panel',(30,47,70))]:
 im=Image.open(BASE/f'{name}.png').convert('RGBA')
 w,h=im.size;side=min(w,h)
 im=im.crop(((w-side)//2,(h-side)//2,(w+side)//2,(h+side)//2))
 im=im.resize((40,40),Image.Resampling.NEAREST)
 bg=Image.new('RGBA',(40,40),(*base_color,255))
 # Convert input alpha just once, preserving bevels and subtle shaded pixels;
 # opaque output eliminates the accidental one-pixel see-through tile seams.
 bg.alpha_composite(im)
 bg.convert('RGB').save(BASE/f'terrain_{name}.png',optimize=True)
 print(f'Wrote terrain_{name}.png 40x40')

from PIL import ImageDraw
for stem in ('terrain_wall_tile_steel','terrain_wall_tile_panel'):
 base=Image.open(BASE/f'{stem}.png').convert('RGBA')
 for version in (1,2):
  pic=base.copy()
  d=ImageDraw.Draw(pic)
  if version==1:
   # A subdued maintenance panel with little physical greeble and no hint of
   # collision, hazards, pickups or controls.
   d.rectangle((9,11,30,29),outline=(20,29,43,255),width=2)
   d.line((13,16,26,16),fill=(79,105,123,255),width=1)
   d.line((13,20,26,20),fill=(28,45,61,255),width=2)
   d.line((13,24,26,24),fill=(72,93,108,255),width=1)
  else:
   # Reinforcing rivets and a subtle double steel seam, not a glowing console.
   d.line((8,7,8,33),fill=(26,39,52,255),width=2)
   d.line((30,7,30,33),fill=(96,115,137,255),width=1)
   for x,y in ((5,5),(34,5),(5,34),(34,34)):
    d.rectangle((x-1,y-1,x+1,y+1),fill=(99,123,139,255))
  pic.convert('RGB').save(BASE/f'{stem}_v{version}.png',optimize=True)
  print('Wrote',f'{stem}_v{version}.png')
