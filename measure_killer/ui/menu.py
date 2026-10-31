"""A vertical menu that works with the keyboard and the mouse.

An item can run an action when chosen, or change a value with left and right (like a volume).
"""

from collections.abc import Callable
from dataclasses import dataclass

import pygame

from measure_killer.audio import Audio
from measure_killer.constants import GREY, INK, POWER_BI_YELLOW, SOFT_WHITE
from measure_killer.ui.text import outlined

UP_KEYS = (pygame.K_UP, pygame.K_w)
DOWN_KEYS = (pygame.K_DOWN, pygame.K_s)
LEFT_KEYS = (pygame.K_LEFT, pygame.K_a)
RIGHT_KEYS = (pygame.K_RIGHT, pygame.K_d)
CHOOSE_KEYS = (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE, pygame.K_e)


@dataclass
class MenuItem:
    label: str | Callable[[], str]
    action: Callable[[], None] | None = None
    change: Callable[[int], None] | None = None  # called with -1 or +1
    enabled: bool = True

    @property
    def text(self) -> str:
        text = self.label() if callable(self.label) else self.label
        return f"<  {text}  >" if self.change else text


class Menu:
    def __init__(self, items: list[MenuItem], font: pygame.font.Font, audio: Audio, center: tuple[int, int], spacing: int = 34):
        self.items = items
        self.font = font
        self.audio = audio
        self.center = center
        self.spacing = spacing
        self.selected = next((i for i, item in enumerate(items) if item.enabled), 0)

    def handle_event(self, event: pygame.event.Event, mouse: tuple[float, float]) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key in UP_KEYS:
                self._move(-1)
            elif event.key in DOWN_KEYS:
                self._move(1)
            elif event.key in LEFT_KEYS:
                self._change(-1)
            elif event.key in RIGHT_KEYS:
                self._change(1)
            elif event.key in CHOOSE_KEYS:
                self._choose()
        elif event.type == pygame.MOUSEMOTION:
            index = self._item_at(mouse)
            if index is not None and index != self.selected:
                self.selected = index
                self.audio.play("menu_move")
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button in (1, 3):
            index = self._item_at(mouse)
            if index is None:
                return
            self.selected = index
            item = self.items[index]
            if item.change:
                self._change(1 if event.button == 1 else -1)
            else:
                self._choose()

    def draw(self, surface: pygame.Surface) -> None:
        for index, item in enumerate(self.items):
            rect = self._rect(index)
            if index == self.selected and item.enabled:
                bar = rect.inflate(36, 10)
                pygame.draw.rect(surface, INK, bar, border_radius=4)
                pygame.draw.rect(surface, POWER_BI_YELLOW, bar, 2, border_radius=4)
                color = POWER_BI_YELLOW
            else:
                color = SOFT_WHITE if item.enabled else GREY
            image = outlined(self.font, item.text, color)
            surface.blit(image, image.get_rect(center=rect.center))

    def _rect(self, index: int) -> pygame.Rect:
        width, height = self.font.size(self.items[index].text)
        top = self.center[1] - (len(self.items) - 1) * self.spacing / 2
        return pygame.Rect(0, 0, width, height).move(self.center[0] - width // 2, round(top + index * self.spacing - height / 2))

    def _item_at(self, mouse: tuple[float, float]) -> int | None:
        for index, item in enumerate(self.items):
            if item.enabled and self._rect(index).inflate(36, 12).collidepoint(mouse):
                return index
        return None

    def _move(self, step: int) -> None:
        for _ in range(len(self.items)):
            self.selected = (self.selected + step) % len(self.items)
            if self.items[self.selected].enabled:
                break
        self.audio.play("menu_move")

    def _change(self, step: int) -> None:
        item = self.items[self.selected]
        if item.enabled and item.change:
            item.change(step)
            self.audio.play("menu_move")

    def _choose(self) -> None:
        item = self.items[self.selected]
        if item.enabled and item.action:
            self.audio.play("menu_select")
            item.action()
