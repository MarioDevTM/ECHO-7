"""Run actual LevelValidator/schema AST functions with a minimal Rectangle stand-in.

Pygame independent. Does not emulate physics or certify gameplay.
"""
from pathlib import Path
import ast,math,json
from graphlib import TopologicalSorter,CycleError
r=Path(__file__).resolve().parents[1]
class Rect:
 def __init__(self,*a):
  if len(a)==1:a=a[0]
  self.x,self.y,self.w,self.h=map(int,a)
 def contains(self,o):return self.x<=o.x and self.y<=o.y and self.x+self.w>=o.x+o.w and self.y+self.h>=o.y+o.h
 def colliderect(self,o):return self.x<o.x+o.w and self.x+self.w>o.x and self.y<o.y+o.h and self.y+self.h>o.y
 def collidelist(self,other):return next((i for i,x in enumerate(other) if self.colliderect(x)),-1)
class Pygame:Rect=Rect
settings={'pygame':Pygame,'math':math,'PLAYER_WIDTH':36,'PLAYER_HEIGHT':46}
module=ast.parse((r/'src/levels/level_schema.py').read_text())
for n in module.body:
 if isinstance(n,(ast.FunctionDef,ast.Assign)):
  exec(compile(ast.Module(body=[n],type_ignores=[]),'schema.py','exec'),settings)
module=ast.parse((r/'src/levels/level_loader.py').read_text())
validator=next(n for n in module.body if isinstance(n,ast.ClassDef) and n.name=='LevelValidator')
settings.update(schema_errors=settings['schema_errors'],TopologicalSorter=TopologicalSorter,CycleError=CycleError,Any=object)
exec(compile(ast.Module(body=[validator],type_ignores=[]),'validator.py','exec'),settings)
val=settings['LevelValidator']
fails={}
for n in range(1,81):
 d=json.loads((r/f'data/levels/level_{n:02}.json').read_text())
 err=val.validate(d)
 if err:fails[n]=err
print('Code-independent LevelValidator schema/links:',80-len(fails),'PASS',len(fails),'FAIL')
for n,errs in fails.items():
 print(f'{n}: '+str(errs)[:2000])
if fails: raise SystemExit(1)
print('NOTE: pygame.Rect stand-in only; not in-engine runtime validation.')
