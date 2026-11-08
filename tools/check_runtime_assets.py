"""Minimal dependency-free validation of ECHO-7 runtime assets.

Does not validate gameplay or visual quality; those require pygame rendering.
"""
from __future__ import annotations
import json
import struct
from pathlib import Path

CHAPTERS = range(1, 9)
ESSENTIAL_ENV = (
    'platform_solid_long', 'terrain_wall_tile_steel', 'terrain_wall_tile_panel',
    'door_airlock_double', 'door_hazard_shutter', 'conveyor_belt',
    'water_surface_tile', 'crate_steel', 'console_cyan', 'laser_emitter_unit',
)
PLAYER_POSES = (
    'idle_0', 'run_0', 'jump_0', 'fall_0', 'death_0', 'dash_0',
    'climb_0', 'interact_0', 'crouch_0', 'wall_0',
)


def check_runtime_assets(root: Path) -> list[str]:
    root = Path(root)
    problems: list[str] = []
    def require(path: Path, png_size=None) -> None:
        rel = str(path.relative_to(root))
        if not path.is_file():
            problems.append(f"missing: {rel}")
            return
        if png_size is not None or path.suffix.lower() == '.png':
            try:
                with path.open('rb') as source:
                    header = source.read(24)
                if (len(header) < 24 or header[:8] != b'\x89PNG\r\n\x1a\n'
                        or header[12:16] != b'IHDR'):
                    raise ValueError('invalid PNG header')
                w, h = struct.unpack('>II', header[16:24])
                if png_size is not None and (w, h) != png_size:
                    raise ValueError(f'expected {png_size}, got {(w, h)}')
            except (OSError, ValueError) as exc:
                problems.append(f"invalid image: {rel} ({exc})")

    for ch in CHAPTERS:
        require(root / f'data/art/backgrounds/chapter_{ch:02d}.png', (1280,720))
        require(root / f'data/art/backgrounds/scenic/chapter_{ch:02d}_scenic.png', (1280,720))
        require(root / f'data/music/chapter_{ch}_quiet.wav')
        require(root / f'data/music/chapter_{ch}_rhythm.wav')
    for ch in (1, 3, 4, 5):
        require(root / f'data/art/backgrounds/pixel/chapter_{ch:02}_hero.png', (640, 360))
        for i in range(3):
            require(root / f'data/art/backgrounds/pixel/chapter_{ch:02}_module_{i}.png', (160, 360))
    require(root / 'data/music/surface_resolution.wav')
    for name in ESSENTIAL_ENV:
        require(root / f'data/art/environment/{name}.png')
    for pose in PLAYER_POSES:
        require(root / f'data/art/player/{pose}.png')

    decoration = root / 'data/art/environment/world_dressing.json'
    require(decoration)
    if decoration.is_file():
        try:
            data = json.loads(decoration.read_text(encoding='utf-8'))
            if not isinstance(data.get('levels'), dict):
                problems.append('world dressing levels must be an object')
        except (ValueError, OSError) as exc:
            problems.append(f'invalid decoration manifest: {exc}')

    files = sorted((root / 'data/levels').glob('level_*.json'))
    expected = {f'level_{i:02d}.json' for i in range(1, 81)}
    if {f.name for f in files} != expected:
        problems.append('required level files must be exactly level_01.json through level_80.json')
    for path in files:
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
            if not isinstance(data, dict) or 'theme' not in data:
                problems.append(f'invalid level data: {path.name}')
        except (ValueError, OSError) as exc:
            problems.append(f'cannot read {path.name}: {exc}')
    return problems


if __name__ == '__main__':
    root = Path(__file__).resolve().parents[1]
    errors = check_runtime_assets(root)
    if errors:
        print('FAIL:', *errors, sep='\n- ')
        raise SystemExit(1)
    print('PASS: required runtime art, audio, decoration manifest and all 80 level files present.')
