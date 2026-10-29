"""Fit the logical game canvas into an arbitrarily resized desktop window.

This is pure geometry, so it can be tested without Pygame or a display.
"""
from __future__ import annotations


def letterbox(canvas_size: tuple[int, int], window_size: tuple[int, int]) -> tuple[int, int, int, int]:
    """Return (left, top, width, height) with no cropping or stretching.

    Keep the camera and UI at fixed logical coordinates; only the finished
    frame is resized. Spare space is split between the two letterbox bars.
    """
    cw, ch = canvas_size
    ww, wh = window_size
    if ww <= 0 or wh <= 0:
        return (0, 0, 0, 0)  # Minimized window.
    if ww * ch <= wh * cw:
        width = ww
        height = max(1, round(ww * ch / cw))
    else:
        height = wh
        width = max(1, round(wh * cw / ch))
    return ((ww - width) // 2, (wh - height) // 2, width, height)
