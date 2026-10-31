"""What happens when the sword, the fireball and a thrown key hit terrain and enemies."""

import math

import pygame

from measure_killer.constants import TILE
from measure_killer.game.materials import Material
from measure_killer.game.tilemap import TileHit

BREAK_ANYTHING = 1000  # a power no block can resist
SWORD_HITS = 2  # the sword needs this many hits to cut a block


def cut_tile(world, x: int, y: int, power: float) -> bool:
    """The sword hits a block, unless the block is too tough. It takes SWORD_HITS hits to cut it.

    Return True when the sword hit a block.
    """
    material = world.tilemap.get(x, y)
    if material is None:
        return False
    if material.toughness > power:
        world.effects.sparks((x + 0.5) * TILE, (y + 0.5) * TILE, (0, -1))
        world.audio.play("ricochet", 0.6)
        world.on_sword_deflected(material)
        return True
    _wear(world, x, y, material, SWORD_HITS)
    return True


def chip_tile(world, x: int, y: int, hits: int) -> None:
    """A thrown key chips a block, whatever it is made of. It takes this many keys to break the block."""
    material = world.tilemap.get(x, y)
    if material is not None:
        _wear(world, x, y, material, hits)


def _wear(world, x: int, y: int, material: Material, hits: int) -> None:
    """Take one of several hits off a block. The block breaks on the last one."""
    if world.tilemap.wear(x, y, material.hp / hits) == TileHit.DESTROYED:
        block_destroyed(world, x, y, material)
    else:
        world.effects.debris((x + 0.5) * TILE, (y + 0.5) * TILE, material.debris, count=4)
        world.audio.play("tile_break", 0.4)


def block_destroyed(world, x: int, y: int, material: Material, debris: int = 10) -> None:
    center_x, center_y = (x + 0.5) * TILE, (y + 0.5) * TILE
    world.effects.debris(center_x, center_y, material.debris, count=debris)
    world.audio.play("tile_break")


def fireball_blast(world, x: float, y: float, radius: float, damage: float) -> None:
    """A fireball bursts: every block within the radius breaks in one hit, and enemies in it burn. The hero is safe."""
    world.effects.fire_burst(x, y)
    world.audio.play("explosion", 0.5)
    world.camera.shake(4)
    for cx, cy, _ in list(world.tilemap.cells_in_circle(x, y, radius)):
        material = world.tilemap.get(cx, cy)
        if world.tilemap.damage(cx, cy, BREAK_ANYTHING) == TileHit.DESTROYED:
            block_destroyed(world, cx, cy, material, debris=5)
    reach = radius * 1.25
    for enemy in world.enemies:
        if not enemy.alive:
            continue
        push = pygame.Vector2(enemy.body.rect.center) - (x, y)
        distance = push.length()
        if distance > reach:
            continue
        direction = push.normalize() if distance > 0 else pygame.Vector2(0, -1)
        enemy.take_hit(world, damage * (1 - 0.5 * distance / reach), direction)


def segment_hits_rect(start: pygame.Vector2, end: pygame.Vector2, rect: pygame.FRect) -> float | None:
    """Return how far along the segment it first enters the rect, or None when it misses."""
    clipped = rect.clipline(start, end)
    if not clipped:
        return None
    return math.dist(start, clipped[0])
