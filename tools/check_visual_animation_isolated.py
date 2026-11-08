"""Standalone animation-controller tests. No game window or pygame needed.

This test stubs the unused pygame import only to exercise state transition
logic. It must NOT be presented as a full Pygame rendering/runtime test.
"""
from pathlib import Path
import importlib.util
import sys
import types

sys.modules.setdefault('pygame', types.ModuleType('pygame'))
FILE = Path(__file__).resolve().parents[1] / 'src' / 'visuals' / 'robot_sprite.py'
spec = importlib.util.spec_from_file_location('echo_animation_isolated', FILE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

p = types.SimpleNamespace(
    alive=True, on_ground=True, on_ladder=False, dashing=False,
    wall_sliding=False, crouching=False, pushing_crate=False,
    interact_flash=0.0, vy=0.0, vx=0.0, facing=1,
    anim_timer=0.0, death_anim_clock=0.0, respawn_visual_timer=0.0,
)

def expect(state):
    result = module.frame_for(p)
    assert result[0] == state, (state, result)
    assert 0 <= result[1] < module.FRAMES[state], result
    return result

expect('idle')
p.anim_timer=.1;p.vx=230;expect('run')
p.anim_timer=.2;p.vy=-300;p.on_ground=False;expect('jump')
p.anim_timer=.3;p.vy=340;expect('fall')
p.anim_timer=.4;p.vy=0;p.on_ground=True;p.vx=0;expect('land')
p.anim_timer=.66;expect('idle')
p.anim_timer=.76;p.interact_flash=.20;expect('interact')
p.anim_timer=.80;p.interact_flash=0;p.dashing=True;expect('dash')
p.anim_timer=.90;p.alive=False;p.dashing=False;expect('death')
p.death_anim_clock=.22
assert expect('death')[1] >= 1
p.alive=True;p.respawn_visual_timer=.32;p.anim_timer=1.0;expect('respawn')
p.anim_timer=1.5;p.respawn_visual_timer=0;expect('idle')
p.anim_timer=1.6;p.on_ladder=True;p.vy=-100;expect('climb')
p.anim_timer=1.8;p.vy=0;expect('climb')
p.anim_timer=1.9;p.on_ladder=False;expect('idle')
print('PASS isolated: animation state timeline, priority, one-shots, respawn and ladder transitions')
