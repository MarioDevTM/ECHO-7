"""Generate comparison frames with a Pillow pygame stand-in (NOT runtime gameplay)."""
import importlib.util
import sys,json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import tools.pillow_render_adapter as shim  # installs fake pygame before importing game modules
from src.core.settings import VIRTUAL_WIDTH,VIRTUAL_HEIGHT

def load_environment(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec); sys.modules[name]=mod
    spec.loader.exec_module(mod)
    return mod.PixelEnvironment()

old=load_environment(ROOT/'docs/polish_qa/pixel_environment_before.py','echo7_before')
new=load_environment(ROOT/'src/visuals/pixel_environment.py','echo7_after')
# If baseline is installed elsewhere, use local baseline path copied from docs.
font=ImageFont.load_default()
canvas=Image.new('RGB',(1204,8*264+45),(10,17,29))
draw=ImageDraw.Draw(canvas)
draw.text((12,12),'ECHO-7 / Procedural art comparison / Pillow approximation, not gameplay',(218,235,245),font=font)
for ch in range(1,9):
    n=(ch-1)*10+5
    d=json.loads((ROOT/f'data/levels/level_{n:02d}.json').read_text())
    cam_x=max(0,min(d['width']-1280,d['spawn'][0]-320))
    cam_y=max(0,min(d['height']-720,d['spawn'][1]-320))
    imgs=[]
    for env in (old,new):
        env.set_focus(*d['spawn'],n)
        env.set_world_tiles([shim.pg.Rect(*t) for t in d['tiles']])
        dest=shim.pg.Surface((1280,720))
        env.draw(dest,ch,cam_x,cam_y,1.0,d['width'],d['height'],False,False)
        imgs.append(dest.im.resize((586,238),Image.Resampling.NEAREST))
    y=43+(ch-1)*264
    for i,img in enumerate(imgs):
        x=10+i*597
        canvas.paste(img,(x,y+19))
        draw.rectangle((x,y+19,x+585,y+256),outline=(63,117,148))
        draw.text((x+3,y),f'Chapter {ch} / Level {n} / {"before" if i==0 else "polished"}',font=font,fill=(190,222,242))
out=ROOT/'docs/polish_qa/BACKGROUND_COMPARISON_OFFLINE.jpg'
out.parent.mkdir(parents=True,exist_ok=True)
canvas.save(out,quality=89)
print(out)
