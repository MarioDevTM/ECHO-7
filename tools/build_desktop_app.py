"""Build a desktop application whose executable icon is the ECHO-7 player's face.

Optional developer tool. Requires PyInstaller installed on the target OS.
Run: python tools/build_desktop_app.py
The player-head icon applies to the executable (Windows .exe) and app window,
not to any in-game menu or progress panel.
"""
from __future__ import annotations
import os
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ICON=ROOT/'data/art/ui/echo7_icon.ico' if sys.platform=='win32' else ROOT/'data/art/ui/echo7_icon.png'


def main():
    if not ICON.is_file():
        raise SystemExit(f'Application icon missing: {ICON}')
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        raise SystemExit('Install the build tool first: python -m pip install pyinstaller') from None

    args=[sys.executable,'-m','PyInstaller','--noconfirm','--clean','--onefile',
          '--windowed','--name','ECHO-7',f'--icon={ICON}',
          '--paths',str(ROOT)]
    for directory in ('data','soundtrack_previews'):
        source=ROOT/directory
        if source.exists():
            args.extend(['--add-data',str(source)+os.pathsep+directory])
    args.append(str(ROOT/'main.py'))
    print('Building ECHO-7 desktop application; icon:',ICON)
    subprocess.run(args,cwd=ROOT,check=True)
    print('Built desktop application in:',ROOT/'dist')


if __name__=='__main__':main()
