"""Offline art-material preview (NOT an in-engine Pygame screenshot)."""
from PIL import Image, ImageDraw
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
OUT=R/'docs'/'REPAIRED_PIXEL_BACKGROUNDS_STATIC_PREVIEW.jpg'
OUT.parent.mkdir(exist_ok=True)
scene=Image.new('RGB',(1280,748),'#111923')
draw=ImageDraw.Draw(scene)
for j,(n,ch) in enumerate(((1,1),(25,3),(31,4),(41,5))):
 data=json.loads((R/f'data/levels/level_{n:02}.json').read_text())
 w,h=max(1280,data['width']),max(720,data['height'])
 aw,ah=(w+1)//2+2,(h+1)//2+2
 base=max(0,ah-365)
 atlas=Image.new('RGB',(aw,ah),['#07111e','#05101f','#0f0c1b','#05121a'][j])
 material=R/'data/art/backgrounds/pixel'
 for i,x in enumerate(range(0,aw,160)):
  mod=Image.open(material/f'chapter_{ch:02}_module_{(i*5+ch*3+i//4)%3}.png')
  atlas.paste(mod,(x,base))
 hero=Image.open(material/f'chapter_{ch:02}_hero.png')
 hx=max(0,min(aw-640,data['spawn'][0]//2-320))
 atlas.paste(hero,(hx,base))
 cx=max(0,min(w-1280,int(data['spawn'][0]-640)))//2
 cy=max(0,min(h-720,int(data['spawn'][1]-389)))//2
 patch=atlas.crop((cx,cy,cx+640,cy+360))
 col=j%2;row=j//2
 scene.paste(patch,(col*640,row*374+27))
 draw.text((col*640+12,row*374+7),f'CHAPTER {ch:02} - LEVEL {n:02} // STATIC SCENE MATERIAL',fill='#c7e6ed')
scene.save(OUT,quality=96)
print(OUT)
