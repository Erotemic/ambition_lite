"""Thin optional SDL GameController adapter; all rules live in controls.py.

SDL maps Xbox, Playstation and other supported controllers onto named buttons.
We intentionally don't guess generic pygame.joystick indices: those vary by pad.
"""
from __future__ import annotations

from .controls import PadState


class Gamepad:
    """Use the first mapped controller; also detect plug/unplug at runtime."""

    def __init__(self):
        # Pygame is imported only when the actual game window starts.
        try:
            from pygame._sdl2 import controller
        except ImportError:
            controller = None

        self.api = controller
        self.device = None
        self._trigger_down = False
        if controller is not None:
            self.api.init()
            self.refresh()

    @property
    def connected(self) -> bool:
        return self.device is not None and self.device.attached()

    def refresh(self):
        if self.api is None:
            return
        if self.connected:
            return
        if self.device is not None:
            self.device.quit()
            self.device = None
        self._trigger_down = False
        for index in range(self.api.get_count()):
            if self.api.is_controller(index):
                self.device = self.api.Controller(index)
                break

    def sample(self) -> PadState:
        self.refresh()
        if not self.connected:
            return PadState()
        api = self.api
        device = self.device
        button_keys = {
            'south': api.CONTROLLER_BUTTON_A,
            'east': api.CONTROLLER_BUTTON_B,
            'west': api.CONTROLLER_BUTTON_X,
            'north': api.CONTROLLER_BUTTON_Y,
            'rb': api.CONTROLLER_BUTTON_RIGHTSHOULDER,
            'start': api.CONTROLLER_BUTTON_START,
            'back': api.CONTROLLER_BUTTON_BACK,
            'left': api.CONTROLLER_BUTTON_DPAD_LEFT,
            'right': api.CONTROLLER_BUTTON_DPAD_RIGHT,
            'up': api.CONTROLLER_BUTTON_DPAD_UP,
            'down': api.CONTROLLER_BUTTON_DPAD_DOWN,
        }
        buttons = {name for name, code in button_keys.items() if device.get_button(code)}
        trigger = max(0.0, device.get_axis(api.CONTROLLER_AXIS_TRIGGERRIGHT) / 32768.0)
        # Same release/press thresholds as Rust; no retrigger on trigger jitter.
        self._trigger_down = trigger > (.30 if self._trigger_down else .55)
        if self._trigger_down:
            buttons.add('rt')
        return PadState(
            buttons=frozenset(buttons),
            stick_x=device.get_axis(api.CONTROLLER_AXIS_LEFTX) / 32768.0,
            stick_y=device.get_axis(api.CONTROLLER_AXIS_LEFTY) / 32768.0,
        )
