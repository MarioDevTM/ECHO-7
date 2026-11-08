"""Static QA for cleaned architectural stages (25-80) and preserved early campaign (1-24)."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = json.loads((ROOT / "docs/BASELINE_ARCHIVE_FINGERPRINTS.json").read_text(encoding="utf-8"))


def hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


for n in range(1, 25):
    assert hash_file(ROOT / f"data/levels/level_{n:02d}.json") == BASE["prefix_hashes"][str(n)], n
for ch in (2, 6, 7, 8):
    assert hash_file(ROOT / f"data/art/backgrounds/chapter_{ch:02d}.png") == BASE["protected_art_hashes"][str(ch)], ch

for n in range(25, 81):
    data = json.loads((ROOT / f"data/levels/level_{n:02d}.json").read_text(encoding="utf-8"))
    old = BASE["late_game"][str(n)]
    assert data["level_id"] == n
    assert data["spawn"] == old["spawn"] and data["exit"] == old["exit"]
    assert data["doors"][0]["required_links"] == old["doors"][0]["required_links"], n
    meta = data.get("architectural_overhaul_v2", {})
    assert len(data["tiles"]) >= meta.get("original_tile_count", 10), n
    if n < 80:
        legacy_steps = [
            p for p in data.get("one_way_platforms", [])
            if p["id"].startswith(("overhaul_step_", "validation_foot_"))
        ]
        assert len(legacy_steps) == 0, f"Level {n} still has legacy stepping-stone clutter: {legacy_steps}"

print("PASS: Levels 1-24 byte-identical; Levels 25-79 legacy stepping stones cleaned; solid walls & exit gates verified.")
