"""Rebuild scenic, deliberately non-traversable 2D chapter backdrops and full-level panoramas.

Generates both:
- data/art/backgrounds/scenic/chapter_XX_scenic.png (1280x720 viewport plate)
- data/art/backgrounds/scenic/chapter_XX_pano.png (1920x960 full-level scrolling panorama)
"""
from __future__ import annotations
import math
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'data/art/backgrounds'
DEST = SRC / 'scenic'
DEST.mkdir(exist_ok=True)
W, H = 1280, 720
PW, PH = 1920, 960

DATA = {
    1: {'base': (9, 25, 38), 'fog': (33, 79, 91), 'light': (60, 195, 220), 'accent': (245, 185, 70), 'start': 145, 'finish': 260, 'kind': 'awakening'},
    2: {'base': (28, 17, 22), 'fog': (84, 40, 28), 'light': (238, 118, 42), 'accent': (255, 180, 75), 'start': 135, 'finish': 250, 'kind': 'mechanical'},
    3: {'base': (10, 20, 44), 'fog': (38, 52, 102), 'light': (68, 182, 248), 'accent': (120, 225, 255), 'start': 115, 'finish': 255, 'kind': 'power'},
    4: {'base': (18, 14, 34), 'fog': (58, 34, 88), 'light': (198, 78, 238), 'accent': (255, 65, 95), 'start': 110, 'finish': 235, 'kind': 'surveillance'},
    5: {'base': (7, 30, 38), 'fog': (26, 82, 95), 'light': (54, 210, 225), 'accent': (255, 170, 60), 'start': 125, 'finish': 260, 'kind': 'flood'},
    6: {'base': (28, 13, 20), 'fog': (96, 38, 26), 'light': (255, 122, 38), 'accent': (255, 68, 52), 'start': 135, 'finish': 265, 'kind': 'core'},
    7: {'base': (24, 16, 38), 'fog': (98, 46, 82), 'light': (224, 82, 122), 'accent': (255, 165, 90), 'start': 160, 'finish': 310, 'kind': 'spire'},
    8: {'base': (11, 24, 46), 'fog': (34, 64, 102), 'light': (82, 208, 248), 'accent': (245, 78, 92), 'start': 220, 'finish': 380, 'kind': 'surface'},
}


def interp(a, b, t):
    return tuple(int(x * (1 - t) + y * t) for x, y in zip(a, b))


def rgba(c, a):
    return (c[0], c[1], c[2], int(a))


def poly(draw, xy, fill, outline=None, width=1):
    draw.polygon(xy, fill=fill)
    if outline:
        draw.line(xy + [xy[0]], fill=outline, width=width, joint='curve')


def draw_echo7_stencil(d, x, y, color, alpha=165):
    """Draws the crisp pixel-art ECHO-7 wall branding sign for Chapter 1."""
    c = rgba(color, alpha)
    # E
    d.rectangle((x, y, x + 6, y + 36), fill=c)
    d.rectangle((x, y, x + 22, y + 6), fill=c)
    d.rectangle((x, y + 15, x + 18, y + 21), fill=c)
    d.rectangle((x, y + 30, x + 22, y + 36), fill=c)
    # C
    cx = x + 30
    d.rectangle((cx, y, cx + 6, y + 36), fill=c)
    d.rectangle((cx, y, cx + 22, y + 6), fill=c)
    d.rectangle((cx, y + 30, cx + 22, y + 36), fill=c)
    # H
    hx = x + 60
    d.rectangle((hx, y, hx + 6, y + 36), fill=c)
    d.rectangle((hx + 16, y, hx + 22, y + 36), fill=c)
    d.rectangle((hx, y + 15, hx + 22, y + 21), fill=c)
    # O
    ox = x + 90
    d.rectangle((ox, y, ox + 22, y + 36), outline=c, width=6)
    # -
    d.rectangle((x + 120, y + 15, x + 134, y + 21), fill=c)
    # 7
    sx = x + 142
    d.rectangle((sx, y, sx + 24, y + 6), fill=c)
    d.line((sx + 21, y + 6, sx + 8, y + 36), fill=c, width=6)


