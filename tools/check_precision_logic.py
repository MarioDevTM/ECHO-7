"""Dependency-free approximate movement checks, not SDL or gameplay certification.

The stand-in represents only pygame.Rect and keycodes. Run the real
pygame-ce tests in src/tests/test_precision.py for genuine engine coverage.
"""
from __future__ import annotations
import sys
from pathlib import Path
from types import ModuleType
from collections import defaultdict
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

class Rect:
    def __init__(self, *args):
        if len(args) == 1:
            a=args[0]
            if isinstance(a,Rect): a=(a.x,a.y,a.width,a.height)
            x,y,w,h=a
        elif len(args)==2: (x,y),(w,h)=args
        else: x,y,w,h=args
        self.x,self.y,self.width,self.height=map(int,(x,y,w,h))
    @property
    def left(self):return self.x
    @left.setter
    def left(self,v):self.x=int(v)
    @property
    def right(self):return self.x+self.width
    @right.setter
    def right(self,v):self.x=int(v)-self.width
    @property
    def top(self):return self.y
    @top.setter
    def top(self,v):self.y=int(v)
    @property
    def bottom(self):return self.y+self.height
    @bottom.setter
    def bottom(self,v):self.y=int(v)-self.height
    @property
    def centerx(self):return self.x+self.width//2
    @centerx.setter
    def centerx(self,v):self.x=int(v)-self.width//2
    @property
    def centery(self):return self.y+self.height//2
    @centery.setter
    def centery(self,v):self.y=int(v)-self.height//2
    @property
    def center(self):return (self.centerx,self.centery)
    @center.setter
    def center(self,p):self.centerx,self.centery=p
    @property
    def topleft(self):return (self.left,self.top)
    @topleft.setter
    def topleft(self,p):self.left,self.top=p
    @property
    def topright(self):return (self.right,self.top)
    @property
    def w(self):return self.width
    @w.setter
    def w(self,v):self.width=int(v)
    @property
    def h(self):return self.height
    @h.setter
    def h(self,v):self.height=int(v)
    def move(self,dx,dy=None):
        if dy is None:dx,dy=dx
        return Rect(self.x+dx,self.y+dy,self.width,self.height)
    def union(self,other):
        l=min(self.left,other.left);t=min(self.top,other.top)
        return Rect(l,t,max(self.right,other.right)-l,max(self.bottom,other.bottom)-t)
    def colliderect(self,other):
        return self.left<other.right and self.right>other.left and self.top<other.bottom and self.bottom>other.top
    def collidelist(self,others):
        return next((i for i,r in enumerate(others) if self.colliderect(r)),-1)
    def inflate(self,dx,dy):return Rect(self.x-dx//2,self.y-dy//2,self.width+dx,self.height+dy)
    def __repr__(self):return f'Rect({self.x}, {self.y}, {self.width}, {self.height})'

pg=ModuleType('pygame')
pg.Rect=Rect
pg.Surface=type('Surface',(),{})
pg.key=type('key',(),{'ScancodeWrapper':object})
pg.__getattr__=lambda name: 1000+sum(map(ord,name)) if name.startswith('K_') else None
sys.modules['pygame']=pg

from src.entities.player import Player
from src.systems.collision import CollisionSystem
from src.systems.precision import PrecisionWorld
from src.core.settings import DASH_SPEED

# Dash vector normalization and charge depletion.
p=Player(40,100);assert not p.begin_dash(1,0)
p.can_dash=True;assert p.begin_dash(1,-1);assert abs((p.vx**2+p.vy**2)**.5-DASH_SPEED)<1e-7
assert p.dash_charges==0 and not p.begin_dash(1,0)

# Solid wall constrains dash even when travel is a full 0.15 seconds.
p=Player(70,100);p.can_dash=True;p.begin_dash(1,0)
wall=Rect(100,50,40,250)
CollisionSystem.move_and_collide_player(p,.15,[wall],[])
assert p.rect.right <= wall.left and p.dash_blocked
p.after_collision([wall]);assert not p.dashing

# Wall jump pushes player AWAY from actual wall.
p=Player(74,90);p.can_wall_jump=True;p.wall_surfaces=[wall]
p.queue_jump();p.coyote_timer=0.0
keybinds={'left':[pg.K_a],'right':[pg.K_d],'up':[pg.K_w],
          'down':[pg.K_s],'jump':[pg.K_SPACE],'run':[pg.K_LSHIFT]}
assert p.update_timers_and_input(1/120,defaultdict(bool,{pg.K_d:True}),keybinds,solids=[wall])
assert p.vx<0 and p.vy<0

# One-way ledge admits upward movement, then catches a falling player.
ledge=Rect(100,120,120,12)
p=Player(120,144);p.vy=-500
CollisionSystem.move_and_collide_player(p,.08,[],[],[ledge]);assert p.rect.y<144
p=Player(120,45);p.vy=650
CollisionSystem.move_and_collide_player(p,.06,[],[],[ledge]);assert p.on_ground and p.rect.bottom==120

# Recharges and bounce only on jump-landing, never while simply standing.
world=PrecisionWorld({'dash_recharges':[{'id':'c','x':100,'y':100}],
                      'springs':[{'id':'s','x':40,'y':188,'w':70}]})
p=Player(100,90);p.can_dash=True;p.dash_charges=0
world.tick(1/120,p);assert p.dash_charges==1
p.set_position(55,154);p.vy=90
CollisionSystem.move_and_collide_player(p,.04,[],[])
world.tick(1/120,p,landed=False,impact_vy=200);assert p.vy>=0
world.tick(1/120,p,landed=True,impact_vy=200);assert p.vy< -800

# Striped panel breaks upon a swept dash and restores on retry.
world=PrecisionWorld({'dash_barriers':[{'id':'b','x':100,'y':100,'w':30,'h':60}]})
p=Player(72,110);p.can_dash=True;p.begin_dash(1,0)
initial=world.snapshot();assert world.break_with_dash(p,1/120,[])
assert not world.solid_barriers();world.restore(initial)
assert len(world.solid_barriers())==1
print('PASS: 6 approximate precision movement and object checks (pygame-free)')
print('NOTE: not a replacement for real pygame-ce collision, rendering, or input-driven tests')
