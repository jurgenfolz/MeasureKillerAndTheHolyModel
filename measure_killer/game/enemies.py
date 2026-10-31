"""The villains: unused measures.

An enemy only attacks while it can see the hero.
It sees him when he is close enough, in front of it, and no block stands in between (see World.can_see_player).
When it loses sight, it remembers his last spot for a short while and then gives up.
"""

import random

import pygame

from measure_killer.animation import Animation, mirrored
from measure_killer.assets import Assets
from measure_killer.constants import DANGER_RED, INK, POWER_BI_YELLOW, SOFT_WHITE, TILE
from measure_killer.game.camera import Camera
from measure_killer.game.physics import Body, approach
from measure_killer.game.projectiles import ThrownKey

SIGHT_CHECK_INTERVAL = 0.1
MEMORY_TIME = 2.5
TAUNT_CHANCE = 0.45
FEET_MARGIN = 2  # the sprite's feet end this many pixel rows above the bottom of the frame


class Enemy:
    # The sprites are horizontal strips of square frames facing east, like the hero's: a path and a frame rate.
    # The walk loops, every other pose plays once.
    SPRITES: dict[str, tuple[str, float]] = {}
    SIZE = (32, 32)  # width and height of the body
    EYE_Y = 8  # height of the eyes, measured from the top of the body
    MAX_HP = 30.0
    SIGHT_RANGE = 400.0
    CONTACT_DAMAGE = 10.0
    DEBRIS: tuple[tuple[int, int, int], ...] = ((120, 120, 120),)
    TAUNTS: tuple[str, ...] = ()

    def __init__(self, spawn_id: int | None, x: float, y: float, assets: Assets):
        """Place the enemy with its feet centered on (x, y)."""
        self.spawn_id = spawn_id
        self.assets = assets
        width, height = self.SIZE
        self.body = Body(x - width / 2, y - height, width, height)
        self.home = pygame.Vector2(self.body.rect.center)
        self._animations = {
            name: _both_ways(assets.strip(path), fps, loop=name == "walk") for name, (path, fps) in self.SPRITES.items()
        }
        font = assets.font(16)
        self._icons = {mark: _icon(font, mark) for mark in "!?"}
        self.hp = self.MAX_HP
        self.alive = True
        self.facing = -1
        self.pose = "walk"
        self.pose_time = random.uniform(0, 2)
        self.flash = 0.0
        self.alerted = False
        self.sees_player = False
        self.memory = 0.0
        self.last_seen: pygame.Vector2 | None = None
        self.icon: str | None = None
        self.icon_timer = 0.0
        self._sight_timer = random.uniform(0, SIGHT_CHECK_INTERVAL)

    @property
    def eye(self) -> pygame.Vector2:
        return pygame.Vector2(self.body.rect.centerx, self.body.rect.top + self.EYE_Y)

    @property
    def speech_anchor(self) -> pygame.Vector2:
        return pygame.Vector2(self.body.rect.centerx, self.body.rect.top - 10)

    def update(self, world, dt: float) -> None:
        self.pose_time += dt
        self.flash = max(0.0, self.flash - dt)
        self.icon_timer -= dt
        self._sight_timer -= dt
        if self._sight_timer <= 0:
            self._sight_timer = SIGHT_CHECK_INTERVAL
            self._look(world)
        self.think(world, dt)
        player = world.player
        if self.CONTACT_DAMAGE and player.alive and self.body.rect.colliderect(player.body.rect):
            player.hurt(world, self.CONTACT_DAMAGE, player.body.rect.centerx - self.body.rect.centerx)
            self.on_contact(world)

    def think(self, world, dt: float) -> None:
        """Move and attack. Each enemy type does this its own way."""

    def on_contact(self, world) -> None:
        """Called after the enemy touched and hurt the hero."""

    def set_pose(self, name: str) -> None:
        """Switch to another pose. A new pose starts its animation from the first frame."""
        if name != self.pose:
            self.pose = name
            self.pose_time = 0.0

    def _look(self, world) -> None:
        self.sees_player = world.can_see_player(self)
        if self.sees_player:
            self.last_seen = world.player.center
            self.memory = MEMORY_TIME
            if not self.alerted:
                self.alerted = True
                self._show_icon("!")
                world.audio.play("enemy_alert")
                if self.TAUNTS and random.random() < TAUNT_CHANCE:
                    world.say(self, random.choice(self.TAUNTS), 2.4)
        elif self.alerted:
            self.memory -= SIGHT_CHECK_INTERVAL
            if self.memory <= 0:
                self.alerted = False
                self._show_icon("?")

    @property
    def image(self) -> pygame.Surface:
        """Return the frame that shows right now, facing the right way."""
        right, left = self._animations[self.pose]
        return (right if self.facing > 0 else left).frame(self.pose_time)

    def take_hit(self, world, damage: float, direction: pygame.Vector2, source: str = "fire") -> None:
        """Hurt the enemy. The source is "sword" or "fire": it decides how the enemy dies."""
        if not self.alive:
            return
        self.hp -= damage
        self.flash = 0.1
        self.body.vel += direction * 90
        world.effects.blood(*self.body.rect.center, count=8, speed=200)
        world.effects.debris(*self.body.rect.center, self.DEBRIS, count=3, speed=110)
        if not self.alerted:
            # Getting hit makes it turn around, but it still has to see the hero to fight back.
            self.alerted = True
            self.memory = MEMORY_TIME
            self.last_seen = world.player.center
            self.face(world.player.center.x)
            self._show_icon("!")
        world.audio.play("enemy_hurt")
        if self.hp <= 0:
            self.alive = False
            world.on_enemy_killed(self, direction, source)

    def face(self, x: float) -> None:
        self.facing = 1 if x >= self.body.rect.centerx else -1

    def _show_icon(self, mark: str) -> None:
        self.icon = mark
        self.icon_timer = 0.9

    def draw(self, surface: pygame.Surface, camera: Camera) -> None:
        frame = self.image
        if self.flash > 0:
            frame = frame.copy()
            frame.fill((255, 255, 255), special_flags=pygame.BLEND_RGB_MAX)
        width, height = frame.get_size()
        rect = self.body.rect
        surface.blit(frame, camera.to_screen(rect.centerx - width / 2, rect.bottom - (height - FEET_MARGIN)))
        top = camera.to_screen(rect.centerx, rect.top)
        if self.hp < self.MAX_HP:
            bar = pygame.Rect(0, 0, 30, 5)
            bar.midbottom = (top[0], top[1] - 2)
            surface.fill(INK, bar)
            surface.fill(DANGER_RED, (bar.x + 1, bar.y + 1, round(28 * max(self.hp, 0) / self.MAX_HP), 3))
        if self.icon and self.icon_timer > 0:
            icon = self._icons[self.icon]
            surface.blit(icon, icon.get_rect(midbottom=(top[0], top[1] - 9)))


