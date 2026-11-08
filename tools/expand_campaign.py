"""Compile the authored late-game rooms. Coordinates in each plan denote bay and elevation."""

import json
from itertools import pairwise
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEVELS = ROOT / "data/levels"

JOKES = (
    "I signed the inspection sheet in pencil.",
    "Our lift has ambitions. Mostly upward.",
    "Two circuits, one wrench. I know which one I am.",
    "Please count the clicks. I keep losing count.",
    "The backup is ready. It even looks worried.",
    "I brought a spare fuse and a very small umbrella.",
    "My reflection never takes the night shift.",
    "The crate gets paid by the metre.",
    "The upper deck has a fine view of the problem.",
    "If you hear applause, that is a loose pipe.",
    "Maintenance says the gap is within budget.",
    "I have reserved us a spot on the other side.",
)


def room(plan):
    n = plan["number"]
    ch = (n - 1) // 10 + 1
    title, layout, required, crossing, theme, topology = (
        plan[k] for k in ("title", "layout", "gate", "crossing", "theme", "topology")
    )
    intro = f"{title}. Check the signal lines before you leave the service deck."
    nodes = [(int(s[0]), int(s[1]), s.split(":")[1]) for s in layout.split()]

    assert len({v[:2] for v in nodes}) == len(nodes), (n, nodes)
    roles = [r.partition(".")[0] for _, _, r in nodes]
    cols = max(x for x, y, r in nodes) + 1
    rows = max(y for x, y, r in nodes) + 1
    gap = 100 + ch * 10 + (n % 4) * 12
    widths = [(390, 340, 432, 362)[(x + n) % 4] for x in range(cols)]
    starts = [150]
    special_col, span, bridge, control = crossing
    for x in range(1, cols):
        starts.append(
            starts[-1] + widths[x - 1] + (span if x - 1 == special_col else gap)
        )
    rowH = 216 + (n % 4) * 12
    W = starts[-1] + widths[-1] + 200
    H = max(720, (rows - 1) * rowH + 490)
    base = H - 135
    pos = [(starts[x], base - y * rowH, widths[x]) for x, y, r in nodes]
    d = {
        k: []
        for k in (
            "tiles",
            "ladders",
            "crates",
            "plates",
            "switches",
            "doors",
            "moving_platforms",
            "conveyors",
            "wind_zones",
            "water_zones",
            "valves",
            "generators",
            "cables",
            "mirrors",
            "crushers",
            "steam_vents",
            "collapsing_platforms",
            "checkpoints",
            "spikes",
            "acids",
            "lasers",
            "optical_beams",
            "sequences",
            "collectibles",
            "decorations",
            "latching_relays",
            "routing_consoles",
            "signal_inverters",
            "npcs",
            "springs",
            "dash_recharges",
            "one_way_platforms",
            "dash_barriers",
        )
    }
    d.update(
        level_id=n,
        width=W,
        height=H,
        name=f"Chamber {n:02} // {title}",
        abilities=dict(wall_jump=ch >= 2, dash=ch >= 3),
    )

    def a(k, **v):
        d[k].append(v)

    def slab(x, y, w, h):
        d["tiles"].append([x, y, w, h])

    def ledge(x, y, w):
        a(
            "one_way_platforms",
            id="walk" + str(len(d["one_way_platforms"])),
            x=x,
            y=y,
            w=w,
            h=12,
        )

    def lift(x, y, w, ex, ey, req=()):
        a(
            "moving_platforms",
            id="car" + str(len(d["moving_platforms"])),
            x=x,
            y=y,
            w=w,
            h=16,
            end_x=ex,
            end_y=ey,
            speed=96 + ch * 4,
            active_by_default=not req,
            required_links=list(req),
        )

    def sign(x, y, t):
        a("decorations", type="monitor", x=x, y=y, text=t)

    slab(0, 0, 36, H)
    slab(W - 36, 0, 36, H)
    slab(36, 0, W - 72, 30)
    # Sunken caissons under the lowest machines; higher bays rest on brackets.
    for j, (x, y, w) in enumerate(pos):
        kind = roles[j]
        if kind == "belt":
            slab(x, y, 70, 30)
            slab(x + w - 90, y, 90, 30)
            a("conveyors", id="freight_line", x=x + 70, y=y, w=w - 160, h=18, speed=85)
        else:
            slab(x, y, w, (H - y if y == base else 23))
        if y != base:
            a(
                "decorations",
                type="warning_stripe",
                x=x + 12,
                y=y + 12,
                w=min(w - 24, 120),
            )
    # Local pools between caissons; additional vertical drops kill through the normal fall boundary.
    banks = sorted(
        [(x, x + w) for x, y, w in pos if y == base] + [(36, 36), (W - 36, W - 36)]
    )
    for (_, left), (right, _) in pairwise(banks):
        if right > left:
            a("acids", x=left, y=H - 75, w=right - left, h=75)
    links = {}
    notes = []
    instructions = {}

    def mark(id, x, y):
        links[id] = (x, y)

    def prompt(id, text):
        instructions[id] = text

    for j, ((x, y, w), kind) in enumerate(zip(pos, roles)):
        t = nodes[j][2]
        req = t.split(".")[1].split(",") if "." in t else []
        if kind in ("alpha", "beta", "proof"):
            req.sort(key=lambda link: link not in ("alpha", "proof", "beta"))
        mid = x + w // 2
        if kind == "start":
            d["spawn"] = [x + 38, y - 46]
            a("npcs", id="kip", x=x + 100, y=y)
        elif kind == "exit":
            # A sealed box with a roof, a back wall and one full-height door.
            gx = x + w // 2 - 58
            slab(gx, y - 134, 155, 18)
            slab(gx + 137, y - 116, 18, 116)
            a(
                "doors",
                id="surface_lock",
                x=gx,
                y=y - 116,
                w=20,
                h=116,
                required_links=required.split(","),
            )
            d["exit"] = [gx + 57, y - 80]
            sign(gx + 23, y - 174, "EXIT LOCK")
        elif kind in ("lever", "timer", "first", "second", "third"):
            mode = (
                "timed"
                if kind == "timer"
                else ("permanent" if kind == "lever" else "sequence")
            )
            window = (24 if ch < 3 else 19) + (5 if n in (39, 70, 78, 79) else 0)
            a(
                "switches",
                link_id=kind,
                x=mid,
                y=y,
                mode=mode,
                duration=window if mode == "timed" else 0,
            )
            mark(kind, mid, y)
            sign(
                mid - 32,
                y - 93,
                {
                    "lever": "RELEASE",
                    "timer": f"ESCAPE {window}s",
                    "first": "01 / IN",
                    "second": "02 / TEST",
                    "third": "03 / OUT",
                }[kind],
            )
            prompt(
                kind,
                (
                    "Start the clock after the other lock lights are green."
                    if kind == "timer"
                    else (
                        "Use the numbered stations in order."
                        if mode == "sequence"
                        else "Use the release panel."
                    )
                ),
            )
        elif kind == "power":
            a("generators", link_id="power", x=mid, y=y)
            mark("power", mid, y)
            sign(mid - 30, y - 100, "ENERGIZE")
            prompt("power", "Start the generator to bring the circuit online.")
        elif kind in ("weight", "tank", "lampbox", "belt"):
            cargo = (
                "freight"
                if kind == "belt"
                else "park" if kind == "lampbox" else "weight"
            )
            platex = x + w - 83
            cx = x + 85 if kind == "belt" else x + 115
            a("crates", id="load", x=cx, y=y - 36)
            a("plates", link_id=cargo, x=platex, y=y)
            mark(cargo, platex, y)
            slab(x + w - 35, y - 17, 10, 17)
            sign(platex - 63, y - 92, "RECEIVING SCALE")
            prompt(cargo, "Move the cargo right until it rests on the receiving scale.")
            if kind == "tank":
                a(
                    "water_zones",
                    id="sump",
                    x=x + 30,
                    y=y - 118,
                    w=w - 50,
                    h=118,
                    drained_y=y,
                    controlled_by="dry",
                )
                a("signal_inverters", link_id="full", input="dry", water_zone="sump")
                mark("full", x + 42, y - 120)
                prompt(
                    "full",
                    "Open the inlet again and let the basin refill. The float will lift off the scale.",
                )
            if kind == "lampbox":
                a(
                    "optical_beams",
                    link_id="light",
                    x=x + 54,
                    y=y - 22,
                    dir=[1, 0],
                    max_length=w - 110,
                    receiver=[x + w - 124, y - 31, 18, 18],
                )
                mark("light", x + w - 124, y - 22)
                prompt("light", "Push the shutter crate past the optical receiver.")
        elif kind in ("valve", "drain"):
            id = "dry" if kind == "drain" else "valve"
            a("valves", link_id=id, x=mid, y=y)
            mark(id, mid, y)
            sign(mid - 48, y - 92, "DRAIN / FILL" if kind == "drain" else "ISOLATE")
            prompt(id, "Turn the handwheel and watch which machinery changes.")
        elif kind in ("prism", "secondprism"):
            mx = mid + 14
            origin = (x + 55, y - 18)
            a("mirrors", id=kind, x=mid, y=y - 36, orientation=1)
            for id, ry in [("up", y - 142), ("down", y - 11)]:
                if kind == "secondprism":
                    id = "east_" + id
                v = dict(
                    link_id=id,
                    x=origin[0],
                    y=origin[1],
                    dir=[1, 0],
                    max_length=w + 90,
                    receiver=[mx - 7, ry, 14, 10],
                )
                if "power" in roles:
                    v["enabled_by"] = "power"
                a("optical_beams", **v)
                mark(id, mx, ry)
            if kind == "secondprism":
                prompt("east_up", "Aim the second reflector at its overhead pickup.")
            prompt("up", "Turn the mirror toward its ceiling pickup.")
            prompt("down", "Turn the mirror toward the low pickup beside its foot.")
        elif kind == "bus":
            a(
                "routing_consoles",
                id="selector",
                route_id="supply",
                x=mid,
                y=y,
                a_signal="A",
                b_signal="B",
            )
            mark("A", mid, y)
            mark("B", mid + 10, y)
            sign(mid - 40, y - 99, "SELECT A / B")
            prompt("A", "Set the supply selector to A.")
            prompt(
                "B", "Transfer the selector to B after recording the A-side reading."
            )
        elif kind in ("alpha", "beta", "proof"):
            a("latching_relays", link_id=kind, x=mid, y=y, required_links=req)
            mark(kind, mid, y)
            sign(mid - 30, y - 100, "HOLD " + " + ".join(req).upper())
            prompt(
                kind,
                "Keep "
                + " and ".join(req)
                + " live, then interact with the recorder to hold the reading.",
            )
        elif kind == "seal":
            a("dash_barriers", id="seal", x=mid, y=y - 88, w=24, h=88)
            sign(mid - 44, y - 132, "DASH SEAL")
        elif kind == "spring":
            a("springs", id="launch", x=mid - 28, y=y - 10, w=56, h=10)
            sign(x + 12, y - 96, "LAUNCH")
        elif kind == "fan":
            a(
                "wind_zones",
                id="column",
                x=x + w - 112,
                y=y - rowH - 135,
                w=104,
                h=rowH + 135,
                vx=0,
                vy=-2400,
                controlled_by=req[0],
                active_by_default=False,
            )
            sign(x + 12, y - 94, "EXHAUST")
        elif kind == "press":
            a(
                "crushers",
                id="ram" + str(j),
                x=mid - 35,
                y=y - 215,
                w=74,
                h=42,
                travel=172,
                period=2.9,
                disabled_by=req,
            )
            sign(x + 10, y - 100, "PRESS LINE")
        elif kind == "vent":
            a(
                "steam_vents",
                id="jet",
                x=mid - 24,
                y=y - 162,
                w=48,
                h=162,
                period=2.7,
                duty_cycle=0.55,
                disabled_by=req,
            )
            sign(x + 10, y - 98, "STEAM LINE")
        if (
            kind
            not in ("start", "exit", "press", "vent", "tank", "spring", "belt", "fan")
            and len(d["collectibles"]) == 0
        ):
            a(
                "collectibles",
                id=f"field_{n:02}",
                x=x + 42,
                y=y - 32,
                title=title + " / Shift Notes",
                text=intro,
            )
    if "first" in roles:
        a("sequences", group_id="order", order=["first", "second", "third"])
        prompt(
            "order", "Stamp 01, 02 and 03 in order. A wrong stamp resets the sequence."
        )
    # Join the authored stations in both directions. Canyon bridges, cranked
    # staircase landings and lift shafts each have their own geometric treatment.
    for j, ((ax, ay, aw), (bx, by, bw)) in enumerate(pairwise(pos)):
        if ax == bx:
            hi, lo = sorted((ay, by))
            right = ax + aw
            outer = right + 18
            if n in (26, 28, 31, 33, 41, 42, 47, 62, 66, 73) and roles[j] != "fan":
                a("ladders", x=right + 2, y=hi - 38, h=lo - hi + 48)
            if roles[j] == "fan":
                # The duct carries the player around the rim of the upper bay.
                d["wind_zones"][-1].update(x=right - 16, w=104)
            elif (j + n) % 3 == 0 or ch == 2:
                req = ["power"] if "power" in roles[: j + 1] and ay > by else []
                lift(outer, lo - 8, 86, outer, hi - 8, req)
            else:
                # Offset the ledges outside the solid upper floor.
                for k in range(1, 4):
                    ledge(
                        right + (40 if k % 2 else 0),
                        round(lo - (lo - hi) * k / 3),
                        70 if ch > 5 else 83,
                    )
            if roles[j] == "spring":
                d["springs"][0]["x"] = right - 55
            if ch >= 6 and roles[j] != "fan":
                # Opposing shaft faces create a fast wall-jump route beside the lift.
                slab(right + 116, hi + 30, 14, lo - hi - 66)
        else:
            if ax < bx:
                l, ly, r, ry = ax + aw, ay, bx, by
            else:
                l, ly, r, ry = bx + bw, by, ax, ay
            dist = r - l
            if dist == span and ly == ry:
                if bridge == "ferry":
                    # Avoid stranding an operator on the far side of a switched-off ferry.
                    lift(
                        l + 4,
                        ly - 14,
                        108,
                        r - 113,
                        ry - 14,
                        [control] if control else [],
                    )
                    if control:
                        ledge(l + dist // 2 - 25, ly + 85, 56)
                elif bridge == "swing":
                    lift(l + dist // 2 - 67, ly - 38, 83, l + dist // 2 + 12, ly + 34)
                elif bridge == "post":
                    slab(
                        l + dist // 2 - 31,
                        ly + 38,
                        62,
                        H - ly - 38 if ly == base else 24,
                    )
                elif bridge == "dash":
                    ledge(l + dist // 2 - 30, ly + 48, 60)
                    a(
                        "dash_recharges",
                        id="span_charge" + str(j),
                        x=l + dist // 2 - 12,
                        y=ly - 66,
                    )
                else:
                    for part, hue in ((0.32, -38), (0.68, 34)):
                        px = l + round(dist * part)
                        ledge(px - 32, ly + hue, 68)
                    if bridge in ("ram", "kiln"):
                        a(
                            "crushers",
                            id="hammer" + str(j),
                            x=l + round(dist * 0.68) - 26,
                            y=ly - 178,
                            w=54,
                            h=33,
                            travel=178,
                            period=3.2,
                            disabled_by=[control] if control else [],
                        )
                    elif bridge == "jet":
                        a(
                            "steam_vents",
                            id="flue" + str(j),
                            x=l + round(dist * 0.32) - 18,
                            y=ly - 143,
                            w=36,
                            h=100,
                            period=2.8,
                            duty_cycle=0.45,
                            disabled_by=[control] if control else [],
                        )
            elif ly != ry:
                count = 4 if dist >= 330 else 3
                for k in range(1, count):
                    px = round(l + dist * k / count)
                    py = round(ly + (ry - ly) * k / count)
                    ledge(px - 29, py, 58 if ch >= 6 else 78)
            elif ch >= 2 and (n + j) % 4 == 1:
                lift(l + 5, ly - 24, 65, r - 70, ry - 66)
            elif ch >= 3 and (n + j) % 3 == 0:
                a("dash_recharges", id="ring" + str(j), x=(l + r) // 2 - 14, y=ly - 98)
            if ch >= 3 and ly == ry and (n + j) % 3 == 2:
                # The plume is visible from both take-off points.
                a(
                    "steam_vents",
                    id="seam" + str(j),
                    x=(l + r) // 2 - 18,
                    y=ly - 85,
                    w=36,
                    h=134,
                    period=3.1,
                    duty_cycle=0.43,
                    disabled_by=[],
                )
    # A beacon near the last major test, with dry space around its spawn.
    candidates = [
        j
        for j in range(1, len(nodes) - 1)
        if roles[j] not in ("belt", "tank", "press", "vent", "fan", "spring")
    ]
    j = (candidates or [0])[-1]
    x, y, w = pos[j]
    a(
        "checkpoints",
        id=f"beacon_{n}",
        x=x + w - 65 if roles[j] not in ("weight", "lampbox") else x + 32,
        y=y,
    )
    if not d["collectibles"]:
        x, y, w = pos[0]
        a(
            "collectibles",
            id=f"field_{n:02}",
            x=x + w - 75,
            y=y - 32,
            title=title + " / Shift Notes",
            text=intro,
        )
    # Cables connect recorder inputs to physical signal producers.
    for obj in d["latching_relays"]:
        for i, id in enumerate(obj["required_links"]):
            if id not in links:
                continue
            sx, sy = links[id]
            tx, ty = obj["x"], obj["y"]
            rail = max(sy, ty) + 24 + 7 * i
            a(
                "cables",
                link_id=id,
                points=[
                    [sx + 9, sy - 12],
                    [sx + 9, rail],
                    [tx + 16, rail],
                    [tx + 16, ty - 10],
                ],
            )
    route = required.split(",")
    # Order hints by dependencies, including the inputs for stored states.
    checklist = []

    def visit(id):
        if id in checklist:
            return
        for o in d["latching_relays"]:
            if o["link_id"] == id:
                for k in o["required_links"]:
                    visit(k)
        if id in ("up", "down") and "power" in roles:
            visit("power")
        if id == "weight" and "tank" in roles:
            visit("dry")
        checklist.append(id)

    for id in route:
        visit(id)
    d["hint_route"] = checklist
    d["hint_notes"] = {
        s: [
            instructions.get(s, "Check the illuminated line."),
            instructions.get(s, "Trace the cable."),
            instructions.get(s, "Return to the control."),
        ]
        for s in checklist
    }
    steps = [instructions[s] for s in checklist if s in instructions]
    d["solution_steps"] = steps
    d["subtitle"] = steps[0] if steps else intro
    d["npcs"][0]["dialogue"] = [
        title + ". " + JOKES[(n - 25) % len(JOKES)],
        steps[0],
        steps[-1],
    ]

    # Route the visible wiring to the destination, including the final gate.
    door = d["doors"][0]
    for idx, signal in enumerate(route):
        if signal not in links:
            continue
        sx, sy = links[signal]
        tx, ty = door["x"] + 8, door["y"] + 60
        rail = max(sy, ty) + 22 + idx * 7
        a(
            "cables",
            link_id=signal,
            points=[[sx, sy - 12], [sx, rail], [tx, rail], [tx, ty]],
        )
    if n in (29, 30, 37, 38, 59, 65, 69, 74, 79):
        x, y, w = pos[-2]
        disable = route[0]
        a(
            "lasers",
            x=x + w - 65,
            y=y - 162,
            dir=[0, 1],
            max_length=155,
            disabled_by=[disable],
        )
    if n in (53, 56, 58, 60, 75, 77):
        for belt in d["conveyors"]:
            if "bus" in roles:
                belt.update(speed=-85, reversed_by="A")
    if ch == 7 or n in (72, 76, 79):
        # Replace exposed stepping stones with timed, recoverable broken decking.
        stones = d["one_way_platforms"]
        targets = stones[::2]
        for stone in targets:
            stones.remove(stone)
            a("collapsing_platforms", **stone, delay=0.42 + (n % 3) * 0.06, respawn=2.4)
        if not targets:
            x, y, w = pos[0]
            a(
                "collapsing_platforms",
                id="broken_lip",
                x=x + w + 12,
                y=y - 12,
                w=69,
                h=16,
                delay=0.44,
                respawn=2.4,
            )
    if n in (30, 35, 40, 45, 50, 60, 70, 75):
        x, y, w = pos[-1]
        a("npcs", id="ada", x=x + 44, y=y)
    d["chapter"] = ch
    d["theme"] = theme
    d["topology"] = topology
    d["collectibles"][0]["id"] = f"log_{n:02}"
    if n == 41:
        for vent in d["steam_vents"]:
            vent["disabled_by"] = ["dry"]
    return d


if __name__ == "__main__":
    import sys
    if "--force-legacy" not in sys.argv:
        raise SystemExit("Legacy template generator would erase the redesigned 25-79 files. "
                         "Run tools/build_late_campaign.py instead, or pass --force-legacy knowingly.")
    for plan in json.loads(Path(__file__).with_name("room_plans.json").read_text()):
        data = room(plan)
        (LEVELS / f"level_{plan['number']:02}.json").write_text(
            json.dumps(data, indent=2) + "\n"
        )
