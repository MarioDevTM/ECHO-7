"""Recreate ECHO-7 application icon from the existing playable character's head.

Pillow is only needed when regenerating the icon, not for game startup.
"""
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/art/ui';OUT.mkdir(exist_ok=True,parents=True)
head=Image.open(ROOT/'data/art/player/idle_0.png').convert('RGBA').crop((0,1,36,35))
base=Image.new('RGBA',(64,64),(7,15,29,255));dr=ImageDraw.Draw(base)
dr.rectangle((2,2,61,61),outline=(60,123,157,255),width=2)
dr.rectangle((6,6,57,57),fill=(12,29,48,255))
for x in (10,18,42,50):
    dr.rectangle((x,10,x+1,16),fill=(42,93,127,255))
    dr.rectangle((x,48,x+1,54),fill=(42,93,127,255))
dr.line((5,4,24,4),fill=(89,217,232,255),width=2)
dr.line((40,59,59,59),fill=(89,217,232,255),width=2)
base.alpha_composite(head.resize((50,47),Image.Resampling.NEAREST),(7,9))
for size in (32,48,64,128,256):
    base.resize((size,size),Image.Resampling.NEAREST).save(OUT/f'echo7_head_{size}.png')
base.resize((256,256),Image.Resampling.NEAREST).save(OUT/'echo7_icon.png')
base.resize((256,256),Image.Resampling.NEAREST).save(OUT/'echo7_icon.ico',format='ICO',
    sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])
print('Generated player-head icon and sizes.')
