"""Four numbers and a rectangle: the collision code uses no Pygame internals."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class Rect:
    x: float
    y: float
    w: float
    h: float

    @property
    def right(self) -> float:
        return self.x + self.w

    @property
    def bottom(self) -> float:
        return self.y + self.h

    @property
    def cx(self) -> float:
        return self.x + self.w / 2

    @property
    def cy(self) -> float:
        return self.y + self.h / 2

    def overlaps(self, other: 'Rect') -> bool:
        return (self.x < other.right and self.right > other.x and
                self.y < other.bottom and self.bottom > other.y)

    def expanded(self, dx: float, dy: float) -> 'Rect':
        return Rect(self.x - dx, self.y - dy, self.w + 2 * dx, self.h + 2 * dy)


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))
