"""Rebuild an evidence-based OFFLINE report (requires Pillow and NumPy)."""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import offline_pygame_adapter as adapter
from src.visuals.scene_renderer import SceneRenderer
chapters=('awakening','mechanical','power','optical','environmental','furnace','spire','surface')
examples=(1,11,25,31,41,51,62,80)
metrics=json.loads((ROOT/'docs/GEMINI_RECOVERY_METRICS.json').read_text())
rows=[]
for i,(theme,level) in enumerate(zip(chapters,examples),1):
 d=json.loads((ROOT/f'data/levels/level_{level:02d}.json').read_text())
 x,y=d['spawn']; camx=max(0,min(d['width']-1280,x-410));camy=max(0,min(d['height']-720,y-460))
 renderer=SceneRenderer();renderer.set_level_context(level);renderer.set_level_focus(x,y)
 surf=adapter.pg.Surface((1280,720))
 renderer.draw_background(surf,theme,camx,camy,.4,d['width'],d['height'],powered=True)
 gray=np.asarray(surf.im.convert('L'), dtype=np.uint8)
 avg=gray.mean();p95=np.percentile(gray,95)
 changed=metrics[str(i)]['changed_pixels_between_times_0_4_and_2_1']
 rows.append((i,theme,level,round(float(avg),1),round(float(p95),1),changed))
assert len(rows)==8

art_bible = '''# ECHO-7 — Code-Generated Background Art Bible

The gameplay backgrounds are original Python/Pygame artwork drawn at a **640×360 logical grid** and scaled 2× using nearest-neighbor to 1280×720. The character, terrain, hazards and UI remain separate, higher-priority gameplay layers.

## Unified architectural language

Eight sector palettes share shaded steel shapes, stepped panel rims, pipe flange patterns, strong silhouettes, one authored landmark per level, six reusable bay types, and three progression compositions (*opening*, *mid_complex*, *late_crisis*). Each chapter has a consistent lower wall/floor boundary where appropriate. Distant layers move at less than full camera speed; near architecture uses the world-coordinate transform.

| Chapter | Visual centerpiece | Supporting detail | Time-driven motion |
|---|---|---|---|
| 1 · Awakening | Cryo-diagnostics observation bay | Aligned research bulkheads, vents, server racks | Slow vent fans and small diagnostic waveforms |
| 2 · Mechanical Depths | Triple-cog foundry press | Cast-iron machine bays, crane braces | Cog rotation and piston strokes |
| 3 · Power Grid | High-voltage substation core | Open electrical hall, insulators, capacitor banks | Localized electrical arcs and conduit pulses |
| 4 · Surveillance Grid | Circular observation aperture | Armored windows, server lockers, sensors | Panning camera pods and status diodes |
| 5 · Flood Control | Hydraulic turbine manifold | Pipe headers, standpipes, gauges | Pressure needle and small leak droplets |
| 6 · Core Collapse | Reactor containment column | Thermal shields, vents and exchange towers | Thermal pulses and sparse embers |
| 7 · Broken Spire | Torn internal hull and structural spine | Cracked bulkheads, exposed rebar, exterior glimpses | Loose cable sway and occasional beacons |
| 8 · Surface Breach | Ruined communications array | Night sky, distant ring, low rubble and towers | Subtle clouds and distant indicators |

Art is inspired by the *design principles* of readable platformers, including Celeste, Shovel Knight, Dead Cells, Animal Well and INSIDE. No sprites, map geometry, brand assets or character designs from those games were imported.
'''
(ROOT/'CHAPTER_ART_BIBLE.md').write_text(art_bible)

