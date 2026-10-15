"""Optional Pygame soundboard, fed by generated WAV files."""
from __future__ import annotations

from .content import asset_root


class Soundboard:
    def __init__(self, enabled=True):
        self.enabled = False
        self.music_name = None
        self.sounds = {}
        if not enabled:
            return
        try:
            import pygame
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=22050, size=-16, channels=1)
            root = asset_root() / 'audio'
            self.sounds = {p.stem: pygame.mixer.Sound(str(p)) for p in root.glob('*.wav')}
            pygame.mixer.set_num_channels(12)
            # Channel 0 is the music loop. Reserve it so effects never
            # interrupt the score. find_channel() skips reserved channels.
            pygame.mixer.set_reserved(1)
            self.enabled = True
        except Exception as ex:  # SDL can fail when a machine has no audio device
            print('Audio disabled:', ex)

    def change_music(self, name: str):
        if not self.enabled or name == self.music_name:
            return
        import pygame
        self.music_name = name
        pygame.mixer.Channel(0).stop()
        sound = self.sounds.get(name)
        if sound:
            pygame.mixer.Channel(0).play(sound, loops=-1)
            pygame.mixer.Channel(0).set_volume(.19)

    def play(self, events):
        if not self.enabled:
            return
        import pygame
        for ev in events:
            name = ev.name
            if name == 'room':
                continue
            sound = self.sounds.get(name)
            if sound:
                channel = pygame.mixer.find_channel()
                if channel is not None:
                    channel.set_volume(.44)
                    channel.play(sound)
