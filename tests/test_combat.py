import pytest

from ambition_lite.combat import MOVES, ActiveAttack
from ambition_lite.geometry import Rect
from ambition_lite.world import World, InputFrame

DT = 1/60


def test_hitbox_changes_with_direction_and_active_window():
    body = Rect(100, 300, 28, 46)
    forward = MOVES['side'].hitbox(body, +1)
    backward = MOVES['side'].hitbox(body, -1)
    upward = MOVES['up'].hitbox(body, +1)
    downward = MOVES['down'].hitbox(body, +1)
    assert forward.x > body.x
    assert backward.right < body.right
    assert upward.y < body.y
    assert downward.y > body.y
    attack = ActiveAttack(MOVES['side'])
    assert not attack.active
    attack.elapsed = .12
    assert attack.active
    attack.elapsed = 1.0
    assert attack.finished


def test_side_slash_damages_one_dinosaur_once():
    w = World()
    w.enemies = w.enemies[:1]
    target = w.enemies[0]
    target.x, target.y = w.player.x + 65, w.player.y
    target.hp = 7
    target.home_x = target.x
    w.step(DT, InputFrame(light=True))
    for i in range(23):
        w.step(DT)
    assert target.hp == 4
    for i in range(30):
        w.step(DT)
    assert target.hp == 4


def test_coconuts_can_be_collected_and_thrown():
    w = World()
    w.enemies = []
    w.player.x, w.player.y = 290, 434
    w.step(DT, InputFrame(light=True))
    assert w.player.carrying
    assert any(i.collected for i in w.items)
    w.step(DT, InputFrame(light=True))
    assert not w.player.carrying
    assert any(p.kind == 'coconut' for p in w.projectiles)


def test_bolt_can_defeat_dinosaur():
    w = World()
    w.enemies = w.enemies[:1]
    e = w.enemies[0]
    e.x = w.player.x + 110
    e.y = w.player.y
    e.hp = 2
    w.step(DT, InputFrame(fire=True))
    for _ in range(30):
        w.step(DT)
    assert not e.alive


def test_trex_phases_and_win_when_hp_zero():
    w = World('primeval_tyrant_hall')
    b = w.boss
    assert b.phase == 1
    b.hp = 25
    assert b.phase == 2
    b.hp = 10
    assert b.phase == 3
    b.hp = 3
    b.x, b.y = w.player.x + 72, w.player.y - 60
    w.step(DT, InputFrame(light=True))
    for _ in range(30):
        w.step(DT)
    assert b.hp == 0
    assert w.won
    assert any(e.name == 'victory' for e in w.events) is False  # one-time event already consumed
    old_x = w.player.x
    w.step(DT, InputFrame(right=True))
    assert w.player.x == old_x  # simulation freezes after win


def test_game_over_stops_simulation_and_restart_recovers():
    w = World()
    w.player.hp = 1
    w.hurt_player(1, -1)
    assert w.game_over
    x = w.player.x
    w.step(DT, InputFrame(right=True))
    assert w.player.x == x
    w.restart()
    assert w.player.hp > 1
    assert not w.game_over
