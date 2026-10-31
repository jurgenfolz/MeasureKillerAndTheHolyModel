"""The far background behind the terrain. It scrolls slower than the camera, which adds depth."""

import pygame

from measure_killer.assets import Assets
from measure_killer.constants import ART_SCALE, ART_TILE, SCREEN_H, SCREEN_W
from measure_killer.game.camera import Camera
from measure_killer.game.materials import TILESET_PATH

SKY_COLOR = (107, 198, 255)
CAVE_COLOR = (34, 21, 29)
CAVE_TILES = ((0, 3), (0, 4), (0, 5), (13, 13), (12, 14))


class Backdrop:
    def __init__(self, theme: str, assets: Assets):
        # The sky repeats only sideways and sits at the bottom of the screen. The cave rock repeats both ways.
        self.repeat_vertically = theme == "cave"
        if theme == "cave":
            self.color = CAVE_COLOR
            self.layers = [(_cave_pattern(assets), 0.4)]
        else:
            self.color = SKY_COLOR
            self.layers = [
                (assets.image("Tiles/Assets/Background_2.png", ART_SCALE), 0.08),
                (assets.image("Tiles/Assets/Background_1.png", ART_SCALE), 0.2),
            ]

    def draw(self, surface: pygame.Surface, camera: Camera) -> None:
        surface.fill(self.color)
        for image, factor in self.layers:
            width, height = image.get_size()
            start_x = -(int(camera.x * factor) % width)
            if self.repeat_vertically:
                rows = range(-(int(camera.y * factor) % height), SCREEN_H, height)
            else:
                rows = [SCREEN_H - height]
            for y in rows:
                for x in range(start_x, SCREEN_W, width):
                    surface.blit(image, (x, y))


def _cave_pattern(assets: Assets) -> pygame.Surface:
    """Build a dark rock pattern from the tileset."""
    sheet = assets.image(TILESET_PATH)
    size = ART_TILE * ART_SCALE
    pattern = pygame.Surface((size * 8, size * 8))
    pattern.fill(CAVE_COLOR)
    for row in range(8):
        for col in range(8):
            cell = CAVE_TILES[(col * 5 + row * 3) % len(CAVE_TILES)]
            tile = sheet.subsurface((cell[0] * ART_TILE, cell[1] * ART_TILE, ART_TILE, ART_TILE))
            pattern.blit(pygame.transform.scale_by(tile, ART_SCALE), (col * size, row * size))
    pattern.fill((105, 96, 118), special_flags=pygame.BLEND_RGB_MULT)
    return pattern
