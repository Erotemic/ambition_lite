"""Pygame presentation. Physics, damage, and level content live elsewhere.

Puppet sprites are NOT precomposed flipbooks: each frame is a new placement
of independently rasterized SVG arms, legs, face, blades, head, and body.
"""
from __future__ import annotations

from functools import lru_cache
import math
from pathlib import Path

import pygame

from . import ai, settings
from .content import ROOM_TITLES, ROOMS, asset_root
from .geometry import clamp
from .pose import Rig

SKY_TOP = (20, 36, 48)
SKY_BOTTOM = (75, 101, 74)
CREAM = (231, 240, 195)
DARK = (22, 36, 31)


def text(screen, font, message, xy, color=CREAM, *, center=False):
    render = font.render(str(message), True, color)
    area = render.get_rect(center=xy) if center else render.get_rect(topleft=xy)
    screen.blit(render, area)


class Puppet:
    """Draw one skeletal rig from per-part SVG PNGs and sampled joint poses."""

    def __init__(self, name: str):
        self.rig = Rig(name)
        root = asset_root() / 'parts' / name
        self.images = {part['name']: pygame.image.load(str(root / (part['name'] + '.png'))).convert_alpha()
                       for part in self.rig.parts}
        self.order = sorted(self.rig.parts, key=lambda p: p.get('z', 0))

    @lru_cache(maxsize=2200)
    def transformed(self, name: str, degrees: int, facing: int, zoom_percent: int):
        base = self.images[name]
        if facing < 0:
            base = pygame.transform.flip(base, True, False)
        return pygame.transform.rotozoom(base, -degrees, zoom_percent / 100.0)

    def draw(self, surface, name: str, seconds: float, foot: tuple[float, float],
             *, facing: int = 1, zoom: float = 1.0, offsets=None, debug=False):
        pose = self.rig.sample(name, seconds)
        if offsets:
            for bone, degree in offsets.items():
                if degree:
                    self.rig.adjust(pose, bone, degree)
        cx = self.rig.frame['center_x']
        ground_y = self.rig.frame['ground_y']
        layers = self.order
        if any(k.startswith('bone.') and k.endswith('.z') for k in pose.params):
            layers = sorted(layers, key=lambda p: p.get('z', 0) + pose.params.get('bone.' + p['bone'] + '.z', 0))
        for part in layers:
            channel = part.get('opacity_channel')
            opacity = pose.params.get(channel, part.get('opacity_default', 0.0)) if channel else 1.0
            if opacity < .16:
                continue
            bx, by, angle = pose.bones[part['bone']]
            # SVG part raster's pivot is in the cropped image, not at its center.
            src = self.images[part['name']]
            pivot_x, pivot_y = part['crop_pivot']
            if facing < 0:
                pivot_x = src.get_width() - pivot_x
            delta = (angle - part.get('rest_angle', 0.0)) * facing
            rounded_delta = int(round(delta / 2)) * 2
            percent = round(zoom * 100)
            transformed = self.transformed(part['name'], rounded_delta, facing, percent)
            rad = math.radians(rounded_delta)
            c, s = math.cos(rad), math.sin(rad)
            dx, dy = (pivot_x - src.get_width() * .5) * zoom, (pivot_y - src.get_height() * .5) * zoom
            offset_x, offset_y = dx * c - dy * s, dx * s + dy * c
            dest_x = foot[0] + (bx - cx) * zoom * facing - transformed.get_width() * .5 - offset_x
            dest_y = foot[1] + (by - ground_y) * zoom - transformed.get_height() * .5 - offset_y
            if opacity < .99:
                tinted = transformed.copy()
                tinted.set_alpha(int(opacity * 255))
                surface.blit(tinted, (round(dest_x), round(dest_y)))
            else:
                surface.blit(transformed, (round(dest_x), round(dest_y)))
        if debug:
            for name, (bx, by, angle) in pose.bones.items():
                x = int(foot[0] + (bx - cx) * zoom * facing)
                y = int(foot[1] + (by - ground_y) * zoom)
                pygame.draw.circle(surface, (255, 136, 72), (x, y), 3)


