"""The game window.

The game draws on a fixed canvas (see SCREEN_SIZE).
The display scales that canvas to the window and adds black bars when the shapes differ.
"""

import pygame

from measure_killer.constants import BLACK, GAME_TITLE, SCREEN_H, SCREEN_SIZE, SCREEN_W
from measure_killer.settings import Settings

COMMON_RESOLUTIONS = (
    (960, 540),
    (1280, 720),
    (1366, 768),
    (1600, 900),
    (1920, 1080),
    (2560, 1440),
    (3840, 2160),
)


def available_resolutions() -> list[tuple[int, int]]:
    """Return the resolutions that fit on the player's screen, smallest first."""
    desktop = pygame.display.get_desktop_sizes()[0]
    fitting = {size for size in COMMON_RESOLUTIONS if size[0] <= desktop[0] and size[1] <= desktop[1]}
    fitting.add(tuple(desktop))
    return sorted(fitting)


class Display:
    def __init__(self, settings: Settings):
        self.canvas = pygame.Surface(SCREEN_SIZE)
        self.window: pygame.Surface | None = None
        self._dest = pygame.Rect(0, 0, *SCREEN_SIZE)
        self._scaled: pygame.Surface | None = None
        pygame.display.set_caption(GAME_TITLE)
        self.apply(settings)

    def apply(self, settings: Settings) -> None:
        """Open the window with the resolution and fullscreen choice in the settings."""
        flags = pygame.FULLSCREEN if settings.fullscreen else 0
        try:
            self.window = pygame.display.set_mode(settings.resolution, flags)
        except pygame.error:
            #! Some systems refuse a fullscreen mode, so we fall back to a normal window.
            self.window = pygame.display.set_mode((1280, 720))
        self._fit_canvas()

    def present(self) -> None:
        """Copy the canvas to the window and show it."""
        if self._dest.size == SCREEN_SIZE:
            self.window.blit(self.canvas, self._dest)
        else:
            pygame.transform.scale(self.canvas, self._dest.size, self._scaled)
            self.window.fill(BLACK)
            self.window.blit(self._scaled, self._dest)
        pygame.display.flip()

    def to_canvas(self, window_pos: tuple[int, int]) -> tuple[float, float]:
        """Turn a mouse position in the window into a position on the canvas."""
        x = (window_pos[0] - self._dest.x) * SCREEN_W / self._dest.width
        y = (window_pos[1] - self._dest.y) * SCREEN_H / self._dest.height
        return (min(max(x, 0), SCREEN_W - 1), min(max(y, 0), SCREEN_H - 1))

    def _fit_canvas(self) -> None:
        window_w, window_h = self.window.get_size()
        scale = min(window_w / SCREEN_W, window_h / SCREEN_H)
        width, height = round(SCREEN_W * scale), round(SCREEN_H * scale)
        self._dest = pygame.Rect((window_w - width) // 2, (window_h - height) // 2, width, height)
        #! Scaling into a ready surface needs the same pixel format on both sides, so both follow the window.
        self.canvas = self.canvas.convert()
        self._scaled = pygame.Surface((width, height), 0, self.canvas)
