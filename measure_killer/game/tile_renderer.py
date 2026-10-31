"""Draws the terrain.

Drawing thousands of tiles every frame is slow, so the map is cut into chunks.
Each chunk is drawn once into its own image, and only drawn again when one of its blocks changes.
"""

import random

import pygame

from measure_killer.assets import Assets
from measure_killer.constants import ART_SCALE, ART_TILE, TILE
from measure_killer.game.camera import Camera
from measure_killer.game.materials import DECORATIONS, TILESET_PATH, Cell, Material
from measure_killer.game.tilemap import TileMap

CHUNK_TILES = 16
CHUNK_PX = CHUNK_TILES * TILE
BACKING_COLOR = (52, 32, 43)
EDGE_COLOR = (33, 20, 28)
WALL_SHADE = (95, 90, 105)  # multiplied with the block art to make the background wall darker
DECORATION_CHANCE = 0.35
CRACK_STAGES = 3


class TileRenderer:
    def __init__(self, tilemap: TileMap, assets: Assets):
        self.tilemap = tilemap
        self._sheet = assets.image(TILESET_PATH)
        self._art: dict[Cell, pygame.Surface] = {}
        self._wall_art: dict[Cell, pygame.Surface] = {}
        self._chunks: dict[tuple[int, int], pygame.Surface] = {}
        self._cracks = _make_cracks()
        self._decorations = self._place_decorations()

    def draw(self, surface: pygame.Surface, camera: Camera) -> None:
        self._forget_changed_chunks()
        ox, oy = camera.offset
        view = camera.view_rect()
        first_cx, last_cx = max(view.left // CHUNK_PX, 0), view.right // CHUNK_PX
        first_cy, last_cy = max(view.top // CHUNK_PX, 0), view.bottom // CHUNK_PX
        for cy in range(first_cy, last_cy + 1):
            for cx in range(first_cx, last_cx + 1):
                if cx * CHUNK_TILES >= self.tilemap.width or cy * CHUNK_TILES >= self.tilemap.height:
                    continue
                chunk = self._chunks.get((cx, cy)) or self._build_chunk(cx, cy)
                surface.blit(chunk, (cx * CHUNK_PX - ox, cy * CHUNK_PX - oy))
        self._draw_details(surface, camera)

    def _draw_details(self, surface: pygame.Surface, camera: Camera) -> None:
        """Draw plants and cracks. They change often, so they skip the chunk cache."""
        ox, oy = camera.offset
        view = camera.view_rect()
        tm = self.tilemap
        for y in range(max(view.top // TILE, 0), min(view.bottom // TILE + 1, tm.height)):
            for x in range(max(view.left // TILE, 0), min(view.right // TILE + 1, tm.width)):
                decoration = self._decorations.get((x, y))
                if decoration is not None and tm.grass[y][x]:
                    surface.blit(decoration, (x * TILE - ox, (y - 1) * TILE - oy))
                ratio = tm.damage_ratio(x, y)
                if ratio > 0:
                    stage = min(int(ratio * CRACK_STAGES), CRACK_STAGES - 1)
                    surface.blit(self._cracks[stage], (x * TILE - ox, y * TILE - oy))

    def _forget_changed_chunks(self) -> None:
        for x, y in self.tilemap.changed:
            # A change also affects the edges drawn on the neighbor blocks, which can sit in another chunk.
            for nx, ny in ((x, y), (x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                self._chunks.pop((nx // CHUNK_TILES, ny // CHUNK_TILES), None)
        self.tilemap.changed.clear()

    def _build_chunk(self, cx: int, cy: int) -> pygame.Surface:
        chunk = pygame.Surface((CHUNK_PX, CHUNK_PX), pygame.SRCALPHA)
        tm = self.tilemap
        for y in range(cy * CHUNK_TILES, min((cy + 1) * CHUNK_TILES, tm.height)):
            for x in range(cx * CHUNK_TILES, min((cx + 1) * CHUNK_TILES, tm.width)):
                pos = ((x - cx * CHUNK_TILES) * TILE, (y - cy * CHUNK_TILES) * TILE)
                material = tm.cells[y][x]
                wall = tm.walls[y][x]
                if wall is not None and (material is None or material.see_through):
                    chunk.blit(self._wall(wall.tiles[_variant(x, y, len(wall.tiles))]), pos)
                if material is not None:
                    self._draw_block(chunk, material, x, y, pos)
        self._chunks[(cx, cy)] = chunk
        return chunk

    def _draw_block(self, chunk: pygame.Surface, material: Material, x: int, y: int, pos: tuple[int, int]) -> None:
        tm = self.tilemap
        grass = tm.grass[y][x]
        tiles = material.top_tiles if grass else material.tiles
        art = self._tile(tiles[_variant(x, y, len(tiles))])
        if not material.see_through and not grass:
            chunk.fill(BACKING_COLOR, (*pos, TILE, TILE))
        chunk.blit(art, pos)
        if material.see_through:
            return
        px, py = pos
        if not _has_edge_neighbor(tm, x - 1, y):
            chunk.fill(EDGE_COLOR, (px, py, 2, TILE))
        if not _has_edge_neighbor(tm, x + 1, y):
            chunk.fill(EDGE_COLOR, (px + TILE - 2, py, 2, TILE))
        if not _has_edge_neighbor(tm, x, y + 1):
            chunk.fill(EDGE_COLOR, (px, py + TILE - 2, TILE, 2))
        if not grass and not _has_edge_neighbor(tm, x, y - 1):
            chunk.fill(EDGE_COLOR, (px, py, TILE, 2))

    def _tile(self, cell: Cell) -> pygame.Surface:
        if cell not in self._art:
            source = self._sheet.subsurface((cell[0] * ART_TILE, cell[1] * ART_TILE, ART_TILE, ART_TILE))
            self._art[cell] = pygame.transform.scale_by(source, ART_SCALE)
        return self._art[cell]

    def _wall(self, cell: Cell) -> pygame.Surface:
        if cell not in self._wall_art:
            wall = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
            wall.fill(BACKING_COLOR)
            wall.blit(self._tile(cell), (0, 0))
            wall.fill(WALL_SHADE, special_flags=pygame.BLEND_RGB_MULT)
            self._wall_art[cell] = wall
        return self._wall_art[cell]

    def _place_decorations(self) -> dict[tuple[int, int], pygame.Surface]:
        tm = self.tilemap
        decorations = {}
        for y in range(1, tm.height):
            for x in range(tm.width):
                if not tm.grass[y][x] or (x - 1, y) in decorations:
                    continue
                rng = random.Random(x * 7919 + y * 104729)
                if rng.random() > DECORATION_CHANCE:
                    continue
                cells = rng.choice(DECORATIONS)
                fits = all(x + i < tm.width and tm.grass[y][x + i] for i in range(len(cells)))
                if fits:
                    decorations[(x, y)] = self._combine(cells)
        return decorations

    def _combine(self, cells: tuple[Cell, ...]) -> pygame.Surface:
        surface = pygame.Surface((TILE * len(cells), TILE), pygame.SRCALPHA)
        for i, cell in enumerate(cells):
            surface.blit(self._tile(cell), (i * TILE, 0))
        return surface


def _variant(x: int, y: int, count: int) -> int:
    """Pick a stable variant for a cell, so the same cell always looks the same."""
    # Mix the bits well. Without the mixing, two variants alternate in a strict ABAB pattern.
    h = (x * 73856093 ^ y * 19349663) & 0xFFFFFFFF
    h = ((h ^ (h >> 16)) * 0x45D9F3B) & 0xFFFFFFFF
    return (h ^ (h >> 16)) % count


def _has_edge_neighbor(tm: TileMap, x: int, y: int) -> bool:
    material = tm.get(x, y)
    if x < 0 or x >= tm.width:
        return True
    return material is not None and not material.see_through


def _make_cracks() -> list[pygame.Surface]:
    rng = random.Random(7)
    cracks = []
    lines: list[tuple[tuple[int, int], tuple[int, int]]] = []
    for _ in range(CRACK_STAGES):
        for _ in range(2):
            start = (rng.randint(6, TILE - 6), rng.randint(6, TILE - 6))
            end = (start[0] + rng.randint(-12, 12), start[1] + rng.randint(-12, 12))
            lines.append((start, end))
        surface = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        for start, end in lines:
            pygame.draw.line(surface, (25, 15, 20, 220), start, end, 2)
        cracks.append(surface)
    return cracks
