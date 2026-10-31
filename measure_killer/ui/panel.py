"""Backgrounds for menus that sit on top of another screen."""

import pygame

from measure_killer.constants import INK, POWER_BI_YELLOW, SCREEN_SIZE

PANEL_COLOR = (24, 22, 34)


def dim(surface: pygame.Surface, alpha: int = 160) -> None:
    """Darken everything drawn so far."""
    shade = pygame.Surface(SCREEN_SIZE, pygame.SRCALPHA)
    shade.fill((*INK, alpha))
    surface.blit(shade, (0, 0))


def panel(surface: pygame.Surface, rect: pygame.Rect) -> None:
    pygame.draw.rect(surface, PANEL_COLOR, rect, border_radius=8)
    pygame.draw.rect(surface, POWER_BI_YELLOW, rect, 2, border_radius=8)
