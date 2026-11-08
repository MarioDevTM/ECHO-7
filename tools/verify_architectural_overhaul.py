from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.visuals.scene_renderer import _subtract_intervals


def test_autotile_interval_subtraction() -> None:
    # Full coverage removes top deck cap completely (no stripe inside stacked walls/piers)
    assert _subtract_intervals(100, 300, [(100, 300)]) == []
    # Partial middle coverage by a 40px pillar splits the exposed walkable deck into left & right ledges
    assert _subtract_intervals(100, 300, [(180, 220)]) == [(100, 180), (220, 300)]
    print("PASS: Neighbor-aware interval subtraction auto-tiling math verified.")


def test_architectural_levels() -> None:
    total_before = 0
    total_after = 0
    for n in range(25, 81):
        d = json.loads((ROOT / f"data/levels/level_{n:02d}.json").read_text(encoding="utf-8"))
        meta = d.get("architectural_overhaul_v2")
        assert meta is not None, f"Level {n:02d} missing architectural_overhaul_v2 metadata"
        assert len(d["tiles"]) >= meta["original_tile_count"], f"Level {n:02d} lost tiles"
        total_before += meta["original_tile_count"]
        total_after += meta["final_tile_count"]

        # Verify spawn and exit never collide with solid tiles
        sx, sy = d["spawn"]
        ex, ey = d["exit"]
        for t in d["tiles"]:
            tx, ty, tw, th = t
            assert not (sx < tx + tw and sx + 26 > tx and sy < ty + th and sy + 46 > ty), f"Spawn collision in {n}"
            assert not (ex < tx + tw and ex + 48 > tx and ey < ty + th and ey + 80 > ty), f"Exit collision in {n}"

    assert total_after > total_before, "Architectural overhaul did not add solid structure!"
    print(f"PASS: Levels 25-80 solid architecture verified ({total_before} -> {total_after} solid blocks).")


def main() -> None:
    test_autotile_interval_subtraction()
    test_architectural_levels()
    for script in (
        "tools/check_level_schema_offline.py",
        "tools/check_level_dependencies_static.py",
        "tools/check_remodel_integrity.py",
        "tools/check_pixel_environment_offline.py",
    ):
        p = ROOT / script
        if p.exists():
            res = subprocess.run([sys.executable, str(p)], cwd=str(ROOT), capture_output=True, text=True)
            assert res.returncode == 0, f"{script} failed:\n{res.stdout}\n{res.stderr}"
            print(f"PASS: {script} -> {res.stdout.strip().splitlines()[0]}")


if __name__ == "__main__":
    main()
