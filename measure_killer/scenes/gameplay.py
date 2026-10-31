"""The screen where you play: it turns keys and mouse into hero actions and moves from level to level."""

import pygame

from measure_killer.constants import DANGER_RED, HERO_GREEN, INK, POWER_BI_YELLOW, SCREEN_H, SCREEN_SIZE, SCREEN_W, SOFT_WHITE
from measure_killer.game.level import level_count, load_level
from measure_killer.game.player import PlayerInput
from measure_killer.game.world import World
from measure_killer.saves import AUTOSAVE_SLOT
from measure_killer.scene import Scene
from measure_killer.ui.hud import Hud
from measure_killer.ui.text import draw_text

JUMP_KEYS = (pygame.K_SPACE, pygame.K_w, pygame.K_UP)
TALK_KEYS = (pygame.K_e, pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE)
BANNER_TIME = 3.5
FADE_TIME = 0.8
TOAST_TIME = 2.0


class GameplayScene(Scene):
    shows_cursor = False

    def __init__(self, app, level_index: int, save: dict | None = None):
        """Start a level. With a save, the level is rebuilt as it was when the game was saved."""
        super().__init__(app)
        self.hud = Hud(app.assets)
        self.small = app.assets.font(8)
        self.font = app.assets.font(16)
        self.playtime = float(save["playtime"]) if save else 0.0
        self.toast = ""
        self.toast_timer = 0.0
        self._presses = PlayerInput()
        self._start_level(level_index, save["world"] if save else None)

    def _start_level(self, index: int, world_state: dict | None) -> None:
        self.level_index = index
        self.world = World(load_level(index), self.app.assets, self.app.audio)
        if world_state is None:
            self.world.begin()
        else:
            self.world.restore(world_state)
        self.banner_timer = BANNER_TIME
        self.fade_in = FADE_TIME
        self.leave_timer = 0.0
        self.app.audio.play_music(self.world.level.music)
        if world_state is None:
            self.save_to(AUTOSAVE_SLOT)

    # Saving

    def game_state(self) -> dict:
        return {
            "level_index": self.level_index,
            "level_name": f"Level {self.level_index + 1} - {self.world.level.name}",
            "playtime": self.playtime,
            "world": self.world.snapshot(),
        }

    def save_to(self, slot: str) -> bool:
        try:
            self.app.saves.write(slot, self.game_state())
        except OSError:
            self._show_toast("COULD NOT SAVE THE GAME")
            return False
        return True

    # Input

    def handle_event(self, event: pygame.event.Event) -> None:
        world = self.world
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            from measure_killer.scenes.pause import PauseScene

            self.app.scenes.push(PauseScene(self.app, self))
            return
        if world.conversation is not None:
            talk = (event.type == pygame.KEYDOWN and event.key in TALK_KEYS) or (
                event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
            )
            if talk:
                world.advance_conversation()
            return
        presses = self._presses
        if event.type == pygame.KEYDOWN and event.key in JUMP_KEYS:
            presses.jump_pressed = True
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            presses.attack_pressed = True
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            presses.fire_pressed = True

    def _read_input(self) -> PlayerInput:
        """Combine the key presses since the last update with the keys held right now."""
        keys = pygame.key.get_pressed()
        inp = self._presses
        self._presses = PlayerInput()
        right = keys[pygame.K_d] or keys[pygame.K_RIGHT]
        left = keys[pygame.K_a] or keys[pygame.K_LEFT]
        inp.move = int(right) - int(left)
        inp.jump_held = any(keys[k] for k in JUMP_KEYS)
        inp.drop = keys[pygame.K_s] or keys[pygame.K_DOWN]
        inp.fire_held = pygame.mouse.get_pressed()[2]
        inp.aim = self.world.camera.to_world(self.app.mouse_pos())
        return inp

    # Update

    def update(self, dt: float) -> None:
        world = self.world
        self.playtime += dt
        self.banner_timer -= dt
        self.fade_in -= dt
        self.toast_timer -= dt
        if self.leave_timer > 0:
            self.leave_timer -= dt
            if self.leave_timer <= 0:
                self._leave_level()
            return
        world.update(dt, self._read_input())
        if world.autosave_requested:
            world.autosave_requested = False
            if self.save_to(AUTOSAVE_SLOT):
                self._show_toast("CHECKPOINT - GAME SAVED")
        if world.outcome is not None:
            self.leave_timer = FADE_TIME

    def _leave_level(self) -> None:
        if self.world.outcome == "level_complete" and self.level_index + 1 < level_count():
            self._start_level(self.level_index + 1, None)
            return
        from measure_killer.scenes.ending import EndingScene

        self.app.scenes.replace_all(EndingScene(self.app, self.playtime, self.world.deleted))

    def _show_toast(self, text: str) -> None:
        self.toast = text
        self.toast_timer = TOAST_TIME

    # Drawing

    def draw(self, surface: pygame.Surface) -> None:
        world = self.world
        world.draw(surface)
        if world.conversation is None:
            self.hud.draw(surface, world.player, world.deleted)
        if self.banner_timer > 0:
            self._draw_banner(surface)
        if not world.player.alive:
            draw_text(surface, self.font, "MODEL CORRUPTED!", (SCREEN_W // 2, SCREEN_H // 2 - 20), DANGER_RED, "center")
            draw_text(surface, self.small, "RESTORING FROM LAST CHECKPOINT...", (SCREEN_W // 2, SCREEN_H // 2 + 10), SOFT_WHITE, "center")
        if self.toast_timer > 0:
            draw_text(surface, self.small, self.toast, (SCREEN_W // 2, SCREEN_H - 30), HERO_GREEN, "center")
        if world.conversation is not None:
            draw_text(surface, self.small, "E / SPACE / CLICK TO CONTINUE", (SCREEN_W - 16, SCREEN_H - 18), SOFT_WHITE, "topright")
        else:
            self._draw_crosshair(surface)
        self._draw_fade(surface)

    def _draw_banner(self, surface: pygame.Surface) -> None:
        alpha = min(1.0, self.banner_timer / 0.6)
        banner = pygame.Surface((SCREEN_W, 64), pygame.SRCALPHA)
        banner.fill((*INK, int(170 * alpha)))
        draw_text(banner, self.small, f"LEVEL {self.level_index + 1}", (SCREEN_W // 2, 12), HERO_GREEN, "midtop")
        draw_text(banner, self.font, self.world.level.name.upper(), (SCREEN_W // 2, 30), POWER_BI_YELLOW, "midtop")
        banner.set_alpha(int(255 * alpha))
        surface.blit(banner, (0, 110))

    def _draw_crosshair(self, surface: pygame.Surface) -> None:
        x, y = (round(v) for v in self.app.mouse_pos())
        for color, width in ((INK, 4), (SOFT_WHITE, 2)):
            pygame.draw.line(surface, color, (x - 10, y), (x - 4, y), width)
            pygame.draw.line(surface, color, (x + 4, y), (x + 10, y), width)
            pygame.draw.line(surface, color, (x, y - 10), (x, y - 4), width)
            pygame.draw.line(surface, color, (x, y + 4), (x, y + 10), width)

    def _draw_fade(self, surface: pygame.Surface) -> None:
        if self.leave_timer > 0:
            amount = 1 - self.leave_timer / FADE_TIME
        elif self.fade_in > 0:
            amount = self.fade_in / FADE_TIME
        else:
            return
        shade = pygame.Surface(SCREEN_SIZE)
        shade.fill(INK)
        shade.set_alpha(int(255 * max(0.0, min(1.0, amount))))
        surface.blit(shade, (0, 0))
