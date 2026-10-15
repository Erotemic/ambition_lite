"""A complete six-room platformer simulation, intentionally independent of Pygame.

World.step() is the only place time advances. The graphical window and the
teaching simulator both call it with the same InputFrame. Collision detection
is a few axis-aligned rectangle comparisons, not a general physics engine.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import math

from . import ai, settings
from .combat import MOVES, ActiveAttack
from .content import ROOMS, Level, load_level
from .geometry import Rect, clamp


@dataclass
class InputFrame:
    left: bool = False
    right: bool = False
    jump: bool = False          # true on NEW press, not while held
    dash: bool = False          # new press
    light: bool = False         # new press, may pick up a coconut
    heavy: bool = False         # new press
    fire: bool = False          # new press
    interact: bool = False      # new press, doors
    up: bool = False
    down: bool = False
    move_x: float | None = None  # optional analog movement (-1.0 to 1.0)
    walk: bool = False           # Shift caps movement speed, not dash


@dataclass
class Player:
    x: float
    y: float
    w: float = 28.0
    h: float = 46.0
    vx: float = 0.0
    vy: float = 0.0
    facing: int = 1
    hp: int = settings.PLAYER_MAX_HP
    on_ground: bool = True
    jumps: int = 0
    dash_time: float = 0.0
    dash_cooldown: float = 0.0
    invulnerable: float = 0.0
    attack: ActiveAttack | None = None
    shot_cooldown: float = 0.0
    carrying: bool = False
    pose_override: str | None = None

    @property
    def rect(self):
        return Rect(self.x, self.y, self.w, self.h)


@dataclass
class Enemy:
    id: int
    kind: str
    x: float
    y: float
    w: float
    h: float
    home_x: float
    home_y: float
    seed: float
    hp: int = 3
    vx: float = 0.0
    vy: float = 0.0
    facing: int = -1
    hurt_time: float = 0.0
    attack_cooldown: float = 0.0
    on_ground: bool = False
    alive: bool = True

    @property
    def rect(self):
        return Rect(self.x, self.y, self.w, self.h)


@dataclass
class Boss:
    x: float
    y: float
    w: float = 140
    h: float = 112
    hp: int = settings.TREX_MAX_HP
    max_hp: int = settings.TREX_MAX_HP
    facing: int = -1
    mode: str = 'idle'
    mode_time: float = 0.0
    rest_time: float = 0.0
    vx: float = 0.0
    hurt_time: float = 0.0
    hit_count: int = 0
    attack_landed: bool = False
    alive: bool = True

    @property
    def rect(self):
        return Rect(self.x, self.y, self.w, self.h)

    @property
    def phase(self) -> int:
        if self.hp <= 0:
            return 3
        if self.hp <= self.max_hp * .26:
            return 3
        if self.hp <= self.max_hp * .62:
            return 2
        return 1

    @property
    def attack_rect(self) -> Rect | None:
        if self.mode not in {'bite', 'stomp', 'tail_swipe'} or not (.26 < self.mode_time < .59):
            return None
        if self.mode == 'stomp':
            return Rect(self.x - 34, self.y + self.h - 38, self.w + 68, 52)
        if self.mode == 'tail_swipe':
            return Rect(self.x - 135 if self.facing > 0 else self.x + self.w - 14,
                        self.y + 40, 150, 76)
        return Rect(self.x + self.w - 10 if self.facing > 0 else self.x - 112,
                    self.y + 12, 122, 81)


@dataclass
class Projectile:
    kind: str
    x: float
    y: float
    vx: float
    vy: float
    damage: int
    lifetime: float = 1.4
    radius: float = 8.0

    @property
    def rect(self):
        return Rect(self.x - self.radius, self.y - self.radius,
                    self.radius * 2, self.radius * 2)


@dataclass
class Item:
    kind: str
    x: float
    y: float
    collected: bool = False

    @property
    def rect(self):
        return Rect(self.x, self.y, 18, 15)


@dataclass
class GameEvent:
    name: str
    x: float
    y: float
    amount: int = 0


class World:
    """The world is simple enough to inspect in a debugger or print in a lab."""

    def __init__(self, room_name: str = ROOMS[0]):
        self.room_name = room_name
        self.room: Level
        self.player: Player
        self.enemies: list[Enemy] = []
        self.items: list[Item] = []
        self.projectiles: list[Projectile] = []
        self.boss: Boss | None = None
        self.time = 0.0
        self.room_time = 0.0
        self.events: list[GameEvent] = []
        self.won = False
        self.game_over = False
        self.kills = 0
        self.load_room(room_name)

    def load_room(self, name: str, *, from_side: str = 'west'):
        """Move to a checkpoint; don't reset the player's health between rooms."""
        self.room = load_level(name)
        self.room_name = name
        spawn_x, spawn_y = self.room.spawn
        if from_side == 'east':
            spawn_x = self.room.width - 112
        hp = self.player.hp if hasattr(self, 'player') else settings.PLAYER_MAX_HP
        self.player = Player(float(spawn_x), float(spawn_y), hp=min(settings.PLAYER_MAX_HP, hp + (2 if hasattr(self, 'player') else 0)))
        # In the teaching edition, every second original LDtk spawn is active.
        # Retain the complete historical population in assets/levels/*.json.
        stride = max(1, settings.ENEMY_STEP)
        spawns = [e for i, e in enumerate(self.room.enemies)
                  if i % stride == 0 and e['kind'] != 'willson']
        # The final triceratops is a useful mini-boss regardless of density.
        spawns.extend(e for e in self.room.enemies if e['kind'] == 'triceratops' and e not in spawns)
        heavy = ai.HEAVIES
        self.enemies = [
            Enemy(id=i, kind=e['kind'], x=float(e['x']), y=float(e['y']),
                  w=float(e['w']), h=float(e['h']),
                  home_x=float(e['x']), home_y=float(e['y']), seed=float(i) * 1.7,
                  hp=6 if e['kind'] in heavy else 4 if e['kind'] in ai.CHARGERS else 2)
            for i, e in enumerate(spawns)
        ]
        self.items = [Item(e['kind'], float(e['x']), float(e['y'])) for e in self.room.items]
        self.projectiles = []
        self.boss = None
        if self.room.boss:
            e = self.room.boss
            self.boss = Boss(x=float(e['x']), y=float(e['y']),
                             w=float(e['w']), h=float(e['h']))
        self.room_time = 0.0
        self.events = [GameEvent('room', self.player.x, self.player.y)]

    def restart(self):
        """Restart this room; the first room is also the game's beginning."""
        self.player.hp = settings.PLAYER_MAX_HP
        self.game_over = False
        self.won = False
        self.load_room(self.room_name)

    def emit(self, kind: str, x: float, y: float, amount: int = 0):
        self.events.append(GameEvent(kind, x, y, amount))

    @staticmethod
    def _rect(raw: tuple[int, int, int, int]) -> Rect:
        return Rect(*raw)

    def _move_solid(self, actor, dt: float, *, one_way: bool = True):
        """Axis-by-axis separation; one-way ledges only catch falling feet."""
        if actor.vx:
            actor.x += actor.vx * dt
            body = actor.rect
            for raw in self.room.solids:
                wall = self._rect(raw)
                if body.overlaps(wall):
                    if actor.vx > 0:
                        actor.x = wall.x - actor.w
                    else:
                        actor.x = wall.right
                    actor.vx = 0.0
                    body = actor.rect
        bottom_before = actor.y + actor.h
        actor.y += actor.vy * dt
        actor.on_ground = False
        for raw in self.room.solids:
            solid = self._rect(raw)
            if actor.rect.overlaps(solid):
                if actor.vy > 0:
                    actor.y = solid.y - actor.h
                    actor.on_ground = True
                elif actor.vy < 0:
                    actor.y = solid.bottom
                actor.vy = 0.0
        if one_way and actor.vy >= 0:
            for raw in self.room.platforms:
                platform = self._rect(raw)
                body = actor.rect
                if (body.x < platform.right and body.right > platform.x and
                        bottom_before <= platform.y + 2 and body.bottom >= platform.y and
                        body.y < platform.y):
                    actor.y = platform.y - actor.h
                    actor.vy = 0.0
                    actor.on_ground = True
        actor.x = clamp(actor.x, 17, self.room.width - 17 - actor.w)
        actor.y = clamp(actor.y, 17, self.room.height - 16 - actor.h)
        if actor.y + actor.h >= self.room.height - 16:
            actor.on_ground = True
            actor.vy = min(0, actor.vy)

    def _try_coconut(self) -> bool:
        player = self.player
        if player.carrying:
            player.carrying = False
            self.projectiles.append(Projectile('coconut',
                player.rect.cx + player.facing * 24, player.y + 12,
                player.facing * 470, -220, damage=5, lifetime=1.6, radius=10))
            self.emit('throw', player.x, player.y)
            return True
        for item in self.items:
            if not item.collected and player.rect.expanded(32, 28).overlaps(item.rect):
                item.collected = True
                player.carrying = True
                self.emit('pickup', player.x, player.y)
                return True
        return False

    def _start_attack(self, keys: InputFrame):
        player = self.player
        if player.attack is not None:
            return
        if keys.light and self._try_coconut():
            return
        move = None
        if keys.heavy:
            move = MOVES['smash']
        elif keys.light:
            if keys.up:
                move = MOVES['up']
            elif keys.down:
                move = MOVES['down']
            elif not player.on_ground:
                move = MOVES['air']
            else:
                move = MOVES['side']
        if move is not None:
            player.attack = ActiveAttack(move)
            self.emit('swing', player.x, player.y)
        if keys.fire and player.shot_cooldown <= 0:
            player.shot_cooldown = .45
            self.projectiles.append(Projectile('bolt', player.rect.cx + 20 * player.facing,
                player.y + 18, player.facing * 610, -260 if keys.up else 0,
                damage=2, lifetime=1.1, radius=6))
            self.emit('shoot', player.x, player.y)

    def _player_step(self, keys: InputFrame, dt: float):
        p = self.player
        p.invulnerable = max(0, p.invulnerable - dt)
        p.dash_cooldown = max(0, p.dash_cooldown - dt)
        p.shot_cooldown = max(0, p.shot_cooldown - dt)
        horizontal = (int(keys.right) - int(keys.left) if keys.move_x is None
                      else clamp(keys.move_x, -1.0, 1.0))
        if horizontal:
            p.facing = 1 if horizontal > 0 else -1
        if keys.jump:
            if p.on_ground:
                p.vy = -settings.JUMP_SPEED
                p.jumps = 1
                p.on_ground = False
                self.emit('jump', p.x, p.y)
            elif p.jumps < 2:
                p.vy = -settings.DOUBLE_JUMP_SPEED
                p.jumps = 2
                self.emit('jump', p.x, p.y)
        if keys.dash and p.dash_cooldown <= 0:
            p.dash_time = settings.DASH_TIME
            p.dash_cooldown = settings.DASH_COOLDOWN
            self.emit('dash', p.x, p.y)
        if p.dash_time > 0:
            p.dash_time = max(0, p.dash_time - dt)
            p.vx = p.facing * settings.DASH_SPEED
        else:
            # Rust caps the movement axis at 0.5 for Shift+Move.
            if keys.walk:
                horizontal = clamp(horizontal, -settings.WALK_AXIS_CAP, settings.WALK_AXIS_CAP)
            p.vx = horizontal * settings.RUN_SPEED
        self._start_attack(keys)
        p.vy = min(settings.MAX_FALL_SPEED, p.vy + settings.GRAVITY * dt)
        self._move_solid(p, dt)
        if p.on_ground:
            p.jumps = 0

    def _hurt_enemy(self, e: Enemy, damage: int, force: int = 0):
        if not e.alive or e.hurt_time > 0:
            return False
        e.hp -= damage
        e.hurt_time = .14
        e.vx = float(force)
        self.emit('hit', e.x, e.y, damage)
        if e.hp <= 0:
            e.alive = False
            self.kills += 1
            self.emit('enemy_down', e.x, e.y)
        return True

    def _hurt_boss(self, damage: int):
        boss = self.boss
        if boss is None or not boss.alive or boss.hurt_time > 0:
            return False
        boss.hp = max(0, boss.hp - damage)
        boss.hurt_time = .12
        boss.hit_count += 1
        self.emit('boss_hit', boss.rect.cx, boss.y, damage)
        if boss.hp == 0:
            boss.alive = False
            boss.mode = 'death'
            boss.mode_time = 0
            self.won = True
            self.emit('victory', boss.rect.cx, boss.y)
        elif boss.hit_count % 4 == 0:
            boss.mode = 'stunned'
            boss.mode_time = 0
        return True

    def _attack_step(self, dt: float):
        p = self.player
        attack = p.attack
        if attack is None:
            return
        attack.elapsed += dt
        if attack.active:
            box = attack.move.hitbox(p.rect, p.facing)
            for e in self.enemies:
                if e.alive and e.id not in attack.hit_ids and box.overlaps(e.rect):
                    if self._hurt_enemy(e, attack.move.damage, p.facing * 70):
                        attack.hit_ids.add(e.id)
            if self.boss and self.boss.alive and -1 not in attack.hit_ids and box.overlaps(self.boss.rect):
                if self._hurt_boss(attack.move.damage):
                    attack.hit_ids.add(-1)
        if attack.finished:
            p.attack = None

    def _enemy_step(self, dt: float):
        p = self.player
        for e in self.enemies:
            if not e.alive:
                continue
            e.hurt_time = max(0, e.hurt_time - dt)
            e.attack_cooldown = max(0, e.attack_cooldown - dt)
            speed_x, speed_y = ai.decide_enemy_velocity(e, p, self.room_time)
            if abs(p.rect.cx - e.rect.cx) > 2:
                e.facing = 1 if p.rect.cx > e.rect.cx else -1
            if e.kind in ai.FLYERS:
                e.vx = speed_x * .7
                e.vy = speed_y
                e.x = clamp(e.x + e.vx * dt, 20, self.room.width - 20 - e.w)
                e.y = clamp(e.y + e.vy * dt, 42, self.room.height - 105)
                if (e.kind == 'african_swallow' and e.attack_cooldown <= 0 and
                        abs(p.rect.cx - e.rect.cx) < 70 and p.y - e.y > 85):
                    self.projectiles.append(Projectile('falling_coconut',
                        e.rect.cx, e.rect.bottom + 2, 0, 65, damage=2, radius=10))
                    e.attack_cooldown = 3.0
                    self.emit('drop', e.x, e.y)
            else:
                e.vx = speed_x
                e.vy = min(settings.MAX_FALL_SPEED, e.vy + settings.GRAVITY * dt)
                self._move_solid(e, dt)
                if (e.kind in ai.SPITTERS and e.attack_cooldown <= 0 and
                        abs(p.rect.cx - e.rect.cx) < 500):
                    e.attack_cooldown = 2.0
                    self.projectiles.append(Projectile('spit',
                        e.rect.cx, e.y + 20, e.facing * 245, -135,
                        damage=1, radius=7))
                    self.emit('spit', e.x, e.y)
            if e.rect.overlaps(p.rect) and p.invulnerable <= 0:
                self.hurt_player(settings.CONTACT_DAMAGE, e.facing)

    def hurt_player(self, damage: int, attacker_facing: int):
        p = self.player
        if p.invulnerable > 0 or self.won or self.game_over:
            return
        p.hp = max(0, p.hp - damage)
        p.invulnerable = 1.15
        p.vy = min(p.vy, -230)
        p.vx = attacker_facing * 180
        self.emit('player_hit', p.x, p.y, damage)
        if p.hp == 0:
            self.game_over = True
            self.emit('game_over', p.x, p.y)

    def _boss_step(self, dt: float):
        b = self.boss
        if b is None or not b.alive:
            return
        p = self.player
        b.hurt_time = max(0, b.hurt_time - dt)
        b.mode_time += dt
        b.rest_time = max(0, b.rest_time - dt)
        distance = p.rect.cx - b.rect.cx
        if abs(distance) > 18:
            b.facing = 1 if distance > 0 else -1
        phase = b.phase
        if b.mode == 'stunned':
            if b.mode_time > .75:
                b.mode, b.mode_time, b.rest_time = 'idle', 0, 1.1
            return
        if b.mode in {'bite', 'stomp', 'tail_swipe', 'roar'}:
            area = b.attack_rect
            if area and not b.attack_landed and area.overlaps(p.rect):
                self.hurt_player(2 if phase < 3 else 3, b.facing)
                b.attack_landed = True
            if b.mode_time >= (.93 if b.mode != 'roar' else .72):
                b.mode, b.mode_time, b.rest_time = 'idle', 0, (.85 if phase == 3 else 1.25)
            return
        if b.mode == 'charge':
            b.vx = b.facing * (220 if phase < 3 else 310)
            b.x = clamp(b.x + b.vx * dt, 20, self.room.width - b.w - 20)
            if b.rect.overlaps(p.rect):
                self.hurt_player(2, b.facing)
            if b.mode_time > .70:
                b.mode, b.mode_time, b.attack_landed = 'stomp', 0, False
                self.emit('boss_stomp', b.x, b.y)
            return
        if abs(distance) > 470:
            b.vx = 0
            return
        # The attack selection deliberately uses readable Python conditions.
        if b.rest_time > 0:
            return
        b.mode_time = 0.0
        b.attack_landed = False
        if abs(distance) > 225:
            b.mode = 'charge'
            self.emit('boss_charge', b.x, b.y)
        elif phase >= 2 and int(self.room_time * 1.2) % 3 == 0:
            b.mode = 'tail_swipe'
            self.emit('boss_roar', b.x, b.y)
        else:
            b.mode = 'bite'
            self.emit('boss_roar', b.x, b.y)

    def _projectile_step(self, dt: float):
        remaining = []
        for bullet in self.projectiles:
            bullet.lifetime -= dt
            bullet.x += bullet.vx * dt
            if bullet.kind != 'bolt':
                bullet.vy += 740 * dt
            bullet.y += bullet.vy * dt
            if bullet.lifetime <= 0 or bullet.x < 0 or bullet.x > self.room.width:
                continue
            if any(bullet.rect.overlaps(self._rect(r)) for r in self.room.solids):
                self.emit('impact', bullet.x, bullet.y)
                continue
            if bullet.kind in {'bolt', 'coconut'}:
                hit = False
                for e in self.enemies:
                    if e.alive and bullet.rect.overlaps(e.rect):
                        hit = self._hurt_enemy(e, bullet.damage, 80 if bullet.vx > 0 else -80)
                        if hit:
                            break
                if not hit and self.boss and self.boss.alive and bullet.rect.overlaps(self.boss.rect):
                    hit = self._hurt_boss(bullet.damage)
                if hit:
                    continue
            elif bullet.rect.overlaps(self.player.rect):
                self.hurt_player(bullet.damage, 1 if bullet.vx > 0 else -1)
                continue
            remaining.append(bullet)
        self.projectiles = remaining

    def _interact_door(self, keys: InputFrame) -> bool:
        if not keys.interact:
            return False
        for door in self.room.doors:
            if self.player.rect.expanded(24, 8).overlaps(Rect(door['x'], door['y'], door['w'], door['h'])):
                to = door['target']
                self.load_room(to, from_side='west' if door['side'] == 'east' else 'east')
                return True
        return False

    def nearby_door(self) -> dict | None:
        for door in self.room.doors:
            if self.player.rect.expanded(46, 8).overlaps(Rect(door['x'], door['y'], door['w'], door['h'])):
                return door
        return None

    def step(self, dt: float, keys: InputFrame | None = None):
        """Advance a frame; when not playing, do not mutate the game state."""
        if keys is None:
            keys = InputFrame()
        self.events = []
        if self.won or self.game_over:
            return
        dt = clamp(dt, 0.0, 1 / 25)  # bound a stalled desktop frame
        self.time += dt
        self.room_time += dt
        if self._interact_door(keys):
            return
        self._player_step(keys, dt)
        self._enemy_step(dt)
        self._attack_step(dt)
        self._boss_step(dt)
        self._projectile_step(dt)
