"""Real pygame runtime smoke checks and station-level signal validation using a temporary save."""

from pathlib import Path
import os, sys, tempfile, traceback, json

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
os.environ["SDL_VIDEODRIVER"] = os.environ["SDL_AUDIODRIVER"] = "dummy"
import pygame
from src.core.game import Game
from src.core.save_manager import SaveManager
from unittest.mock import patch

save = SaveManager(Path(tempfile.mkdtemp()) / "save.json")
with patch("src.core.game.SaveManager", return_value=save):
    game = Game()
# Keep the fresh save locked_level=1 to verify unrestricted stage selection.

r = game.level_manager
for n in range(1, 81):
    game.main_menu._trigger_action(f"LEVEL_{n}")
    assert r.current_level_num == n, (n, r.current_level_num)
    for i in range(6):
        r.update(1 / 60, [])
    r.draw(game.canvas)
    cm = r.checkpoint_manager
    for cp in cm.checkpoints:
        assert cm.update(
            1 / 60,
            cp.rect.copy(),
            r.crates,
            r.moving_platforms,
            r.puzzle_manager,
            r.puzzle_manager.collapsing_platforms,
        )
    r.trigger_manual_restart()
    for i in range(22):
        r.update(1 / 60, [])
    assert r.player.alive
print("All 80 selected, drawn, checkpointed, restarted.")

r = game.level_manager
for n in range(25, 80):
    try:
        r.load_level(n)
        p = r.puzzle_manager
        d = r.level_loader.load_level_data(n)
        away = pygame.Rect(-1000, -1000, 26, 46)

        def tick(count=2):
            for _ in range(count):
                p.update(1 / 60, away, r.crates, r.tiles, r.moving_platforms)

        def use(o):
            assert p.try_interact(o.rect.copy()), o.rect
            tick()

        def ensure(k):
            if k in p.active_signals:
                return
            if k in ("up", "down", "east_up", "east_down"):
                if p.generators:
                    ensure("power")
                if k not in p.active_signals:
                    use(p.mirrors[int(k.startswith("east"))])
            elif k in ("A", "B") or any(k in (x.a_signal, x.b_signal)
                                                 for x in p.routing_consoles):
                panel = next(x for x in p.routing_consoles
                             if k in (x.a_signal, x.b_signal))
                desired = 0 if k == panel.a_signal else 1
                if p.route_modes[panel.route_id] != desired:
                    use(panel)
                tick()
            elif k in p.timer_mech.sequences:
                for switch_id in p.timer_mech.sequences[k]["order"]:
                    use(p.switches_by_id[switch_id])
                tick()
            elif k in ("light", "park", "freight", "weight"):
                if k == "light":
                    ensure("park")
                else:
                    if k == "weight" and p.water_zones:
                        ensure("dry")
                        tick(160)
                    plate = next(o for o in p.plates if o.link_id == k)
                    r.crates[0].rect.midbottom = plate.base_rect.midbottom
                    tick()
            elif k == "full":
                if "dry" in p.active_signals:
                    use(p.valves[[q.link_id for q in p.valves].index("dry")])
                    tick(180)
            elif k == "order":
                for i in ["first", "second", "third"]:
                    use(p.switches_by_id[i])
            else:
                o = next(
                    o
                    for o in p.switches + p.generators + p.valves + p.latching_relays
                    if o.link_id == k
                )
                for q in getattr(o, "required_links", []):
                    ensure(q)
                use(o)
            assert k in p.active_signals, (k, p.active_signals)

        tick()
        for k in p.doors[0].required_links:
            ensure(k)
        # Doors have a visual opening interval; logical and physical exit
        # permissions agree only when the bulkhead has fully retracted.
        tick(25)
        assert p.doors[0].is_open and not p.doors[0].is_solid, p.active_signals
        print("PASS", n)
    except Exception as exc:
        raise AssertionError(f"Room {n}") from exc

# The real exit handler of 79 advances to 80 after the validated gate opens.
r.player.set_position(r.exit_rect.x + 4, r.exit_rect.bottom - r.player.rect.height)
assert r.update(1 / 60, []) == "NEXT_LEVEL"
assert r.current_level_num == 80
# A shaking bridge must survive round-trip capture, not silently return to idle.
bridge = r.puzzle_manager.collapsing_platforms[0]
bridge.state, bridge.timer = "SHAKING", 0.24
snap = r.checkpoint_manager
parts = (r.crates, r.moving_platforms, r.puzzle_manager, r.puzzle_manager.collapsing_platforms)
snap.save_snapshot(*parts)
bridge.reset()
snap.restore_snapshot(r.player, *parts)
assert bridge.state == "SHAKING" and abs(bridge.timer-0.24)<1e-6
# Continue from a persisted finale save and check all chapter gallery channels.
save.data["current_level"] = 80
save.save()
reloaded = SaveManager(save.save_path)
assert reloaded.data["current_level"] == 80
game.main_menu._trigger_action("CONTINUE")
assert r.current_level_num == 80
assert game.audio.enabled
for ch in range(1, 9):
    game.main_menu._trigger_action("GALLERY_" + str(ch))
    assert game.audio.gallery_active and game.audio.current_chapter_track == ch
    assert (
        game.audio.ambient_channel.get_busy() and game.audio.rhythm_channel.get_busy()
    )
    assert game.audio.toggle_gallery_pause()
    assert not game.audio.toggle_gallery_pause()
game.audio.leave_gallery()
# Exercise keyboard page-forward in the actual game loop, then exit the test.
game.start_level(79)
with patch(
    "pygame.event.get",
    side_effect=[
        [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_PAGEDOWN)],
        [pygame.event.Event(pygame.QUIT)],
    ],
), patch("pygame.quit"):
    try:
        game.run()
    except SystemExit:
        pass
assert r.current_level_num == 80
print(
    "PASS: Continue, page-forward from 79, all eight soundtrack pairs, gallery pause/resume."
)
