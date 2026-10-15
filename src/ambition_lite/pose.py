"""Small, editable pose player: character = SVG parts + animated joints.

The slow original Ambition spline / IK solver is NOT needed in the game. Its
sampled joint positions are in assets/rigs/*.json. You can adjust individual
joints live (F2 pose lab), or author new poses by editing the JSON.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import math
from .content import asset_root


@dataclass
class Pose:
    bones: dict[str, tuple[float, float, float]]
    params: dict[str, float]


def interpolate_angle(a: float, b: float, ratio: float) -> float:
    delta = (b - a + 180) % 360 - 180
    return a + ratio * delta


class Rig:
    def __init__(self, name: str):
        self.name = name
        self.data = json.loads((asset_root() / 'rigs' / (name + '.json')).read_text())
        self.parts = self.data['parts']
        self.clips = self.data['clips']
        self.frame = self.data['frame']
        self.parents = {b['name']: b['parent'] for b in self.data['bones']}

    def sample(self, clip: str, seconds: float, *, interpolate: bool = True) -> Pose:
        if clip not in self.clips:
            clip = 'idle'
        data = self.clips[clip]
        frames = data['frames']
        n = len(frames)
        pos = max(0, seconds) / (data['frame_ms'] / 1000)
        if data['loop']:
            pos %= n
        else:
            pos = min(pos, n - 1)
        a = int(pos)
        b = (a + 1) % n if data['loop'] else min(a + 1, n - 1)
        ratio = pos - a if interpolate else 0.0
        before, after = frames[a], frames[b]
        bones = {}
        for name, (x1, y1, angle1) in before['bones'].items():
            x2, y2, angle2 = after['bones'][name]
            bones[name] = (x1 + (x2 - x1) * ratio,
                           y1 + (y2 - y1) * ratio,
                           interpolate_angle(angle1, angle2, ratio))
        param_keys = before['params'].keys() | after['params'].keys()
        params = {key: before['params'].get(key, 0.0) * (1 - ratio) +
                        after['params'].get(key, 0.0) * ratio
                  for key in param_keys}
        return Pose(bones, params)

    def adjust(self, pose: Pose, bone_name: str, degrees: float):
        """Pose one bone AND its children (so hands follow elbows, etc)."""
        if bone_name not in pose.bones:
            raise ValueError(f'Unknown bone {bone_name!r}')
        rootx, rooty, _ = pose.bones[bone_name]
        descendants = {bone_name}
        changed = True
        while changed:
            changed = False
            for name, parent in self.parents.items():
                if parent in descendants and name not in descendants:
                    descendants.add(name)
                    changed = True
        radians = math.radians(degrees)
        c, s = math.cos(radians), math.sin(radians)
        for name in descendants:
            x, y, angle = pose.bones[name]
            dx, dy = x - rootx, y - rooty
            pose.bones[name] = (rootx + dx * c - dy * s,
                                rooty + dx * s + dy * c, angle + degrees)
        return pose
