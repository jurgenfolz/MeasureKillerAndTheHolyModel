"""Loads images and fonts from the resources folder and keeps them in memory.

A missing image never crashes the game.
It shows as a magenta box, so you can see what still needs art.
"""

from pathlib import Path

import pygame

from measure_killer.constants import FONTS_DIR, RESOURCES_DIR

FONT_FILE = FONTS_DIR / "PressStart2P-Regular.ttf"
PLACEHOLDER_COLOR = (255, 0, 255)


class Assets:
    def __init__(self, root: Path = RESOURCES_DIR):
        self.root = root
        self._images: dict[tuple[str, float], pygame.Surface | None] = {}
        self._fonts: dict[int, pygame.font.Font] = {}
        self._frames: dict[tuple, list[pygame.Surface]] = {}

    def image(self, path: str, scale: float = 1) -> pygame.Surface:
        """Return the image at this path inside resources, scaled with sharp pixels."""
        surface = self._load(path, scale)
        return surface if surface is not None else _placeholder((32, 32))

    def strip(self, path: str) -> list[pygame.Surface]:
        """Cut a horizontal strip of square frames. The frame size is the height of the strip."""
        size = self.image(path).get_height()
        return self.frames(path, size, size)

    def frames(self, path: str, frame_w: int, frame_h: int, scale: float = 1, row: int | None = None) -> list[pygame.Surface]:
        """Cut a sprite sheet into frames, left to right and top to bottom.

        Pass a row number to get only the frames of that row.
        """
        key = (path, frame_w, frame_h, scale, row)
        if key not in self._frames:
            self._frames[key] = self._cut(path, frame_w, frame_h, scale, row)
        return self._frames[key]

    def _cut(self, path: str, frame_w: int, frame_h: int, scale: float, row: int | None) -> list[pygame.Surface]:
        sheet = self._load(path, 1)
        if sheet is None:
            return [_placeholder((round(frame_w * scale), round(frame_h * scale)))]
        rows = range(sheet.get_height() // frame_h) if row is None else [row]
        frames = []
        for r in rows:
            for col in range(sheet.get_width() // frame_w):
                frame = sheet.subsurface((col * frame_w, r * frame_h, frame_w, frame_h))
                frames.append(_scale(frame, scale))
        return frames

    def font(self, size: int) -> pygame.font.Font:
        if size not in self._fonts:
            path = FONT_FILE if FONT_FILE.exists() else None
            self._fonts[size] = pygame.font.Font(path, size)
        return self._fonts[size]

    def _load(self, path: str, scale: float) -> pygame.Surface | None:
        key = (path, scale)
        if key not in self._images:
            file = self.root / path
            if file.exists():
                self._images[key] = _scale(pygame.image.load(file).convert_alpha(), scale)
            else:
                print(f"[assets] missing image: {file}")
                self._images[key] = None
        return self._images[key]


def _scale(surface: pygame.Surface, scale: float) -> pygame.Surface:
    if scale == 1:
        return surface.copy()
    size = (round(surface.get_width() * scale), round(surface.get_height() * scale))
    return pygame.transform.scale(surface, size)


def _placeholder(size: tuple[int, int]) -> pygame.Surface:
    surface = pygame.Surface(size, pygame.SRCALPHA)
    surface.fill(PLACEHOLDER_COLOR)
    pygame.draw.rect(surface, (0, 0, 0), surface.get_rect(), 2)
    return surface
