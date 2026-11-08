"""Verify the eight chapter-specific far and mid procedural layers without SDL.

Requires Pillow. Does not constitute native Pygame runtime or aesthetic testing.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))
import offline_pygame_adapter as adapter
from src.visuals.pixel_environment import PixelEnvironment, archetype_for_level


def digest(surface) -> str:
    return hashlib.sha256(surface.im.tobytes()).hexdigest()


def main() -> None:
    environment = PixelEnvironment()
    far = []
    mid = []
    for chapter in range(1, 9):
        archetype = archetype_for_level((chapter - 1) * 10 + 1)
        f = environment._build_far_strip(chapter, archetype)
        far.append(digest(f))
        layer = adapter.pg.Surface((640, 360))
        environment._draw_mid_plane(layer, chapter, archetype, 0, 0, 0.0)
        mid.append(digest(layer))
    assert len(set(far)) == len(set(mid)) == 8, 'A chapter has duplicate visual layers'
    print('PASS: all 8 chapters have distinct far-silhouette and mid-parallax layers.')
    print('LIMITATION: Pillow-backed renderer does not validate actual Pygame/SDL frame behavior.')


if __name__ == '__main__':
    main()
