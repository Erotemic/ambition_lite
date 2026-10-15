"""Test the real input semantics without opening a Pygame window."""

import pytest

from ambition_lite import settings
from ambition_lite.controls import (
    DEFAULT_PRESET, PRESETS, ControlReader, PadState, deadzone_stick,
)
from ambition_lite.gamepad import Gamepad
from ambition_lite.world import World

DT = 1 / 60


def test_default_matches_rusts_first_keyboard_preset():
    reader = ControlReader()
    preset = reader.preset
    assert DEFAULT_PRESET == 'classic'
    assert preset.movement == ('left', 'right', 'up', 'down')
    assert (preset.jump, preset.attack, preset.burst, preset.secondary,
            preset.projectile, preset.interact) == ('z', 'x', 'c', 'a', 'v', 'f')
    frame = reader.sample({'right', 'up', 'z', 'x', 'c', 'a', 'v', 'f'}).frame
    assert frame.right and frame.up and not frame.down
    assert (frame.jump, frame.light, frame.dash, frame.heavy,
            frame.fire, frame.interact) == (True,) * 6
    assert not ControlReader().sample({'a'}).frame.left


@pytest.mark.parametrize('name, movement, actions', [
    ('wasd', ('a', 'd', 'w', 's'), ('space', 'j', 'k', 'l', 'h', 'e')),
    ('qwer', ('left', 'right', 'up', 'down'), ('q', 'e', 'w', 'r', 'v', 'f')),
    ('uipo', ('a', 'd', 'w', 's'), ('u', 'p', 'i', 'o', 'l', 'e')),
])
def test_rust_alternate_presets(name, movement, actions):
    reader = ControlReader(name)
    assert reader.preset.movement == movement
    assert (reader.preset.jump, reader.preset.attack, reader.preset.burst,
            reader.preset.secondary, reader.preset.projectile,
            reader.preset.interact) == actions
    assert reader.sample({movement[1], actions[0], actions[1], actions[2]}).frame.dash


def test_each_preset_has_unique_action_keys_and_correct_hud():
    assert len({p.key for p in PRESETS}) == 4
    for preset in PRESETS:
        assert len({preset.jump, preset.attack, preset.burst, preset.secondary,
                    preset.projectile, preset.interact}) == 6
        assert preset.jump.upper() in preset.summary
        assert preset.interact.upper() in preset.help_line


def test_action_press_is_an_edge_and_does_not_auto_repeat():
    reader = ControlReader()
    assert reader.sample({'x', 'c'}).frame.light
    held = reader.sample({'x', 'c'}).frame
    assert not held.light and not held.dash
    reader.sample(set())
    released_and_repressed = reader.sample({'x', 'c'}).frame
    assert released_and_repressed.light and released_and_repressed.dash


def test_switching_preset_does_not_inject_attack_or_dash():
    reader = ControlReader()
    reader.sample({'right', 'x'})
    assert reader.cycle_preset().key == 'wasd'
    # A physically held J should not attack just because the preset changed.
    suppressed = reader.sample({'d', 'j', 'k'}, suppress_edges=True).frame
    assert suppressed.right and not suppressed.light and not suppressed.dash
    assert not reader.sample({'d', 'j', 'k'}).frame.light
    reader.sample({'d'})
    pressed = reader.sample({'d', 'j', 'k'}).frame
    assert pressed.light and pressed.dash


def test_rust_shift_is_walk_not_dash():
    reader = ControlReader()
    frame = reader.sample({'right', 'shift'}).frame
    assert frame.walk and not frame.dash
    world = World()
    world.step(DT, frame)
    assert world.player.vx == pytest.approx(settings.RUN_SPEED * .5)
    world.step(DT, reader.sample({'right', 'shift', 'c'}).frame)
    assert world.player.vx == settings.DASH_SPEED
    # Dash remains directional; releasing C does not repeat it.
    assert not reader.sample({'right', 'shift', 'c'}).frame.dash


