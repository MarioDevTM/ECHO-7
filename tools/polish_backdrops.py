"""Build 8 architecturally distinct chapter environments from scratch (Part IV & IX).

Each chapter uses a completely different structural silhouette, horizon geometry,
and industrial architecture so that even in grayscale, all 8 chapters are
unmistakably distinct and faithful to the ECHO-7 Concept Board.
"""
from pathlib import Path
import math, random
from PIL import Image, ImageDraw, ImageFilter, ImageChops

ROOT = Path(__file__).resolve().parents[1]
BG = ROOT / 'data' / 'art' / 'backgrounds'
BG.mkdir(parents=True, exist_ok=True)
W, H = 1280, 720
INK = (6, 15, 30, 255)


def quantized_halo(d, cx, cy, radii, color, alphas):
    for r, a in zip(radii, alphas):
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(*color, a))


def draw_gear(d, cx, cy, r, teeth, fill_col, rim_col, hub_col):
    for k in range(teeth):
        ang = 2 * math.pi * k / teeth
        tx = cx + int((r + 9) * math.cos(ang))
        ty = cy + int((r + 9) * math.sin(ang))
        d.rectangle((tx - 8, ty - 8, tx + 8, ty + 8), fill=fill_col, outline=INK, width=2)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=fill_col, outline=INK, width=3)
    d.ellipse((cx - r + 5, cy - r + 5, cx + r - 5, cy + r - 5), outline=rim_col, width=4)
    inner_r = int(r * 0.68)
    d.ellipse((cx - inner_r, cy - inner_r, cx + inner_r, cy + inner_r), fill=(12, 16, 26, 235), outline=INK, width=3)
    for k in range(6):
        ang = 2 * math.pi * k / 6
        x1 = cx + int(22 * math.cos(ang))
        y1 = cy + int(22 * math.sin(ang))
        x2 = cx + int(inner_r * math.cos(ang))
        y2 = cy + int(inner_r * math.sin(ang))
        d.line((x1, y1, x2, y2), fill=rim_col, width=9)
    d.ellipse((cx - 26, cy - 26, cx + 26, cy + 26), fill=hub_col, outline=INK, width=3)
    d.ellipse((cx - 10, cy - 10, cx + 10, cy + 10), fill=INK)


