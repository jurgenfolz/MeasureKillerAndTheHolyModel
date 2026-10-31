"""The menu that saves a game to a slot, or loads one from a slot."""

import pygame

from measure_killer.constants import DANGER_RED, HERO_GREEN, POWER_BI_YELLOW, SCREEN_W
from measure_killer.saves import ALL_SLOTS, MANUAL_SLOTS, SaveError, SlotInfo
from measure_killer.scene import Scene
from measure_killer.scenes.gameplay import GameplayScene
from measure_killer.ui.menu import Menu, MenuItem
from measure_killer.ui.panel import dim, panel
from measure_killer.ui.text import draw_text


def start_from_save(app, slot: str) -> str | None:
    """Start the game from a save slot. Return an error message when the save cannot be used."""
    try:
        data = app.saves.read(slot)
        scene = GameplayScene(app, int(data["level_index"]), data)
    except SaveError as error:
        return str(error).upper()
    except (KeyError, TypeError, ValueError, IndexError, AttributeError):
        return "THIS SAVE IS DAMAGED AND CANNOT BE LOADED"
    app.scenes.replace_all(scene)
    return None


class SlotScene(Scene):
    draws_below = True

    def __init__(self, app, mode: str, gameplay: GameplayScene | None = None):
        """Mode is "load" or "save". Saving needs the running gameplay scene."""
        super().__init__(app)
        self.mode = mode
        self.gameplay = gameplay
        self.font = app.assets.font(16)
        self.small = app.assets.font(8)
        self.message = ""
        self.message_color = HERO_GREEN
        self._build_menu()

    def _build_menu(self) -> None:
        slots = ALL_SLOTS if self.mode == "load" else MANUAL_SLOTS
        items = []
        for slot in slots:
            info = self.app.saves.info(slot)
            # Any slot can be overwritten, but only a good save can be loaded.
            enabled = self.mode == "save" or info.status == "ok"
            items.append(MenuItem(_describe(info), lambda s=slot: self._pick(s), enabled=enabled))
        items.append(MenuItem("BACK", self.app.scenes.pop))
        self.menu = Menu(items, self.small, self.app.audio, center=(SCREEN_W // 2, 280), spacing=36)

    def _pick(self, slot: str) -> None:
        if self.mode == "save":
            if self.gameplay.save_to(slot):
                self._show("GAME SAVED", HERO_GREEN)
            else:
                self._show("COULD NOT WRITE THE SAVE FILE", DANGER_RED)
            self._build_menu()
            return
        error = start_from_save(self.app, slot)
        if error:
            self._show(error, DANGER_RED)

    def _show(self, message: str, color) -> None:
        self.message = message
        self.message_color = color

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.app.scenes.pop()
            return
        self.menu.handle_event(event, self.app.mouse_pos())

    def draw(self, surface: pygame.Surface) -> None:
        dim(surface, 200)
        panel(surface, pygame.Rect(SCREEN_W // 2 - 330, 120, 660, 320))
        title = "LOAD GAME" if self.mode == "load" else "SAVE GAME"
        draw_text(surface, self.font, title, (SCREEN_W // 2, 150), POWER_BI_YELLOW, "center")
        self.menu.draw(surface)
        if self.message:
            draw_text(surface, self.small, self.message, (SCREEN_W // 2, 416), self.message_color, "center")


def _describe(info: SlotInfo) -> str:
    if info.status == "empty":
        return f"{info.title}:  - EMPTY -"
    if info.status == "damaged":
        return f"{info.title}:  DAMAGED SAVE"
    when = info.saved_at.strftime("%Y-%m-%d %H:%M")
    return f"{info.title}:  {info.level_name.upper()}  ({when})"
