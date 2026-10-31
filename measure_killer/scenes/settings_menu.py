"""The settings menu.

Volume changes take effect and are saved right away.
Resolution and fullscreen changes wait for "APPLY DISPLAY", because a new window size can be a surprise.
"""

import dataclasses

import pygame

from measure_killer.constants import HERO_GREEN, POWER_BI_YELLOW, SCREEN_W
from measure_killer.display import available_resolutions
from measure_killer.scene import Scene
from measure_killer.settings import save_settings
from measure_killer.ui.menu import Menu, MenuItem
from measure_killer.ui.panel import dim, panel
from measure_killer.ui.text import draw_text

VOLUME_STEP = 0.1


class SettingsScene(Scene):
    draws_below = True

    def __init__(self, app):
        super().__init__(app)
        self.draft = dataclasses.replace(app.settings)
        self.resolutions = available_resolutions()
        if self.draft.resolution not in self.resolutions:
            self.resolutions.append(self.draft.resolution)
            self.resolutions.sort()
        self.font = app.assets.font(16)
        self.small = app.assets.font(8)
        self.message = ""
        self.menu = Menu(
            [
                MenuItem(lambda: "RESOLUTION: {}x{}".format(*self.draft.resolution), change=self._change_resolution),
                MenuItem(lambda: "FULLSCREEN" if self.draft.fullscreen else "WINDOW", change=self._toggle_fullscreen),
                MenuItem("APPLY DISPLAY", self._apply_display),
                MenuItem(lambda: f"MUSIC: {round(self.draft.music_volume * 100)}%", change=self._change_music),
                MenuItem(lambda: f"SOUND: {round(self.draft.sfx_volume * 100)}%", change=self._change_sound),
                MenuItem("BACK", app.scenes.pop),
            ],
            self.font,
            app.audio,
            center=(SCREEN_W // 2, 290),
            spacing=40,
        )

    def _change_resolution(self, step: int) -> None:
        index = self.resolutions.index(self.draft.resolution)
        self.draft.resolution = self.resolutions[(index + step) % len(self.resolutions)]

    def _toggle_fullscreen(self, _step: int) -> None:
        self.draft.fullscreen = not self.draft.fullscreen

    def _apply_display(self) -> None:
        self.app.settings.resolution = self.draft.resolution
        self.app.settings.fullscreen = self.draft.fullscreen
        self.app.display.apply(self.app.settings)
        self._save()
        self.message = "DISPLAY APPLIED"

    def _change_music(self, step: int) -> None:
        self.draft.music_volume = _step_volume(self.draft.music_volume, step)
        self.app.settings.music_volume = self.draft.music_volume
        self._apply_volume()

    def _change_sound(self, step: int) -> None:
        self.draft.sfx_volume = _step_volume(self.draft.sfx_volume, step)
        self.app.settings.sfx_volume = self.draft.sfx_volume
        self._apply_volume()

    def _apply_volume(self) -> None:
        self.app.audio.set_volumes(self.app.settings.music_volume, self.app.settings.sfx_volume)
        self._save()

    def _save(self) -> None:
        try:
            save_settings(self.app.settings)
        except OSError:
            self.message = "COULD NOT SAVE THE SETTINGS FILE"

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.app.scenes.pop()
            return
        self.menu.handle_event(event, self.app.mouse_pos())

    def draw(self, surface: pygame.Surface) -> None:
        dim(surface, 190)
        panel(surface, pygame.Rect(SCREEN_W // 2 - 260, 110, 520, 360))
        draw_text(surface, self.font, "SETTINGS", (SCREEN_W // 2, 140), POWER_BI_YELLOW, "center")
        self.menu.draw(surface)
        hint = self.message or "LEFT / RIGHT TO CHANGE A VALUE"
        draw_text(surface, self.small, hint, (SCREEN_W // 2, 448), HERO_GREEN, "center")


def _step_volume(volume: float, step: int) -> float:
    return round(min(1.0, max(0.0, volume + step * VOLUME_STEP)), 2)
