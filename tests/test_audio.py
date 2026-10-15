"""Verify the optional soundboard without requiring an SDL device in CI."""
from pathlib import Path
from types import SimpleNamespace
import sys

from ambition_lite.audio import Soundboard
from ambition_lite.world import GameEvent


class FakeChannel:
    def __init__(self):
        self.played = []
        self.volume = None
        self.loops = []

    def stop(self):
        pass

    def play(self, sound, loops=0):
        self.played.append(sound)
        self.loops.append(loops)

    def set_volume(self, value):
        self.volume = value


class FakeMixer:
    def __init__(self):
        self.music = FakeChannel()
        self.effects = FakeChannel()
        self.reserved = 0

    def get_init(self):
        return True

    def Sound(self, filepath):
        return Path(filepath).stem

    def set_num_channels(self, n):
        self.num_channels = n

    def set_reserved(self, n):
        self.reserved = n

    def Channel(self, index):
        assert index == 0
        return self.music

    def find_channel(self):
        # Only ever offer the non-reserved effects channel.
        return self.effects


def test_music_and_fx_use_different_reserved_channels(monkeypatch):
    mixer = FakeMixer()
    monkeypatch.setitem(sys.modules, 'pygame', SimpleNamespace(mixer=mixer))
    board = Soundboard()
    assert board.enabled
    assert mixer.reserved == 1
    board.change_music('primeval')
    board.play([GameEvent('jump', 0, 0), GameEvent('dash', 0, 0)])
    assert mixer.music.played == ['primeval']
    assert mixer.music.loops == [-1]
    assert mixer.effects.played == ['jump', 'dash']
    board.change_music('boss')
    assert mixer.music.played == ['primeval', 'boss']


def test_silent_mode_needs_no_pygame():
    board = Soundboard(enabled=False)
    assert not board.enabled
    board.change_music('primeval')
    board.play([GameEvent('jump', 0, 0)])
