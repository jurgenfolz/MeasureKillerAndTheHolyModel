"""Talking.

A conversation is a list of lines that the player reads one by one. The game waits while it runs.
A bark is a short line above a character's head that does not stop the game, like an enemy taunt.
"""

from dataclasses import dataclass

import pygame

from measure_killer.audio import Audio
from measure_killer.constants import GOLD, HERO_GREEN, POWER_BI_YELLOW, SOFT_WHITE
from measure_killer.game.camera import Camera
from measure_killer.ui.balloon import SpeechBalloon

SPEAKERS = {
    "player": ("Measure Killer", HERO_GREEN),
    "pedro": ("Pedro Smiderle", POWER_BI_YELLOW),
    "holy_model": ("The Holy Model", GOLD),
}


@dataclass(frozen=True)
class DialogLine:
    speaker: str  # a key of SPEAKERS, or "narrator" for a box without a speaker
    text: str


class Conversation:
    def __init__(self, lines: list[DialogLine], font: pygame.font.Font, audio: Audio):
        self.lines = lines
        self.font = font
        self.audio = audio
        self.index = 0
        self.balloon = self._balloon()

    @property
    def finished(self) -> bool:
        return self.index >= len(self.lines)

    @property
    def speaker(self) -> str:
        return self.lines[self.index].speaker

    def advance(self) -> None:
        """Show the whole line at once, or go to the next line when it is already complete."""
        if not self.balloon.done:
            self.balloon.finish()
            return
        self.index += 1
        if not self.finished:
            self.balloon = self._balloon()

    def update(self, dt: float) -> None:
        self.balloon.update(dt)

    def draw(self, surface: pygame.Surface, anchor: tuple[float, float] | None) -> None:
        self.balloon.draw(surface, anchor, prompt=True)

    def _balloon(self) -> SpeechBalloon:
        line = self.lines[self.index]
        name, color = SPEAKERS.get(line.speaker, (None, SOFT_WHITE))
        return SpeechBalloon(line.text, self.font, name, color, on_blip=lambda: self.audio.play("dialog_blip"))


class Barks:
    def __init__(self, font: pygame.font.Font):
        self.font = font
        self._active: list[list] = []  # [speaker, balloon, seconds left]

    def say(self, speaker, text: str, duration: float) -> None:
        """Show a line above the speaker. A new line replaces the speaker's old one."""
        self._active = [bark for bark in self._active if bark[0] is not speaker]
        self._active.append([speaker, SpeechBalloon(text, self.font, letters_per_second=70), duration])

    def update(self, dt: float) -> None:
        for bark in self._active:
            bark[1].update(dt)
            bark[2] -= dt
        self._active = [bark for bark in self._active if bark[2] > 0 and getattr(bark[0], "alive", True)]

    def clear(self) -> None:
        self._active.clear()

    def draw(self, surface: pygame.Surface, camera: Camera) -> None:
        for speaker, balloon, _ in self._active:
            anchor = speaker.speech_anchor
            balloon.draw(surface, camera.to_screen(anchor.x, anchor.y))
