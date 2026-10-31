"""The pause menu, opened with Escape during play."""

import pygame

from measure_killer.constants import HERO_GREEN, POWER_BI_YELLOW, SOFT_WHITE
from measure_killer.scene import Scene
from measure_killer.scenes.settings_menu import SettingsScene
from measure_killer.scenes.slots import SlotScene
from measure_killer.ui.menu import Menu, MenuItem
from measure_killer.ui.panel import dim, panel
from measure_killer.ui.text import draw_text

CONTROLS = (
    ("A / D", "MOVE"),
    ("SPACE / W", "JUMP (HOLD FOR HIGHER)"),
    ("S", "DROP THROUGH PLATFORMS"),
    ("MOUSE", "AIM"),
    ("LEFT CLICK", "SWORD"),
    ("RIGHT CLICK", "THROW A FIREBALL"),
    ("E", "TALK / CONTINUE"),
)


class PauseScene(Scene):
    draws_below = True

    def __init__(self, app, gameplay):
        super().__init__(app)
        self.gameplay = gameplay
        self.font = app.assets.font(16)
        self.small = app.assets.font(8)
        self.menu = Menu(
            [
                MenuItem("RESUME", app.scenes.pop),
                MenuItem("SAVE GAME", lambda: app.scenes.push(SlotScene(app, "save", gameplay))),
                MenuItem("LOAD GAME", lambda: app.scenes.push(SlotScene(app, "load"))),
                MenuItem("SETTINGS", lambda: app.scenes.push(SettingsScene(app))),
                MenuItem("QUIT TO TITLE", self._quit_to_title),
            ],
            self.font,
            app.audio,
            center=(320, 290),
            spacing=40,
        )

    def _quit_to_title(self) -> None:
        from measure_killer.scenes.title import TitleScene

        self.app.scenes.replace_all(TitleScene(self.app))

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.app.scenes.pop()
            return
        self.menu.handle_event(event, self.app.mouse_pos())

    def draw(self, surface: pygame.Surface) -> None:
        dim(surface, 150)
        panel(surface, pygame.Rect(150, 130, 340, 320))
        draw_text(surface, self.font, "PAUSED", (320, 160), POWER_BI_YELLOW, "center")
        self.menu.draw(surface)
        panel(surface, pygame.Rect(520, 130, 300, 320))
        draw_text(surface, self.small, "CONTROLS", (670, 152), POWER_BI_YELLOW, "center")
        for row, (key, action) in enumerate(CONTROLS):
            y = 184 + row * 30
            draw_text(surface, self.small, key, (540, y), HERO_GREEN)
            draw_text(surface, self.small, action, (540, y + 11), SOFT_WHITE)
