"""Things that fly: the hero's fireballs and the keys the unused measures throw.

Each update moves a shot along a line and checks the whole line for hits.
That way a fast shot never jumps over a thin wall or a small enemy.
"""

import math

import pygame

from measure_killer.animation import Animation
from measure_killer.assets import Assets
from measure_killer.game import combat
from measure_killer.game.camera import Camera

FIREBALL_SPEED = 620.0
FIREBALL_DAMAGE = 30.0
FIREBALL_BLAST = 40.0  # pixels: the block it hits and most of the blocks next to it
FIREBALL_LIFE = 1.2
FIREBALL_SPRITE = "effects/fireball.png"
FIREBALL_FRAME = 16
FIRE_COLORS = ((255, 236, 140), (255, 160, 50), (230, 80, 30))
KEY_SPEED = 260.0  # slower than a fireball
KEY_DAMAGE = 12.0
KEY_HITS = 3  # a block breaks after this many keys hit it
KEY_LIFE = 3.0
KEY_SPRITE = "effects/thrown_key.png"
KEY_FRAME = 16


class Fireball:
    def __init__(self, x: float, y: float, angle: float, assets: Assets):
        self.pos = pygame.Vector2(x, y)
        self.direction = pygame.Vector2(math.cos(angle), math.sin(angle))
        self.angle = angle
        self.animation = Animation(assets.frames(FIREBALL_SPRITE, FIREBALL_FRAME, FIREBALL_FRAME, scale=2), fps=12)
        self.age = 0.0
        self.alive = True

    def update(self, world, dt: float) -> None:
        self.age += dt
        if self.age > FIREBALL_LIFE:
            self.alive = False
            return
        end = self.pos + self.direction * FIREBALL_SPEED * dt
        tile = world.tilemap.raycast(self.pos.x, self.pos.y, end.x, end.y)
        enemy, enemy_distance = world.first_enemy_on_line(self.pos, end, set())
        if enemy is not None and (tile is None or enemy_distance <= tile.distance):
            self.pos += self.direction * enemy_distance
            self._explode(world)
        elif tile is not None:
            # Step back a little from the wall, so the blast center is not inside the block.
            self.pos += self.direction * (tile.distance - 2)
            self._explode(world)
        else:
            self.pos = end
            if world.effects.wants_trail():
                world.effects.ember(self.pos.x, self.pos.y, FIRE_COLORS)

    def _explode(self, world) -> None:
        self.alive = False
        combat.fireball_blast(world, self.pos.x, self.pos.y, FIREBALL_BLAST, FIREBALL_DAMAGE)

    def draw(self, surface: pygame.Surface, camera: Camera) -> None:
        frame = pygame.transform.rotate(self.animation.frame(self.age), -math.degrees(self.angle))
        surface.blit(frame, frame.get_rect(center=camera.to_screen(self.pos.x, self.pos.y)))


class ThrownKey:
    """A calculator key an unused measure throws at the hero. It flies straight and chips the block it hits."""

    def __init__(self, x: float, y: float, direction: pygame.Vector2, assets: Assets):
        self.pos = pygame.Vector2(x, y)
        self.vel = direction.normalize() * KEY_SPEED if direction.length_squared() > 0 else pygame.Vector2(KEY_SPEED, 0)
        self.animation = Animation(assets.frames(KEY_SPRITE, KEY_FRAME, KEY_FRAME), fps=12)
        self.age = 0.0
        self.alive = True

    def update(self, world, dt: float) -> None:
        self.age += dt
        if self.age > KEY_LIFE:
            self.alive = False
            return
        end = self.pos + self.vel * dt
        player = world.player
        if player.alive and combat.segment_hits_rect(self.pos, end, player.body.rect) is not None:
            player.hurt(world, KEY_DAMAGE, self.vel.x)
            self.alive = False
            return
        tile = world.tilemap.raycast(self.pos.x, self.pos.y, end.x, end.y)
        if tile is not None:
            combat.chip_tile(world, *tile.cell, KEY_HITS)
            world.effects.sparks(tile.x, tile.y, tile.normal, count=4)
            self.alive = False
            return
        self.pos = end

    def draw(self, surface: pygame.Surface, camera: Camera) -> None:
        frame = self.animation.frame(self.age)
        surface.blit(frame, frame.get_rect(center=camera.to_screen(self.pos.x, self.pos.y)))