def build_chapter_1() -> Image.Image:
    """Ch.1 Awakening: Horizontal abandoned lab, tall blue-tinted multi-pane windows, ECHO-7 wall stencil, hanging vines."""
    im = Image.new('RGB', (W, H), (10, 22, 34, 255))
    d = ImageDraw.Draw(im, 'RGBA')
    rng = random.Random(101)
    # Upper & lower horizontal steel laboratory bulkheads
    d.rectangle((0, 0, W, 86), fill=(16, 32, 48, 255), outline=INK, width=3)
    d.rectangle((0, 468, W, H), fill=(13, 27, 41, 255), outline=INK, width=3)
    # 3 large recessed multi-pane observation windows with pale daylight sky outside
    for wx, ww in ((320, 270), (630, 280), (950, 270)):
        d.rectangle((wx - 8, 92, wx + ww + 8, 452), fill=(22, 44, 62, 255), outline=INK, width=3)
        d.rectangle((wx, 102, wx + ww, 442), fill=(36, 98, 128, 255), outline=(92, 188, 212, 255), width=2)
        # Pale daylight gradient bands & distant exterior silhouettes inside window
        d.rectangle((wx + 2, 104, wx + ww - 2, 215), fill=(72, 158, 186, 255))
        d.rectangle((wx + 2, 215, wx + ww - 2, 320), fill=(48, 122, 152, 255))
        # Window mullions (vertical & horizontal muntin bars)
        for mx in range(wx + 54, wx + ww - 20, 54):
            d.rectangle((mx - 2, 102, mx + 2, 442), fill=(18, 38, 54, 255))
        for my in (186, 272, 358):
            d.rectangle((wx, my - 2, wx + ww, my + 2), fill=(18, 38, 54, 255))
        # Diagonal light shafts entering lab
        d.polygon([(wx + 20, 104), (wx + 110, 104), (wx + 165, 442), (wx + 55, 442)], fill=(145, 232, 245, 28))

    # Left solid steel bulkhead with large stenciled "ECHO-7" plaque (matches Ch.1 reference)
    d.rectangle((32, 96, 296, 452), fill=(26, 48, 66, 255), outline=INK, width=3)
    d.rectangle((52, 156, 276, 248), fill=(36, 64, 86, 255), outline=(82, 138, 165, 255), width=2)
    d.text((88, 192), "ECHO-7 // LAB-01", fill=(175, 228, 242, 255))
    # Lower laboratory server racks & cyan diagnostic monitors
    for cx in range(60, 1220, 190):
        d.rectangle((cx, 486, cx + 135, 610), fill=(20, 39, 56, 255), outline=INK, width=2)
        d.rectangle((cx + 14, 502, cx + 76, 542), fill=(8, 58, 78, 255), outline=(75, 212, 225, 255), width=2)
        d.line((cx + 20, 514, cx + 68, 514), fill=(165, 248, 255, 255), width=2)
        quantized_halo(d, cx + 45, 522, (42, 24), (75, 212, 225), (16, 34))

    # Hanging green vines from ceiling & window frames
    for vx in (140, 335, 485, 575, 660, 810, 975, 1120, 1210):
        vlen = rng.randint(110, 265)
        pts = [(vx, 72), (vx + 8, 72 + vlen // 3), (vx - 7, 72 + 2 * vlen // 3), (vx + 4, 72 + vlen)]
        d.line(pts, fill=(24, 92, 58, 255), width=4)
        for ly in range(84, 72 + vlen, 16):
            ox = pts[min(3, (ly - 72) // max(1, vlen // 3))][0]
            d.rectangle((ox - 7, ly, ox + 7, ly + 6), fill=(48, 148, 88, 255), outline=INK, width=1)
            d.rectangle((ox - 4, ly + 1, ox + 2, ly + 3), fill=(106, 208, 132, 255))
    return im


def build_chapter_2() -> Image.Image:
    """Ch.2 Mechanical Depths: Colossal interlocking gear train, heavy shafts, riveted catwalks, amber furnace glow."""
    im = Image.new('RGB', (W, H), (24, 14, 12, 255))
    d = ImageDraw.Draw(im, 'RGBA')
    # Warm localized glow behind the giant central gear train
    quantized_halo(d, 740, 340, (340, 250, 170, 100), (255, 148, 52), (22, 38, 58, 85))
    quantized_halo(d, 310, 390, (220, 145, 85), (245, 130, 42), (18, 34, 55))

    # Heavy horizontal drive shafts & vertical A-frame machine housings physically supporting the gears
    for sy in (230, 330, 425):
        d.rectangle((0, sy - 14, W, sy + 14), fill=(48, 30, 24, 255), outline=INK, width=3)
        d.line((0, sy - 8, W, sy - 8), fill=(118, 74, 52, 255), width=3)
    for gx in (290, 740, 1050):
        d.polygon([(gx - 75, H), (gx - 28, 120), (gx + 28, 120), (gx + 75, H)], fill=(36, 22, 18, 255), outline=INK)

    # Colossal interlocking gear train (meshed teeth & connected hubs)
    draw_gear(d, 740, 330, 195, 24, (78, 44, 28, 255), (235, 142, 62, 255), (145, 82, 42, 255))
    draw_gear(d, 445, 425, 122, 16, (64, 36, 24, 255), (205, 118, 50, 255), (120, 68, 36, 255))
    draw_gear(d, 1035, 230, 112, 16, (68, 38, 26, 255), (218, 128, 55, 255), (128, 72, 38, 255))
    draw_gear(d, 185, 255, 86, 12, (54, 32, 22, 255), (175, 98, 44, 255), (98, 56, 30, 255))

    # Foreground riveted I-beam columns & suspended catwalks with industrial railings
    for cy in (135, 515):
        d.rectangle((0, cy, W, cy + 24), fill=(42, 28, 24, 255), outline=INK, width=3)
        # Industrial handrail above catwalk
        d.line((0, cy - 22, W, cy - 22), fill=(138, 86, 56, 255), width=3)
        for rx in range(20, W, 48):
            d.line((rx, cy - 22, rx, cy), fill=(92, 58, 40, 255), width=2)
            # Yellow-black hazard chevrons on catwalk fascia
            if (rx // 48) % 2 == 0:
                d.polygon([(rx, cy + 4), (rx + 18, cy + 4), (rx + 10, cy + 20), (rx - 8, cy + 20)], fill=(250, 178, 52, 255))
    return im


def build_chapter_3() -> Image.Image:
    """Ch.3 Power Grid: Tall vertical transformer towers, ceramic insulator stacks, overhead catenary cables & live blue arcs."""
    im = Image.new('RGB', (W, H), (8, 16, 32, 255))
    d = ImageDraw.Draw(im, 'RGBA')
    # Distant vertical substation lattice columns
    for lx in range(60, W, 160):
        d.rectangle((lx, 0, lx + 28, H), fill=(14, 28, 52, 255), outline=INK, width=2)
        for ly in range(20, H, 36):
            d.line((lx, ly, lx + 28, ly + 18), fill=(26, 52, 88, 255), width=2)

    # 4 Main High-Voltage Transformer Towers with ceramic insulator ribs
    tower_xs = (170, 470, 810, 1110)
    for tx in tower_xs:
        d.rectangle((tx - 48, 95, tx + 48, 640), fill=(18, 36, 62, 255), outline=INK, width=3)
        d.rectangle((tx - 36, 110, tx + 36, 620), fill=(24, 48, 80, 255), outline=(64, 138, 196, 255), width=2)
        # Horizontal ceramic insulator coils along tower
        for iy in range(145, 520, 48):
            d.rectangle((tx - 62, iy, tx + 62, iy + 18), fill=(30, 64, 104, 255), outline=INK, width=2)
            d.line((tx - 56, iy + 6, tx + 56, iy + 6), fill=(78, 192, 255, 255), width=3)
            d.line((tx - 48, iy + 11, tx + 48, iy + 11), fill=(195, 245, 255, 255), width=1)
        # Yellow high-voltage warning triangle plaque
        d.polygon([(tx, 540), (tx - 18, 572), (tx + 18, 572)], fill=(255, 206, 58, 255), outline=INK)
        d.line((tx, 550, tx, 565), fill=INK, width=2)
        # Glowing top node sphere
        quantized_halo(d, tx, 88, (75, 48, 26), (78, 192, 255), (22, 45, 85))
        d.ellipse((tx - 16, 72, tx + 16, 104), fill=(0, 218, 255, 255), outline=INK, width=3)
        d.ellipse((tx - 8, 80, tx + 8, 96), fill=(225, 252, 255, 255))

    # High-voltage electric arcs & catenary cables bridging between the 4 towers
    for x1, x2 in zip(tower_xs[:-1], tower_xs[1:]):
        mid = (x1 + x2) // 2
        arc_pts = [(x1 + 16, 88), (x1 + 85, 68), (mid, 106), (x2 - 85, 64), (x2 - 16, 88)]
        d.line(arc_pts, fill=(42, 145, 235, 255), width=6)
        d.line(arc_pts, fill=(195, 248, 255, 255), width=2)
        # Secondary lower bus arc
        arc2 = [(x1 + 58, 248), (mid - 40, 232), (mid + 40, 264), (x2 - 58, 248)]
        d.line(arc2, fill=(42, 145, 235, 255), width=5)
        d.line(arc2, fill=(185, 245, 255, 255), width=2)
    return im


def build_chapter_4() -> Image.Image:
    """Ch.4 Optical Works: Geometric purple laboratory, octagonal prism chamber, 45-degree laser conduits & clean lab walls."""
    im = Image.new('RGB', (W, H), (22, 12, 38, 255))
    d = ImageDraw.Draw(im, 'RGBA')
    # Clean geometric laboratory wall grid (octagonal & rectangular recessed chambers)
    for bx in (40, 920):
        d.rectangle((bx, 75, bx + 310, 560), fill=(34, 20, 58, 255), outline=INK, width=3)
        d.rectangle((bx + 18, 95, bx + 292, 540), fill=(44, 26, 74, 255), outline=(138, 78, 190, 255), width=2)
        # Illuminated purple containment window inside wing
        d.rectangle((bx + 48, 135, bx + 262, 365), fill=(68, 34, 112, 255), outline=(209, 106, 244, 255), width=3)
        d.rectangle((bx + 76, 165, bx + 234, 335), fill=(115, 52, 168, 255))

    # Central Octagonal Optical Interferometer Ring
    cx, cy = 635, 315
    quantized_halo(d, cx, cy, (220, 160, 105), (209, 106, 244), (20, 38, 65))
    oct_outer = [(cx + int(185 * math.cos(math.radians(45 * k + 22.5))),
                  cy + int(185 * math.sin(math.radians(45 * k + 22.5)))) for k in range(8)]
    oct_inner = [(cx + int(125 * math.cos(math.radians(45 * k + 22.5))),
                  cy + int(125 * math.sin(math.radians(45 * k + 22.5)))) for k in range(8)]
    d.polygon(oct_outer, fill=(38, 22, 66, 255), outline=INK)
    d.polygon(oct_inner, fill=(20, 10, 36, 255), outline=(209, 106, 244, 255))
    d.ellipse((cx - 58, cy - 58, cx + 58, cy + 58), fill=(52, 24, 88, 255), outline=(255, 115, 245, 255), width=3)
    d.ellipse((cx - 22, cy - 22, cx + 22, cy + 22), fill=(245, 195, 255, 255))

    # Geometric 45-degree optical conduit channels & reflector nodes in background wall
    conduit_paths = [
        [(195, 445), (420, 445), (550, 315)],
        [(720, 315), (855, 180), (1075, 180)],
        [(635, 130), (635, 40)],
        [(635, 500), (635, 640)],
    ]
    for path in conduit_paths:
        d.line(path, fill=(135, 48, 178, 255), width=8)
        d.line(path, fill=(245, 135, 255, 255), width=2)
    return im


def build_chapter_5() -> Image.Image:
    """Ch.5 Flood Control: Massive flanged pipelines, sluice waterfall chutes, prominent rotary turbine & flooded reservoir."""
    im = Image.new('RGB', (W, H), (8, 26, 36, 255))
    d = ImageDraw.Draw(im, 'RGBA')
    # Vertical waterfall chutes pouring from upper sluice gates
    for wx in (210, 560, 1060):
        d.rectangle((wx - 45, 60, wx + 45, 540), fill=(12, 48, 64, 255), outline=INK, width=3)
        d.rectangle((wx - 32, 68, wx + 32, 540), fill=(28, 128, 152, 255))
        for sx in range(wx - 24, wx + 28, 12):
            d.line((sx, 70, sx, 538), fill=(115, 228, 235, 210), width=3)
        quantized_halo(d, wx, 520, (68, 38), (73, 222, 213), (24, 48))

    # Massive horizontal & vertical flanged hydraulic pipelines with bolted elbow joints
    for py in (145, 295):
        d.rectangle((0, py - 22, W, py + 22), fill=(20, 62, 78, 255), outline=INK, width=3)
        d.line((0, py - 12, W, py - 12), fill=(68, 168, 186, 255), width=4)
        for fx in range(90, W, 180):
            d.rectangle((fx - 8, py - 28, fx + 8, py + 28), fill=(36, 94, 114, 255), outline=INK, width=2)

    # Prominent Circular Hydro-Turbine Impeller (matches Ch.5 reference)
    tcx, tcy = 835, 345
    quantized_halo(d, tcx, tcy, (185, 135, 85), (73, 222, 213), (20, 38, 62))
    draw_gear(d, tcx, tcy, 142, 14, (18, 68, 84, 255), (73, 222, 213, 255), (38, 124, 142, 255))

    # Lower submerged reservoir basin with layered pixel-art water surface reflections
    d.rectangle((0, 525, W, H), fill=(10, 58, 78, 255), outline=INK, width=3)
    d.line((0, 528, W, 528), fill=(145, 245, 240, 255), width=4)
    for wy in range(546, H - 10, 22):
        offset = (wy * 17) % 60
        for wx in range(-offset, W, 90):
            d.line((wx, wy, wx + 52, wy), fill=(52, 168, 188, 255), width=2)
    return im


def build_chapter_6() -> Image.Image:
    """Ch.6 Furnace: Massive overhead foundry press & crucible pouring molten orange-gold steel into a central slag pit."""
    im = Image.new('RGB', (W, H), (24, 11, 10, 255))
    d = ImageDraw.Draw(im, 'RGBA')
    # Dark heavy industrial steel background walls (NO uniform orange screen tint!)
    for cx in (60, 260, 960, 1140):
        d.rectangle((cx, 0, cx + 84, H), fill=(36, 20, 18, 255), outline=INK, width=3)
        for vy in range(90, 580, 95):
            d.rectangle((cx + 16, vy, cx + 68, vy + 36), fill=(92, 32, 20, 255), outline=INK, width=2)
            d.line((cx + 22, vy + 18, cx + 62, vy + 18), fill=(255, 138, 52, 255), width=3)

    # Localized intense furnace glow originating strictly from the central crucible & molten pour
    quantized_halo(d, 640, 380, (360, 260, 180, 110), (255, 135, 42), (18, 36, 62, 95))

    # Overhead Foundry Crucible & Hydraulic Press Hood (x=430..850, y=0..290)
    d.polygon([(410, 0), (870, 0), (810, 210), (470, 210)], fill=(44, 24, 20, 255), outline=INK)
    d.rectangle((495, 210, 785, 285), fill=(58, 30, 24, 255), outline=INK, width=3)
    for sx in range(510, 770, 28):
        d.polygon([(sx, 218), (sx + 14, 218), (sx + 6, 242), (sx - 8, 242)], fill=(255, 182, 52, 255))

    # Central Molten Pour Column & Slag Cauldron Basin
    d.rectangle((565, 285, 715, 585), fill=(215, 78, 24, 255))
    d.rectangle((590, 285, 690, 585), fill=(255, 158, 48, 255))
    d.rectangle((618, 285, 662, 585), fill=(255, 232, 135, 255))
    # Lower cauldron vat catching molten stream
    d.polygon([(440, 565), (840, 565), (795, 695), (485, 695)], fill=(52, 26, 22, 255), outline=INK)
    d.rectangle((475, 565, 805, 592), fill=(255, 172, 62, 255), outline=INK, width=2)

    # Rising pixel embers around the furnace core
    rng = random.Random(606)
    for _ in range(65):
        ex = rng.randint(360, 920)
        ey = rng.randint(120, 620)
        d.rectangle((ex, ey, ex + 3, ey + 5), fill=(255, 205, 88, 235))
    return im


def build_chapter_7() -> Image.Image:
    """Ch.7 Broken Spire: Sheared diagonal megastructure girders, collapsed bridges, distant ruined spires & red warning strobes."""
    im = Image.new('RGB', (W, H), (20, 12, 26, 255))
    d = ImageDraw.Draw(im, 'RGBA')
    # Jagged ruined spire skyline in the distance
    d.polygon([
        (0, 440), (95, 260), (145, 310), (240, 145), (330, 340), (470, 210),
        (580, 390), (710, 130), (835, 330), (960, 175), (1095, 360), (1190, 195),
        (W, 310), (W, H), (0, H)
    ], fill=(38, 22, 44, 255), outline=INK)

    # Sheared diagonal structural steel girders & collapsed truss spans
    sheared_beams = [
        ((0, 520), (490, 165), 34),
        ((340, 585), (880, 140), 38),
        ((740, 560), (1260, 210), 32),
        ((180, 110), (690, 490), 26),
    ]
    for (x1, y1), (x2, y2), w in sheared_beams:
        d.line((x1, y1, x2, y2), fill=INK, width=w + 6)
        d.line((x1, y1, x2, y2), fill=(58, 38, 56, 255), width=w)
        d.line((x1, y1, x2, y2), fill=(158, 72, 92, 255), width=4)

    # Fractured vertical support columns with red hazard triangle signs & emergency strobe beacons
    for px, top_y in ((165, 230), (525, 275), (895, 220), (1145, 260)):
        d.rectangle((px - 34, top_y, px + 34, H), fill=(32, 22, 38, 255), outline=INK, width=3)
        # Jagged broken column top
        d.polygon([(px - 34, top_y), (px - 12, top_y - 24), (px + 10, top_y - 8), (px + 34, top_y - 28), (px + 34, top_y)],
                  fill=(48, 30, 52, 255), outline=INK)
        # Red warning triangle plaque
        d.polygon([(px, top_y + 70), (px - 20, top_y + 104), (px + 20, top_y + 104)],
                  fill=(235, 64, 78, 255), outline=(255, 220, 225, 255))
        # Localized crimson strobe beacon
        quantized_halo(d, px, top_y - 26, (56, 34, 16), (255, 82, 102), (24, 48, 92))
        d.rectangle((px - 6, top_y - 32, px + 6, top_y - 20), fill=(255, 110, 124, 255), outline=INK, width=2)
    return im


def build_chapter_8() -> Image.Image:
    """Ch.8 Surface Breach: Open blue-lavender night sky, large full moon, distant skyline, breached exterior & lush flora."""
    im = Image.new('RGB', (W, H), (16, 28, 56, 255))
    d = ImageDraw.Draw(im, 'RGBA')
    # Open night sky horizon bands (indigo -> blue-lavender horizon)
    d.rectangle((0, 0, W, 170), fill=(16, 28, 58, 255))
    d.rectangle((0, 170, W, 330), fill=(26, 46, 84, 255))
    d.rectangle((0, 330, W, 495), fill=(38, 68, 112, 255))

    # Crisp pixel starfield in upper sky
    rng = random.Random(808)
    for _ in range(90):
        sx = rng.randint(20, W - 20)
        sy = rng.randint(15, 290)
        d.rectangle((sx, sy, sx + 2, sy + 2), fill=(210, 232, 255, 220))

    # Prominent Luminous Full Moon (matches Ch.8 Surface Breach concept art)
    mcx, mcy, mr = 965, 160, 78
    quantized_halo(d, mcx, mcy, (165, 128, 98), (165, 220, 250), (22, 38, 64))
    d.ellipse((mcx - mr, mcy - mr, mcx + mr, mcy + mr), fill=(228, 246, 255, 255), outline=(145, 215, 245, 255), width=3)
    # Subtle lunar craters
    d.ellipse((mcx - 36, mcy - 24, mcx - 8, mcy + 4), fill=(202, 228, 244, 255))
    d.ellipse((mcx + 12, mcy + 10, mcx + 42, mcy + 36), fill=(202, 228, 244, 255))

    # Distant industrial skyline & towers silhouetted against moonlit horizon
    for bx in range(0, W, 68):
        bh = rng.randint(95, 245)
        btop = 540 - bh
        d.rectangle((bx, btop, bx + 54, 550), fill=(22, 42, 72, 255), outline=INK, width=2)
        for wx in range(bx + 8, bx + 46, 12):
            for wy in range(btop + 14, 530, 20):
                if rng.random() < 0.55:
                    d.rectangle((wx, wy, wx + 5, wy + 8), fill=(115, 219, 250, 185))

    # Foreground breached exterior superstructure on left & right flanks (leaving center sky wide open!)
    for fx in (35, 1105):
        d.rectangle((fx, 180, fx + 140, H), fill=(28, 50, 76, 255), outline=INK, width=3)
        d.rectangle((fx + 20, 215, fx + 120, 320), fill=(18, 88, 118, 255), outline=(115, 219, 250, 255), width=2)
        # Overgrown green vines & violet flowers along exterior breach structures
        for vx in range(fx + 10, fx + 130, 24):
            d.rectangle((vx, 174, vx + 16, 196), fill=(46, 142, 88, 255), outline=INK, width=1)
            d.rectangle((vx + 4, 170, vx + 10, 176), fill=(175, 138, 238, 255))
    return im


BUILDERS = {
    1: build_chapter_1,
    2: build_chapter_2,
    3: build_chapter_3,
    4: build_chapter_4,
    5: build_chapter_5,
    6: build_chapter_6,
    7: build_chapter_7,
    8: build_chapter_8,
}


def weather_surface(im, chapter):
    """Pixel-scale machining marks and reflected light over chapter-specific architecture."""
    rng = random.Random(481 + chapter)
    im = im.convert('RGB')
    pen = ImageDraw.Draw(im, 'RGBA')
    if chapter == 8:
        # Pitted lunar mare, cloud wisps and silhouette of the broken launch gantry.
        for _ in range(170):
            x, y = rng.randrange(-72, 73), rng.randrange(-72, 73)
            size = rng.choice((2, 3, 4, 6, 9))
            if math.hypot(x, y) + size < 76:
                pen.ellipse((965+x,160+y,965+x+size,161+y+size), fill=(106,160,200,64))
                pen.line((965+x,160+y+size,965+x+size//2,160+y+size), fill=(245,255,255,125))
        for base_x, base_y in ((70,212),(360,132),(682,239),(1050,90)):
            for k in range(8):
                x=base_x+k*12
                pen.ellipse((x,base_y-rng.randrange(3,16),x+42,base_y+8),fill=(92,124,178,58))
        for x,y in ((100,520),(1190,556)):
            pen.line((x,y,x+119,y-270),fill=(15,28,52,255),width=9)
            pen.line((x+42,y,x+122,y-274),fill=(21,39,61,255),width=7)
            for i in range(9):
                h=i*26
                pen.line((x+int(h*.44),y-h,x+42+int((h+26)*.3),y-h-26),fill=(27,52,78,255),width=5)
    if chapter in (1, 7, 8):
        roots=({1:[(146,76),(476,78),(810,80),(1110,73)],7:[(161,255),(909,241)],8:[(40,182),(103,185),(1135,185),(1228,182)]})[chapter]
        for x,y in roots:
            for branch in range(10):
                bx=x+rng.randint(-17,18);by=y
                for step in range(rng.randrange(6,22)):
                    nx=bx+rng.randrange(-3,4);ny=by+rng.randrange(4,8)
                    pen.line((bx,by,nx,ny),fill=(23,69,58,220),width=2)
                    side=rng.choice((-1,1));end=nx+side*rng.randrange(4,10)
                    pen.polygon([(nx,ny),(end,ny-3),(end-side*2,ny+3),(nx,ny+4)],fill=rng.choice(((40,91,65,220),(71,117,71,210),(99,142,80,180))))
                    bx,by=nx,ny
    # Apply fine wear only to solid dark material, preserving open sky and lit screens.
    for _ in range(15000):
        x=rng.randrange(1,W-8);y=rng.randrange(1,H-3)
        if chapter==8 and y<330 and 175 < x <1105:continue
        color=im.getpixel((x,y))
        if max(color)>155:continue
        length=rng.choices((1,2,3,6,11),weights=(7,6,4,2,1))[0]
        pen.line((x,y,x+length,y),fill=(185,190,180,rng.randrange(5,21)))
        if length>5:pen.line((x+1,y+1,x+length-1,y+1),fill=(2,7,13,35))
    # Thin luminous bloom, followed by a pixel-scale bevel across material boundaries.
    lights=im.point(lambda c:max(0,(c-135)*2))
    bloom=lights.filter(ImageFilter.GaussianBlur(9))
    return ImageChops.screen(im,Image.blend(Image.new('RGB',im.size),bloom,.48))


def main():
    contact_color = Image.new('RGB', (W // 2 * 2 + 24, H // 2 * 4 + 40), (8, 14, 24))
    contact_comp = Image.new('RGB', (W // 4 * 2 + 24, H // 4 * 8 + 72), (8, 14, 24))
    comp_draw = ImageDraw.Draw(contact_comp)

    for ch in range(1, 9):
        p = BG / f'chapter_{ch:02d}.png'
        im = weather_surface(BUILDERS[ch](), ch)
        temp = p.with_suffix(".part")
        im.save(temp, format="PNG", optimize=True)
        with Image.open(temp) as check:
            check.verify()
        temp.replace(p)

        thumb = im.resize((W // 2, H // 2), Image.Resampling.NEAREST)
        col_idx = (ch - 1) % 2
        row_idx = (ch - 1) // 2
        contact_color.paste(thumb, (8 + col_idx * (W // 2 + 8), 8 + row_idx * (H // 2 + 8)))

        # Also build Color vs Grayscale Architectural Silhouette Comparison Sheet (Section 25)
        small_col = im.resize((W // 4, H // 4), Image.Resampling.NEAREST)
        small_gray = im.convert('L').convert('RGB').resize((W // 4, H // 4), Image.Resampling.NEAREST)
        y_off = 8 + (ch - 1) * (H // 4 + 8)
        contact_comp.paste(small_col, (8, y_off))
        contact_comp.paste(small_gray, (16 + W // 4, y_off))
        comp_draw.rectangle((14, y_off + 6, 175, y_off + 26), fill=(6, 15, 30))
        comp_draw.text((20, y_off + 10), f"CH.{ch:02d} COLOR", fill=(115, 219, 250))
        comp_draw.rectangle((22 + W // 4, y_off + 6, 210 + W // 4, y_off + 26), fill=(6, 15, 30))
        comp_draw.text((28 + W // 4, y_off + 10), f"CH.{ch:02d} GRAYSCALE", fill=(220, 230, 240))
        print(f"Built architecturally distinct chapter_{ch:02d}.png ({p.stat().st_size:,} bytes)")

    contact_color.save(ROOT / 'docs' / 'enhanced_background_contact.png', optimize=True)
    contact_comp.save(ROOT / 'docs' / 'chapter_environment_comparison.png', optimize=True)
    print("Saved docs/enhanced_background_contact.png and docs/chapter_environment_comparison.png")


if __name__ == '__main__':
    main()
