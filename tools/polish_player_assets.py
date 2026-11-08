"""Generate ECHO-7's reference-accurate animated pixel robot (36x56 canvas)."""
from pathlib import Path
import math
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'data' / 'art' / 'player'
DEST.mkdir(parents=True, exist_ok=True)

INK = (6, 15, 30, 255)             # #060F1E Dark Navy Ink outline
SHADE = (117, 145, 177, 255)       # #7591B1 Blue-gray shadowed edge
DARK_MECH = (74, 98, 125, 255)     # #4A627D Darker gray rear helmet attachment
MID_ARMOR = (180, 206, 227, 255)   # #B4CEE3 Secondary light-gray armor shade
WHITE = (239, 249, 255, 255)       # #EFF9FF Bright off-white primary armor
HIGHLIGHT = (255, 255, 255, 255)   # #FFFFFF Specular pixel cluster
VISOR_FRAME = (5, 32, 68, 255)     # #052044 Very dark navy visor bezel
VISOR_EDGE = (24, 128, 188, 255)   # #1880BC Darker blue visor inner rim
CYAN = (0, 213, 250, 255)          # #00D5FA Bright cyan-blue central visor
CYAN_BRIGHT = (185, 250, 255, 255) # #B9FAFF Pale-blue/white visor highlight
SPARK = (120, 255, 224, 255)       # #78FFE0 Thruster / interaction spark
CRIMSON = (255, 110, 98, 255)      # #FF6E62 Overload warning crimson

COUNT = {
    'idle': 4,
    'run': 8,
    'jump': 3,
    'fall': 3,
    'land': 3,
    'interact': 4,
    'turn': 2,
    'death': 4,
    'respawn': 4,
    'dash': 3,
    'crouch': 2,
    'wall': 2,
}


