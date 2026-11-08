"""Check both stages of deliberate platform removal against immutable pre-finale data.

The 35 already-pruned walk-platform IDs must remain gone; additional removals
are allowed only on Levels 25–80. This does not prove live traversability.
"""
from __future__ import annotations
from pathlib import Path
import ast
import json
ROOT=Path(__file__).resolve().parents[1]
old=json.loads((ROOT/'docs/FINAL_OVERHAUL_ORIGINAL_PLATFORM_PRUNING.json').read_text())
latest=json.loads((ROOT/'docs/PLATFORM_PRUNING_AUDIT.json').read_text())
assert len(old)==len(latest)==80
prior_removed={v['level']:{p['id'] for p in v['removed']} for v in old}
assert sum(map(len,prior_removed.values()))==35
additional=0
for row in latest:
    n=row['level']
    updated=json.loads((ROOT/f'data/levels/level_{n:02d}.json').read_text())
    base=json.loads((ROOT/f'data/levels_pre_finale_overhaul_backup/level_{n:02d}.json').read_text()) if n>=25 else updated
    before_ids={p['id'] for p in base['one_way_platforms']}
    after_ids={p['id'] for p in updated['one_way_platforms']}
    assert after_ids <= before_ids,(n,'unexpected added platform')
    assert not (prior_removed[n] & after_ids),(n,'restored old platform')
    assert len(updated['one_way_platforms'])==row['remaining'],n
    if n<=24:
        assert before_ids==after_ids,n
    else:
        additional+=len(before_ids-after_ids)
    for deleted in row['removed']:
        assert deleted['id'] not in after_ids,(n,deleted['id'])
assert additional>0,'Finale/late-game pruning did not remove additional platforms'
menu=(ROOT/'src/ui/main_menu.py').read_text()
core=(ROOT/'src/core/game.py').read_text()
assert 'echo7_icon.png' not in menu
assert 'player/idle_0.png' in menu
assert 'pygame.display.set_icon(self._app_icon)' in core
assert core.index('pygame.display.set_mode(') < core.index('pygame.display.set_icon(self._app_icon)')
for f in ('src/ui/main_menu.py','src/core/game.py','tools/prune_redundant_platforms.py',
          'tools/build_desktop_app.py','tools/install_linux_desktop_icon.py'):
    ast.parse((ROOT/f).read_text(),filename=f)
assert (ROOT/'data/art/ui/echo7_icon.ico').is_file()
assert (ROOT/'data/art/ui/echo7_icon.png').is_file()
print(f'PASS: Original 35 removed catwalks remain absent; {additional} additional removals from late-game baseline.')
print('PASS: Player-head artwork is an OS/window icon, not a new main-menu emblem.')
print('LIMITATION: Geometric dependency checks are not a human playthrough.')
