import sys
from pathlib import Path

# Ensure the project root is on sys.path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

def main() -> None:
    from tools.check_runtime_assets import check_runtime_assets
    # Also works when pygame isn't installed, unlike the live game renderer.
    if "--check-assets" in sys.argv:
        errors = check_runtime_assets(ROOT_DIR)
        if errors:
            for error in errors:
                print("ASSET ERROR:", error)
        else:
            print("PASS: required images, soundtrack files and all 80 JSON levels are present.")
        sys.exit(1 if errors else 0)

    # Optional CLI flag to verify all 80 levels without opening a window.
    if "--validate" in sys.argv:
        from src.levels.level_loader import LevelLoader
        loader = LevelLoader()
        report = loader.validate_all_levels()
        total_errors = sum(len(errs) for errs in report.values())
        for lvl_num, errs in sorted(report.items()):
            status = "OK" if not errs else f"ERRORS: {errs}"
            print(f"Level {lvl_num:02d}: {status}")
        sys.exit(0 if total_errors == 0 else 1)

    errors = check_runtime_assets(ROOT_DIR)
    if errors:
        print("Game assets are missing or invalid; cannot launch ECHO-7:", file=sys.stderr)
        for error in errors:
            print(" - " + error, file=sys.stderr)
        print("Extract the complete game archive, including data/art/.", file=sys.stderr)
        sys.exit(2)

    # Persist a useful traceback if the desktop application closes unexpectedly.
    # Re-raise rather than hiding errors or pretending that game startup worked.
    try:
        from src.core.game import Game
        game = Game()
        game.run()
    except Exception:
        import traceback
        from datetime import datetime, timezone
        report = (
            "ECHO-7 crash on " + datetime.now(timezone.utc).isoformat()
            + "\nPython " + sys.version + "\n\n" + traceback.format_exc()
        )
        try:
            log = ROOT_DIR / "logs" / "last_crash.log"
            log.parent.mkdir(parents=True, exist_ok=True)
            log.write_text(report, encoding="utf-8")
            print("ECHO-7 crash report: " + str(log), file=sys.stderr)
        except OSError:
            print("ECHO-7 could not write the crash report.", file=sys.stderr)
        raise


if __name__ == "__main__":
    main()