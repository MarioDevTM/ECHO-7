"""Capture REAL Pygame backgrounds locally for visual QA (not gameplay images).

Requires pygame-ce. The resulting PNGs are screenshots, not active art assets.
Usage: python3 tools/capture_procedural_scenes.py
"""
import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
from pathlib import Path
import sys
import pygame
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.visuals.scene_renderer import SceneRenderer

pygame.init()
pygame.display.set_mode((1280,720))
renderer=SceneRenderer()
out=ROOT/'docs'/'procedural_runtime_captures'
out.mkdir(parents=True,exist_ok=True)
for chapter,theme in enumerate(('awakening','mechanical','power','optical',
                                'environmental','furnace','spire','surface'),1):
    renderer.set_level_context(1+(chapter-1)*10)
    surface=pygame.Surface((1280,720))
    renderer.draw_background(surface,theme,camera_x=240,camera_y=0,
                             elapsed=4,level_width=2800,level_height=960,
                             signals={'power'})
    filename=out/f'chapter_{chapter:02d}_runtime.png'
    pygame.image.save(surface,str(filename))
    print(filename)
pygame.quit()
