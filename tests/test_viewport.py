"""Resizable display geometry is independent of Pygame/SDL."""

import pytest

from ambition_lite import settings
from ambition_lite.viewport import letterbox


def test_gameplay_view_is_not_reduced_by_the_hud():
    assert settings.VIEW_SIZE == (960, 540)
    assert settings.WINDOW_SIZE == (960, 540 + settings.HUD_HEIGHT)
    assert settings.HUD_HEIGHT == 56


@pytest.mark.parametrize('view_size', [settings.VIEW_SIZE, (320, 180)])
def test_painter_constructor_creates_gameplay_sized_sky(monkeypatch, tmp_path, view_size):
    pygame = pytest.importorskip('pygame')
    from ambition_lite import graphics

    # No desktop display is needed to exercise the constructor. Avoid sprite
    # loading here so the test checks viewport initialization specifically.
    pygame.font.init()
    (tmp_path / 'creatures').mkdir()
    monkeypatch.setattr(graphics, 'Puppet', lambda name: object())
    monkeypatch.setattr(graphics, 'asset_root', lambda: tmp_path)

    painter = graphics.Painter(view_size)
    assert (painter.width, painter.height) == view_size
    assert painter.sky.get_size() == view_size


@pytest.mark.parametrize('window,expected', [
    ((960, 596), (0, 0, 960, 596)),
    ((1920, 1192), (0, 0, 1920, 1192)),
    ((1280, 720), (60, 0, 1160, 720)),
    ((640, 480), (0, 41, 640, 397)),
    ((4, 4), (0, 1, 4, 2)),
    ((0, 0), (0, 0, 0, 0)),
])
def test_letterbox(window, expected):
    assert letterbox(settings.WINDOW_SIZE, window) == expected


def test_arbitrary_resizes_preserve_aspect_and_center():
    cw, ch = settings.WINDOW_SIZE
    for ww, wh in ((320, 200), (2400, 1200), (300, 1000), (8192, 720), (60, 60)):
        x, y, w, h = letterbox((cw, ch), (ww, wh))
        assert 0 <= x < ww and 0 <= y < wh
        assert 0 < w <= ww and 0 < h <= wh
        assert abs((ww - w) - 2 * x) <= 1
        assert abs((wh - h) - 2 * y) <= 1
        assert abs((w / h) - (cw / ch)) < .025


def test_footer_does_not_paint_over_gameplay_pixels():
    pygame = pytest.importorskip('pygame')
    from ambition_lite.graphics import Painter
    from ambition_lite.world import World

    pygame.font.init()
    canvas = pygame.Surface(settings.WINDOW_SIZE)
    canvas.fill((203, 17, 56))
    painter = Painter.__new__(Painter)  # HUD doesn't require sprite assets.
    painter.width, painter.height = settings.VIEW_SIZE
    painter.font = pygame.font.Font(None, 29)
    painter.small = pygame.font.Font(None, 22)
    painter._hud(canvas, World('primeval_canopy'))
    assert canvas.get_at((8, settings.VIEW_SIZE[1] - 1))[:3] == (203, 17, 56)
    assert canvas.get_at((8, settings.VIEW_SIZE[1] + 3))[:3] == (12, 30, 30)
