"""Run the playable game or the teaching-friendly headless simulation.

    python -m ambition_lite
    python -m ambition_lite --headless --room primeval_run --frames 120
"""
from __future__ import annotations

import argparse
from .content import ROOMS
from .controls import PRESET_BY_NAME, DEFAULT_PRESET


def main(argv=None):
    parser = argparse.ArgumentParser(description='Ambition Lite: the Primeval Trail')
    parser.add_argument('--room', choices=ROOMS, default=ROOMS[0])
    parser.add_argument('--headless', action='store_true', help='run without Pygame, sprites, sound or a desktop')
    parser.add_argument('--frames', type=int, default=120, help='number of frames in a headless demonstration')
    parser.add_argument('--trace', action='store_true', help='print new game events from headless simulation')
    parser.add_argument('--mute', action='store_true', help='play without generated music or effects')
    parser.add_argument('--controls', choices=tuple(PRESET_BY_NAME), default=DEFAULT_PRESET,
                        help='Rust-style keyboard preset (can also cycle with F4)')
    parser.add_argument('--screenshot', metavar='PNG', help='save one Pygame frame then exit')
    args = parser.parse_args(argv)
    if args.headless:
        from .world import World, InputFrame
        world = World(args.room)
        for i in range(max(0, args.frames)):
            world.step(1/60, InputFrame(right=i % 240 < 160,
                                      jump=i in (30, 63),
                                      light=i % 45 == 0,
                                      dash=i % 210 == 140))
            if args.trace:
                for event in world.events:
                    print(f'{i:04}  {event.name:16} x={event.x:6.1f} y={event.y:6.1f}')
        print(f'room={world.room_name} frames={max(0,args.frames)} '
              f'pos=({world.player.x:.1f},{world.player.y:.1f}) '
              f'hp={world.player.hp} enemies={sum(e.alive for e in world.enemies)} '
              f'projectiles={len(world.projectiles)} won={world.won}')
        return 0
    from .game import run
    return run(args)


if __name__ == '__main__':
    raise SystemExit(main())
