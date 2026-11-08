"""Static and optional native Pygame tests for the reference-driven renderer.

    python3 tools/check_procedural_backgrounds.py
    python3 tools/check_procedural_backgrounds.py --runtime

The static check is NOT evidence of a playable game. Native tests require pygame-ce.
"""
from __future__ import annotations
import ast
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def check_static() -> None:
    painter = (ROOT / 'src/visuals/pixel_environment.py').read_text(encoding='utf-8')
    renderer = (ROOT / 'src/visuals/scene_renderer.py').read_text(encoding='utf-8')
    level_mgr = (ROOT / 'src/levels/level_manager.py').read_text(encoding='utf-8')
    for text in (painter, renderer, level_mgr):
        ast.parse(text)
    assert 'pygame.image.load' not in painter
    assert '_pano_background' not in renderer
    assert 'pygame.image.load' not in renderer
    assert 'pixel_environment.draw' in renderer
    assert 'pixel_environment.menu_background' in renderer
    assert 'pixel_environment.set_level' in renderer
    assert 'signals=self.puzzle_manager.active_signals' in level_mgr
    assert 'powered=powered or' in renderer
    assert 'LOGICAL_W = VIRTUAL_WIDTH // SCALE' in painter
    levels = sorted((ROOT / 'data/levels').glob('level_??.json'))
    assert len(levels) == 80
    for i, file in enumerate(levels, 1):
        data = json.loads(file.read_text())
        assert data['level_id'] == i
        assert data['chapter'] == (i - 1) // 10 + 1
    assert len(list((ROOT / 'data/art/backgrounds').glob('chapter_??.png'))) == 8
    print('STATIC PASS: all 80 level files, chapter art preserved as reference, renderer integration')


def check_runtime() -> None:
    os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
    import pygame
    from unittest.mock import patch
    pygame.init()
    pygame.display.set_mode((1280, 720))
    sys.path.insert(0, str(ROOT))
    from src.visuals.pixel_environment import PixelEnvironment, screen_x, parallax_x
    from src.visuals.scene_renderer import SceneRenderer
    assert screen_x(760, 235) == 525
    assert parallax_x(760, 235, .4) == 666
    renderer = SceneRenderer()
    target = pygame.Surface((1280, 720))
    themes = ('awakening', 'mechanical', 'power', 'optical',
              'environmental', 'furnace', 'spire', 'surface')
    with patch.object(pygame.image, 'load', side_effect=AssertionError('Unexpected background picture')):
        for ch, theme in enumerate(themes, 1):
            env = PixelEnvironment()
            env.set_level((ch - 1) * 10 + 3)
            env.set_focus(750, 430)
            for x, y in ((0, 0), (101, 0), (283, 247), (1720, 340)):
                env.draw(target, ch, x, y, 2.5, 3000, 1060, powered=True)
            renderer.set_level_context((ch - 1) * 10 + 3)
            renderer.set_level_focus(750, 430)
            renderer.draw_background(target, theme, 83, 37, 1.5, 3000, 1060,
                                     powered=True, signals=('power',))
            renderer.draw_menu_background(target, ch)
            renderer.get_chapter_preview(ch)
    pygame.quit()
    print('RUNTIME PASS: all 8 chapters, scrolling offsets, menu previews, no image plate loads')


if __name__ == '__main__':
    check_static()
    if '--runtime' in sys.argv:
        try:
            check_runtime()
        except ModuleNotFoundError as exc:
            if exc.name == 'pygame':
                print('RUNTIME NOT TESTED: pygame-ce unavailable')
                sys.exit(2)
            raise