notes='''# ECHO-7 — Gemini Recovery and Renderer Integration

## What was continued

The supplied Gemini transcript ended during its final verification/packaging script with `IndexError: list index out of range`. The immediate error came from printing the first line of captured stdout even when the subprocess produced no stdout. That masked the actual failing check.

The latest **recoverable 640×360 procedural renderer** from the transcript has been integrated into the previous complete ECHO-7 source ZIP and kept compatible with its existing `SceneRenderer` calls.

## Implemented repairs

- Installed the recovered `PixelEnvironment` source while preserving all earlier game logic.
- Reintroduced `set_level` and `menu_background` methods required by the existing scene-renderer/menu integration.
- Verified that game scene backgrounds are drawn from code and not from image plates; the original chapter paintings remain as non-runtime design references.
- Added deterministic progression geometry to all eight chapters. In particular, Chapters 2 and 6 now produce three distinct opening/middle/late environment variants instead of repeating identical compositions.
- Added corrected Pygame-free AST/coordinate/palette tests; fixed the old isolated-execution `VIRTUAL_WIDTH` NameError in Gemini's proposed test script.
- Bundled reproducible Pillow preview tools, 24 archetype samples, and eight gameplay-scale **offline compositions**.
- Preserved old levels, puzzle systems, progress-selection logic, exit gate protection and reference backgrounds.

## Runtime design

- Logical pixel grid: 640×360; output: 1280×720, nearest-neighbor.
- Distant parallax: 0.16× horizontal; mid plane: 0.40× horizontal / 0.20× vertical; foreground decorative wall/bay architecture: 1.00× camera translation.
- Static bay/hero/far-strip surfaces cached; effects drawn using elapsed time.
- Per-level room context set once on level load, not continuously from the moving player.
- Eight distinct facility chapters, with Chapter 3 remaining an indoor open power chamber, Chapter 7 an interior breach and Chapter 8 nocturnal exterior ruins.

## Limits

The main game was not run through native Pygame here: `pygame-ce` was unavailable and could not be installed from the package index. Pillow-based drawing adapters approximate Pygame graphics and cannot prove proper FPS, input handling, collision resolution, lighting compositing, or gameplay solvability. The real platformer terrain is sampled from the shipped JSON; offline compositions are **not actual in-game screenshots**. This is a **statically validated continuation build**, not a final playtested release.

## Running locally

```bash
cd ECHO-7
python3 -m pip install -r requirements.txt
python3 tools/check_pixel_environment_offline.py
python3 tools/check_procedural_backgrounds.py --runtime
python3 main.py --validate
python3 main.py
```
'''
(ROOT/'GEMINI_RECOVERY_IMPLEMENTATION.md').write_text(notes)

report='''# ECHO-7 — Recovery QA Report

## Evidence type

All numbers below were measured from the project's procedural painter with a **Pillow-backed pygame approximation**, at the camera positions specified by the stored spawn points. They measure the rendered background only; they do not replace native engine capture or user playtests.

| Chapter | Sample level | Background mean luma | Background 95th-percentile luma | Pixels changed by idle animation (0.4s → 2.1s) |
|---|---:|---:|---:|---:|
'''
for ch,theme,level,avg,p95,diff in rows:
 report+=f'| {ch}: {theme} | {level} | {avg} | {p95} | {diff} |\n'
report+='''
## Verification status

| Test | Result | Limitation |
|---|---|---|
| Full Python AST compilation | PASS | Does not import/run native Pygame |
| `check_pixel_environment_offline.py` | PASS | Pure rendering/math contracts |
| `check_procedural_backgrounds.py` | PASS (static) | Native runtime is unavailable |
| `check_repaired_release.py` | PASS | Checks original hashes, exit guard, assets |
| `check_level_schema_offline.py` | PASS: 80/80 | Data and bounds, not physical solvability |
| `check_level_dependencies_static.py` | PASS: 80/80 | Signal graphs, not physical traversal |
| `check_ui_logic_without_pygame.py` | PASS | Isolated UI logic only |
| `check_runtime_assets.py` | PASS | Presence checks only |
| Eight offscreen chapter renders at two timestamps | PASS | Pillow approximation |
| 24 archetype variants: 3 per chapter | PASS, all distinct | Offline images only |
| Actual game launch, player navigation, 60 FPS, audio, full level completion | NOT TESTED | `pygame-ce` not installed |

All gameplay and levels 1–80 are retained from the input project. **No new late-level redesign was performed in this continuation.**

Preview: `docs/GEMINI_RECOVERY_PREVIEW.jpg`; per-chapter images under `docs/background_recovery_previews/`; 24 archetype samples under `docs/screenshots/archetypes/`.
'''
(ROOT/'docs/GEMINI_RECOVERY_QA.md').write_text(report)
print('Wrote art bible, implementation documentation, QA report with',len(rows),'measured chapters')
