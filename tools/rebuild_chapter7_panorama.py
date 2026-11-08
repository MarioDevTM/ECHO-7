"""Remove the flat magenta placeholder area from the old Chapter 7 panorama.

The protected user-approved chapter_07.png is not modified. The 1920x960
renderer plate is a deterministic same-aspect expansion of that source.
"""
from pathlib import Path
from PIL import Image, ImageOps
ROOT=Path(__file__).resolve().parents[1]
src=ROOT/'data/art/backgrounds/chapter_07.png'
dst=ROOT/'data/art/backgrounds/scenic/chapter_07_pano.png'
image=Image.open(src).convert('RGB')
assert image.size==(1280,720)
# Uniform 4/3 upscale to 960 high, with only ~107px outpaint on each side.
full_w=1920; target_h=960
w=round(image.width*target_h/image.height)
core=image.resize((w,target_h),Image.Resampling.LANCZOS)
left=(full_w-w)//2; right=full_w-w-left
canvas=Image.new('RGB',(full_w,target_h))
canvas.paste(core,(left,0))
canvas.paste(ImageOps.mirror(core.crop((0,0,left,target_h))),(0,0))
canvas.paste(ImageOps.mirror(core.crop((w-right,0,w,target_h))),(left+w,0))
canvas.save(dst,optimize=True)
print('Rebuilt',dst,'with full-height interior artwork; protected source unchanged')
