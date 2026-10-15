#!/usr/bin/env python3
"""Write two original loopable chiptune tracks and simple gameplay SFX.

No soundfont, tracker, synthesizer, DAW, ffmpeg or NumPy required:
    python tools/build_audio.py
"""
from __future__ import annotations

from array import array
import math
from pathlib import Path
import random
import struct
import wave

ROOT = Path(__file__).resolve().parents[1] / 'assets/audio'
RATE = 22050


def note_number(name: str) -> int | None:
    if name in {'-', '.', ''}:
        return None
    pitch = {'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5,
             'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11}
    key = name[:-1]
    return pitch[key] + (int(name[-1]) + 1) * 12


def hz(name: str) -> float:
    midi = note_number(name)
    return 0 if midi is None else 440.0 * 2 ** ((midi - 69) / 12)


def osc(t: float, frequency: float, voice: str) -> float:
    if frequency <= 0:
        return 0.0
    phase = (t * frequency) % 1.0
    if voice == 'square':
        return 1.0 if phase < .5 else -1.0
    if voice == 'pulse':
        return 1.0 if phase < .22 else -.28
    if voice == 'triangle':
        return 1.0 - 4 * abs(phase - .5)
    if voice == 'sine':
        return math.sin(t * frequency * 2 * math.pi)
    raise ValueError(voice)


def add_note(mix: list[float], name: str, when: float, duration: float,
             volume: float, voice='square'):
    f = hz(name)
    if not f:
        return
    start = int(when * RATE)
    n = min(int(duration * RATE), len(mix)-start)
    for i in range(n):
        t = i / RATE
        envelope = min(1.0, t / .004) * min(1.0, (duration - t) / .047)
        mix[start+i] += osc(t, f, voice) * volume * max(0, envelope)


def drums(mix: list[float], beat: float, bars: int):
    randomizer = random.Random(60)
    for n in range(bars * 4):
        start = int(n * beat * RATE)
        kind = 'kick' if n % 4 in (0, 2) else 'snare'
        duration = .14 if kind == 'kick' else .1
        for i in range(min(int(duration * RATE), len(mix)-start)):
            t = i / RATE
            if kind == 'kick':
                f = 115 - 85 * min(1, t / .14)
                val = math.sin(2*math.pi*f*t) * math.exp(-t*23) * .27
            else:
                val = randomizer.uniform(-1,1) * math.exp(-t*27) * .17
            mix[start+i] += val


def write_wav(path: Path, signal: list[float]):
    # Soft limiting, then convert to signed 16-bit PCM.
    samples = array('h', (int(clamp * 32767) for x in signal
                          for clamp in [max(-.96, min(.96, x))]))
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), 'wb') as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(RATE)
        out.writeframes(samples.tobytes())


STAGE_LEAD = [
    'E5','G5','A5','-','G5','E5','D5','E5',
    'C5','E5','G5','-','A5','G5','E5','D5',
    'E5','G5','B5','A5','G5','E5','D5','C5',
    'D5','E5','G5','A5','E5','D5','C5','-',
    'G5','A5','B5','-','A5','G5','E5','G5',
    'F5','A5','C6','-','B5','A5','G5','E5',
    'E5','G5','A5','G5','E5','D5','C5','E5',
    'D5','E5','G5','-','E5','D5','C5','-',
]
STAGE_BASS = ['C3','C3','G2','G2','A2','A2','E3','E3',
              'F3','F3','C3','C3','G2','G2','C3','C3']
BOSS_LEAD = [
    'E5','E5','G5','A#5','A5','G5','E5','-',
    'D5','D5','F5','A5','G5','F5','D5','-',
    'E5','G5','A#5','C6','B5','A#5','G5','F5',
    'E5','E5','G5','B5','A#5','A5','G5','-',
    'A5','A5','C6','D6','C6','A5','G5','E5',
    'F5','F5','A5','C6','A5','G5','F5','D5',
    'E5','G5','B5','A#5','A5','G5','E5','D5',
    'E5','-','E5','G5','A5','G5','E5','-',
]
BOSS_BASS = ['E2','E2','E2','D2','D2','D2','C2','C2',
             'E2','E2','E2','F2','F2','G2','E2','E2']


def render_track(name: str, bpm: int, lead: list[str], bass: list[str]):
    beat = 60.0 / bpm
    bars = 8
    length = bars * 4 * beat
    mix = [0.0] * int(length * RATE)
    for i, pitch in enumerate(lead):
        add_note(mix, pitch, i * beat / 2, beat * .49, .18, 'pulse')
        if i % 2 == 0 and pitch not in {'-','.'}:
            # Counterpoint one octave lower, softly.
            add_note(mix, pitch[:-1] + str(int(pitch[-1]) - 1),
                     i * beat / 2, beat * .42, .035, 'triangle')
    for i in range(bars * 2):
        bass_pitch = bass[i % len(bass)]
        add_note(mix, bass_pitch, i * beat * 2, beat * 1.65, .16, 'triangle')
    drums(mix, beat, bars)
    write_wav(ROOT / (name + '.wav'), mix)
    print(f'composed {name}: {length:.1f}s, {bpm} bpm')


def sound_effect(name: str, pitch: float, duration: float, shape: str, glide: float = 0):
    randomizer = random.Random(17)
    mix = [0.0] * int(RATE * duration)
    for i in range(len(mix)):
        t = i / RATE
        env = min(1, t/.006) * ((1 - t / duration) ** 1.7)
        f = pitch + glide * (t / duration)
        if shape == 'noise':
            val = randomizer.uniform(-1, 1)
        else:
            val = osc(t, f, shape)
        mix[i] = val * env * .35
    write_wav(ROOT / (name + '.wav'), mix)


def main():
    render_track('primeval', 144, STAGE_LEAD, STAGE_BASS)
    render_track('boss', 156, BOSS_LEAD, BOSS_BASS)
    for values in (
        ('jump', 370, .18, 'triangle', 250),
        ('dash', 200, .15, 'pulse', -140),
        ('swing', 450, .12, 'noise', 0),
        ('hit', 290, .18, 'square', -200),
        ('boss_hit', 180, .24, 'square', -110),
        ('shoot', 900, .12, 'pulse', -500),
        ('pickup', 450, .16, 'triangle', 210),
        ('throw', 350, .16, 'triangle', -175),
        ('player_hit', 240, .24, 'noise', 0),
        ('enemy_down', 380, .16, 'square', -290),
        ('boss_roar', 175, .45, 'square', -95),
        ('boss_charge', 125, .32, 'pulse', 150),
        ('boss_stomp', 120, .36, 'noise', 0),
        ('victory', 680, .5, 'triangle', 190),
        ('room', 560, .25, 'triangle', 160),
        ('impact', 260, .10, 'noise', 0),
        ('drop', 430, .16, 'triangle', -130),
        ('spit', 490, .18, 'pulse', -250),
        ('game_over', 290, .5, 'triangle', -180),
    ):
        sound_effect(*values)
    print('audio complete')


if __name__ == '__main__':
    main()
