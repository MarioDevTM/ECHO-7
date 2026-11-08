"""Shared ECHO-7 pixel-industrial UI primitives in virtual 1280x720 space.

Draw and input geometry are the same rect supplied by the owning screen.
No physics or gameplay objects are created by these components.
"""
from __future__ import annotations
import pygame
from src.ui.text_layout import draw_fitted

BG = (8, 16, 25)
PANEL = (15, 26, 39)
RAISED = (24, 42, 58)
BORDER = (70, 91, 106)
CYAN = (86, 207, 226)
AMBER = (241, 174, 91)
TEXT = (229, 239, 245)
MUTED = (154, 173, 187)
DISABLED = (96, 113, 128)


def _pixel_box(surface, rect, fill, edge, *, selected=False):
    """Square-cornered panels with four crisp notched corners."""
    r = pygame.Rect(rect)
    if r.width <= 0 or r.height <= 0:
        return
    pygame.draw.rect(surface, (4, 9, 16), r.move(0, 3))
    pygame.draw.rect(surface, fill, r)
    pygame.draw.rect(surface, edge, r, 1)
    cut = min(6, r.width // 7, r.height // 7)
    if cut:
        for x,y,sgnx,sgny in ((r.left,r.top,1,1),
                               (r.right-1,r.top,-1,1),
                               (r.left,r.bottom-1,1,-1),
                               (r.right-1,r.bottom-1,-1,-1)):
            pygame.draw.line(surface, BG,(x,y+cut*sgny),(x+cut*sgnx,y),2)
            pygame.draw.line(surface,edge,(x+2*sgnx,y+cut*sgny),(x+cut*sgnx,y+2*sgny))
    if selected:
        pygame.draw.rect(surface,CYAN,(r.x+9,r.y+7,3,max(4,r.h-14)))
        pygame.draw.line(surface,(50,106,121),(r.x+17,r.bottom-6),(r.right-17,r.bottom-6))


def panel(surface, rect, *, accented=False):
    r=pygame.Rect(rect)
    _pixel_box(surface,r,PANEL,CYAN if accented else BORDER,selected=False)
    if r.width >= 90:
        pygame.draw.line(surface,CYAN if accented else (77,124,139),
                         (r.left+22,r.top+1),(min(r.right-22,r.left+165),r.top+1),3)
        pygame.draw.rect(surface,(38,74,91),(r.right-29,r.top+8,16,3))
        pygame.draw.rect(surface,(38,74,91),(r.right-20,r.top+15,7,3))


def button(surface, rect, label, *, selected=False, enabled=True, primary=False,
           size=18, align='center'):
    rect=pygame.Rect(rect)
    if not enabled:
        fill,edge,ink=(19,27,38),(53,68,79),DISABLED
    elif selected:
        fill,edge,ink=(31,64,81),CYAN,TEXT
    elif primary:
        fill,edge,ink=(26,55,70),(88,161,178),TEXT
    else:
        fill,edge,ink=(21,36,50),BORDER,TEXT
    _pixel_box(surface,rect,fill,edge,selected=selected and enabled)
    if not enabled:
        # A crossed status icon, not an apparently clickable bright control.
        x,y=rect.right-18,rect.centery
        pygame.draw.line(surface,DISABLED,(x-4,y-4),(x+4,y+4),2)
        pygame.draw.line(surface,DISABLED,(x-4,y+4),(x+4,y-4),2)
    elif selected:
        x,y=rect.right-18,rect.centery
        pygame.draw.polygon(surface,CYAN,[(x-3,y-5),(x+3,y),(x-3,y+5)])
    inner=rect.inflate(-44,-10)
    if inner.width>0 and inner.height>0:
        draw_fitted(surface,label,inner,ink,size=size,min_size=12,
                    bold=bool(selected or primary),align=align)


def section(surface,title,rect,subtitle=None):
    draw_fitted(surface,title,rect,CYAN,size=23,min_size=17,bold=True,align='left')
    if subtitle:
        draw_fitted(surface,subtitle,rect.move(0,35),MUTED,size=16,min_size=12,align='left')


def progress(surface, rect, done, total):
    r=pygame.Rect(rect)
    pygame.draw.rect(surface,(34,53,66),r)
    ratio=min(1.0,max(0.0,float(done)/max(1,total)))
    if ratio:
        pygame.draw.rect(surface,CYAN,(r.x,r.y,max(2,round(r.w*ratio)),r.h))