def render_scene_canvas(idx: int, canvas_w: int, canvas_h: int) -> Image.Image:
    cfg = DATA[idx]
    rng = random.Random(700 + idx * 31 + canvas_w)
    src_orig = Image.open(SRC / f'chapter_{idx:02d}.png').convert('RGB')
    src = src_orig.resize((canvas_w, canvas_h), Image.Resampling.BICUBIC)

    base = Image.new('RGB', (canvas_w, canvas_h))
    draw = ImageDraw.Draw(base)
    for y in range(canvas_h):
        t = (y / canvas_h) ** 0.85
        c = interp(cfg['base'], cfg['fog'], 0.20 + 0.24 * (1 - t))
        c = interp(c, (3, 7, 15), 0.25 * t)
        draw.line((0, y, canvas_w, y), fill=c)

    blurred = ImageEnhance.Brightness(src.filter(ImageFilter.GaussianBlur(radius=36))).enhance(0.34)
    base = Image.blend(base, blurred, 0.20).convert('RGBA')
    d = ImageDraw.Draw(base, 'RGBA')
    kind = cfg['kind']
    bcol, fog, light, accent = cfg['base'], cfg['fog'], cfg['light'], cfg['accent']
    sx = canvas_w / 1280.0
    sy = canvas_h / 720.0

    if kind == 'surface':
        # Nocturnal moonlit exterior escape: starry sky, moon, mountains, ruined ECHO-7 silhouette
        for _ in range(int(95 * sx)):
            st_x = rng.randint(12, canvas_w - 12)
            st_y = rng.randint(12, int(330 * sy))
            br = rng.randint(145, 235)
            d.rectangle((st_x, st_y, st_x + 1, st_y + 1), fill=(br, br + 10, 255, 200))
        moon_x, moon_y, moon_r = int(1040 * sx), int(155 * sy), int(46 * sy)
        for rr, al in ((moon_r * 2.4, 24), (moon_r * 1.6, 48), (moon_r, 215)):
            d.ellipse((moon_x - rr, moon_y - rr, moon_x + rr, moon_y + rr), fill=rgba((185, 235, 255), al))
        for dist_idx in (0, 1, 2):
            base_y = int((455 + dist_idx * 80) * sy)
            mc = interp(fog, bcol, 0.28 + 0.22 * dist_idx)
            pts = [(0, canvas_h)]
            for x in range(0, canvas_w + 60, 44):
                h = (64 + 36 * math.sin(x / 110.0 + idx * 2 + dist_idx) + rng.randint(-16, 22)) * sy
                pts.append((x, int(base_y - h)))
            pts.append((canvas_w, canvas_h))
            poly(d, pts, rgba(mc, 240))
        # Distant ruined megastructure silhouette on left/mid horizon with red warning beacons
        fac_w = int(380 * sx)
        d.polygon([
            (int(60 * sx), canvas_h),
            (int(60 * sx), int(275 * sy)),
            (int(195 * sx), int(235 * sy)),
            (int(265 * sx), int(290 * sy)),
            (int(360 * sx), int(250 * sy)),
            (int(60 * sx) + fac_w, int(340 * sy)),
            (int(60 * sx) + fac_w, canvas_h),
        ], fill=rgba((8, 16, 30), 225))
        for bx, by in ((140, 265), (210, 255), (335, 270), (390, 315)):
            px, py = int(bx * sx), int(by * sy)
            d.ellipse((px - 8, py - 8, px + 8, py + 8), fill=rgba(accent, 55))
            d.ellipse((px - 2, py - 2, px + 2, py + 2), fill=rgba(accent, 220))
    else:
        # Interior megastructure chapters (Chapters 1 to 7)
        step_x = int(150 * sx)
        for x in range(-40, canvas_w + 120, max(90, step_x)):
            mod = (x // max(1, step_x)) % 3
            shade = interp(bcol, fog, 0.22 if mod else 0.36)
            d.rectangle((x + 8, int((135 + mod * 28) * sy), x + int(48 * sx), canvas_h), fill=rgba(shade, 165))
            d.line((x + 14, int((135 + mod * 28) * sy), x + 14, canvas_h), fill=rgba(light, 22), width=2)

        win_specs = [(120, 230, 290, 350), (490, 205, 280, 440), (855, 235, 295, 390)]
        if canvas_w > 1400:
            win_specs.append((1235, 220, 285, 410))
            win_specs.append((1585, 240, 265, 370))
        for wx0, wy0, ww0, wh0 in win_specs:
            x, y, w, h = int(wx0 * sx), int(wy0 * sy), int(ww0 * sx), int(wh0 * sy)
            border = interp(bcol, fog, 0.54)
            d.rounded_rectangle((x - 10, y - 10, x + w + 10, y + h + 10), radius=18,
                                fill=rgba((5, 11, 24), 160), outline=rgba(border, 150), width=4)
            d.rounded_rectangle((x, y, x + w, y + h), radius=12,
                                fill=rgba(interp(bcol, light, 0.14), 85), outline=rgba(light, 46), width=2)
            for frac in (0.33, 0.66):
                xx = x + int(w * frac)
                d.line((xx, y + 6, xx, y + h - 6), fill=rgba((4, 12, 22), 130), width=4)

        if kind == 'awakening':
            # Clean research corridor with prominent ECHO-7 wall branding plaque
            plaque_x, plaque_y = int(145 * sx), int(305 * sy)
            d.rounded_rectangle((plaque_x - 18, plaque_y - 16, plaque_x + 190, plaque_y + 58),
                                radius=8, fill=rgba((8, 19, 32), 215), outline=rgba(light, 95), width=2)
            draw_echo7_stencil(d, plaque_x, plaque_y, light, 185)
            if canvas_w > 1400:
                p2_x = int(1265 * sx)
                d.rounded_rectangle((p2_x - 18, plaque_y - 16, p2_x + 190, plaque_y + 58),
                                    radius=8, fill=rgba((8, 19, 32), 205), outline=rgba(light, 85), width=2)
                draw_echo7_stencil(d, p2_x, plaque_y, light, 170)

        elif kind == 'mechanical':
            # Deep background gear assemblies & vertical hydraulic columns
            gears = [(310, 495, 86), (680, 365, 142), (1070, 505, 98)]
            if canvas_w > 1400:
                gears.extend([(1420, 390, 124), (1735, 515, 92)])
            for gx, gy, gr in gears:
                cx, cy, r = int(gx * sx), int(gy * sy), int(gr * sy)
                for rr, al in ((r, 88), (int(r * 0.78), 58), (int(r * 0.45), 76)):
                    d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), outline=rgba(light, al), width=5)
                for j in range(12):
                    th = j * math.tau / 12
                    d.line((cx + math.cos(th) * (r - 16), cy + math.sin(th) * (r - 16),
                            cx + math.cos(th) * (r + 4), cy + math.sin(th) * (r + 4)),
                           fill=rgba(light, 72), width=6)

        elif kind == 'power':
            # Enclosed high-voltage capacitor banks, vertical busbars & insulator columns
            for cx0 in range(160, int(canvas_w / sx), 260):
                cx = int(cx0 * sx)
                top_y, bot_y = int(210 * sy), int(655 * sy)
                d.rounded_rectangle((cx - 22, top_y, cx + 22, bot_y), radius=10,
                                    fill=rgba((12, 26, 52), 185), outline=rgba(light, 75), width=3)
                for ring_y in range(top_y + 28, bot_y - 24, int(34 * sy)):
                    d.line((cx - 26, ring_y, cx + 26, ring_y), fill=rgba(light, 92), width=4)
                d.line((cx, top_y + 12, cx, bot_y - 12), fill=rgba(accent, 65), width=3)

        elif kind == 'surveillance':
            # Monitored high-security corridor: dark one-way observation bays & ceiling camera pods with red LEDs
            for cx0 in range(210, int(canvas_w / sx), 280):
                cx = int(cx0 * sx)
                cy = int(195 * sy)
                # Ceiling mount & camera housing
                d.line((cx, int(110 * sy), cx, cy), fill=rgba((28, 22, 48), 220), width=6)
                d.polygon([(cx - 24, cy), (cx + 28, cy + 12), (cx + 22, cy + 30), (cx - 26, cy + 18)],
                          fill=rgba((20, 16, 38), 230), outline=rgba(light, 95))
                # Active red surveillance lens + faint scanning cone
                lx, ly = cx + 24, cy + 21
                d.polygon([(lx, ly), (lx + int(95 * sx), ly + int(240 * sy)), (lx - int(45 * sx), ly + int(240 * sy))],
                          fill=rgba(accent, 18))
                d.ellipse((lx - 6, ly - 6, lx + 6, ly + 6), fill=rgba(accent, 90))
                d.ellipse((lx - 3, ly - 3, lx + 3, ly + 3), fill=rgba((255, 95, 115), 235))

        elif kind == 'flood':
            # Ruptured interior conduits, leaking pipe joints, vertical steam/water streaks (no fake pools)
            for px0 in range(220, int(canvas_w / sx), 310):
                px = int(px0 * sx)
                py = int(285 * sy)
                d.rectangle((px - 18, int(130 * sy), px + 18, canvas_h), fill=rgba((14, 42, 54), 190), outline=rgba(light, 60), width=2)
                # Ruptured flange & vertical leak mist
                d.rectangle((px - 24, py - 8, px + 24, py + 8), fill=rgba((28, 68, 82), 215), outline=rgba(accent, 110), width=2)
                for dx in (-10, -3, 4, 11):
                    d.line((px + dx, py + 10, px + dx, int(640 * sy)), fill=rgba(light, 38), width=2)

        elif kind == 'core':
            # Catastrophic core failure: unstable central reactor vessel & fractured containment rings
            cores = [640] if canvas_w <= 1400 else [580, 1380]
            for c0 in cores:
                cx = int(c0 * sx)
                top_y, bot_y = int(215 * sy), int(685 * sy)
                d.rounded_rectangle((cx - int(95 * sx), top_y, cx + int(95 * sx), bot_y),
                                    radius=50, fill=rgba(light, 28), outline=rgba(accent, 88), width=6)
                for ry in range(top_y + int(55 * sy), bot_y - int(45 * sy), int(75 * sy)):
                    d.arc((cx - int(115 * sx), ry - 24, cx + int(115 * sx), ry + 24),
                          start=15, end=165, fill=rgba(light, 115), width=6)
                    d.arc((cx - int(115 * sx), ry - 24, cx + int(115 * sx), ry + 24),
                          start=195, end=345, fill=rgba(accent, 95), width=5)

        elif kind == 'spire':
            # Disintegrating interior megastructure: slanted broken girders, snapped cables, sky breach rifts
            for i in range(int(6 * sx)):
                gx = int((110 + i * 250) * sx)
                d.polygon([(gx, int(160 * sy)), (gx + int(85 * sx), int(160 * sy)),
                           (gx + int(35 * sx), int(520 * sy)), (gx - int(25 * sx), int(490 * sy))],
                          fill=rgba(fog, 52))
                d.line((gx - int(40 * sx), int(660 * sy), gx + int(135 * sx), int(240 * sy)),
                       fill=rgba((48, 36, 66), 195), width=16)
                d.line((gx - int(32 * sx), int(655 * sy), gx + int(141 * sx), int(238 * sy)),
                       fill=rgba(light, 48), width=3)

    # Atmospheric haze and soft localized glow
    glow = Image.new('RGBA', (canvas_w, canvas_h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow, 'RGBA')
    gd.ellipse((int(canvas_w * 0.35), int(canvas_h * 0.28), int(canvas_w * 0.68), int(canvas_h * 0.76)),
               fill=rgba(light, 42))
    glow = glow.filter(ImageFilter.GaussianBlur(80))
    base = Image.alpha_composite(base, glow)

    # Blend upper ceiling/sky from chapter reference while dissolving lower fake catwalks
    mask = Image.new('L', (1, canvas_h), 0)
    start_y = int(cfg['start'] * sy)
    finish_y = int(cfg['finish'] * sy)
    for y in range(canvas_h):
        if y < start_y:
            a = 232
        elif y >= finish_y:
            a = 0
        else:
            t = (y - start_y) / max(1, finish_y - start_y)
            a = round(232 * (0.5 + 0.5 * math.cos(t * math.pi)))
        mask.putpixel((0, y), a)
    mask = mask.resize((canvas_w, canvas_h), Image.Resampling.NEAREST)
    src_dark = ImageEnhance.Brightness(src).enhance(0.78)
    out = Image.composite(src_dark, base.convert('RGB'), mask).convert('RGBA')

    # Re-apply ECHO-7 stencil in Chapter 1 so upper mask never dims it
    if kind == 'awakening':
        sd = ImageDraw.Draw(out, 'RGBA')
        draw_echo7_stencil(sd, int(145 * sx), int(305 * sy), light, 195)

    veil = Image.new('RGBA', (canvas_w, canvas_h), (0, 0, 0, 0))
    vdraw = ImageDraw.Draw(veil)
    vstart = int(280 * sy)
    for y in range(vstart, canvas_h):
        a = int((y - vstart) / max(1, canvas_h - vstart) * 30)
        vdraw.line((0, y, canvas_w, y), fill=(*bcol, a), width=1)
    out = Image.alpha_composite(out, veil).convert('RGB')
    return out


def create(idx: int) -> Image.Image:
    scenic_im = render_scene_canvas(idx, W, H)
    scenic_path = DEST / f'chapter_{idx:02d}_scenic.png'
    scenic_im.save(scenic_path, optimize=True)

    pano_im = render_scene_canvas(idx, PW, PH)
    pano_path = DEST / f'chapter_{idx:02d}_pano.png'
    pano_im.save(pano_path, optimize=True)
    return scenic_im


if __name__ == '__main__':
    for n in range(1, 9):
        im = create(n)
        print('wrote scenic & panoramic backdrops for chapter', n, im.size)
