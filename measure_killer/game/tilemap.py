"""The terrain grid: which block sits in each cell, how damaged it is, and what blocks a line.

Every block can be destroyed.
The left and right edges of the map act as walls you cannot break.
Falling below the bottom edge kills you.
"""

import math
from dataclasses import dataclass
from enum import Enum, auto

from measure_killer.constants import TILE
from measure_killer.game.materials import Material


class TileHit(Enum):
    NONE = auto()  # there was no block
    DEFLECTED = auto()  # the shot was too weak
    DAMAGED = auto()
    DESTROYED = auto()


@dataclass
class RayHit:
    x: float
    y: float
    distance: float
    cell: tuple[int, int]
    normal: tuple[int, int]


class TileMap:
    def __init__(self, cells: list[list[Material | None]]):
        self.cells = cells
        self.height = len(cells)
        self.width = len(cells[0])
        self.hp = [[m.hp if m else 0.0 for m in row] for row in cells]
        # A broken block leaves a wall in the background. The wall keeps the old material for its look.
        self.walls: list[list[Material | None]] = [[None] * self.width for _ in range(self.height)]
        self.grass = [[self._starts_with_grass(x, y) for x in range(self.width)] for y in range(self.height)]
        self.original = [[m is not None for m in row] for row in cells]
        # Cells that changed since the renderer last looked. The renderer empties this list.
        self.changed: list[tuple[int, int]] = []

    @property
    def pixel_width(self) -> int:
        return self.width * TILE

    @property
    def pixel_height(self) -> int:
        return self.height * TILE

    def get(self, x: int, y: int) -> Material | None:
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.cells[y][x]
        return None

    def is_solid(self, x: int, y: int) -> bool:
        """Return True when a body cannot pass through this cell from the side."""
        if x < 0 or x >= self.width:
            return True
        material = self.get(x, y)
        return material is not None and not material.one_way

    def blocks_ray(self, x: int, y: int) -> bool:
        """Return True when bullets and eyesight cannot pass this cell. Thin platforms let them through."""
        return self.is_solid(x, y)

    def damage(self, x: int, y: int, power: float) -> TileHit:
        material = self.get(x, y)
        if material is None:
            return TileHit.NONE
        if power < material.toughness:
            return TileHit.DEFLECTED
        return self.wear(x, y, power)

    def wear(self, x: int, y: int, amount: float) -> TileHit:
        """Take hit points off a block, however tough it is. Return whether it broke."""
        if self.get(x, y) is None:
            return TileHit.NONE
        self.hp[y][x] -= amount
        if self.hp[y][x] <= 0:
            self.destroy(x, y)
            return TileHit.DESTROYED
        self.changed.append((x, y))
        return TileHit.DAMAGED

    def destroy(self, x: int, y: int) -> None:
        material = self.get(x, y)
        if material is None:
            return
        self.cells[y][x] = None
        self.hp[y][x] = 0.0
        self.grass[y][x] = False
        if material.leaves_wall:
            self.walls[y][x] = material
        self.changed.append((x, y))

    def damage_ratio(self, x: int, y: int) -> float:
        """Return 0 for an intact block and close to 1 for a nearly broken one."""
        material = self.get(x, y)
        if material is None:
            return 0.0
        return 1 - self.hp[y][x] / material.hp

    def destroyed_cells(self) -> list[list[int]]:
        """Return every cell that had a block at level start and is empty now. Save games store this."""
        return [
            [x, y]
            for y in range(self.height)
            for x in range(self.width)
            if self.original[y][x] and self.cells[y][x] is None
        ]

    def cells_in_circle(self, cx: float, cy: float, radius: float):
        """Yield (x, y, distance) for every block whose center lies within the radius."""
        left, right = int((cx - radius) // TILE), int((cx + radius) // TILE)
        top, bottom = int((cy - radius) // TILE), int((cy + radius) // TILE)
        for y in range(max(top, 0), min(bottom, self.height - 1) + 1):
            for x in range(max(left, 0), min(right, self.width - 1) + 1):
                if self.cells[y][x] is None:
                    continue
                distance = math.hypot((x + 0.5) * TILE - cx, (y + 0.5) * TILE - cy)
                if distance <= radius:
                    yield x, y, distance

    def raycast(self, x0: float, y0: float, x1: float, y1: float) -> RayHit | None:
        """Walk the grid from the start point to the end point and return the first blocking cell.

        This is the classic grid walk (Amanatides and Woo).
        It visits every cell the line touches, so a fast bullet cannot skip through a thin wall.
        """
        dx, dy = x1 - x0, y1 - y0
        length = math.hypot(dx, dy)
        cx, cy = int(x0 // TILE), int(y0 // TILE)
        if self.blocks_ray(cx, cy):
            return RayHit(x0, y0, 0.0, (cx, cy), (0, 0))
        if length == 0:
            return None
        dir_x, dir_y = dx / length, dy / length
        step_x = 1 if dir_x > 0 else -1
        step_y = 1 if dir_y > 0 else -1
        t_max_x = ((cx + (step_x > 0)) * TILE - x0) / dir_x if dir_x else math.inf
        t_max_y = ((cy + (step_y > 0)) * TILE - y0) / dir_y if dir_y else math.inf
        t_delta_x = TILE / abs(dir_x) if dir_x else math.inf
        t_delta_y = TILE / abs(dir_y) if dir_y else math.inf
        while True:
            if t_max_x < t_max_y:
                t = t_max_x
                t_max_x += t_delta_x
                cx += step_x
                normal = (-step_x, 0)
            else:
                t = t_max_y
                t_max_y += t_delta_y
                cy += step_y
                normal = (0, -step_y)
            if t > length:
                return None
            if self.blocks_ray(cx, cy):
                return RayHit(x0 + dir_x * t, y0 + dir_y * t, t, (cx, cy), normal)

    def line_of_sight(self, x0: float, y0: float, x1: float, y1: float) -> bool:
        return self.raycast(x0, y0, x1, y1) is None

    def _starts_with_grass(self, x: int, y: int) -> bool:
        material = self.cells[y][x]
        if material is None or not material.top_tiles:
            return False
        return y == 0 or self.cells[y - 1][x] is None
