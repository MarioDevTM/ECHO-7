"""Dependency-free verification for a release when pygame-ce cannot be executed."""
from pathlib import Path
import ast,json,wave,zipfile,sys
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
LEVELS=ROOT/'data'/'levels'
NAME=['Awakening','Mechanical Depths','Power Grid','Optical Works','Flood Control','Furnace','Broken Spire','Surface Breach']

def validate(original=None):
    fails=[]
    levels=sorted(LEVELS.glob('level_*.json'))
    if len(levels)!=80:fails.append(f'{len(levels)} rooms instead of 80')
    for n in range(1,81):
        p=LEVELS/f'level_{n:02d}.json'
        if not p.exists():fails.append(f'level {n} missing');continue
        d=json.loads(p.read_text())
        if d.get('chapter')!=(n-1)//10+1:fails.append(f'chapter mismatch level {n}')
        if not d.get('tiles'):fails.append(f'no terrain level {n}')
    if original:
        with zipfile.ZipFile(original) as z:
            for n in range(1,25):
                p=LEVELS/f'level_{n:02d}.json'
                if p.read_bytes()!=z.read(f'ECHO-7/data/levels/level_{n:02d}.json'):
                    fails.append(f'level {n} modified')
            for py in ('src/core/settings.py','src/systems/collision.py'):
                if (ROOT/py).read_bytes()!=z.read('ECHO-7/'+py):fails.append(f'{py} modified')
    for n in range(1,9):
        p=ROOT/f'data/art/backgrounds/chapter_{n:02d}.png'
        if not p.exists():fails.append(f'chapter {n} background missing')
        else:
            with Image.open(p) as img:
                if img.size !=(1280,720):fails.append(f'wrong backdrop dimensions chapter {n}')
        samples=[]
        for layer in ('quiet','rhythm'):
            p=ROOT/f'data/music/chapter_{n}_{layer}.wav'
            if not p.exists():fails.append(f'chapter {n} {layer} missing');continue
            with wave.open(str(p)) as w:
                if (w.getnchannels(),w.getsampwidth(),w.getframerate())!=(1,2,22050):
                    fails.append(f'incompatible WAV chapter {n} {layer}')
                samples.append(w.getnframes())
        if len(samples)==2 and samples[0]!=samples[1]:fails.append(f'chapter {n} loop layers out of sync')
        if not (ROOT/f'soundtrack_previews/Chapter_{n:02d}_preview.ogg').exists():
            fails.append(f'preview OGG missing chapter {n}')
    for state,num in [('idle',2),('run',4),('jump',1),('fall',1),('land',1),('interact',1),('death',1)]:
        for i in range(num):
            p=ROOT/f'data/art/player/{state}_{i}.png'
            if not p.exists():fails.append(f'robot frame missing {p.name}');continue
            with Image.open(p) as img:
                if img.size!=(36,56):fails.append(f'robot frame size invalid {p.name}')
    for p in ROOT.rglob('*.py'):
        try:ast.parse(p.read_text(encoding='utf-8'))
        except SyntaxError as exc:fails.append(f'Python syntax invalid {p}:{exc}')
    print(f'Checked 80 levels, 8 environments, 16 adaptive tracks, 8 previews, 11 astronaut sprites, and Python syntax.')
    if fails:
        for f in fails: print('FAIL:',f)
        return 1
    print('PASS: all dependency-free static release checks.')
    print('NOT RUN: pygame visual, physics, UI and audio-device integration tests.')
    return 0

if __name__=='__main__':sys.exit(validate(sys.argv[1] if len(sys.argv)>1 else None))
