"""Moving boxes that collide with the terrain."""

import math

import pygame

from measure_killer.constants import GRAVITY, MAX_FALL_SPEED, TILE
from measure_killer.game.materials import Material
from measure_killer.game.tilemap import TileMap

MAX_SPEED = 900.0


class Body:
    """A box with a speed. It moves one axis at a time and stops at solid blocks."""

    def __init__(self, x: float, y: float, width: float, height: float):
        self.rect = pygame.FRect(x, y, width, height)
        self.vel = pygame.Vector2()
        self.on_ground = False
        self.hit_wall = 0  # -1 when it bumped a wall on the left, 1 on the right
        self.touched: set[Material] = set()

    def move(self, tilemap: TileMap, dt: float, gravity: bool = True, drop_through: bool = False) -> None:
        if gravity:
            self.vel.y = min(self.vel.y + GRAVITY * dt, MAX_FALL_SPEED)
        #! The speed limit keeps each step smaller than one tile, so a body never skips through a block.
        self.vel.x = max(-MAX_SPEED, min(MAX_SPEED, self.vel.x))
        self.vel.y = max(-MAX_SPEED, self.vel.y)
        self.touched.clear()
        self.rect.x += self.vel.x * dt
        self._collide_x(tilemap)
        old_bottom = self.rect.bottom
        self.rect.y += self.vel.y * dt
        self._collide_y(tilemap, old_bottom, drop_through)

    def _rows(self) -> range:
        return range(math.floor(self.rect.top / TILE), math.floor((self.rect.bottom - 0.01) / TILE) + 1)

    def _columns(self) -> range:
        return range(math.floor(self.rect.left / TILE), math.floor((self.rect.right - 0.01) / TILE) + 1)

    def _collide_x(self, tilemap: TileMap) -> None:
        self.hit_wall = 0
        if self.vel.x == 0:
            return
        moving_right = self.vel.x > 0
        column = math.floor((self.rect.right - 0.01) / TILE) if moving_right else math.floor(self.rect.left / TILE)
        for row in self._rows():
            if tilemap.is_solid(column, row):
                self._touch(tilemap, column, row)
                if moving_right:
                    self.rect.right = column * TILE
                    self.hit_wall = 1
                else:
                    self.rect.left = (column + 1) * TILE
                    self.hit_wall = -1
                self.vel.x = 0
                return

    def _collide_y(self, tilemap: TileMap, old_bottom: float, drop_through: bool) -> None:
        self.on_ground = False
        if self.vel.y == 0:
            return
        moving_down = self.vel.y > 0
        row = math.floor((self.rect.bottom - 0.01) / TILE) if moving_down else math.floor(self.rect.top / TILE)
        for column in self._columns():
            material = tilemap.get(column, row)
            if material is not None and material.one_way:
                lands = moving_down and not drop_through and old_bottom <= row * TILE + 0.5
                if not lands:
                    continue
            elif not tilemap.is_solid(column, row):
                continue
            self._touch(tilemap, column, row)
            if moving_down:
                self.rect.bottom = row * TILE
                self.on_ground = True
            else:
                self.rect.top = (row + 1) * TILE
            self.vel.y = 0
            return

    def _touch(self, tilemap: TileMap, column: int, row: int) -> None:
        material = tilemap.get(column, row)
        if material is not None:
            self.touched.add(material)


def approach(value: float, target: float, step: float) -> float:
    """Move value toward target by at most step."""
    if value < target:
        return min(value + step, target)
    return max(value - step, target)
