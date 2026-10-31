"""The camera follows the hero and shakes when something big happens."""

import math
import random

import pygame

from measure_killer.constants import SCREEN_H, SCREEN_W


class Camera:
    def __init__(self, world_width: int, world_height: int):
        self.world_width = world_width
        self.world_height = world_height
        self.x = 0.0
        self.y = 0.0
        self._shake = 0.0
        self._shake_offset = (0, 0)

    def snap_to(self, target: pygame.Vector2) -> None:
        self.x, self.y = self._clamp(target.x - SCREEN_W / 2, target.y - SCREEN_H * 0.55)

    def follow(self, target: pygame.Vector2, dt: float) -> None:
        goal_x, goal_y = self._clamp(target.x - SCREEN_W / 2, target.y - SCREEN_H * 0.55)
        rate = 1 - math.exp(-7 * dt)
        self.x += (goal_x - self.x) * rate
        self.y += (goal_y - self.y) * rate
        self._shake = max(0.0, self._shake - 30 * dt)
        amount = self._shake
        self._shake_offset = (random.uniform(-amount, amount), random.uniform(-amount, amount))

    def shake(self, amount: float) -> None:
        self._shake = min(max(self._shake, amount), 14)

    @property
    def offset(self) -> tuple[int, int]:
        return (round(self.x + self._shake_offset[0]), round(self.y + self._shake_offset[1]))

    def to_screen(self, x: float, y: float) -> tuple[int, int]:
        ox, oy = self.offset
        return (round(x - ox), round(y - oy))

    def to_world(self, screen_pos: tuple[float, float]) -> pygame.Vector2:
        ox, oy = self.offset
        return pygame.Vector2(screen_pos[0] + ox, screen_pos[1] + oy)

    def view_rect(self, margin: int = 0) -> pygame.Rect:
        ox, oy = self.offset
        return pygame.Rect(ox - margin, oy - margin, SCREEN_W + 2 * margin, SCREEN_H + 2 * margin)

    def _clamp(self, x: float, y: float) -> tuple[float, float]:
        x = min(max(x, 0), max(self.world_width - SCREEN_W, 0))
        y = min(max(y, 0), max(self.world_height - SCREEN_H, 0))
        return x, y
