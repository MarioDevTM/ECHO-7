"""Clear the finale with keyboard input from spawn and check the saved completion."""

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
save.data["unlocked_level"] = 80

pg = pygame
r = game.level_manager
from collections import defaultdict
from unittest.mock import patch

keys = defaultdict(bool)
patch("pygame.key.get_pressed", return_value=keys).start()


def frame(direction=0, press=None, sprint=False):
    keys.clear()
    if direction:
        keys[pg.K_d if direction == 1 else pg.K_a] = True
    if sprint:
        keys[pg.K_LSHIFT] = True
    s = r.update(
        1 / 120, [] if press is None else [pg.event.Event(pg.KEYDOWN, key=press)]
    )
    if s != "PLAYING":
        raise Done(s)
    assert r.player.alive, ("died", r.player.rect)


class Done(Exception):
    pass


def walk(x):
    p = r.player
    for _ in range(1600):
        delta = x - p.rect.centerx
        if abs(delta) <= 3:
            return
        frame(1 if delta > 0 else -1)
    raise ValueError(("walk", x, p.rect))


def rest():
    for i in range(28):
        frame()


def use(x):
    walk(x)
    rest()
    frame(press=pg.K_e)
    frame()


def hop(start, target, y, boost=False):
    walk(start)
    p = r.player
    # start with a little momentum when possible, steer onto target using braking distance
    sign = 1 if target > start else -1
    frame(sign, pg.K_SPACE, True)
    for i in range(250):
        delta = target - p.rect.centerx
        if boost and i == 34:
            keys.clear()
            keys[pg.K_w] = True
            keys[pg.K_d if sign == 1 else pg.K_a] = True
            r.update(1 / 120, [pg.event.Event(pg.KEYDOWN, key=pg.K_x)])
        else:
            frame(
                (
                    0
                    if abs(delta) < 6
                    or (delta * p.vx > 0 and abs(delta) < p.vx**2 / 1500 / 2)
                    else (1 if delta > 0 else -1)
                ),
                sprint=True,
            )
        if i > 8 and p.on_ground:
            if abs(p.rect.bottom - y) <= 1:
                return
            raise ValueError(("land", start, target, y, p.rect))
    raise ValueError(("air", p.rect))


game.main_menu._trigger_action("LEVEL_80")
rest()
# Move west, crossing the breakaway lip in one jump. Hop over the lens crate.
hop(1010, 795, 880)
hop(777, 599, 880)
hop(545, 402, 880)
use(385)
use(268)
walk(675)
rest()
print("cargo", r.crates[0].rect, r.puzzle_manager.active_signals, flush=True)
use(586)
hop(653, 793, 880)
hop(810, 1030, 880)
hop(1820, 2036, 880)
hop(2420, 2490, 800)
hop(2456, 2370, 723)
use(2328)
hop(2420, 2510, 800)
use(2572)
walk(2395)
rest()
hop(2030, 1822, 880)
hop(1225, 1145, 802)
hop(1198, 1294, 727)
hop(1254, 1160, 652)
hop(1180, 1270, 578)
hop(1238, 1135, 511)
hop(1160, 1236, 444)
try:
    walk(1465)
except Done as done:
    print("FINALE", done, flush=True)
    assert 80 in SaveManager(save.save_path).data["completed_levels"]
    assert str(done) == "GAME_COMPLETED"
else:
    raise RuntimeError("No completion")