def robot(state: str, n: int) -> Image.Image:
    im = Image.new('RGBA', (36, 56), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    total = max(1, COUNT.get(state, 1))
    phase = n / total
    run = (state == 'run')
    stride = math.sin(phase * 2 * math.pi)

    bob = 0
    lean = 0
    if run:
        bob = round(1.6 * abs(stride))
        lean = 2
    elif state == 'idle':
        bob = 1 if n in (1, 2) else 0
    elif state == 'land':
        bob = [4, 2, 0][min(n, 2)]
    elif state == 'crouch':
        bob = 8 + (n % 2)
    elif state == 'respawn':
        bob = [3, 2, 1, 0][min(n, 3)]
    elif state == 'death':
        bob = [0, 1, 2, 3][min(n, 3)]
    elif state == 'dash':
        lean = 3
        bob = 1
    elif state == 'jump':
        bob = [1, -1, -2][min(n, 2)]

    # 1. Compact rear life-support pack
    bp_x = 5 + (1 if lean > 0 else 0)
    d.rounded_rectangle((bp_x, 28 + bob, bp_x + 6, 39 + bob), radius=2, fill=INK)
    d.rectangle((bp_x + 2, 30 + bob, bp_x + 4, 37 + bob), fill=SHADE)
    d.point((bp_x + 3, 32 + bob), fill=CYAN_BRIGHT if (n % 2 == 0) else CYAN)

    if state == 'dash':
        plume_len = 4 + (n % 3) * 2
        d.rectangle((max(0, bp_x - plume_len), 31 + bob, bp_x, 35 + bob), fill=CYAN)
        d.line((max(0, bp_x - plume_len + 1), 33 + bob, bp_x, 33 + bob), fill=CYAN_BRIGHT, width=1)
    elif state == 'fall':
        d.rectangle((bp_x + 1, 39 + bob, bp_x + 4, 41 + bob + (n % 2)), fill=SPARK)

    # 2. Short expressive legs & wide stability boots anchored cleanly to platform
    hip_y = 40 + bob
    if run:
        dx0 = round(4.8 * stride)
        dx1 = -dx0
        ly0 = round(3.4 * max(0.0, -stride))
        ly1 = round(3.4 * max(0.0, stride))
    elif state == 'jump':
        poses = [(-1, 2, -1, 0), (-4, 4, -5, -2), (-5, 5, -6, -3)]
        dx0, dx1, ly0, ly1 = poses[min(n, 2)]
    elif state == 'fall':
        poses = [(3, -2, 1, 2), (4, -3, 2, 3), (3, -4, 1, 3)]
        dx0, dx1, ly0, ly1 = poses[min(n, 2)]
    elif state == 'dash':
        poses = [(-5, 3, -4, 1), (-6, 4, -5, 2), (-5, 4, -4, 2)]
        dx0, dx1, ly0, ly1 = poses[min(n, 2)]
    elif state == 'wall':
        dx0, dx1, ly0, ly1 = (-3, 4, -3, 0) if n == 0 else (-2, 4, -2, 1)
    elif state == 'land':
        dx0, dx1, ly0, ly1 = (-2, 2, 0, 0) if n == 0 else (-1, 1, 0, 0)
    else:
        dx0 = dx1 = ly0 = ly1 = 0

    for idx_leg, (hx, dx, dy) in enumerate([(13 + lean // 2, dx0, ly0), (22 + lean // 2, dx1, ly1)]):
        ankle_y = min(52, 49 + bob + dy)
        ankle = (hx + dx, ankle_y)
        knee = (hx + dx // 2, (hip_y + ankle_y) // 2)
        d.line(((hx, hip_y), knee, ankle), fill=INK, width=6)
        leg_fill = WHITE if idx_leg == 1 else MID_ARMOR
        d.line(((hx, hip_y + 1), (knee[0], knee[1]), (ankle[0], ankle[1] - 1)), fill=leg_fill, width=3)
        d.rectangle((knee[0] - 2, knee[1] - 1, knee[0] + 2, knee[1] + 1), fill=INK)
        # Wide stability boot silhouette (9x5 px)
        d.rectangle((ankle[0] - 4, ankle[1] - 2, ankle[0] + 5, min(55, ankle[1] + 3)), fill=INK)
        d.rectangle((ankle[0] - 2, ankle[1] - 2, ankle[0] + 4, min(54, ankle[1] + 1)), fill=WHITE if idx_leg == 1 else MID_ARMOR)
        d.line((ankle[0] - 2, min(54, ankle[1] + 1), ankle[0] + 4, min(54, ankle[1] + 1)), fill=SHADE, width=1)
        d.point((ankle[0] + 2, ankle[1] - 2), fill=HIGHLIGHT)

    # Visual-only landing dust/impact particles matching the LAND reference panel
    if state == 'land' and n in (0, 1):
        spread = 2 if n == 0 else 4
        for px, py in ((6 - spread, 52), (4 - spread, 50), (29 + spread, 52), (31 + spread, 50)):
            if 0 <= px < 35 and 0 <= py < 55:
                d.rectangle((px, py, px + 2, py + 2), fill=WHITE if n == 0 else MID_ARMOR)
                d.point((px, py), fill=HIGHLIGHT)

    # 3. Back arm (drawn behind torso for clear separation)
    swing = round(4.5 * stride) if run else 0
    for x_base, side in [(9 + lean // 2, -1), (27 + lean // 2, 1)]:
        y = 29 + bob + (swing if side < 0 else -swing)
        x = x_base
        if state == 'interact' and side == 1:
            x += [2, 4, 4, 1][min(n, 3)]
            y = 26 + bob + [1, -2, -3, 0][min(n, 3)]
        elif state in ('jump', 'fall'):
            y -= [2, 4, 5][min(n, 2)]
            x += side * 2
        elif state == 'land' and n == 0:
            x += side * 2
            y += 1
        elif state == 'dash':
            x -= 2 if side < 0 else -1
        if side < 0:
            d.rounded_rectangle((x - 3, y, x + 3, y + 11), radius=2, fill=INK)
            d.rectangle((x - 1, y + 2, x + 1, y + 7), fill=SHADE)
            d.line((x - 1, y + 7, x + 1, y + 7), fill=INK, width=1)
            d.rectangle((x - 2, y + 8, x + 2, y + 11), fill=INK)
            d.rectangle((x - 1, y + 9, x + 1, y + 10), fill=MID_ARMOR)

    # 4. Dark mechanical neck ring & compact white armored torso (smaller than helmet)
    tx0, ty0, tx1, ty1 = 10 + lean // 2, 27 + bob, 26 + lean // 2, 42 + bob
    d.rectangle((tx0 + 3, ty0 - 2, tx1 - 3, ty0 + 1), fill=INK)
    d.rounded_rectangle((tx0, ty0, tx1, ty1), radius=4, fill=INK)
    d.rectangle((tx0 + 2, ty0 + 2, tx1 - 2, ty1 - 2), fill=WHITE)
    d.line((tx0 + 3, ty0 + 2, tx1 - 3, ty0 + 2), fill=HIGHLIGHT, width=1)
    d.rectangle((tx0 + 2, ty1 - 4, tx1 - 2, ty1 - 2), fill=SHADE)
    d.line((tx0 + 2, ty0 + 3, tx0 + 3, ty1 - 3), fill=MID_ARMOR, width=1)
    chest_led = CRIMSON if state == 'death' else (CYAN_BRIGHT if n % 2 == 0 else CYAN)
    d.rectangle((tx0 + 6, ty0 + 5, tx0 + 13, ty0 + 10), fill=MID_ARMOR)
    d.rectangle((tx0 + 7, ty0 + 6, tx0 + 12, ty0 + 9), fill=INK)
    d.line((tx0 + 8, ty0 + 7, tx0 + 11, ty0 + 7), fill=chest_led, width=2)

    # 5. Front articulated arm (clearly separated from torso with shoulder, elbow, and hand)
    for x_base, side in [(27 + lean // 2, 1)]:
        y = 29 + bob - swing
        x = x_base
        if state == 'interact':
            x += [2, 4, 4, 1][min(n, 3)]
            y = 26 + bob + [1, -2, -3, 0][min(n, 3)]
        elif state in ('jump', 'fall'):
            y -= [2, 4, 5][min(n, 2)]
            x += 2
        elif state == 'land' and n == 0:
            x += 2
            y += 1
        elif state == 'dash':
            x += 1
        d.rounded_rectangle((x - 3, y, x + 3, y + 11), radius=2, fill=INK)
        d.rectangle((x - 1, y + 2, x + 1, y + 7), fill=WHITE)
        d.point((x, y + 2), fill=HIGHLIGHT)
        d.line((x - 1, y + 7, x + 1, y + 7), fill=INK, width=1)
        d.rectangle((x - 2, y + 8, x + 3, y + 11), fill=INK)
        d.rectangle((x - 1, y + 9, x + 2, y + 10), fill=WHITE)

    # 6. Reference-Accurate Helmet + Rear Gray Mechanical/Comm Attachment (Section 4)
    helmet_y = 5 + bob + (1 if (state == 'idle' and n == 2) else 0)
    if state == 'death':
        helmet_y += min(2, n)
    hx0, hx1 = 5 + lean, 31 + lean
    # Subtle rear darker gray mechanical/communication attachment on back of helmet
    d.rounded_rectangle((hx0 - 2, helmet_y + 8, hx0 + 3, helmet_y + 17), radius=2, fill=INK)
    d.rectangle((hx0 - 1, helmet_y + 10, hx0 + 1, helmet_y + 15), fill=DARK_MECH)
    d.point((hx0, helmet_y + 11), fill=SHADE)

    # Softly rounded rectangular helmet (radius=5, flattened upper profile)
    d.rounded_rectangle((hx0, helmet_y, hx1, helmet_y + 22), radius=5, fill=INK)
    d.rounded_rectangle((hx0 + 2, helmet_y + 2, hx1 - 2, helmet_y + 20), radius=3, fill=WHITE)
    d.line((hx0 + 6, helmet_y + 2, hx1 - 6, helmet_y + 2), fill=HIGHLIGHT, width=2)
    d.line((hx0 + 4, helmet_y + 4, hx0 + 12, helmet_y + 4), fill=HIGHLIGHT, width=1)
    d.rectangle((hx0 + 2, helmet_y + 5, hx0 + 5, helmet_y + 19), fill=MID_ARMOR)
    d.rectangle((hx0 + 2, helmet_y + 13, hx0 + 4, helmet_y + 19), fill=SHADE)
    d.rectangle((hx0 + 3, helmet_y + 18, hx1 - 3, helmet_y + 20), fill=SHADE)
    d.line((hx0 + 4, helmet_y + 17, hx1 - 4, helmet_y + 17), fill=MID_ARMOR, width=1)
    # Recessed side ear-comm detail
    d.rectangle((hx0 + 4, helmet_y + 10, hx0 + 7, helmet_y + 15), fill=SHADE)
    d.point((hx0 + 5, helmet_y + 12), fill=INK)

    # 7. Prominent horizontally oriented rounded-rectangle cyan visor
    v_shift = -3 if state == 'turn' else 0
    vx0, vx1 = hx0 + 9 + v_shift, hx1 - 1 + v_shift
    vy0, vy1 = helmet_y + 6, helmet_y + 17
    d.rounded_rectangle((vx0, vy0, vx1, vy1), radius=3, fill=INK)
    d.rounded_rectangle((vx0 + 1, vy0 + 1, vx1 - 1, vy1 - 1), radius=2, fill=VISOR_FRAME)

    if state == 'death':
        d.rectangle((vx0 + 2, vy0 + 2, vx1 - 2, vy1 - 2), fill=(90, 20, 28, 255))
        d.line((vx0 + 2, vy0 + 2, vx1 - 3, vy1 - 3), fill=CRIMSON, width=2)
    elif state == 'respawn' and n == 0:
        d.rectangle((vx0 + 2, vy0 + 3, vx1 - 2, vy1 - 3), fill=VISOR_EDGE)
    else:
        spec_dx = 1 if (state == 'idle' and n in (1, 2)) else 0
        d.rectangle((vx0 + 2, vy0 + 2, vx1 - 2, vy1 - 2), fill=VISOR_EDGE)
        d.rectangle((vx0 + 3, vy0 + 2, vx1 - 2, vy1 - 3), fill=CYAN)
        d.line((vx0 + 4 + spec_dx, vy0 + 3, vx0 + 9 + spec_dx, vy0 + 3), fill=CYAN_BRIGHT, width=2)
        d.point((vx0 + 4 + spec_dx, vy0 + 5), fill=HIGHLIGHT)
        d.line((vx0 + 4, vy1 + 1, vx1 - 4, vy1 + 1), fill=(135, 225, 248, 255), width=1)

    # 8. State-specific interaction/wall/respawn effects
    if state == 'interact':
        d.rectangle((32, 22 + bob, 35, 25 + bob), fill=SPARK)
        if n in (1, 2):
            d.line((31, 19 + bob, 35, 16 + bob), fill=CYAN_BRIGHT, width=1)
            d.line((31, 27 + bob, 35, 30 + bob), fill=CYAN, width=1)
    elif state == 'wall':
        sy = 28 + (n * 6)
        d.rectangle((32, sy, 34, sy + 2), fill=SPARK)
        d.point((31, sy - 2), fill=CYAN_BRIGHT)
    elif state == 'respawn':
        scan_y = 52 - n * 12
        d.rectangle((5, max(4, scan_y - 6), 32, 54), outline=(55, 205, 246, 190), width=1)
        d.line((4, scan_y, 33, scan_y), fill=CYAN_BRIGHT, width=2)

    return im


def build_all():
    for state, count in COUNT.items():
        for n in range(count):
            robot(state, n).save(DEST / f'{state}_{n}.png')

    cols = max(COUNT.values())
    rows = len(COUNT)
    rgba_sheet = Image.new('RGBA', (cols * 36, rows * 56), (0, 0, 0, 0))
    contact = Image.new('RGBA', (cols * 44 + 110, rows * 62 + 20), (9, 20, 35, 255))
    cd = ImageDraw.Draw(contact)

    for row, (state, count) in enumerate(COUNT.items()):
        y_label = row * 62 + 28
        cd.rectangle((8, row * 62 + 12, 98, row * 62 + 56), fill=(15, 31, 52, 255), outline=(55, 110, 148, 255))
        cd.text((16, y_label), state.upper(), fill=(120, 228, 250, 255))
        for i in range(count):
            frame = robot(state, i)
            rgba_sheet.alpha_composite(frame, (i * 36, row * 56))
            cell_x = 108 + i * 44
            cell_y = row * 62 + 10
            cd.rectangle((cell_x - 2, cell_y - 2, cell_x + 38, cell_y + 58), fill=(14, 28, 46, 255), outline=(36, 70, 102, 255))
            contact.alpha_composite(frame, (cell_x, cell_y))

    rgba_sheet.save(DEST / 'sprite_sheet.png')
    contact.convert('RGB').save(ROOT / 'docs' / 'player_animation_contact.png')
    print('Generated', sum(COUNT.values()), 'reference-accurate animation frames + sprite_sheet.png')


if __name__ == '__main__':
    build_all()
