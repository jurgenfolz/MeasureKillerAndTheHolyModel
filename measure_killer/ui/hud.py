"""The heads-up display: health, fireball energy and the count of deleted enemies."""

import pygame

from measure_killer.assets import Assets
from measure_killer.constants import DANGER_RED, HERO_GREEN, INK, POWER_BI_YELLOW, SOFT_WHITE
from measure_killer.game.player import MAX_ENERGY, MAX_HEALTH, Player
from measure_killer.ui.text import draw_text

BAR_WIDTH = 180
ENERGY_COLOR = (255, 150, 40)


class Hud:
    def __init__(self, assets: Assets):
        self.small = assets.font(8)

    def draw(self, surface: pygame.Surface, player: Player, deleted: int) -> None:
        self._draw_health(surface, player)
        self._draw_energy(surface, player)
        draw_text(surface, self.small, f"UNUSED OBJECTS DELETED: {deleted}", (16, 72), SOFT_WHITE)

    def _draw_energy(self, surface: pygame.Surface, player: Player) -> None:
        """One flame pip per fireball charge. An empty pip refills as the charge comes back."""
        draw_text(surface, self.small, "FIREBALLS", (16, 46), ENERGY_COLOR)
        for i in range(MAX_ENERGY):
            pip = pygame.Rect(16 + i * 24, 57, 20, 8)
            pygame.draw.rect(surface, INK, pip.inflate(4, 4), border_radius=2)
            surface.fill((60, 40, 50), pip)
            if i < player.energy:
                surface.fill(ENERGY_COLOR, pip)
            elif i == player.energy:
                surface.fill((140, 70, 30), (pip.x, pip.y, round(pip.width * player.recharge_share), pip.height))

    def _draw_health(self, surface: pygame.Surface, player: Player) -> None:
        draw_text(surface, self.small, "HEALTH", (16, 12), HERO_GREEN)
        bar = pygame.Rect(16, 24, BAR_WIDTH, 14)
        pygame.draw.rect(surface, INK, bar.inflate(4, 4), border_radius=3)
        share = max(player.health, 0) / MAX_HEALTH
        color = HERO_GREEN if share > 0.5 else POWER_BI_YELLOW if share > 0.25 else DANGER_RED
        surface.fill((60, 40, 50), bar)
        surface.fill(color, (bar.x, bar.y, round(bar.width * share), bar.height))
        surface.fill((255, 255, 255), (bar.x, bar.y, round(bar.width * share), 2))
