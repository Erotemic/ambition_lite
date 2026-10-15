import pytest

from ambition_lite import settings
from ambition_lite.ai import decide_enemy_velocity
from ambition_lite.world import World, InputFrame

DT = 1 / 60


def test_running_right_and_left_moves_the_robot():
    w = World()
    old = w.player.x
    for i in range(20):
        w.step(DT, InputFrame(right=True))
    assert w.player.x > old + 80
    for i in range(20):
        w.step(DT, InputFrame(left=True))
    assert w.player.x < old + 20
    assert w.player.facing == -1


def test_double_jump_but_no_third_jump():
    w = World()
    w.step(DT, InputFrame(jump=True))
    assert w.player.jumps == 1
    assert w.player.vy < 0
    w.step(DT, InputFrame(jump=True))
    assert w.player.jumps == 2
    assert w.player.vy < 0
    before = w.player.vy
    w.step(DT, InputFrame(jump=True))
    assert w.player.jumps == 2
    assert w.player.vy > before  # gravity only, no third jump impulse


def test_ground_restores_jump_count():
    w = World()
    w.step(DT, InputFrame(jump=True))
    for _ in range(180):
        w.step(DT)
    assert w.player.on_ground
    assert w.player.jumps == 0
    assert w.player.y == pytest.approx(480 - w.player.h)


def test_dash_has_burst_and_cooldown():
    w = World()
    w.step(DT, InputFrame(right=True, dash=True))
    assert w.player.vx == settings.DASH_SPEED
    cooldown = w.player.dash_cooldown
    assert cooldown > 0
    w.step(DT, InputFrame(dash=True))
    assert w.player.dash_cooldown < cooldown
    for _ in range(55):
        w.step(DT)
    w.step(DT, InputFrame(dash=True))
    assert w.player.vx == settings.DASH_SPEED


def test_one_way_platform_catches_descending_player():
    w = World()
    w.player.x = 655
    w.player.y = 315
    w.player.on_ground = False
    w.player.vy = 0
    for _ in range(100):
        w.step(DT)
    # first trailhead ledge starts at (620,400)
    assert w.player.y == pytest.approx(400 - w.player.h)
    assert w.player.on_ground


def test_readable_ai_direction_and_notice_range():
    w = World()
    enemy = w.enemies[0]
    enemy.x = w.player.x + 120
    vx, vy = decide_enemy_velocity(enemy, w.player, 0)
    assert vx < 0
    enemy.x = w.player.x + settings.ENEMY_NOTICE_RANGE + 200
    vx, vy = decide_enemy_velocity(enemy, w.player, 0)
    assert vx == 0
