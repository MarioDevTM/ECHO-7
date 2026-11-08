"""Rebuild and verify the updated 25–80 campaign and five-act Level 80 finale.

Uses the definitive, repeatable 25–80 finale overhaul rather than the older
cleanup or step-injection scripts, so new terrain is not accidentally undone.
"""
from __future__ import annotations
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = Path(__file__).resolve().parent


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true", help="Audit level cleanup without writing files")
    args = ap.parse_args()

    cmd = [sys.executable, str(TOOLS / "rebuild_finale_and_late_campaign.py")]
    if args.dry_run:
        cmd.append("--dry-run")
    subprocess.run(cmd, cwd=str(ROOT), check=True)

    for script in (
        "check_level_schema_offline.py",
        "check_level_dependencies_static.py",
        "check_background_clarity.py",
        "check_pixel_environment_offline.py",
        "check_finale_overhaul.py",
        "check_platform_pruning.py",
        "check_focused_polish.py",
    ):
        p = TOOLS / script
        if p.exists():
            print("RUN", script, flush=True)
            subprocess.run([sys.executable, str(p)], cwd=str(ROOT), check=True)


if __name__ == "__main__":
    main()
