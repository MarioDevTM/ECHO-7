"""Consistent 2D pixel-art sprite loading and dimension-safe presentation.

Original artwork is cached at native size. A request for another footprint
returns a transparent target canvas containing an aspect-preserved sprite;
never squash circular fans or widen character-like decals into billboards.
"""
from collections import OrderedDict
from pathlib import Path
import pygame

ENV_ART = Path(__file__).resolve().parents[2] / 'data' / 'art' / 'environment'
_SOURCE_CACHE: dict[str, pygame.Surface | None] = {}
_SCALED_CACHE: OrderedDict[tuple[str, tuple[int, int]], pygame.Surface] = OrderedDict()
_SCALED_BYTES = 0
_MAX_SCALED_BYTES = 48 * 1024 * 1024
_MAX_SCALED_ENTRIES = 192


def get_env_sprite(name: str, size: tuple[int, int] | None = None) -> pygame.Surface | None:
    """Return an aspect-preserved sprite with bounded memory for scaled variants.

    Native art is retained; requested resized canvases use an LRU budget to
    prevent hundreds of distinct 80-level placements growing memory forever.
    """
    global _SCALED_BYTES
    if name not in _SOURCE_CACHE:
        p = ENV_ART / (name + '.png')
        if not p.is_file():
            _SOURCE_CACHE[name] = None
        else:
            image = pygame.image.load(str(p))
            if pygame.display.get_init() and pygame.display.get_surface() is not None:
                image = image.convert_alpha()
            _SOURCE_CACHE[name] = image
    source = _SOURCE_CACHE[name]
    if source is None or size is None:
        return source
    size = tuple(max(1, int(v)) for v in size)
    if size == source.get_size():
        return source

    key = name, size
    if key in _SCALED_CACHE:
        _SCALED_CACHE.move_to_end(key)
        return _SCALED_CACHE[key]

    sw, sh = source.get_size()
    dw, dh = size
    ratio = min(dw / sw, dh / sh)
    w, h = max(1, min(dw, round(sw * ratio))), max(1, min(dh, round(sh * ratio)))
    scaled = pygame.transform.scale(source, (w, h))
    canvas = pygame.Surface(size, pygame.SRCALPHA)
    canvas.blit(scaled, ((dw - w) // 2, (dh - h) // 2))

    estimate = dw * dh * 4
    if estimate <= _MAX_SCALED_BYTES:
        while (_SCALED_CACHE and
               (len(_SCALED_CACHE) >= _MAX_SCALED_ENTRIES or
                _SCALED_BYTES + estimate > _MAX_SCALED_BYTES)):
            old_key, old_surf = _SCALED_CACHE.popitem(last=False)
            _SCALED_BYTES -= old_surf.get_width() * old_surf.get_height() * 4
        _SCALED_CACHE[key] = canvas
        _SCALED_BYTES += estimate
    return canvas
