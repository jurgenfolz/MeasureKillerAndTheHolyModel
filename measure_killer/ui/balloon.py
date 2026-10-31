"""Comic-style speech balloons with typewriter text."""

from collections.abc import Callable

import pygame

from measure_killer.constants import INK, SCREEN_H, SCREEN_W, SOFT_WHITE, WHITE
from measure_killer.ui.text import wrap

PADDING = 8
LINE_GAP = 5
MAX_TEXT_WIDTH = 280
TAIL_HEIGHT = 12
SCREEN_MARGIN = 6
BLIP_EVERY = 3  # play the typing sound once every few letters


class SpeechBalloon:
    def __init__(
        self,
        text: str,
        font: pygame.font.Font,
        name: str | None = None,
        name_color: tuple[int, int, int] = SOFT_WHITE,
        name_font: pygame.font.Font | None = None,
        letters_per_second: float = 45,
        on_blip: Callable[[], None] | None = None,
    ):
        self.font = font
        self.lines = wrap(font, text, MAX_TEXT_WIDTH)
        self.total = sum(len(line) for line in self.lines)
        self.shown = 0.0
        self.speed = letters_per_second
        self.on_blip = on_blip
        self.age = 0.0
        self._name = (name_font or font).render(name, False, name_color) if name else None
        self._blips = 0

    @property
    def done(self) -> bool:
        return self.shown >= self.total

    def finish(self) -> None:
        self.shown = self.total

    def update(self, dt: float) -> None:
        self.age += dt
        if self.done:
            return
        self.shown = min(self.total, self.shown + self.speed * dt)
        blips = int(self.shown) // BLIP_EVERY
        if blips > self._blips and self.on_blip:
            self.on_blip()
        self._blips = blips

    def draw(self, surface: pygame.Surface, anchor: tuple[float, float] | None, prompt: bool = False) -> None:
        """Draw the balloon above the anchor point, with its tail pointing at it.

        Without an anchor the balloon sits at the top of the screen, like a narrator box.
        """
        line_h = self.font.get_linesize() + LINE_GAP
        width = max(self.font.size(line)[0] for line in self.lines) + 2 * PADDING
        if self._name:
            width = max(width, self._name.get_width() + 2 * PADDING)
        height = len(self.lines) * line_h - LINE_GAP + 2 * PADDING + (6 if prompt else 0)
        box = pygame.Rect(0, 0, max(width, 48), height)
        if anchor is None:
            box.midtop = (SCREEN_W // 2, 48)
        else:
            box.midbottom = (round(anchor[0]), round(anchor[1]) - TAIL_HEIGHT)
        box.clamp_ip(pygame.Rect(SCREEN_MARGIN, SCREEN_MARGIN + 14, SCREEN_W - 2 * SCREEN_MARGIN, SCREEN_H - 2 * SCREEN_MARGIN - 14))

        if anchor is not None and anchor[1] > box.bottom:
            tail_x = min(max(anchor[0], box.left + 12), box.right - 12)
            tail = [(tail_x - 7, box.bottom - 2), (tail_x + 5, box.bottom - 2), (anchor[0], anchor[1] - 2)]
            pygame.draw.polygon(surface, WHITE, tail)
            pygame.draw.lines(surface, INK, False, tail, 2)
        pygame.draw.rect(surface, WHITE, box, border_radius=6)
        pygame.draw.rect(surface, INK, box, 2, border_radius=6)
        if anchor is not None and anchor[1] > box.bottom:
            # Paint over the border where the tail joins the box.
            surface.fill(WHITE, (tail_x - 5, box.bottom - 2, 10, 2))

        if self._name:
            tab = self._name.get_rect(bottomleft=(box.left + 8, box.top + 2)).inflate(10, 6)
            pygame.draw.rect(surface, INK, tab, border_radius=3)
            surface.blit(self._name, self._name.get_rect(center=tab.center))

        remaining = int(self.shown)
        y = box.top + PADDING
        for line in self.lines:
            if remaining <= 0:
                break
            visible = line[:remaining]
            remaining -= len(line)
            surface.blit(self.font.render(visible, False, INK), (box.left + PADDING, y))
            y += line_h

        if prompt and self.done and int(self.age * 3) % 2 == 0:
            x, y = box.right - 12, box.bottom - 9
            pygame.draw.polygon(surface, INK, [(x - 4, y - 3), (x + 4, y - 3), (x, y + 2)])
