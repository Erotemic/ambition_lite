"""Readable and adjustable combat table, with startup / active / recovery.

A move describes the hitbox RELATIVE to the player's top-left. For sideways
moves x is measured in the direction the player faces; for upward moves the
rectangle crosses the body. The game never reads a Rust moveset at runtime.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from .geometry import Rect


@dataclass(frozen=True)
class Move:
    name: str
    animation: str
    startup: float
    active: float
    recovery: float
    damage: int
    reach: float
    height: float
    vertical: str = 'side'

    @property
    def duration(self):
        return self.startup + self.active + self.recovery

    def hitbox(self, body: Rect, facing: int) -> Rect:
        if self.vertical == 'up':
            return Rect(body.cx - self.reach * .5, body.y - self.height + 10,
                        self.reach, self.height)
        if self.vertical == 'down':
            return Rect(body.cx - self.reach * .5, body.bottom - 8,
                        self.reach, self.height)
        x = body.right - 4 if facing > 0 else body.x + 4 - self.reach
        return Rect(x, body.y - 12, self.reach, self.height)


MOVES = {
    'jab': Move('jab', 'jab', .055, .11, .12, 2, 65, 58),
    'side': Move('side', 'attack_side', .10, .16, .19, 3, 88, 78),
    'up': Move('up', 'attack_up', .10, .16, .18, 3, 80, 96, 'up'),
    'down': Move('down', 'attack_down', .09, .15, .18, 3, 82, 64, 'down'),
    'air': Move('air', 'air_neutral', .09, .20, .21, 3, 82, 82),
    'smash': Move('smash', 'smash_forward', .26, .20, .40, 7, 110, 88),
}


@dataclass
class ActiveAttack:
    move: Move
    elapsed: float = 0.0
    hit_ids: set[int] = field(default_factory=set)

    @property
    def active(self) -> bool:
        return self.move.startup <= self.elapsed < self.move.startup + self.move.active

    @property
    def finished(self) -> bool:
        return self.elapsed >= self.move.duration