def test_stick_walks_with_radial_deadzone():
    assert deadzone_stick(.10, -.10) == (0.0, 0.0)
    x, y = deadzone_stick(.59, 0.0)
    assert 0 < x < 1.0 and y == 0
    reader = ControlReader()
    frame = reader.sample(pad=PadState(stick_x=.59)).frame
    assert frame.move_x == pytest.approx(x)
    w = World()
    w.step(DT, frame)
    assert w.player.vx == pytest.approx(x * settings.RUN_SPEED)
    # Shift caps already-slow analog movement; it never boosts it.
    frame = reader.sample({'shift'}, PadState(stick_x=.32)).frame
    assert frame.walk and frame.move_x < .5


def test_dpad_direction_priority_over_stick_and_up_slash():
    reader = ControlReader()
    pad = PadState(frozenset({'left', 'up', 'west'}), stick_x=1.0, stick_y=1.0)
    frame = reader.sample(pad=pad).frame
    assert frame.left and not frame.right and frame.up and not frame.down
    w = World()
    w.step(DT, frame)
    assert w.player.attack.move.name == 'up'
    assert w.player.facing == -1


def test_gamepad_main_buttons_follow_rust_layout():
    reader = ControlReader()
    pad = PadState(frozenset({'south', 'west', 'rt', 'north', 'rb', 'east'}))
    frame = reader.sample(pad=pad).frame
    assert (frame.jump, frame.light, frame.dash, frame.fire,
            frame.interact, frame.heavy) == (True,) * 6
    # North is the projectile, east was Blink and is repurposed for heavy.
    assert not reader.sample(pad=pad).frame.jump
    reader.sample()
    assert reader.sample(pad=pad).frame.jump


def test_gamepad_start_and_back_controls_are_edges():
    reader = ControlReader()
    first = reader.sample(pad=PadState(frozenset({'start', 'back'})))
    assert first.pause and first.reset
    second = reader.sample(pad=PadState(frozenset({'start', 'back'})))
    assert not second.pause and not second.reset


class FakeController:
    def __init__(self):
        self.buttons = set()
        self.axes = {}

    def attached(self):
        return True

    def get_button(self, code):
        return code in self.buttons

    def get_axis(self, code):
        return self.axes.get(code, 0)


class FakeSdl:
    CONTROLLER_BUTTON_A = 1
    CONTROLLER_BUTTON_B = 2
    CONTROLLER_BUTTON_X = 3
    CONTROLLER_BUTTON_Y = 4
    CONTROLLER_BUTTON_RIGHTSHOULDER = 5
    CONTROLLER_BUTTON_START = 6
    CONTROLLER_BUTTON_BACK = 7
    CONTROLLER_BUTTON_DPAD_LEFT = 8
    CONTROLLER_BUTTON_DPAD_RIGHT = 9
    CONTROLLER_BUTTON_DPAD_UP = 10
    CONTROLLER_BUTTON_DPAD_DOWN = 11
    CONTROLLER_AXIS_TRIGGERRIGHT = 12
    CONTROLLER_AXIS_LEFTX = 13
    CONTROLLER_AXIS_LEFTY = 14


def test_sdl_adapter_trigger_hysteresis_and_button_names():
    pad = Gamepad.__new__(Gamepad)
    pad.api = FakeSdl()
    pad.device = FakeController()
    pad._trigger_down = False
    pad.device.buttons = {pad.api.CONTROLLER_BUTTON_A,
                          pad.api.CONTROLLER_BUTTON_DPAD_RIGHT}
    pad.device.axes = {pad.api.CONTROLLER_AXIS_LEFTX: 16384}
    a = pad.sample()
    assert a.buttons == frozenset({'south', 'right'})
    assert a.stick_x == pytest.approx(.5)
    pad.device.axes[pad.api.CONTROLLER_AXIS_TRIGGERRIGHT] = int(.57 * 32768)
    assert 'rt' in pad.sample().buttons
    pad.device.axes[pad.api.CONTROLLER_AXIS_TRIGGERRIGHT] = int(.41 * 32768)
    assert 'rt' in pad.sample().buttons
    pad.device.axes[pad.api.CONTROLLER_AXIS_TRIGGERRIGHT] = int(.24 * 32768)
    assert 'rt' not in pad.sample().buttons
    pad.device.axes[pad.api.CONTROLLER_AXIS_TRIGGERRIGHT] = int(.40 * 32768)
    assert 'rt' not in pad.sample().buttons
