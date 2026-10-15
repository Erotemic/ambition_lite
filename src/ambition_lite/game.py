"""One screen, one event loop, one simulation. This is deliberately boring."""
from __future__ import annotations

import os
import pygame
from . import settings
from .audio import Soundboard
from .graphics import Painter
from .world import World, InputFrame


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
    show_pose_lab = False
    bones = list(painter.robot.rig.parents)
    selected = 0
    offsets: dict[str, float] = {}
    running = True
    while running:
        dt = min(1/20, clock.tick(settings.FPS) / 1000)
        newly = set()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                newly.add(event.key)
                if event.key == pygame.K_ESCAPE:
                    running = False
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
        if not running:
            break
        pressed = pygame.key.get_pressed()
        if not show_pose_lab:
            inp = InputFrame(
                left=bool(pressed[pygame.K_a] or pressed[pygame.K_LEFT]),
                right=bool(pressed[pygame.K_d] or pressed[pygame.K_RIGHT]),
                up=bool(pressed[pygame.K_w] or pressed[pygame.K_UP]),
                down=bool(pressed[pygame.K_s] or pressed[pygame.K_DOWN]),
                jump=pygame.K_SPACE in newly,
                dash=pygame.K_LSHIFT in newly or pygame.K_RSHIFT in newly,
                light=pygame.K_j in newly,
                heavy=pygame.K_k in newly,
                fire=pygame.K_l in newly,
                interact=pygame.K_e in newly,
            )
            world.step(dt, inp)
            sounds.play(world.events)
            sounds.change_music('boss' if world.boss else 'primeval')
        painter.track(world, dt)
        painter.render(screen, world, pose_lab=show_pose_lab,
                       pose_offsets=offsets, pose_bone=bones[selected])
        pygame.display.flip()
        if args.screenshot:
            pygame.image.save(screen, args.screenshot)
            print('Wrote screenshot:', args.screenshot)
            break
    pygame.quit()
    return 0
