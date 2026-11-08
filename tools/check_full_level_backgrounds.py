"""Pygame-independent proof of chapter panorama coverage at camera endpoints.

Does NOT establish running-game screenshot quality or smoothness on actual SDL.
"""
from pathlib import Path
import json
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
VPW, VPH=1280, 720

def offset(camera, world, viewport, image):
    if world <= viewport:
        return 0
    t=max(0,min(1,camera/max(1,world-viewport)))
    return -round(t*max(0,image-viewport))

def run():
    for chapter in range(1,9):
        path=ROOT / f'data/art/backgrounds/scenic/chapter_{chapter:02}_pano.png'
        with Image.open(path) as im:
            pw,ph=im.size
            assert pw>=VPW and ph>=VPH,(chapter,im.size)
        for n in range((chapter-1)*10+1,chapter*10+1):
            data=json.loads((ROOT / f'data/levels/level_{n:02}.json').read_text())
            w,h=data['width'],data['height']
            for cx in (0,max(0,(w-VPW)//2),max(0,w-VPW)):
                for cy in (0,max(0,(h-VPH)//2),max(0,h-VPH)):
                    bx=offset(cx,w,VPW,pw)
                    by=offset(cy,h,VPH,ph)
                    assert bx<=0 and by<=0 and bx+pw>=VPW and by+ph>=VPH, (n,cx,cy,bx,by)
    print('PASS: 8 panorama dimensions and 80 levels x 9 camera viewpoints cover the complete viewport.')
    print('NOTE: mathematical source/buffer coverage only; not a real game capture.')

if __name__=='__main__':run()
