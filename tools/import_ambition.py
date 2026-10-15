#!/usr/bin/env python3
"""Optional one-off importer of authored Ambition LDtk levels and SVG pose rigs.

    python tools/import_ambition.py --ambition-root ../ambition
    python tools/build_parts.py

Normal users never need this script: playable levels, pose samples, original SVGs,
and extracted PNGs are checked into ambition_lite. Importing fresh clips needs the
source repo's existing sprite renderer on PYTHONPATH, but the game does not.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROOMS = ('primeval_trailhead', 'primeval_run', 'primeval_rookery',
         'primeval_ridge', 'primeval_canopy', 'primeval_tyrant_hall')
CLIPS = {
    'robot': ('idle', 'walk', 'run', 'jump', 'fall', 'double_jump',
              'dash_startup', 'dash', 'dash_attack', 'jab', 'attack_side',
              'attack_up', 'attack_down', 'air_neutral', 'air_forward',
              'smash_forward', 'shoot', 'hit', 'celebrate', 'death'),
    'trex': ('idle', 'walk', 'charge', 'bite', 'roar', 'tail_swipe',
             'stomp', 'hurt', 'death', 'stunned'),
}
RIGS = {
    'robot': ('player_robot_v3/player_robot_v3.rig.json', 'player-robot-v3.svg'),
    'trex': ('trex_enemy/trex_enemy_side.rig.json', 'trex_enemy.svg'),
}


def rectangles(grid, width, height, val, size):
    """Turn horizontal same-type LDtk cells into readable platform rectangles."""
    spans = []
    for y in range(height):
        x = 0
        while x < width:
            if grid[y * width + x] != val:
                x += 1
                continue
            start = x
            while x < width and grid[y * width + x] == val:
                x += 1
            spans.append([start * size, y * size, (x - start) * size, size])
    # Coalesce vertical runs with identical horizontal bounds.
    merged = []
    active = {}
    for x, y, w, h in spans:
        key = (x, w)
        prev = active.get(key)
        if prev is not None and merged[prev][1] + merged[prev][3] == y:
            merged[prev][3] += h
        else:
            active[key] = len(merged)
            merged.append([x, y, w, h])
    return merged


def import_levels(source: Path):
    ldtk = source / 'game/ambition_map_assets/ambition_content/worlds/sandbox.ldtk'
    levels = json.loads(ldtk.read_text())['levels']
    for raw in levels:
        if raw['identifier'] not in ROOMS:
            continue
        collision = next(layer for layer in raw['layerInstances'] if layer['__identifier'] == 'Collision')
        entities = next(layer for layer in raw['layerInstances'] if layer['__identifier'] == 'Ambition')
        data = {
            'name': raw['identifier'], 'width': raw['pxWid'], 'height': raw['pxHei'],
            'solid': rectangles(collision['intGridCsv'], collision['__cWid'], collision['__cHei'], 1, 16),
            'platforms': rectangles(collision['intGridCsv'], collision['__cWid'], collision['__cHei'], 2, 16),
            'spawn': [90, raw['pxHei'] - 32 - 46], 'doors': [], 'enemies': [],
            'props': [], 'items': [], 'boss': None,
        }
        for entity in entities['entityInstances']:
            fields = {f['__identifier']: f['__value'] for f in entity['fieldInstances']}
            kind, xy = entity['__identifier'], entity['px']
            base = {'x': xy[0], 'y': xy[1], 'w': entity['width'], 'h': entity['height']}
            if kind == 'PlayerStart':
                data['spawn'] = xy
            elif kind == 'LoadingZone' and fields.get('target_room') in ROOMS:
                data['doors'].append({**base, 'target': fields['target_room'], 'side': 'east' if xy[0] > raw['pxWid'] / 2 else 'west'})
            elif kind == 'EnemySpawn':
                data['enemies'].append({**base, 'kind': fields['character_id']})
            elif kind == 'Prop':
                data['props'].append({**base, 'kind': fields['kind']})
            elif kind == 'GroundItem':
                data['items'].append({**base, 'kind': fields.get('held_item', fields.get('name', 'coconut'))})
            elif kind == 'BossSpawn':
                data['boss'] = {**base, 'kind': 'trex'}
        out = ROOT / 'assets/levels' / (data['name'] + '.json')
        out.write_text(json.dumps(data, indent=2) + '\n')
        print('room', data['name'], len(data['enemies']), 'enemies', len(data['platforms']), 'ledges')


def import_rigs(source: Path):
    sprites_root = source / 'tools/ambition_sprite2d_renderer'
    sys.path.insert(0, str(sprites_root))
    from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument
    for short, (rel, filename) in RIGS.items():
        rig_file = sprites_root / 'ambition_sprite2d_renderer/targets/characters/rigged' / rel
        original = RigDocument.load(rig_file)
        source_svg = original._svg_path()
        (ROOT / 'assets/svg' / filename).write_bytes(source_svg.read_bytes())
        meta = {
            'name': short,
            'frame': original.frame,
            'bones': [{'name': b['name'], 'parent': b.get('parent')} for b in original.bones],
            'svg_source': {**original.svg_source, 'filename': filename},
            'parts': [{k: part[k] for k in ('name', 'bone', 'z', 'include', 'pivot', 'rest_angle', 'opacity_channel', 'opacity_default', 'svg_source_order') if k in part}
                       for part in original.parts if part['kind'] == 'sprite'],
            'clips': {},
        }
        for name in CLIPS[short]:
            raw_clip = original.clips[name]
            frames = []
            for i in range(int(raw_clip['frames'])):
                t = original.frame_time(name, i)
                bone_world, params = original.solve(name, t)
                frames.append({
                    'bones': {k: [round(v.origin[0], 4), round(v.origin[1], 4), round(v.angle, 4)] for k, v in bone_world.items()},
                    'params': {k: round(float(v), 4) for k, v in params.items() if
                               k.endswith('_vis') or k.startswith('eye.') or
                               (k.startswith('bone.') and (k.endswith('.scale_y') or k.endswith('.flip_x') or k.endswith('.z')))},
                })
            meta['clips'][name] = {'loop': bool(raw_clip.get('loop', True)),
                                   'frame_ms': int(raw_clip['duration_ms']), 'frames': frames}
        (ROOT / 'assets/rigs' / f'{short}.json').write_text(json.dumps(meta, indent=2) + '\n')
        print('rig', short, len(meta['parts']), 'parts', len(meta['clips']), 'clips')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ambition-root', type=Path, required=True)
    args = parser.parse_args()
    source = args.ambition_root.resolve()
    import_levels(source)
    import_rigs(source)


if __name__ == '__main__':
    main()
