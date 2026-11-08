"""Approximate offline preview shim from the supplied Gemini transcript.
NOT a replacement for Pygame gameplay/render testing.
"""
import sys, os, types, math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
pg = types.ModuleType("pygame")
pg.SRCALPHA = 1

class PgRect:
    def __init__(self, *args):
        if len(args) == 1 and isinstance(args[0], (tuple, list, PgRect)):
            a = args[0]
            self.x, self.y, self.w, self.h = int(a[0]), int(a[1]), int(a[2]), int(a[3])
        elif len(args) == 4:
            self.x, self.y, self.w, self.h = int(args[0]), int(args[1]), int(args[2]), int(args[3])
        else:
            self.x = self.y = self.w = self.h = 0
    @property
    def width(self): return self.w
    @property
    def height(self): return self.h
    @property
    def left(self): return self.x
    @property
    def top(self): return self.y
    @property
    def right(self): return self.x + self.w
    @property
    def bottom(self): return self.y + self.h
    @property
    def centerx(self): return self.x + self.w // 2
    @property
    def centery(self): return self.y + self.h // 2
    @property
    def center(self): return (self.centerx, self.centery)
    @property
    def topleft(self): return (self.x, self.y)
    @property
    def size(self): return (self.w, self.h)
    def __iter__(self):
        yield self.x; yield self.y; yield self.w; yield self.h
    def __getitem__(self, idx):
        return (self.x, self.y, self.w, self.h)[idx]
    def move(self, dx, dy):
        return PgRect(self.x + dx, self.y + dy, self.w, self.h)
    def inflate(self, dw, dh):
        return PgRect(self.x - dw // 2, self.y - dh // 2, self.w + dw, self.h + dh)
    def clip(self, other):
        other = PgRect(other)
        nx = max(self.x, other.x)
        ny = max(self.y, other.y)
        nr = min(self.right, other.right)
        nb = min(self.bottom, other.bottom)
        return PgRect(nx, ny, max(0, nr - nx), max(0, nb - ny))
    def colliderect(self, other):
        other = PgRect(other)
        return self.x < other.right and self.right > other.x and self.y < other.bottom and self.bottom > other.y
    def contains(self, other):
        other = PgRect(other)
        return self.x <= other.x and self.y <= other.y and self.right >= other.right and self.bottom >= other.bottom
    def collidelist(self, rects):
        for i, r in enumerate(rects):
            if self.colliderect(r):
                return i
        return -1

class PgSurface:
    def __init__(self, size, flags=0, pil_img=None):
        w, h = max(1, int(size[0])), max(1, int(size[1]))
        if pil_img is not None:
            self.im = pil_img
        else:
            mode = "RGBA" if (flags & pg.SRCALPHA) else "RGB"
            self.im = Image.new(mode, (w, h), (0, 0, 0, 0) if mode == "RGBA" else (0, 0, 0))
        self.dr = ImageDraw.Draw(self.im)
        self._clip = PgRect(0, 0, w, h)
    def get_width(self): return self.im.size[0]
    def get_height(self): return self.im.size[1]
    def get_size(self): return self.im.size
    def get_rect(self, **kw):
        r = PgRect(0, 0, self.im.size[0], self.im.size[1])
        return r
    def convert(self): return self
    def convert_alpha(self): return self
    def fill(self, color, rect=None):
        c = tuple(int(x) for x in color)
        if self.im.mode == "RGBA" and len(c) == 3:
            c = (*c, 255)
        if rect is None:
            self.dr.rectangle([0, 0, self.get_width() - 1, self.get_height() - 1], fill=c)
        else:
            r = PgRect(rect)
            self.dr.rectangle([r.x, r.y, r.right - 1, r.bottom - 1], fill=c)
    def blit(self, source, dest, area=None):
        if isinstance(dest, PgRect):
            dx, dy = dest.x, dest.y
        else:
            dx, dy = int(dest[0]), int(dest[1])
        src_im = source.im
        if area is not None:
            ar = PgRect(area)
            src_im = src_im.crop((ar.x, ar.y, ar.right, ar.bottom))
        if src_im.mode == "RGBA":
            self.im.paste(src_im, (dx, dy), src_im)
        else:
            self.im.paste(src_im, (dx, dy))
        self.dr = ImageDraw.Draw(self.im)
    def subsurface(self, rect):
        r = PgRect(rect)
        cropped = self.im.crop((r.x, r.y, r.right, r.bottom))
        return PgSurface(cropped.size, pil_img=cropped)
    def get_clip(self): return self._clip
    def set_clip(self, rect):
        self._clip = rect if rect is not None else PgRect(0, 0, self.get_width(), self.get_height())

class PgDraw:
    @staticmethod
    def _col(surf, color):
        c = tuple(int(x) for x in color)
        if surf.im.mode == "RGBA" and len(c) == 3:
            return (*c, 255)
        return c
    @staticmethod
    def rect(surf, color, rect, width=0, border_radius=0):
        r = PgRect(rect)
        if r.w <= 0 or r.h <= 0:
            return
        c = PgDraw._col(surf, color)
        box = [r.x, r.y, r.right - 1, r.bottom - 1]
        if width == 0:
            surf.dr.rectangle(box, fill=c)
        else:
            surf.dr.rectangle(box, outline=c, width=int(width))
    @staticmethod
    def line(surf, color, start_pos, end_pos, width=1):
        c = PgDraw._col(surf, color)
        p1 = (int(start_pos[0]), int(start_pos[1]))
        p2 = (int(end_pos[0]), int(end_pos[1]))
        surf.dr.line([p1, p2], fill=c, width=max(1, int(width)))
    @staticmethod
    def lines(surf, color, closed, points, width=1):
        c = PgDraw._col(surf, color)
        pts = [(int(p[0]), int(p[1])) for p in points]
        if closed and len(pts) > 2:
            pts = pts + [pts[0]]
        surf.dr.line(pts, fill=c, width=max(1, int(width)))
    @staticmethod
    def circle(surf, color, center, radius, width=0):
        r = int(radius)
        if r <= 0:
            return
        cx, cy = int(center[0]), int(center[1])
        c = PgDraw._col(surf, color)
        box = [cx - r, cy - r, cx + r, cy + r]
        if width == 0:
            surf.dr.ellipse(box, fill=c)
        else:
            surf.dr.ellipse(box, outline=c, width=int(width))
    @staticmethod
    def polygon(surf, color, points, width=0):
        c = PgDraw._col(surf, color)
        pts = [(int(p[0]), int(p[1])) for p in points]
        if width == 0:
            surf.dr.polygon(pts, fill=c)
        else:
            surf.dr.polygon(pts, outline=c, width=int(width))
    @staticmethod
    def arc(surf, color, rect, start_angle, stop_angle, width=1):
        r = PgRect(rect)
        c = PgDraw._col(surf, color)
        deg1 = -math.degrees(stop_angle)
        deg2 = -math.degrees(start_angle)
        surf.dr.arc([r.x, r.y, r.right - 1, r.bottom - 1], start=deg1, end=deg2, fill=c, width=max(1, int(width)))

class PgTransform:
    @staticmethod
    def scale(surf, size, dest_surf=None):
        w, h = max(1, int(size[0])), max(1, int(size[1]))
        resized = surf.im.resize((w, h), resample=Image.Resampling.NEAREST)
        if dest_surf is not None:
            dest_surf.im.paste(resized, (0, 0))
            dest_surf.dr = ImageDraw.Draw(dest_surf.im)
            return dest_surf
        return PgSurface((w, h), pil_img=resized)
    @staticmethod
    def smoothscale(surf, size):
        w, h = max(1, int(size[0])), max(1, int(size[1]))
        resized = surf.im.resize((w, h), resample=Image.Resampling.BILINEAR)
        return PgSurface((w, h), pil_img=resized)
    @staticmethod
    def rotate(surf, angle):
        rot = surf.im.rotate(angle, resample=Image.Resampling.NEAREST, expand=True)
        return PgSurface(rot.size, pil_img=rot)

class PgImage:
    @staticmethod
    def load(path):
        im = Image.open(path).convert("RGBA")
        return PgSurface(im.size, pg.SRCALPHA, pil_img=im)

class PgDisplay:
    @staticmethod
    def get_init(): return False
    @staticmethod
    def get_surface(): return None

pg.Rect = PgRect
pg.Surface = PgSurface
pg.draw = PgDraw
pg.transform = PgTransform
pg.image = PgImage
pg.display = PgDisplay
for k in ("a","d","w","s","e","x","r","LEFT","RIGHT","UP","DOWN","SPACE","LSHIFT","RSHIFT","ESCAPE"):
    setattr(pg, f"K_{k}", hash(k) % 1000)

sys.modules["pygame"] = pg
pg.time = types.SimpleNamespace(get_ticks=lambda: 0)
