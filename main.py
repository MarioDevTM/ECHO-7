import asyncio
import os
import sys
from pathlib import Path


def get_root_dir() -> Path:
    """Resolve the read-only bundle/asset root across source, PyInstaller, and Pygbag."""
    if getattr(sys, "frozen", False):
        # PyInstaller >= 6.0 places bundled data in sys._MEIPASS (_internal/)
        if hasattr(sys, "_MEIPASS"):
            meipass = Path(sys._MEIPASS)
            if (meipass / "data").exists():
                return meipass
        exe_dir = Path(sys.executable).resolve().parent
        if (exe_dir / "data").exists():
            return exe_dir
        if (exe_dir / "_internal" / "data").exists():
            return exe_dir / "_internal"
        return exe_dir
    return Path(__file__).resolve().parent


def get_user_dir() -> Path:
    """Resolve a writable directory for logs and save files next to the executable."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


ROOT_DIR = get_root_dir()
USER_DIR = get_user_dir()

# Ensure the project root is on sys.path and set as working directory
# so relative paths inside src/ (like "data/...") resolve from anywhere.
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    os.chdir(ROOT_DIR)
except OSError:
    pass


async def async_main() -> None:
    from tools.check_runtime_assets import check_runtime_assets

    # Also works when pygame isn't installed, unlike the live game renderer.
    if "--check-assets" in sys.argv:
        errors = check_runtime_assets(ROOT_DIR)
        if errors:
            for error in errors:
                print("ASSET WARNING:", error)
        else:
            print("PASS: required images, soundtrack files and all 80 JSON levels are present.")
        sys.exit(0)

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
        print("Note: Some static assets were not found (using procedural fallback):", file=sys.stderr)
        for error in errors:
            print(" - " + error, file=sys.stderr)

    # Persist a useful traceback if the desktop application closes unexpectedly.
    # Re-raise rather than hiding errors or pretending that game startup worked.
    try:
        from src.core.game import Game
        game = Game()
        if hasattr(game, "run_async"):
            await game.run_async()
        else:
            game.run()
    except Exception:
        import traceback
        from datetime import datetime, timezone
        report = (
            "ECHO-7 crash on " + datetime.now(timezone.utc).isoformat()
            + "\nPython " + sys.version + "\n\n" + traceback.format_exc()
        )
        try:
            log = USER_DIR / "logs" / "last_crash.log"
            log.parent.mkdir(parents=True, exist_ok=True)
            log.write_text(report, encoding="utf-8")
            print("ECHO-7 crash report: " + str(log), file=sys.stderr)
        except OSError:
            print("ECHO-7 could not write the crash report.", file=sys.stderr)
        raise


def main() -> None:
    asyncio.run(async_main())


if __name__ == "__main__":
    main()