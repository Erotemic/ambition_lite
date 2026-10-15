"""One screen, one event loop, one simulation (with Rust-style controls)."""
from __future__ import annotations

import os
import pygame

from . import settings
from .audio import Soundboard
from .controls import ControlReader, KEY_NAMES
from .gamepad import Gamepad
from .graphics import Painter
from .world import World


def run(args):
    # Use the SDL dummy video driver for --screenshot in a headless CI job.
    if args.screenshot and not os.environ.get('DISPLAY') and not os.environ.get('WAYLAND_DISPLAY'):
        os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
        os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
    pygame.mixer.pre_init(frequency=22050, size=-16, channels=1, buffer=512)
    pygame.init()
    screen = pygame.display.set_mode(settings.WINDOW_SIZE)
    pygame.display.set_caption('Ambition Lite - The Primeval Trail')
    clock = pygame.time.Clock()
    world = World(args.room)
    painter = Painter()
    sounds = Soundboard(enabled=not args.mute)
    sounds.change_music('boss' if world.boss else 'primeval')

    controls = ControlReader(args.controls)
    # Query only keys declared by controls.py. Both shift keys mean "walk".
    key_codes = {name: pygame.key.key_code(name) for name in KEY_NAMES if name != 'shift'}
    pad = Gamepad()
    show_pose_lab = False
    paused = False
    bones = list(painter.robot.rig.parents)
    selected = 0
    offsets: dict[str, float] = {}
    running = True

    while running:
        dt = min(1/20, clock.tick(settings.FPS) / 1000)
        changed_preset = False
        toggle_pause = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and not getattr(event, 'repeat', False):
                if event.key == pygame.K_ESCAPE:
                    toggle_pause = True
                elif event.key == pygame.K_q and paused and not show_pose_lab:
                    running = False
                elif event.key == pygame.K_F4:
                    controls.cycle_preset()
                    changed_preset = True
                elif event.key == pygame.K_F3:
                    painter.debug = not painter.debug
                elif event.key == pygame.K_F2:
                    show_pose_lab = not show_pose_lab
                elif event.key == pygame.K_r:
                    if show_pose_lab:
                        offsets.clear()
                    else:
                        world.restart()
                        sounds.change_music('boss' if world.boss else 'primeval')
                if show_pose_lab:
                    if event.key == pygame.K_TAB:
                        selected = (selected + 1) % len(bones)
                    elif event.key == pygame.K_LEFTBRACKET:
                        offsets[bones[selected]] = offsets.get(bones[selected], 0) - 5
                    elif event.key == pygame.K_RIGHTBRACKET:
                        offsets[bones[selected]] = offsets.get(bones[selected], 0) + 5
            elif event.type == pygame.WINDOWFOCUSLOST:
                paused = True
        if not running:
            break

        pressed = pygame.key.get_pressed()
        held_keys = {name for name, key_code in key_codes.items() if pressed[key_code]}
        if pressed[pygame.K_LSHIFT] or pressed[pygame.K_RSHIFT]:
            held_keys.add('shift')
        sample = controls.sample(held_keys, pad.sample(),
                                 suppress_edges=changed_preset)
        if toggle_pause or sample.pause:
            paused = not paused
        if sample.reset and not show_pose_lab:
            world.restart()
            sounds.change_music('boss' if world.boss else 'primeval')

        if not show_pose_lab and not paused:
            world.step(dt, sample.frame)
            sounds.play(world.events)
            sounds.change_music('boss' if world.boss else 'primeval')
        painter.track(world, dt)
        painter.render(screen, world, pose_lab=show_pose_lab,
                       pose_offsets=offsets, pose_bone=bones[selected],
                       control_preset=controls.preset, paused=paused,
                       gamepad_connected=pad.connected)
        pygame.display.flip()
        if args.screenshot:
            pygame.image.save(screen, args.screenshot)
            print('Wrote screenshot:', args.screenshot)
            break
    pygame.quit()
    return 0
