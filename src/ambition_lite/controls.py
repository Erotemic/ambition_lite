"""Small input adapter based on Ambition's keyboard presets.

This module has no Pygame dependency: pass in held key names and an optional
controller sample, and receive a normal World.InputFrame. Students can change
bindings without changing the simulation or reading SDL device code.

Source: ambition_input/src/presets.rs (Ambition, 2026-10-15 archive).
The Blink/secondary key is deliberately reused for Lite's heavy attack.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import hypot
from typing import Collection

from .world import InputFrame


@dataclass(frozen=True)
class KeyboardPreset:
    key: str
    label: str
    movement: tuple[str, str, str, str]  # left, right, up, down
    jump: str
    attack: str
    burst: str
    secondary: str  # Blink in Rust; heavy attack in Lite
    projectile: str
    interact: str

    @property
    def summary(self) -> str:
        left, right, up, down = self.movement
        if (left, right) == ('left', 'right'):
            directions = 'ARROWS'
        else:
            directions = 'WASD'
        return (
            f'{directions} move/aim   {self.jump.upper()} jump x2   '
            f'{self.attack.upper()} slash   {self.burst.upper()} dash   '
            f'{self.secondary.upper()} smash   {self.projectile.upper()} bolt'
        )

    @property
    def help_line(self) -> str:
        return (
            f'{self.interact.upper()} door   SHIFT walk   F4 change preset   '
            'F2 pose lab   ESC pause'
        )


# Exact gameplay keys from Rust's KeyboardPreset::presets(), except Secondary
# which is intentionally the heavy attack in Lite (there is no Blink).
PRESETS = (
    KeyboardPreset('classic', 'Arrows + Z/X/C',
                   ('left', 'right', 'up', 'down'), 'z', 'x', 'c', 'a', 'v', 'f'),
    KeyboardPreset('wasd', 'WASD + Space/J/K/L',
                   ('a', 'd', 'w', 's'), 'space', 'j', 'k', 'l', 'h', 'e'),
    KeyboardPreset('qwer', 'Arrows + Q/W/E/R',
                   ('left', 'right', 'up', 'down'), 'q', 'e', 'w', 'r', 'v', 'f'),
    KeyboardPreset('uipo', 'WASD + U/I/P/O',
                   ('a', 'd', 'w', 's'), 'u', 'p', 'i', 'o', 'l', 'e'),
)
PRESET_BY_NAME = {preset.key: preset for preset in PRESETS}
DEFAULT_PRESET = 'classic'

# When using pygame.key.get_pressed, query only gameplay keys.
KEY_NAMES = frozenset(
    {key for preset in PRESETS for key in (
        *preset.movement, preset.jump, preset.attack, preset.burst,
        preset.secondary, preset.projectile, preset.interact,
    )} | {'shift'}
)


@dataclass(frozen=True)
class PadState:
    """Normalized SDL controller sample, independent of brand/button numbers.

    Positive stick_y means down, like the level coordinates.  The named
    buttons are: south, east, west, north, rb, rt, start, back, and D-pad dirs.
    """
    buttons: frozenset[str] = frozenset()
    stick_x: float = 0.0
    stick_y: float = 0.0


def deadzone_stick(x: float, y: float, deadzone: float = .18) -> tuple[float, float]:
    """Rust-like radial deadzone and rescaling for analog walking."""
    magnitude = hypot(x, y)
    if magnitude <= deadzone:
        return (0.0, 0.0)
    scale = min(1.0, (magnitude - deadzone) / (1.0 - deadzone)) / magnitude
    return (x * scale, y * scale)


@dataclass(frozen=True)
class ControlSample:
    frame: InputFrame
    pause: bool = False
    reset: bool = False


class ControlReader:
    """Convert held device buttons into just-pressed gameplay actions.

    Holding Attack during auto-repeat, switching presets or returning from
    Pose Lab must not produce repeated attacks. `suppress_edges` is useful for
    modal changes such as switching the keyboard preset mid-game.
    """

    def __init__(self, preset: str = DEFAULT_PRESET):
        self.preset = PRESET_BY_NAME[preset]
        self._previous = frozenset()

    def cycle_preset(self) -> KeyboardPreset:
        index = PRESETS.index(self.preset)
        self.preset = PRESETS[(index + 1) % len(PRESETS)]
        return self.preset

    def sample(self, keys: Collection[str] = (), pad: PadState | None = None,
               *, suppress_edges: bool = False) -> ControlSample:
        keys = frozenset(keys)
        pad = pad or PadState()
        buttons = pad.buttons
        preset = self.preset
        left, right, up, down = preset.movement

        analog_x, analog_y = deadzone_stick(pad.stick_x, pad.stick_y)
        # Physical D-pad inputs take precedence over the analog stick; an
        # active keyboard axis takes precedence over the controller's axis.
        dpad_x = int('right' in buttons) - int('left' in buttons)
        dpad_y = int('down' in buttons) - int('up' in buttons)
        pad_x = float(dpad_x) if 'right' in buttons or 'left' in buttons else analog_x
        pad_y = float(dpad_y) if 'down' in buttons or 'up' in buttons else analog_y
        key_x = int(right in keys) - int(left in keys)
        key_y = int(down in keys) - int(up in keys)
        axis_x = float(key_x) if left in keys or right in keys else pad_x
        axis_y = float(key_y) if up in keys or down in keys else pad_y

        active = frozenset(action for action, yes in (
            ('jump', preset.jump in keys or 'south' in buttons),
            ('light', preset.attack in keys or 'west' in buttons),
            ('dash', preset.burst in keys or 'rt' in buttons),
            ('heavy', preset.secondary in keys or 'east' in buttons),
            ('fire', preset.projectile in keys or 'north' in buttons),
            ('interact', preset.interact in keys or 'rb' in buttons),
            ('pause', 'start' in buttons),
            ('reset', 'back' in buttons),
        ) if yes)
        new_actions = active - self._previous
        self._previous = active
        if suppress_edges:
            new_actions = frozenset()

        return ControlSample(
            frame=InputFrame(
                left=axis_x < 0, right=axis_x > 0,
                up=axis_y < -.4, down=axis_y > .4,
                move_x=axis_x, walk='shift' in keys,
                jump='jump' in new_actions, dash='dash' in new_actions,
                light='light' in new_actions, heavy='heavy' in new_actions,
                fire='fire' in new_actions, interact='interact' in new_actions,
            ),
            pause='pause' in new_actions,
            reset='reset' in new_actions,
        )
