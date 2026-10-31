"""Starts pygame, owns the shared services and runs the main loop."""

import pygame

from measure_killer.assets import Assets
from measure_killer.audio import Audio
from measure_killer.constants import DT, FPS
from measure_killer.display import Display
from measure_killer.game.camera import Camera
from measure_killer.game.player import standing_hero
from measure_killer.saves import SaveManager
from measure_killer.scene import SceneStack
from measure_killer.settings import load_settings
from measure_killer.storage import saves_dir

MAX_UPDATES_PER_FRAME = 5


class App:
    def __init__(self):
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.init()
        self.settings = load_settings()
        self.display = Display(self.settings)
        self.assets = Assets()
        pygame.display.set_icon(_window_icon(self.assets))
        self.audio = Audio(self.settings.music_volume, self.settings.sfx_volume)
        self.saves = SaveManager(saves_dir())
        self.scenes = SceneStack()
        self.clock = pygame.time.Clock()
        self.running = True

        from measure_killer.scenes.title import TitleScene

        self.scenes.push(TitleScene(self))

    def mouse_pos(self) -> tuple[float, float]:
        """Return the mouse position on the game canvas."""
        return self.display.to_canvas(pygame.mouse.get_pos())

    def quit(self) -> None:
        self.running = False

    def run(self) -> None:
        """Run the game until the player quits.

        The game logic always steps in fixed slices of DT seconds.
        That keeps jumps and shots the same on fast and slow computers.
        """
        lag = 0.0
        while self.running:
            lag += min(self.clock.tick(FPS) / 1000, 0.25)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif self.scenes.top:
                    self.scenes.top.handle_event(event)
            updates = 0
            while lag >= DT and updates < MAX_UPDATES_PER_FRAME:
                self.scenes.top.update(DT)
                lag -= DT
                updates += 1
            if updates == MAX_UPDATES_PER_FRAME:
                lag = 0.0
            pygame.mouse.set_visible(self.scenes.top.shows_cursor)
            self.scenes.draw(self.display.canvas)
            self.display.present()
        pygame.quit()


def _window_icon(assets: Assets) -> pygame.Surface:
    """Return the hero standing, for the window and the taskbar."""
    icon = pygame.Surface((64, 64), pygame.SRCALPHA)
    hero = standing_hero(assets, aim=0.0)
    hero.body.rect.midbottom = (32, 63)
    hero.draw(icon, Camera(*icon.get_size()))
    return icon
