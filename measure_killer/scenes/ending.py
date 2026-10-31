"""The ending: the hero found the Holy Model."""

import math

import pygame

from measure_killer.animation import Animation
from measure_killer.constants import GOLD, HERO_GREEN, POWER_BI_YELLOW, SCREEN_H, SCREEN_W, SOFT_WHITE
from measure_killer.scene import Scene
from measure_killer.ui.text import draw_text

FACTS = (
    "REFRESH TIME: 4.2 SECONDS",
    "UNUSED MEASURES: 0",
    "UNUSED COLUMNS: 0",
    "BEST PRACTICES: POWER BI PRO"
)


class EndingScene(Scene):
    def __init__(self, app, playtime: float, deleted: int):
        super().__init__(app)
        frames = app.assets.frames("items/holy_model.png", 96, 96, scale=2)
        self.model = Animation(frames, fps=8)
        self.font = app.assets.font(16)
        self.big = app.assets.font(24)
        self.small = app.assets.font(8)
        minutes, seconds = divmod(int(playtime), 60)
        self.stats = f"TIME: {minutes:02d}:{seconds:02d}     UNUSED OBJECTS DELETED: {deleted}"
        self.age = 0.0
        app.audio.play_music("menu")

    def handle_event(self, event: pygame.event.Event) -> None:
        pressed = event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE)
        clicked = event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
        if (pressed or clicked) and self.age > 1.5:
            from measure_killer.scenes.title import TitleScene

            self.app.scenes.replace_all(TitleScene(self.app))

    def update(self, dt: float) -> None:
        self.age += dt

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((18, 16, 30))
        for i in range(40):
            # Slowly turning rays of light behind the model.
            angle = i * math.tau / 40 + self.age * 0.2
            end = (SCREEN_W // 2 + math.cos(angle) * 700, 170 + math.sin(angle) * 700)
            pygame.draw.line(surface, (40, 34, 30) if i % 2 else (30, 26, 40), (SCREEN_W // 2, 170), end, 18)
        frame = self.model.frame(self.age)
        surface.blit(frame, frame.get_rect(center=(SCREEN_W // 2, 170 + math.sin(self.age * 1.5) * 6)))
        draw_text(surface, self.big, "YOU FOUND THE HOLY MODEL!", (SCREEN_W // 2, 300), GOLD, "center")
        for row, fact in enumerate(FACTS):
            draw_text(surface, self.small, fact, (SCREEN_W // 2, 340 + row * 18), SOFT_WHITE, "center")
        draw_text(surface, self.small, self.stats, (SCREEN_W // 2, 430), HERO_GREEN, "center")
        draw_text(surface, self.font, "THANK YOU FOR PLAYING!", (SCREEN_W // 2, 466), POWER_BI_YELLOW, "center")
        if self.age > 1.5 and int(self.age * 2) % 2 == 0:
            draw_text(surface, self.small, "PRESS ENTER TO RETURN TO THE TITLE", (SCREEN_W // 2, SCREEN_H - 30), SOFT_WHITE, "center")
