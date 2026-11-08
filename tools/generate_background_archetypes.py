"""Generate 24 OFFLINE pixel-environment reference previews via a Pillow Pygame adapter.
These are not actual game-engine screenshots. Requires Pillow.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sys
from PIL import Image
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import offline_pygame_adapter as shim  # installs a pygame approximation before imports
from src.visuals.scene_renderer import SceneRenderer
OUT = ROOT/'docs/screenshots/archetypes'
OUT.mkdir(parents=True, exist_ok=True)
results = {}
for chapter, theme in enumerate(('awakening','mechanical','power','optical',
                                'environmental','furnace','spire','surface'),1):
    hashes = []
    for offset, name in ((1, 'opening'),(5, 'mid_complex'),(9,'late_crisis')):
        level = (chapter - 1)*10 + offset
        renderer = SceneRenderer()
        renderer.set_level_context(level)
        renderer.set_level_focus(920, 510)
        surf = shim.pg.Surface((1280,720))
        renderer.draw_background(surf,theme,80,40,1.0,2600,1000,powered=offset!=9)
        im = surf.im.resize((640,360), Image.Resampling.NEAREST)
        output=OUT/f'ch{chapter:02}_{name}_lvl{level:02}.png'
        im.save(output,optimize=True)
        hashes.append(hashlib.sha256(im.tobytes()).hexdigest())
    results[chapter]={'three_distinct_images':len(set(hashes))==3}
    print('Chapter',chapter, 'distinct archetypes:', results[chapter]['three_distinct_images'])
assert all(row['three_distinct_images'] for row in results.values())
(ROOT/'docs/ARCHETYPE_OFFLINE_VERIFICATION.json').write_text(json.dumps(results,indent=2))
print('PASS: 24 offline archetype previews written.')
