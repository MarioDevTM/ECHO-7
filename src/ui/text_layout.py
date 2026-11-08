"""Measured, bounds-aware UI text wrapping for pygame surfaces.

Every wrap decision uses Font.size, not a guessed character width. Split very long
unbroken tokens rather than allowing them to overflow. Pure layout functions can
be regression tested without opening the game window.
"""
from __future__ import annotations

import pygame
from functools import lru_cache

@lru_cache(maxsize=128)
def _font(font_name: str, px: int, bold: bool):
    # Font construction is not free; these sizes are reused every frame.
    if _font.cache_info().currsize == 0:
        pygame.register_quit(_font.cache_clear)
    return pygame.font.SysFont(font_name, px, bold=bold)


def wrap_text(text: str, font: pygame.font.Font, max_width: int) -> list[str]:
    if max_width < 1:
        raise ValueError("max_width must be positive")
    lines = []
    for paragraph in str(text).split("\n"):
        if not paragraph.strip():
            lines.append("")
            continue
        current = ""
        for word in paragraph.split():
            trial = (current + " " + word).strip()
            if font.size(trial)[0] <= max_width:
                current = trial
                continue
            if current:
                lines.append(current)
                current = ""
            if font.size(word)[0] <= max_width:
                current = word
                continue
            # No word may extend beyond the panel (including URLs and codes).
            segment = ""
            for glyph in word:
                trial = segment + glyph
                if segment and font.size(trial)[0] > max_width:
                    lines.append(segment)
                    segment = glyph
                else:
                    segment = trial
            current = segment
        if current:
            lines.append(current)
    return lines or [""]


def paginate(lines: list[str], max_lines: int) -> list[list[str]]:
    if max_lines < 1:
        raise ValueError("max_lines must be positive")
    return [lines[i:i + max_lines] for i in range(0, len(lines), max_lines)] or [[""]]


def draw_lines(surface: pygame.Surface, font: pygame.font.Font, lines: list[str],
               area: pygame.Rect, color, *, line_gap: int = 4, align: str = "left") -> None:
    """Draw only complete lines inside area; never paint outside its rectangle."""
    height = font.get_linesize()
    total = len(lines) * height + max(0, len(lines) - 1) * line_gap
    y = area.y + max(0, (area.height - total) // 2)
    old_clip = surface.get_clip()
    surface.set_clip(area.clip(old_clip))
    try:
        for line in lines:
            image = font.render(line, True, color)
            if align == "center":
                x = area.centerx - image.get_width() // 2
            elif align == "right":
                x = area.right - image.get_width()
            else:
                x = area.left
            surface.blit(image, (x, y))
            y += height + line_gap
    finally:
        surface.set_clip(old_clip)


def draw_fitted(surface: pygame.Surface, text: str, area: pygame.Rect,
                color, *, size: int = 20, min_size: int = 12,
                bold: bool = False, align: str = "center", line_gap: int = 2,
                font_name: str = "consolas") -> None:
    """Shrink font only when necessary and wrap within both axes of the area.

    Long freeform messages should use paginated panels instead. This is designed
    for headings, menu labels and short captions which must always fit.
    """
    if not str(text).strip():
        return
    inner = area.inflate(-2, -2)
    if inner.width <= 0 or inner.height <= 0:
        return
    for px in range(size, min_size - 1, -1):
        font = _font(font_name, px, bold)
        lines = wrap_text(text, font, inner.width)
        line_height = font.get_linesize()
        needed = len(lines) * line_height + (len(lines) - 1) * line_gap
        if needed <= inner.height:
            draw_lines(surface, font, lines, inner, color,
                       line_gap=line_gap, align=align)
            return
    # Extremely long titles are displayed within a clipped scroll-free area;
    # regular prose must use pagination to guarantee that *all* text is accessible.
    font = _font(font_name, min_size, bold)
    lines = wrap_text(text, font, inner.width)
    max_lines = max(1, (inner.height + line_gap) // (font.get_linesize() + line_gap))
    draw_lines(surface, font, lines[:max_lines], inner, color,
               line_gap=line_gap, align=align)
