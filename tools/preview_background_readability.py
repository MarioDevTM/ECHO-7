"""PIL-only static composition previews; NOT screenshots from running Pygame.

For art review only. Shows approximated collision floor and player to illustrate
visual hierarchy against the original/scenic backdrops. The actual renderer can
look different, and this tool must not be cited as runtime verification.
"""
from pathlib import Path
import json
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
BACK=ROOT/'data/art/backgrounds'
ART=ROOT/'data/art/environment'
LEVELS=ROOT/'data/levels'
OUT=ROOT/'docs/background_clarity_static_preview.png'

def draw_static(level_num,new):
    data=json.loads((LEVELS/f'level_{level_num:02d}.json').read_text())
    ch=data['chapter'];path=(BACK/'scenic'/f'chapter_{ch:02d}_scenic.png') if new else (BACK/f'chapter_{ch:02d}.png')
    out=Image.open(path).convert('RGBA');d=ImageDraw.Draw(out,'RGBA')
    ox=max(0,int(data['spawn'][0]-280));oy=max(0,int(data['spawn'][1]-360))
    stone=Image.open(ART/'terrain_wall_tile_steel.png').convert('RGBA')
    top=Image.open(ART/'platform_solid_long.png').convert('RGBA')
    for tx,ty,tw,th in data['tiles']:
      x=tx-ox;y=ty-oy
      if x>1280 or x+tw<0 or y>720 or y+th<0:continue
      d.rectangle((x,y,x+tw-1,y+th-1),fill=(40,58,74,255))
      for xx in range((x//40)*40,x+tw,40):
       for yy in range((y//40)*40,y+th,40):
        if x<=xx<x+tw and y<=yy<y+th:
         out.alpha_composite(stone,(xx,yy)) if xx>=0 and yy>=0 and xx+40<=1280 and yy+40<=720 else None
      d.rectangle((x,y,x+tw-1,y+3),fill=(66,166,185,255))
      d.rectangle((x,y,x+tw-1,y+th-1),outline=(6,15,30,255),width=2)
    # Explicitly *not* a real gameplay screenshot: simulated sprite placement.
    robot=Image.open(ROOT/'data/art/player/idle_0.png').convert('RGBA')
    px=int(data['spawn'][0]-ox);py=int(data['spawn'][1]-oy)
    if px>=0 and py>=0 and px+36<=1280 and py+56<=720:out.alpha_composite(robot,(px,py))
    out=out.convert('RGB').resize((640,360),Image.Resampling.NEAREST)
    return out

def main():
    levels=(1,21,51,71,80)
    whole=Image.new('RGB',(1320,len(levels)*400),(14,21,34))
    d=ImageDraw.Draw(whole)
    for i,n in enumerate(levels):
       y=i*400
       whole.paste(draw_static(n,False),(0,y+25))
       whole.paste(draw_static(n,True),(670,y+25))
       d.text((10,y+5),f'LEVEL {n:02d} / ORIGINAL BACKGROUND',fill=(219,227,242))
       d.text((680,y+5),f'LEVEL {n:02d} / SCENIC BACKGROUND',fill=(219,227,242))
    d.text((15,whole.height-12),'STATIC ART COMPOSITION PREVIEW - NOT A REAL PYGAME SCREENSHOT',fill=(253,179,96))
    whole.save(OUT,optimize=True)
    print('Wrote',OUT)
if __name__=='__main__': main()
