"""The title screen and main menu.

A plain grey room. Pedro and the hero stand on the left, and the Holy Model shines on the right.
"""

import math
import random

import pygame

from measure_killer import __version__
from measure_killer.animation import Animation
from measure_killer.constants import DANGER_RED, GOLD, GREY, HERO_GREEN, SCREEN_H, SCREEN_SIZE, SCREEN_W
from measure_killer.game.camera import Camera
from measure_killer.game.effects import BLOOD
from measure_killer.game.player import standing_hero
from measure_killer.scene import Scene
from measure_killer.scenes.gameplay import GameplayScene
from measure_killer.scenes.settings_menu import SettingsScene
from measure_killer.scenes.slots import SlotScene, start_from_save
from measure_killer.ui.menu import Menu, MenuItem
from measure_killer.ui.text import draw_text

CONTROLS = "A/D MOVE   SPACE JUMP   LEFT CLICK SWORD   RIGHT CLICK FIREBALL   E TALK   ESC PAUSE"
GROUND = SCREEN_H - 94  # where everyone stands on the title screen
PEDRO_FEET = (72, GROUND)
HERO_FEET = (190, GROUND)
HOLY_MODEL_FEET = (846, GROUND + 6)
SCALE = 2
WALL = (44, 44, 50)
FLOOR = (34, 34, 40)
SEAM = (50, 50, 56)  # faint lines between the wall panels
FLOOR_EDGE = (70, 70, 78)
PANEL = 96  # width of a wall panel
BLOOD_DROPS = 16  # on the floor, always the same ones
GLOW = (255, 214, 92)  # the light the Holy Model throws on the wall


class TitleScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        assets = app.assets
        self.background = _background()
        # The hero breathes on a small canvas of his own, which is scaled up like the others.
        self.hero = standing_hero(assets, aim=0.0)
        self._hero_canvas = pygame.Surface((96, 96), pygame.SRCALPHA)
        self.pedro = Animation(_big(assets.frames("characters/pedro.png", 48, 64)), fps=4)
        self.holy_model = Animation(_big(assets.frames("items/holy_model.png", 96, 96)), fps=8)
        self.glow = _glow(220)
        self.title_font = assets.font(32)
        self.font = assets.font(16)
        self.small = assets.font(8)
        self.age = 0.0
        self.message = ""
        self._build_menu()
        app.audio.play_music("menu")

    def on_resume(self) -> None:
        # A save may have been made or deleted, so "Continue" may change.
        self._build_menu()

    def _build_menu(self) -> None:
        latest = self.app.saves.latest_slot()
        items = []
        if latest:
            items.append(MenuItem("CONTINUE", lambda: self._load(latest)))
        items += [
            MenuItem("NEW GAME", self._new_game),
            MenuItem("LOAD GAME", lambda: self.app.scenes.push(SlotScene(self.app, "load"))),
            MenuItem("SETTINGS", lambda: self.app.scenes.push(SettingsScene(self.app))),
            MenuItem("QUIT", self.app.quit),
        ]
        self.menu = Menu(items, self.font, self.app.audio, center=(SCREEN_W // 2, 350), spacing=36)

    def _new_game(self) -> None:
        self.app.scenes.replace_all(GameplayScene(self.app, 0))

    def _load(self, slot: str) -> None:
        error = start_from_save(self.app, slot)
        if error:
            self.message = error

    def handle_event(self, event: pygame.event.Event) -> None:
        self.menu.handle_event(event, self.app.mouse_pos())

    def update(self, dt: float) -> None:
        self.age += dt
        self.hero.pose_time += dt

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self.background, (0, 0))
        self._draw_holy_model(surface)
        bob = math.sin(self.age * 2) * 4
        draw_text(surface, self.title_font, "MEASURE KILLER", (SCREEN_W // 2, 96 + bob), DANGER_RED, "center")
        draw_text(surface, self.font, "AND THE HOLY MODEL", (SCREEN_W // 2, 146), GOLD, "center")
        pedro = self.pedro.frame(self.age)
        surface.blit(pedro, pedro.get_rect(midbottom=PEDRO_FEET))
        self._draw_hero(surface)
        self.menu.draw(surface)
        if self.message:
            draw_text(surface, self.small, self.message, (SCREEN_W // 2, 470), (255, 120, 120), "center")
        draw_text(surface, self.small, CONTROLS, (SCREEN_W // 2, SCREEN_H - 34), HERO_GREEN, "center")
        draw_text(surface, self.small, f"v{__version__}", (SCREEN_W - 8, SCREEN_H - 14), GREY, "topright")

    def _draw_hero(self, surface: pygame.Surface) -> None:
        self._hero_canvas.fill((0, 0, 0, 0))
        self.hero.body.rect.midbottom = (48, 94)
        self.hero.draw(self._hero_canvas, _STILL_CAMERA)
        big = pygame.transform.scale_by(self._hero_canvas, SCALE)
        surface.blit(big, big.get_rect(midbottom=HERO_FEET))

    def _draw_holy_model(self, surface: pygame.Surface) -> None:
        """The Holy Model floats a little and lights the night around it."""
        hover = math.sin(self.age * 1.5) * 6
        frame = self.holy_model.frame(self.age)
        rect = frame.get_rect(midbottom=(HOLY_MODEL_FEET[0], HOLY_MODEL_FEET[1] + hover))
        surface.blit(self.glow, self.glow.get_rect(center=rect.center), special_flags=pygame.BLEND_RGB_ADD)
        surface.blit(frame, rect)


def _background() -> pygame.Surface:
    """A grey wall of panels over a darker floor, with a few drops of blood on the floor."""
    background = pygame.Surface(SCREEN_SIZE)
    background.fill(WALL)
    for x in range(PANEL, SCREEN_W, PANEL):
        background.fill(SEAM, (x, 0, 2, GROUND))
    for y in range(PANEL, GROUND, PANEL):
        background.fill(SEAM, (0, y, SCREEN_W, 2))
    background.fill(FLOOR, (0, GROUND, SCREEN_W, SCREEN_H - GROUND))
    background.fill(FLOOR_EDGE, (0, GROUND, SCREEN_W, 2))
    drops = random.Random(7)
    for _ in range(BLOOD_DROPS):
        size = drops.choice((2, 3, 3, 4, 6))
        x = drops.randrange(0, SCREEN_W - size)
        y = drops.randrange(GROUND + 4, SCREEN_H - 44)
        background.fill(drops.choice(BLOOD), (x, y, size, size))
    return background


def _glow(size: int) -> pygame.Surface:
    """A soft round light that fades toward its edge. It is added onto the picture, so it brightens the night."""
    glow = pygame.Surface((size, size))
    center = size // 2
    for radius in range(center, 0, -2):
        strength = (1 - radius / center) ** 2
        color = tuple(int(c * strength * 0.35) for c in GLOW)
        pygame.draw.circle(glow, color, (center, center), radius)
    return glow


_STILL_CAMERA = Camera(96, 96)


def _big(frames: list[pygame.Surface]) -> list[pygame.Surface]:
    return [pygame.transform.scale_by(frame, SCALE) for frame in frames]
