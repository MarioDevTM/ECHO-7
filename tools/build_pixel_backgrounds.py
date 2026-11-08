"""Create game-ready, low-resolution scene materials from approved chapter art.

This does not modify or overwrite the approved 1280x720 source images. The
output is authored once and packed with the game, never regenerated at runtime.
"""
from pathlib import Path
from PIL import Image, ImageEnhance, ImageOps

ROOT = Path(__file__).resolve().parents[1]
BG = ROOT / 'data' / 'art' / 'backgrounds'
DEST = BG / 'pixel'
DEST.mkdir(parents=True, exist_ok=True)
CHAPTERS = (1, 3, 4, 5)
# Distinct repeatable source crops deliberately avoid the main logo/lettering.
CROPS = {
    1: ((545, 775), (735, 970), (785, 995)),
    3: ((365, 630), (570, 810), (845, 1105)),
    4: ((60, 320), (955, 1180), (1035, 1255)),
    5: ((70, 335), (1025, 1255), (870, 1090)),
}

def stylize(im, size):
    im = ImageOps.fit(im.convert('RGB'), size, method=Image.Resampling.BOX)
    im = ImageEnhance.Color(im).enhance(0.86)
    im = ImageEnhance.Contrast(im).enhance(1.11)
    # No dithering: distant machinery remains clear rather than noisy.
    im = im.quantize(colors=144, method=Image.Quantize.FASTOCTREE,
                     dither=Image.Dither.NONE).convert('RGB')
    return im

for number in CHAPTERS:
    src = Image.open(BG / f'chapter_{number:02}.png').convert('RGB')
    assert src.size == (1280, 720), (number, src.size)
    stylize(src, (640, 360)).save(DEST / f'chapter_{number:02}_hero.png', optimize=True)
    for i, (left, right) in enumerate(CROPS[number]):
        patch = src.crop((left, 0, right, 720))
        stylize(patch, (160, 360)).save(DEST / f'chapter_{number:02}_module_{i}.png', optimize=True)
print('Built 4 pixel hero scenes and 12 architectural expansion modules. Source assets preserved.')