class UnusedMeasure(Enemy):
    """A walking calculator. It patrols on the ground, and charges when it sees you.

    Now and then, when you are a bit away, it throws one of its keys at you instead.
    """

    SPRITES = {"walk": ("enemies/measure/walk.png", 8.0), "throw": ("enemies/measure/throw.png", 10.0)}
    SIZE = (32, 54)
    EYE_Y = 14
    MAX_HP = 55.0
    SIGHT_RANGE = 380.0
    CONTACT_DAMAGE = 18.0
    WALK_SPEED = 45.0
    CHARGE_SPEED = 150.0
    THROW_CHANCE = 0.2  # one chance in five turns into a throw
    THROW_CHECK = 1.0  # seconds between two chances
    THROW_RANGE = 150.0  # it only throws when the hero is at least this far away
    THROW_MOMENT = 0.65  # how far into the throw the key leaves its hand, on the fling frame
    HAND = (12, 18)  # where the key leaves, in pixels in front of the body's middle and below its top
    DEBRIS = ((190, 190, 200), (120, 120, 140), (60, 60, 80), (220, 50, 70))
    TAUNTS = (
        "I might be used someday!",
        "Don't delete me! I'm [Total Sales v2 FINAL]!",
        "#ERROR! #ERROR!",
        "Nobody references me... so I'll reference YOU!",
    )

    def __init__(self, spawn_id: int | None, x: float, y: float, assets: Assets):
        super().__init__(spawn_id, x, y, assets)
        self.throw_time: float | None = None  # how long the current throw has run, or None between throws
        self.key_thrown = False
        self.throw_check = self.THROW_CHECK

    @property
    def throwing(self) -> bool:
        return self.throw_time is not None

    def think(self, world, dt: float) -> None:
        body = self.body
        if self.throwing:
            self._throw(world, dt)
            target = 0.0
        elif self.sees_player:
            self.face(world.player.center.x)
            target = self.facing * self.CHARGE_SPEED
            self._maybe_throw(world, dt)
        elif self.alerted and self.last_seen is not None and abs(self.last_seen.x - body.rect.centerx) > 12:
            self.face(self.last_seen.x)
            target = self.facing * self.CHARGE_SPEED * 0.7
        elif self.alerted:
            target = 0.0
        else:
            if body.on_ground and self._ledge_ahead(world):
                self.facing *= -1
            target = self.facing * self.WALK_SPEED
        body.vel.x = approach(body.vel.x, target, 900 * dt)
        body.move(world.tilemap, dt)
        if body.hit_wall:
            if self.alerted and body.on_ground and not self.throwing:
                body.vel.y = -520
            elif not self.alerted:
                self.facing = -body.hit_wall
        self.set_pose("throw" if self.throwing else "walk")

    def on_contact(self, world) -> None:
        self.body.vel.x = -self.facing * 220

    def _maybe_throw(self, world, dt: float) -> None:
        """Every so often, while the hero is far enough, roll the dice for a throw."""
        if abs(world.player.center.x - self.body.rect.centerx) < self.THROW_RANGE or not self.body.on_ground:
            return
        self.throw_check -= dt
        if self.throw_check > 0:
            return
        self.throw_check = self.THROW_CHECK
        if random.random() < self.THROW_CHANCE:
            self.start_throw()

    def start_throw(self) -> None:
        """Stop and throw a key at the hero. The key leaves partway through the throw animation."""
        self.throw_time = 0.0
        self.key_thrown = False

    def _throw(self, world, dt: float) -> None:
        self.throw_time += dt
        duration = self._animations["throw"][0].duration
        if not self.key_thrown and self.throw_time >= duration * self.THROW_MOMENT:
            self.key_thrown = True
            rect = self.body.rect
            hand = pygame.Vector2(rect.centerx + self.facing * self.HAND[0], rect.top + self.HAND[1])
            world.add_projectile(ThrownKey(hand.x, hand.y, world.player.center - hand, self.assets))
            world.audio.play("enemy_shoot")
        if self.throw_time >= duration:
            self.throw_time = None

    def _ledge_ahead(self, world) -> bool:
        rect = self.body.rect
        x = rect.centerx + self.facing * (rect.width / 2 + 4)
        return world.tilemap.get(int(x // TILE), int((rect.bottom + 4) // TILE)) is None


ENEMY_TYPES: dict[str, type[Enemy]] = {
    "measure": UnusedMeasure,
}


def _both_ways(frames: list[pygame.Surface], fps: float, loop: bool) -> tuple[Animation, Animation]:
    """Return the animation facing right and the same one facing left."""
    return Animation(frames, fps, loop), Animation(mirrored(frames), fps, loop)


def _icon(font: pygame.font.Font, mark: str) -> pygame.Surface:
    """A small "!" or "?" sign that pops up above an enemy's head."""
    text = font.render(mark, False, INK)
    icon = pygame.Surface((text.get_width() + 8, text.get_height() + 6), pygame.SRCALPHA)
    pygame.draw.rect(icon, INK, icon.get_rect(), border_radius=3)
    color = POWER_BI_YELLOW if mark == "!" else SOFT_WHITE
    pygame.draw.rect(icon, color, icon.get_rect().inflate(-4, -4), border_radius=2)
    icon.blit(text, (4, 3))
    return icon
