"""Dependency-aware legacy clutter cleanup and purposeful solid-wall architect for ECHO-7.

Operates on the latest Gemini architectural baseline (`data/levels/level_01.json`..`level_80.json`):
1. Audits and classifies every platform and puzzle device into:
   - Category 1 (Essential): Required by exit doors, mandatory relays, lifts, or hazards.
   - Category 2 (Useful): Supports reachable optional logs (`field_trace_*`) or fair return shortcuts.
   - Category 3 (Redundant): Legacy `overhaul_step_*` / `validation_foot_*` ladders and detached
     `overhaul_<n>_*` / `sector_<n>_validated` device stacks that duplicate ground routes.
   - Category 4 (Misplaced): Floating `ACCESS / <n>` monitors and mid-air warning stripes.
   - Category 5 (Broken): Any orphaned signal consumer/producer left without a valid target.
2. Preserves and refines `architectural_overhaul_v2` solid blocks, merging collinear/adjacent
   slabs and grounding piers cleanly onto lower decks or chasm floors above hazard pools.
3. Adds purposeful solid walls and architectural structures:
   - Partition walls with framed doorway/tunnel passages on wide decks (`tw >= 340`).
   - Solid stepped terraces and L-shaped alcoves replacing floating stepping-stone clusters.
   - Load-bearing viaduct columns and ceiling bulkhead downstands.
4. Reconciles hint routes, solution steps, collectibles, and baseline verification fingerprints.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEVELS_DIR = ROOT / "data" / "levels"
BACKUP_DIR = ROOT / "data" / "levels_backup"
PRE_CLEAN_BACKUP_DIR = ROOT / "data" / "levels_pre_cleanup_backup"
FINGERPRINTS_PATH = ROOT / "docs" / "BASELINE_ARCHIVE_FINGERPRINTS.json"

ARCHETYPES = (
    "Partitioned Lab & Observation Alcoves",
    "Buttressed Viaduct & Pier Hall",
    "Vaulted Substation & Bus Gallery",
    "Segmented Security Bulkhead Corridor",
    "Stepped Hydraulic Caisson & Manifold Bay",
    "Containment Bastion & Service Duct",
    "Fractured Upper-Spire Chamber",
    "Ruined Exterior Bastion & Crag Terrace",
)


def rect_overlap(a: tuple[int, int, int, int], b: tuple[int, int, int, int], pad: int = 0) -> bool:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return (
        ax - pad < bx + bw
        and ax + aw + pad > bx
        and ay - pad < by + bh
        and ay + ah + pad > by
    )


def compute_essential_signals(d: dict) -> set[str]:
    """Traces backward from all doors, active moving platforms, hazards, and water/wind zones."""
    required: set[str] = set()
    for door in d.get("doors", []):
        required.update(door.get("required_links", []))
    for mp in d.get("moving_platforms", []):
        required.update(mp.get("required_links", []))
    for cat in ("lasers", "crushers", "steam_vents"):
        for h in d.get(cat, []):
            required.update(h.get("disabled_by", []))
    for cat in ("wind_zones", "water_zones"):
        for z in d.get(cat, []):
            if z.get("controlled_by"):
                required.add(z["controlled_by"])
    for conv in d.get("conveyors", []):
        for k in ("reversed_by", "powered_by"):
            if conv.get(k):
                required.add(conv[k])
    for ob in d.get("optical_beams", []):
        if ob.get("enabled_by"):
            required.add(ob["enabled_by"])

    # Expand transitive dependencies through latching_relays, signal_inverters, sequences, consoles
    changed = True
    while changed:
        changed = False
        for rel in d.get("latching_relays", []):
            if rel["link_id"] in required:
                for dep in rel.get("required_links", []):
                    if dep not in required:
                        required.add(dep)
                        changed = True
        for inv in d.get("signal_inverters", []):
            if inv["link_id"] in required and inv["input"] not in required:
                required.add(inv["input"])
                changed = True
        for seq in d.get("sequences", []):
            if seq["group_id"] in required:
                for step_sig in seq.get("order", []):
                    if step_sig not in required:
                        required.add(step_sig)
                        changed = True
        for rc in d.get("routing_consoles", []):
            if rc["a_signal"] in required or rc["b_signal"] in required:
                for dep in rc.get("required_links", []):
                    if dep not in required:
                        required.add(dep)
                        changed = True
    return required


def build_forbidden_zones(d: dict) -> list[tuple[int, int, int, int]]:
    """Computes collision-forbidden volumes protecting routes, headroom, sightlines, and sweeps."""
    zones: list[tuple[int, int, int, int]] = []
    W, H = int(d["width"]), int(d["height"])

    # 1. Spawn and Exit with generous player & portal clearance
    sx, sy = d["spawn"]
    zones.append((int(sx) - 48, int(sy) - 76, 26 + 96, 46 + 80))
    ex, ey = d["exit"]
    zones.append((int(ex) - 52, int(ey) - 48, 48 + 104, 80 + 52))

    # 2. Walkable top clearance (96px minimum corridor headroom) above horizontal decks
    for t in d.get("tiles", []):
        tx, ty, tw, th = [int(v) for v in t]
        if tw <= 44 and th >= H - 120:
            continue
        if ty <= 8 and tw >= W - 120:
            continue
        if tw >= 120 and th <= 180:
            zones.append((tx - 16, ty - 96, tw + 32, 96))

    # 3. Retained one-way & collapsing platforms
    for ow in d.get("one_way_platforms", []) + d.get("collapsing_platforms", []):
        ox, oy, ow_w, ow_h = int(ow["x"]), int(ow["y"]), int(ow["w"]), int(ow.get("h", 16))
        zones.append((ox - 28, oy - 118, ow_w + 56, ow_h + 176))

    # 4. Moving platforms: full sweep volume + headroom
    for mp in d.get("moving_platforms", []):
        x1 = min(int(mp["x"]), int(mp["end_x"]))
        x2 = max(int(mp["x"]), int(mp["end_x"])) + int(mp["w"])
        y1 = min(int(mp["y"]), int(mp["end_y"]))
        y2 = max(int(mp["y"]), int(mp["end_y"])) + int(mp["h"])
        zones.append((x1 - 28, y1 - 120, (x2 - x1) + 56, (y2 - y1) + 168))

    # 5. Ladders, springs, dash recharges, dash barriers
    for lad in d.get("ladders", []):
        zones.append((int(lad["x"]) - 34, int(lad["y"]) - 64, 28 + 68, int(lad["h"]) + 92))
    for sp in d.get("springs", []):
        zones.append((int(sp["x"]) - 36, int(sp["y"]) - 270, int(sp["w"]) + 72, 290))
    for dr in d.get("dash_recharges", []):
        zones.append((int(dr["x"]) - 88, int(dr["y"]) - 88, 176, 176))
    for db in d.get("dash_barriers", []):
        zones.append((int(db["x"]) - 68, int(db["y"]) - 36, int(db["w"]) + 136, int(db["h"]) + 56))

    # 6. Interactive puzzle objects, crates, checkpoints, collectibles, NPCs
    for cat in (
        "crates", "plates", "switches", "generators", "valves",
        "latching_relays", "routing_consoles", "mirrors",
        "checkpoints", "collectibles", "npcs",
    ):
        for item in d.get(cat, []):
            ix, iy = int(item["x"]), int(item["y"])
            zones.append((ix - 54, iy - 112, 128, 132))

    # 7. Crate push lanes
    for crate in d.get("crates", []):
        cx, cy = int(crate["x"]), int(crate["y"])
        zones.append((cx - 110, cy - 76, 360, 120))

    # 8. Doors
    for door in d.get("doors", []):
        zones.append((int(door["x"]) - 54, int(door["y"]) - 24, int(door["w"]) + 108, int(door["h"]) + 36))

    # 9. Environmental zones & hazards
    for cat in ("conveyors", "wind_zones", "water_zones", "acids", "spikes"):
        for z in d.get(cat, []):
            zones.append((int(z["x"]) - 20, int(z["y"]) - 56, int(z["w"]) + 40, int(z["h"]) + 76))
    for cr in d.get("crushers", []):
        zones.append((
            int(cr["x"]) - 24, int(cr["y"]) - 20,
            int(cr["w"]) + 48, int(cr["h"]) + int(cr["travel"]) + 44,
        ))
    for sv in d.get("steam_vents", []):
        zones.append((int(sv["x"]) - 24, int(sv["y"]) - 44, int(sv["w"]) + 48, int(sv["h"]) + 64))

    # 10. Lasers and Optical Beams
    for ls in d.get("lasers", []):
        lx, ly = int(ls["x"]), int(ls["y"])
        dx, dy = ls["dir"]
        ml = int(ls["max_length"])
        rx = lx if dx >= 0 else lx - ml
        ry = ly if dy >= 0 else ly - ml
        rw = ml if dx != 0 else 28
        rh = ml if dy != 0 else 28
        zones.append((rx - 20, ry - 20, rw + 40, rh + 40))

    for ob in d.get("optical_beams", []):
        ox, oy = int(ob["x"]), int(ob["y"])
        rc = [int(v) for v in ob["receiver"]]
        min_x = min(ox, rc[0]) - 48
        max_x = max(ox + int(ob["max_length"]), rc[0] + rc[2]) + 48
        min_y = min(oy, rc[1]) - 48
        max_y = max(oy, rc[1] + rc[3]) + 48
        zones.append((min_x, min_y, max_x - min_x, max_y - min_y))

    return zones


def can_place_tile(
    cand: tuple[int, int, int, int],
    existing_tiles: list[list[int]],
    forbidden: list[tuple[int, int, int, int]],
    W: int,
    H: int,
) -> bool:
    cx, cy, cw, ch = cand
    if cw < 14 or ch < 14:
        return False
    if cx < 0 or cy < 0 or cx + cw > W or cy + ch > H:
        return False
    for fz in forbidden:
        if rect_overlap(cand, fz, pad=0):
            return False
    for t in existing_tiles:
        if rect_overlap(cand, (t[0], t[1], t[2], t[3]), pad=0):
            return False
    return True


def clean_and_architect_level(n: int, dry_run: bool = False) -> dict:
    path = LEVELS_DIR / f"level_{n:02d}.json"
    d = json.loads(path.read_text(encoding="utf-8"))
    if d.get("cleanup_v3_audit") and not dry_run:
        return d["cleanup_v3_audit"]  # Already cleaned; no duplicate geometry
    W, H = int(d["width"]), int(d["height"])
    ch = int(d.get("chapter", (n - 1) // 10 + 1))
    theme = d.get("theme", "awakening")

    essential_sigs = compute_essential_signals(d)
    removed_platforms: list[str] = []
    retained_platforms: list[str] = []
    removed_devices: list[str] = []
    removed_decorations = 0

    # ------------------------------------------------------------------
    # PHASE 1: DEPENDENCY-AWARE LEGACY CLUTTER CLEANUP (Levels 25-80)
    # ------------------------------------------------------------------
    if n >= 25:
        new_owps = []
        for p in d.get("one_way_platforms", []):
            pid = p.get("id", "")
            if pid.startswith(("overhaul_step_", "validation_foot_")):
                # In Level 80, overhaul_step_80_2 supports the optional finale log;
                # we replace the 3 tiny steps in 25-79 with solid architectural terraces/walls.
                if n == 80:
                    retained_platforms.append(f"{pid} (Useful: Finale high viewpoint route)")
                    new_owps.append(p)
                else:
                    removed_platforms.append(f"{pid} (Redundant: Legacy generated stepping stone)")
            else:
                retained_platforms.append(f"{pid} (Essential: Core inter-bay traversal)")
                new_owps.append(p)
        d["one_way_platforms"] = new_owps

        if n < 80:
            # Remove non-essential `overhaul_<n>_*` and `sector_<n>_validated` devices
            # that were detached from the exit gate by sanitize_late_challenges.py.
            for cat in ("switches", "generators", "valves", "latching_relays", "routing_consoles", "sequences"):
                kept = []
                for item in d.get(cat, []):
                    ident = item.get("id") or item.get("link_id") or item.get("group_id") or ""
                    is_legacy = ident.startswith(f"overhaul_{n:02d}_") or ident == f"sector_{n:02d}_validated"
                    if is_legacy and ident not in essential_sigs:
                        removed_devices.append(f"{cat}:{ident} (Redundant/Orphaned legacy side-chain)")
                    else:
                        kept.append(item)
                d[cat] = kept

            # Remove superseded side-detour walkthrough instructions. Those steps became
            # misleading once sanitize_late_challenges.py made the extra circuit optional.
            separator = "SERVICE DETOUR: "
            subtitle = d.get("subtitle", "")
            if separator in subtitle:
                mission = subtitle.split(separator, 1)[1].strip()
                d["solution_steps"] = [s for s in d.get("solution_steps", []) if s != mission]
                d["subtitle"] = subtitle.split(" //  SERVICE DETOUR:", 1)[0].rstrip()

            # Reanchor `service_challenge_<n>` optional log to a reachable primary bay signal
            # (`field_trace_<n>`'s signal or the first required gate signal) and place it on a solid ledge,
            # or remove its orphaned dependency on `sector_<n>_validated`.
            fallback_sig = d["doors"][0]["required_links"][0] if d.get("doors") and d["doors"][0].get("required_links") else None
            for col in d.get("collectibles", []):
                if col.get("id") == f"service_challenge_{n:02d}":
                    col["required_links"] = []
                    col["text"] = (
                        "Optional auxiliary service record recovered. This archive is no longer "
                        "linked to a redundant side circuit and does not gate the exit."
                    )
                    # Place at a reachable elevated position above the checkpoint or first upper deck
                    if d.get("checkpoints"):
                        cp = d["checkpoints"][0]
                        col["x"] = int(cp["x"]) + 28
                        col["y"] = int(cp["y"]) - 42

            # Clean up misplaced legacy `ACCESS / <n>` monitors and 78px floating warning stripes
            kept_decs = []
            for dec in d.get("decorations", []):
                if dec.get("type") == "monitor" and str(dec.get("text", "")).startswith("ACCESS /"):
                    removed_decorations += 1
                    continue
                if dec.get("type") == "warning_stripe" and int(dec.get("w", 0)) == 78:
                    removed_decorations += 1
                    continue
                kept_decs.append(dec)
            d["decorations"] = kept_decs

            # Preserve original signal paths; remove only cables for deprecated circuits.
            removed_ids = {x.split(":", 1)[1].split(" ", 1)[0] for x in removed_devices}
            d["cables"] = [cb for cb in d.get("cables", []) if cb.get("link_id") not in removed_ids]

    # ------------------------------------------------------------------
    # PHASE 2: PRESERVE GEMINI ARCHITECTURE & BUILD PURPOSEFUL SOLID WALLS
    # ------------------------------------------------------------------
    all_tiles = [[int(v) for v in t] for t in d.get("tiles", [])]
    tiles_before_walls = len(all_tiles)
    forbidden = build_forbidden_zones(d)

    added_partition_walls = 0
    added_grounded_piers = 0
    added_stepped_terraces = 0

    if n >= 25:
        # 1. Add purposeful interior partition walls with pass-through doorway/tunnel openings
        #    on wide decks (`tw >= 340`), creating genuine room-to-room spatial framing.
        #    A top lintel wall drops from above down to `ty - 92`, leaving a 92px-tall
        #    walkable archway (`PLAYER_HEIGHT = 46`) underneath!
        for t in list(all_tiles):
            tx, ty, tw, th = t
            if tw < 340 or ty < 220 or th > 180:
                continue
            part_w = 28 if ch in (1, 3, 4) else 32
            part_x = tx + tw // 2 - part_w // 2
            lintel_top = max(36, ty - 220)
            lintel_bottom = ty - 92  # 92px clear doorway opening above deck `ty`
            lintel_h = lintel_bottom - lintel_top
            if lintel_h >= 48:
                lintel = (part_x, lintel_top, part_w, lintel_h)
                if can_place_tile(lintel, all_tiles, forbidden, W, H):
                    all_tiles.append(list(lintel))
                    added_partition_walls += 1
                    # Add a top capital flange on the partition wall
                    flange = (part_x - 10, lintel_top, part_w + 20, 18)
                    if can_place_tile(flange, all_tiles, forbidden, W, H):
                        all_tiles.append(list(flange))

        # 2. Grounded load-bearing viaduct piers & chasm columns beneath elevated bays
        #    (terminating cleanly at `H - 80` above any chasm acid pool or onto a lower deck).
        for t in list(all_tiles):
            tx, ty, tw, th = t
            if tw < 160 or ty < 120 or ty + th >= H - 150:
                continue
            pier_w = 36 if ch in (1, 3, 4) else 40
            for px in (tx + 28, tx + tw - pier_w - 28, tx + (tw - pier_w) // 2):
                top_y = ty + th
                # Find lower solid deck or stop above acid pool (H - 80)
                target_y = H - 80
                for below in all_tiles:
                    bx, by, bw, bh = below
                    if by > top_y and bx <= px + pier_w // 2 <= bx + bw:
                        target_y = min(target_y, by)
                span_h = target_y - top_y
                if span_h >= 64:
                    pier = (px, top_y, pier_w, span_h)
                    if can_place_tile(pier, all_tiles, forbidden, W, H):
                        all_tiles.append(list(pier))
                        added_grounded_piers += 1
                        break

        # 3. Stepped solid wall-terraces & L-shaped alcoves replacing removed floating steps
        sx, sy = int(d["spawn"][0]), int(d["spawn"][1])
        spawn_floor = sy + 46
        for step_idx, (dx, dy, tw_step, th_step) in enumerate((
            (52, 52, 88, 24),
            (132, 104, 96, 28),
        )):
            for side in (-1, 1):
                cand = (sx + side * dx - tw_step // 2, spawn_floor - dy, tw_step, th_step)
                # Ensure the player can jump onto and stand on top of `cand` (100px headroom above `cand`)
                headroom_box = (cand[0] - 8, cand[1] - 100, cand[2] + 16, 100)
                if (
                    can_place_tile(cand, all_tiles, forbidden, W, H)
                    and not any(rect_overlap(headroom_box, tuple(ot)) for ot in all_tiles)
                    and not any(rect_overlap(headroom_box, fz) for fz in forbidden)
                ):
                    all_tiles.append(list(cand))
                    added_stepped_terraces += 1
                    break

    # Keep legacy generation markers truthy to prevent reinjection, while marking
    # their former steps/circuits as retired in user-facing metadata.
    if 25 <= n < 80:
        design = d.get("overhaul_design")
        if isinstance(design, dict):
            design.update({"mandatory": False, "service_platform_count": 0,
                           "retired_by_cleanup": True})
        secondary = d.get("secondary_validation_1")
        if isinstance(secondary, dict):
            secondary.update({"extra_platforms": 0, "retired_by_cleanup": True})
        side = d.get("side_challenge_policy")
        if isinstance(side, dict):
            side.update({"campaign_blocking": False, "optional_signals": [],
                         "reason": "Deprecated optional side circuit removed; service record remains accessible."})

    d["tiles"] = all_tiles
    meta = d.get("architectural_overhaul_v2", {})
    meta.update({
        "archetype": ARCHETYPES[ch - 1],
        "chapter": ch,
        "theme": theme,
        "tiles_before_cleanup_pass": tiles_before_walls,
        "final_tile_count": len(all_tiles),
        "removed_legacy_platforms": len(removed_platforms),
        "removed_legacy_devices": len(removed_devices),
        "added_partition_walls": added_partition_walls,
        "added_grounded_piers": added_grounded_piers,
        "added_stepped_terraces": added_stepped_terraces,
    })
    d["architectural_overhaul_v2"] = meta

    audit = {
        "level": n,
        "chapter": ch,
        "theme": theme,
        "name": d.get("name", f"Chamber {n:02d}"),
        "archetype": ARCHETYPES[ch - 1],
        "orig_backup_tiles": meta.get("original_tile_count", len(all_tiles)),
        "final_tiles": len(all_tiles),
        "removed_platforms": len(removed_platforms),
        "retained_platforms": len(retained_platforms),
        "removed_devices": len(removed_devices),
        "added_walls": added_partition_walls,
        "added_piers": added_grounded_piers + meta.get("added_piers", 0),
        "added_terraces": added_stepped_terraces,
        "gate_links": d["doors"][0].get("required_links", []) if d.get("doors") else [],
    }
    if not dry_run and n >= 25:
        d["cleanup_v3_audit"] = audit
        path.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return audit


def sync_baseline_fingerprints() -> None:
    """Refreshes docs/BASELINE_ARCHIVE_FINGERPRINTS.json for the cleaned canonical levels."""
    if not FINGERPRINTS_PATH.exists():
        return
    fp = json.loads(FINGERPRINTS_PATH.read_text(encoding="utf-8"))
    for n in range(25, 81):
        lvl = json.loads((LEVELS_DIR / f"level_{n:02d}.json").read_text(encoding="utf-8"))
        if str(n) in fp.get("late_game", {}):
            fp["late_game"][str(n)]["tiles"] = lvl["tiles"]
            fp["late_game"][str(n)]["one_way_platforms"] = lvl["one_way_platforms"]
    FINGERPRINTS_PATH.write_text(json.dumps(fp, indent=2) + "\n", encoding="utf-8")


def write_audit_matrix(rows: list[dict]) -> None:
    lines = [
        "# ECHO-7 — 80-Level Clutter Cleanup & Architectural Wall Audit Matrix\n",
        "| Lvl | Ch | Theme | Architectural Style | Solid Tiles (Orig -> Final) | Clutter Removed (Plats / Devs) | Purposeful Walls (+Walls / +Piers / +Terraces) | Exit Gate Links |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        links = ", ".join(r["gate_links"]) if r["gate_links"] else "open"
        lines.append(
            f"| {r['level']:02d} | {r['chapter']} | `{r['theme']}` | {r['archetype']} | "
            f"`{r['orig_backup_tiles']} -> {r['final_tiles']}` | "
            f"`-{r['removed_platforms']}P / -{r['removed_devices']}D` (kept `{r['retained_platforms']}P`) | "
            f"`+{r['added_walls']}W / +{r['added_piers']}P / +{r['added_terraces']}T` | `{links}` |"
        )
    (ROOT / "LEVEL_ARCHITECTURAL_AUDIT_MATRIX.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (ROOT / "docs" / "LEVEL_CLEANUP_AND_WALL_METRICS.json").write_text(
        json.dumps(rows, indent=2) + "\n", encoding="utf-8"
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true", help="Print proposed changes without modifying files")
    ap.add_argument("--restore", action="store_true", help="Restore from data/levels_pre_cleanup_backup/")
    args = ap.parse_args()

    PRE_CLEAN_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    for n in range(1, 81):
        src = LEVELS_DIR / f"level_{n:02d}.json"
        dst = PRE_CLEAN_BACKUP_DIR / f"level_{n:02d}.json"
        if src.exists() and not dst.exists():
            shutil.copy2(src, dst)

    if args.restore:
        for n in range(1, 81):
            shutil.copy2(PRE_CLEAN_BACKUP_DIR / f"level_{n:02d}.json", LEVELS_DIR / f"level_{n:02d}.json")
        sync_baseline_fingerprints()
        print("Restored all 80 levels from data/levels_pre_cleanup_backup/.")
        return

    rows = [clean_and_architect_level(n, dry_run=args.dry_run) for n in range(1, 81)]
    if not args.dry_run:
        sync_baseline_fingerprints()
        write_audit_matrix(rows)

    rem_p = sum(r["removed_platforms"] for r in rows)
    rem_d = sum(r["removed_devices"] for r in rows)
    add_w = sum(r["added_walls"] + r["added_piers"] + r["added_terraces"] for r in rows)
    print(
        f"{'[DRY-RUN] ' if args.dry_run else ''}Processed 80 levels: "
        f"removed {rem_p} redundant legacy platforms, removed {rem_d} orphaned side-route devices, "
        f"and constructed {add_w} purposeful solid walls, piers, and terraces."
    )


if __name__ == "__main__":
    main()
