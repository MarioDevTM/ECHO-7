"""Optional Linux desktop launcher with the player's head as an OS application icon.

Run: python tools/install_linux_desktop_icon.py
Remove: python tools/install_linux_desktop_icon.py --uninstall
Requires an extracted ECHO-7 project that stays at the same path.
"""
from __future__ import annotations
import argparse
import os
import shutil
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
APPDATA=Path(os.environ.get('XDG_DATA_HOME',Path.home()/'.local/share'))
ICON=APPDATA/'icons/hicolor/256x256/apps/echo7.png'
DESKTOP=APPDATA/'applications/echo7.desktop'

def escape_desktop(s: str) -> str:
    return s.replace('\\','\\\\').replace('"','\\"').replace('$','\\$').replace('`','\\`')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--uninstall',action='store_true')
    args=parser.parse_args()
    if args.uninstall:
        DESKTOP.unlink(missing_ok=True)
        ICON.unlink(missing_ok=True)
        print('Removed the ECHO-7 Linux launcher and icon')
        return
    if sys.platform!='linux':
        raise SystemExit('This helper is only for Linux. Windows users should build with tools/build_desktop_app.py.')
    src=ROOT/'data/art/ui/echo7_icon.png'
    if not src.is_file():
        raise SystemExit('Missing application icon: '+str(src))
    ICON.parent.mkdir(parents=True,exist_ok=True)
    DESKTOP.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(src,ICON)
    # Desktop launcher executes the extracted project's main.py with the
    # same interpreter used to install the launcher.
    desktop='''[Desktop Entry]
Version=1.0
Type=Application
Name=ECHO-7
Comment=Abandoned Facility Puzzle Platformer
Exec="{python}" "{main}"
Path={cwd}
Icon=echo7
Terminal=false
Categories=Game;
'''.format(python=escape_desktop(sys.executable),main=escape_desktop(str(ROOT/'main.py')),
           cwd=str(ROOT))
    DESKTOP.write_text(desktop,encoding='utf-8')
    DESKTOP.chmod(0o644)
    print('Installed ECHO-7 desktop icon:',ICON)
    print('Installed application launcher:',DESKTOP)

if __name__=='__main__':main()
