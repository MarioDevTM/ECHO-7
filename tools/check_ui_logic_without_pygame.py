"""Pygame-free UI policy smoke tests. Not a substitute for in-engine UI tests."""
from pathlib import Path
import ast
import json
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1]

class DummyRect:
    def __init__(self,x,y,w,h):self.x,self.y,self.w,self.h=x,y,w,h
    def collidepoint(self,p):return self.x<=p[0]<self.x+self.w and self.y<=p[1]<self.y+self.h

key_names=('K_UP','K_DOWN','K_w','K_s','K_LEFT','K_RIGHT','K_a','K_d','K_1','K_8','K_RETURN','K_SPACE','K_ESCAPE','K_PAGEUP','K_PAGEDOWN')
key_codes={name:index+10 for index,name in enumerate(key_names)}
# Numeral keys must have a sequential offset for chapter shortcut behavior.
key_codes['K_1']=101;key_codes['K_8']=108
pg=SimpleNamespace(Surface=object,Rect=DummyRect,event=SimpleNamespace(Event=object),
                   font=SimpleNamespace(SysFont=lambda *a,**k: object()),
                   KEYDOWN=1,MOUSEMOTION=2,MOUSEBUTTONDOWN=3,**key_codes)
source=(ROOT/'src/ui/main_menu.py').read_text()
class_node=next(n for n in ast.parse(source).body if isinstance(n,ast.ClassDef) and n.name=='MainMenu')
compiled=compile(ast.Module(body=[class_node],type_ignores=[]),str(ROOT/'src/ui/main_menu.py'),'exec')
metadata={k:{'title':f'Chapter {k}','description':'','levels':list(range((k-1)*10+1,k*10+1))} for k in range(1,9)}
class Audio:
    gallery_active=False
    gallery_paused=False
    def play(self,*args):pass
    def leave_gallery(self):pass
    def preview_chapter(self,*args):pass
class Save:
    def __init__(self,unlocked):self.data={'unlocked_level':unlocked,'current_level':min(2,unlocked),
                                              'completed_levels':[],'collected_logs':[],'completed_auxiliary':[]}
    def reset_new_game(self):self.data.update(unlocked_level=1,current_level=1,completed_levels=[],collected_logs=[])
class Game:
    def __init__(self,unlocked):
        self.save_manager=Save(unlocked);self.level_loader=SimpleNamespace(TOTAL_LEVELS=80,TOTAL_CHAPTERS=8,
             get_chapter_for_level=lambda n:(n-1)//10+1)
        self.audio=Audio();self.started=[];self.running=True
    def start_level(self,n):self.started.append(n)
    def open_settings(self,source):pass
    def window_to_virtual(self,p):return p

g={'pygame':pg,'json':json,'LEVELS_DIR':ROOT/'data/levels','VIRTUAL_WIDTH':1280,'VIRTUAL_HEIGHT':720,
   'CHAPTER_METADATA':metadata,'AUXILIARY_ROOMS':{},'COLORS':{},'SceneRenderer':lambda:object(),
   'draw_fitted':lambda *a,**k:None,'ui':object(),'DEFAULT_LEVELS':{}}
exec(compiled,g)
Menu=g['MainMenu']
app=Game(1);m=Menu(app)
assert not m._action_locked('LEVEL_80')
assert not m._action_locked('OPEN_CHAPTER_8')
m.mode='CHAPTER_SELECT';assert '[LOCKED]' not in m._get_items()[2][0]
m._trigger_action('LEVEL_80');assert app.started==[80]
m._trigger_action('OPEN_CHAPTER_8');assert m.mode=='LEVEL_SELECT'
app=Game(35);m=Menu(app)
assert all(not m._action_locked(f'LEVEL_{i}') for i in range(1,81))
assert not m._action_locked('OPEN_CHAPTER_8')
m._trigger_action('NEW_GAME');assert m.mode=='CONFIRM_NEW_GAME' and not app.started
m._trigger_action('CANCEL_RESET');assert m.mode=='ROOT' and app.save_manager.data['unlocked_level']==35
m._trigger_action('NEW_GAME');m._trigger_action('CONFIRM_RESET');assert app.started==[1]

# Actual Game.window_to_virtual unbound function isolated from graphical runtime.
node=next(n for n in ast.parse((ROOT/'src/core/game.py').read_text()).body if isinstance(n,ast.ClassDef) and n.name=='Game')
fn=next(x for x in node.body if isinstance(x,ast.FunctionDef) and x.name=='window_to_virtual')
exec(compile(ast.Module(body=[fn],type_ignores=[]),'virtual_pointer','exec'),g)
func=g['window_to_virtual']
for size,pt,expected in [((1280,720),(640,360),(640,360)),
                         ((1600,900),(800,450),(640,360)),
                         ((1024,768),(512,384),(640,360)),
                         ((1024,768),(512,40),(-1,-1))]:
    self=SimpleNamespace(screen=SimpleNamespace(get_size=lambda:size))
    assert func(self,pt)==expected,(size,pt,func(self,pt),expected)
print('PASS: free access all 80, no chapter locks, new-game confirmation, save reset, pointer letterboxing.')
print('NOTE: isolated class/method tests; real Pygame event and drawing tests NOT RUN.')