class Painter:
    def __init__(self, window_size=settings.WINDOW_SIZE):
        self.width, self.height = window_size
        self.font = pygame.font.Font(None, 29)
        self.small = pygame.font.Font(None, 22)
        self.big = pygame.font.Font(None, 72)
        self.robot = Puppet('robot')
        self.trex = Puppet('trex')
        self.creatures = {}
        for file in (asset_root() / 'creatures').glob('*.png'):
            self.creatures[file.stem] = pygame.image.load(str(file)).convert_alpha()
        self._scaled_creatures = {}
        self.sky = pygame.Surface(window_size)
        for y in range(self.height):
            t = y / max(1, self.height)
            col = tuple(int(a + (b - a) * t) for a, b in zip(SKY_TOP, SKY_BOTTOM))
            pygame.draw.line(self.sky, col, (0, y), (self.width, y))
        self.fx = []
        self.camera_x = 0.0
        self.camera_y = 0.0
        self.debug = False

    def track(self, world, dt: float):
        x = clamp(world.player.rect.cx - self.width * .35, 0,
                  max(0, world.room.width - self.width))
        y = clamp(world.player.rect.cy - self.height * .67, 0,
                  max(0, world.room.height - self.height))
        # The world doesn't depend on the camera; just smooth its presentation.
        amount = min(1, dt * 9)
        self.camera_x += (x - self.camera_x) * amount
        self.camera_y += (y - self.camera_y) * amount
        for ev in world.events:
            if ev.name in {'hit', 'boss_hit', 'enemy_down', 'player_hit'}:
                self.fx.append([ev.name, ev.x, ev.y, .58, ev.amount])
        for puff in self.fx:
            puff[3] -= dt
        self.fx = [p for p in self.fx if p[3] > 0]

    def pos(self, x: float, y: float):
        return (round(x - self.camera_x), round(y - self.camera_y))

    def _background(self, screen, world):
        screen.blit(self.sky, (0, 0))
        pygame.draw.circle(screen, (153, 174, 113),
                           (int(self.width * .81 - self.camera_x * .05) % (self.width + 240), 117), 55)
        # Simple parallax prehistoric ridgelines; geometry is generated, not a bitmap.
        for parallax, baseline, amplitude, color in (
            (.12, 320, 48, (42, 74, 69)),
            (.24, 386, 60, (35, 66, 53)),
            (.42, 452, 54, (25, 58, 46)),
        ):
            points = [(-2, self.height)]
            for px in range(-32, self.width + 65, 24):
                depth = math.sin((px + self.camera_x * parallax) / 130) * amplitude
                depth += math.sin((px + self.camera_x * parallax) / 49) * amplitude * .24
                points.append((px, int(baseline - self.camera_y * .08 + depth)))
            points.extend([(self.width + 2, self.height)])
            pygame.draw.polygon(screen, color, points)
        # Distant silhouettes repeat independently of level geometry.
        for i in range(-1, int(world.room.width // 240) + 3):
            x = int(i * 240 - self.camera_x * .45)
            if -100 < x < self.width + 100:
                height = 105 + (i * 43 % 90)
                ground = int(449 - self.camera_y * .13)
                pygame.draw.line(screen, (23, 49, 43), (x, ground), (x, ground - height), 8)
                for n in range(4):
                    yy = ground - height + n * 23
                    reach = 35 + n * 7
                    pygame.draw.polygon(screen, (24, 54, 44),
                                        ((x, yy - 34), (x - reach, yy + 28), (x + reach, yy + 28)))

    def _palm(self, screen, x, y, scale=1.0):
        sx, sy = self.pos(x + 72, y + 185)
        s = scale
        if sx < -160 or sx > self.width + 160:
            return
        pygame.draw.line(screen, (87, 59, 37), (sx, sy), (sx + 19 * s, sy - 135 * s), max(3, int(12*s)))
        top = (sx + 19 * s, sy - 135 * s)
        for v in range(8):
            angle = (v / 8) * 2 * math.pi
            tip = (top[0] + math.cos(angle) * 85 * s, top[1] + math.sin(angle) * 31 * s + 8 * s)
            middle = (top[0] + math.cos(angle) * 46 * s, top[1] + math.sin(angle) * 20 * s - 12 * s)
            pygame.draw.polygon(screen, (42 + v * 2, 103, 57), (top, middle, tip))
        pygame.draw.circle(screen, (113, 75, 39), (int(top[0] + 7*s), int(top[1] + 9*s)), max(2,int(8*s)))

    def _terrain(self, screen, world):
        for prop in world.room.props:
            if prop['kind'] == 'coconut_palm':
                self._palm(screen, prop['x'], prop['y'])
        for x, y, w, h in world.room.solids:
            posx, posy = self.pos(x, y)
            if posx > self.width or posx + w < 0 or posy > self.height or posy + h < 0:
                continue
            area = pygame.Rect(posx, posy, w, h)
            pygame.draw.rect(screen, (49, 64, 43), area)
            pygame.draw.rect(screen, (98, 129, 76), (posx, posy, w, min(8, h)))
            for tx in range(max(0, (posx//26)*26), min(self.width, posx + w), 26):
                pygame.draw.line(screen, (37, 54, 40), (tx, posy+12), (tx+7, posy+16), 1)
        for x, y, w, h in world.room.platforms:
            sx, sy = self.pos(x, y)
            if sx + w < 0 or sx > self.width:
                continue
            pygame.draw.rect(screen, (92, 75, 53), (sx, sy, w, 15), border_radius=3)
            pygame.draw.line(screen, (152, 188, 103), (sx, sy), (sx + w, sy), 5)
            for vine in range(sx + 20, sx + w, 34):
                pygame.draw.line(screen, (52, 100, 65), (vine, sy + 11), (vine+2, sy+27), 2)
        for door in world.room.doors:
            x, y = self.pos(door['x'], door['y'])
            pygame.draw.rect(screen, (37, 73, 70), (x, y, door['w'], door['h']), border_radius=11)
            pygame.draw.rect(screen, (104, 221, 174), (x+3, y+3, door['w']-6, door['h']-6), width=3, border_radius=10)
            pygame.draw.rect(screen, (71, 148, 123), (x+12, y+10, door['w']-24, door['h']-20), border_radius=8)
            text(screen, self.small, '>', (x+17, y+30), (226, 246, 174))

    def _items(self, screen, world):
        for it in world.items:
            if it.collected:
                continue
            x, y = self.pos(it.x, it.y)
            pygame.draw.ellipse(screen, (105, 62, 31), (x, y, 18, 15))
            pygame.draw.arc(screen, (214, 159, 92), (x+3,y+2,12,10), .3, 2.4, 2)
        for bullet in world.projectiles:
            x, y = self.pos(bullet.x, bullet.y)
            if bullet.kind in {'coconut', 'falling_coconut'}:
                col = (145, 95, 44)
            elif bullet.kind == 'bolt':
                col = (104, 240, 248)
            else:
                col = (157, 226, 69)
            pygame.draw.circle(screen, col, (x,y), int(bullet.radius))
            pygame.draw.circle(screen, (239, 247, 203), (x-2,y-2), max(2,int(bullet.radius/3)))

    def _creature(self, screen, e, elapsed):
        name = 'raptor_stalker' if e.kind == 'npc_raptor_stalker' else e.kind
        source = self.creatures.get(name)
        if source is None:
            return
        # Scale relative to authored collision body while keeping expressive art.
        target_h = max(32, int(e.h * (1.06 if e.kind in ai.FLYERS else 1.24)))
        target_w = int(source.get_width() * target_h / source.get_height())
        if target_w > e.w * 2.7:
            target_w = int(e.w * 2.7)
        dims = (max(3, target_w), max(3, target_h))
        key = (name, dims, e.facing)
        if key not in self._scaled_creatures:
            scaled = pygame.transform.smoothscale(source, dims)
            if e.facing < 0:
                scaled = pygame.transform.flip(scaled, True, False)
            self._scaled_creatures[key] = scaled
        art = self._scaled_creatures[key]
        wobble = math.sin(elapsed * 8 + e.seed) * (2 if e.kind in ai.FLYERS else 1)
        x, y = self.pos(e.rect.cx - art.get_width() / 2, e.rect.bottom - art.get_height() + wobble)
        screen.blit(art, (x,y))
        if e.hurt_time > 0:
            pygame.draw.circle(screen, (255, 220, 151), self.pos(e.rect.cx, e.rect.cy), 11, width=2)
        if self.debug:
            self._hitbox(screen, e.rect, (255,100,80))

    def _hitbox(self, screen, body, col):
        x,y = self.pos(body.x, body.y)
        pygame.draw.rect(screen, col, (x,y,body.w,body.h), width=1)

    def _robot(self, screen, world, *, pose_lab=False, pose_offsets=None):
        p = world.player
        if p.invulnerable > 0 and int(world.time * 13) % 2 == 0 and not pose_lab:
            return
        if pose_lab:
            clip, animation_s = 'idle', 0
        elif p.attack is not None:
            clip = p.attack.move.animation
            anim = self.robot.rig.clips[clip]
            length = anim['frame_ms'] / 1000 * (len(anim['frames']) - 1)
            animation_s = p.attack.elapsed / max(.001, p.attack.move.duration) * length
        elif p.dash_time > 0:
            clip, animation_s = 'dash', world.time
        elif not p.on_ground:
            clip, animation_s = ('jump' if p.vy < 0 else 'fall'), world.time
        elif abs(p.vx) > 15:
            clip, animation_s = 'run', world.time
        else:
            clip, animation_s = 'idle', world.time
        foot = self.pos(p.rect.cx, p.rect.bottom)
        self.robot.draw(screen, clip, animation_s, foot, facing=p.facing,
                        zoom=.74, offsets=pose_offsets, debug=pose_lab)
        if p.carrying:
            x, y = foot
            pygame.draw.ellipse(screen, (157, 91, 42), (x + p.facing * 23 - 8, y - 33, 15, 13))
        if p.attack and p.attack.active:
            area = p.attack.move.hitbox(p.rect, p.facing)
            ax, ay = self.pos(area.x, area.y)
            if self.debug:
                pygame.draw.rect(screen, (243, 226, 108), (ax, ay, area.w, area.h), 2)
            arc = pygame.Rect(ax - 12, ay - 12, area.w + 24, area.h + 24)
            pygame.draw.arc(screen, (152, 240, 249), arc, .2, 2.5, 6)
            pygame.draw.arc(screen, (241, 250, 210), arc.inflate(-12,-12), .35, 2.3, 2)
        if self.debug:
            self._hitbox(screen, p.rect, (119, 239, 238))

    def _boss(self, screen, world):
        b = world.boss
        if b is None:
            return
        name = b.mode if b.mode in self.trex.rig.clips else 'idle'
        foot = self.pos(b.rect.cx, b.rect.bottom)
        # Explicitly include death pose rather than making the boss vanish.
        self.trex.draw(screen, name, b.mode_time if b.mode != 'idle' else world.time,
                       foot, facing=b.facing, zoom=.48)
        if b.hurt_time > 0:
            pygame.draw.circle(screen, (248, 204, 123), self.pos(b.rect.cx, b.rect.cy), 40, width=3)
        if b.attack_rect and self.debug:
            self._hitbox(screen, b.attack_rect, (255, 68, 79))
        if self.debug:
            self._hitbox(screen, b.rect, (255, 185, 60))

    def _fx(self, screen):
        for kind, world_x, world_y, ttl, amount in self.fx:
            x, y = self.pos(world_x, world_y - (0.58-ttl) * 40)
            label = str(amount) if amount else '*'
            color = (255, 122, 88) if kind == 'player_hit' else (247, 227, 123)
            text(screen, self.font, label, (x,y), color, center=True)

    def _hud(self, screen, world, *, pose_lab=False, pose_bone='',
             control_preset=None, paused=False, gamepad_connected=False):
        top = pygame.Surface((self.width, 67), pygame.SRCALPHA)
        top.fill((15, 30, 28, 220))
        screen.blit(top, (0, 0))
        index = ROOMS.index(world.room_name)
        text(screen, self.font, ROOM_TITLES[index], (18, 11))
        text(screen, self.small, f'HP {world.player.hp}/{settings.PLAYER_MAX_HP}', (19, 40), (188, 230, 202))
        for i in range(settings.PLAYER_MAX_HP):
            pygame.draw.rect(screen, (241, 180, 102) if i < world.player.hp else (61, 72, 67),
                             (103 + i * 17, 43, 13, 11), border_radius=2)
        total_progress = index + (world.player.rect.cx / world.room.width)
        pygame.draw.line(screen, (58, 91, 82), (self.width - 253, 26), (self.width - 26, 26), 7)
        pygame.draw.circle(screen, (141, 237, 193), (int(self.width - 253 + total_progress / len(ROOMS) * 227), 26), 7)
        text(screen, self.small, f'{index+1}/{len(ROOMS)}  PRIMEVAL TRAIL', (self.width - 245, 42))
        b = world.boss
        if b and b.alive:
            total = 320
            bx = (self.width - total)//2
            pygame.draw.rect(screen, (56, 47, 38), (bx, 76, total, 14), border_radius=5)
            pygame.draw.rect(screen, (222, 125, 78), (bx, 76, int(total * b.hp/b.max_hp), 14), border_radius=5)
            text(screen, self.small, f'T-REX  {b.hp}/{b.max_hp}  / PHASE {b.phase}', (bx + total//2, 101), center=True)
        bottom = pygame.Surface((self.width, 56), pygame.SRCALPHA)
        bottom.fill((12, 30, 30, 215))
        screen.blit(bottom, (0, self.height - 56))
        if control_preset is not None:
            text(screen, self.small, control_preset.summary, (15, self.height - 49))
            text(screen, self.small, control_preset.help_line, (15, self.height - 26),
                 (184, 217, 199))
            if gamepad_connected:
                text(screen, self.small, 'PAD', (self.width - 54, 13), (144, 224, 196))
        door = world.nearby_door()
        if door and not pose_lab:
            key = control_preset.interact.upper() if control_preset else 'F'
            hint = key + '   ENTER  ' + door['target'].replace('primeval_', '').replace('_', ' ').upper()
            text(screen, self.font, hint, (self.width // 2, self.height - 80), (217, 249, 185), center=True)
        if pose_lab:
            msg = 'POSE LAB: TAB select joint  [ / ] rotate  R reset  F2 resume'
            pygame.draw.rect(screen, (14, 41, 49), (220, 124, 520, 82), border_radius=10)
            text(screen, self.font, msg, (235, 134), (220, 245, 185))
            text(screen, self.font, 'Selected: ' + pose_bone, (235, 166), (142, 233, 244))

    def render(self, screen, world, *, pose_lab=False, pose_offsets=None, pose_bone='',
               control_preset=None, paused=False, gamepad_connected=False):
        self._background(screen, world)
        self._terrain(screen, world)
        self._items(screen, world)
        for e in world.enemies:
            if e.alive:
                self._creature(screen, e, world.room_time)
        self._boss(screen, world)
        self._robot(screen, world, pose_lab=pose_lab, pose_offsets=pose_offsets)
        self._fx(screen)
        self._hud(screen, world, pose_lab=pose_lab, pose_bone=pose_bone,
                  control_preset=control_preset, paused=paused,
                  gamepad_connected=gamepad_connected)
        if world.won or world.game_over:
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((10, 22, 24, 195))
            screen.blit(overlay, (0, 0))
            if world.won:
                text(screen, self.big, 'THE TYRANT FALLS!', (self.width//2, 220), (242, 230, 152), center=True)
                text(screen, self.font, 'The Primeval Trail is yours.   R: replay boss room',
                     (self.width//2, 284), center=True)
            else:
                text(screen, self.big, 'ROBOT DOWN', (self.width//2, 220), (242, 168, 130), center=True)
                text(screen, self.font, 'R: retry this room', (self.width//2, 284), center=True)
        if paused and not pose_lab:
            dim = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            dim.fill((12, 24, 26, 165))
            screen.blit(dim, (0, 0))
            text(screen, self.big, 'PAUSED', (self.width // 2, 200),
                 (232, 245, 219), center=True)
            text(screen, self.font, 'ESC / START resume    Q quit    F4 keyboard preset',
                 (self.width // 2, 270), center=True)
