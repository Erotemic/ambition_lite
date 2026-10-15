"""Enemy AI: a handful of decisions, intended to be explored by students."""
from __future__ import annotations
import math
from . import settings

FLYERS = {'african_swallow', 'european_swallow', 'owl', 'vulture'}
SPITTERS = {'dilophosaurus'}
CHARGERS = {'npc_raptor_stalker', 'emu', 'cassowary', 'ostrich', 'ostrich_hen'}
HEAVIES = {'triceratops', 'pachycephalosaurus'}


def decide_enemy_velocity(enemy, player, elapsed: float) -> tuple[float, float]:
    """Return (horizontal speed, vertical speed) for the next frame.

    Predict -> modify -> investigate: what changes if the notice range is
    doubled? What happens if a flyer always moves toward player.y?
    """
    delta = player.rect.cx - enemy.rect.cx
    distance = abs(delta)
    pace = settings.enemy_speed(enemy.kind)
    if distance < settings.ENEMY_NOTICE_RANGE:
        # Close, but do not crowd a player from both sides every frame.
        horizontal = (1 if delta > 0 else -1) * pace if distance > 32 else 0.0
    else:
        # Stay near your original LDtk spawn; no complicated patrol system.
        horizontal = 0.0
    if enemy.kind in FLYERS:
        target_y = enemy.home_y + math.sin(elapsed * 2.4 + enemy.seed) * 25
        if distance < 230:
            target_y = min(target_y, player.y - 50)
        vertical = max(-120.0, min(120.0, (target_y - enemy.y) * 2.8))
    else:
        vertical = enemy.vy
    return horizontal, vertical
