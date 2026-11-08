"""Curated, 2D world-space decoration data.

Screen coordinates are derived from stored world coordinates and the SAME
camera transform used by terrain and the player. No sprite derives its
position from the player's location, the rendered tile rect, or elapsed time.
The manifest is allowed to be empty; visual dressing never changes collisions.
"""
from __future__ import annotations
import json
from pathlib import Path

MANIFEST = Path(__file__).resolve().parents[2] / 'data/art/environment/world_dressing.json'
_FALLBACK = {'levels': {}, 'chapter_policy': {}}


def load_world_dressing(path=MANIFEST):
    if not Path(path).is_file():
        return _FALLBACK
    return json.loads(Path(path).read_text(encoding='utf-8'))


def placements_for_level(level_number, theme, manifest=None):
    manifest = manifest if manifest is not None else load_world_dressing()
    permitted = set(manifest.get('chapter_policy', {}).get(theme, []))
    if not permitted:
        return ()
    result = []
    for data in manifest.get('levels', {}).get(str(level_number), ()):
        if data.get('sprite') not in permitted or data.get('role') != 'decorative':
            continue
        if data.get('layer') != 'back_terrain':
            continue
        world = data.get('world')
        if not isinstance(world, list) or len(world) != 2:
            continue
        result.append(data)
    return tuple(result)


def anchor_for(camera_x, camera_y, world_x, world_y, width, height, anchor):
    """Pure world-to-screen transform used for static geometry and animation QA."""
    x = int(world_x) - int(camera_x)
    y = int(world_y) - int(camera_y)
    if anchor in ('top_center','bottom_center'):
        x -= width // 2
    if anchor == 'bottom_center':
        y -= height
    return x, y
