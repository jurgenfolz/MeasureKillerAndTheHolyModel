"""Sound effects and music.

The game still runs without a sound card: every call then does nothing.
A missing sound file is skipped in silence too.
"""

from pathlib import Path

import pygame

from measure_killer.constants import MUSIC_DIR, SOUNDS_DIR

AUDIO_EXTENSIONS = (".ogg", ".wav", ".mp3", ".flac")

# Some sound files are much louder than others, so each one gets its own volume.
SOUND_VOLUME = {
    "cast": 0.6,
    "sword": 0.5,
    "explosion": 0.9,
    "jump": 0.35,
    "land": 0.35,
    "player_hurt": 0.6,
    "enemy_hurt": 0.4,
    "enemy_alert": 0.45,
    "enemy_shoot": 0.5,
    "ricochet": 0.55,
    "dialog_blip": 0.25,
    "menu_move": 0.5,
    "menu_select": 0.6,
    "pickup": 0.6,
}

# The same sound cannot start again within this many milliseconds.
# An explosion can break 30 tiles at once, and we want one crumble sound, not 30.
MIN_REPLAY_MS = 45


class Audio:
    def __init__(self, music_volume: float, sfx_volume: float):
        self.enabled = pygame.mixer.get_init() is not None
        self.music_volume = music_volume
        self.sfx_volume = sfx_volume
        self._sounds: dict[str, pygame.mixer.Sound | None] = {}
        self._last_played: dict[str, int] = {}
        self._music: str | None = None
        if self.enabled:
            pygame.mixer.set_num_channels(32)

    def play(self, name: str, volume: float = 1.0) -> None:
        if not self.enabled:
            return
        now = pygame.time.get_ticks()
        if now - self._last_played.get(name, -MIN_REPLAY_MS) < MIN_REPLAY_MS:
            return
        sound = self._sound(name)
        if sound is None:
            return
        self._last_played[name] = now
        channel = sound.play()
        if channel is not None:
            channel.set_volume(min(1.0, self.sfx_volume * volume * SOUND_VOLUME.get(name, 1.0)))

    def play_music(self, name: str) -> None:
        """Loop a music track. Asking for the track that already plays does nothing."""
        if not self.enabled or name == self._music:
            return
        path = _find_file(MUSIC_DIR, name)
        if path is None:
            self.stop_music()
            return
        pygame.mixer.music.load(path)
        pygame.mixer.music.set_volume(self.music_volume)
        pygame.mixer.music.play(-1, fade_ms=800)
        self._music = name

    def stop_music(self) -> None:
        if self.enabled:
            pygame.mixer.music.fadeout(500)
        self._music = None

    def set_volumes(self, music_volume: float, sfx_volume: float) -> None:
        self.music_volume = music_volume
        self.sfx_volume = sfx_volume
        if self.enabled:
            pygame.mixer.music.set_volume(music_volume)

    def _sound(self, name: str) -> pygame.mixer.Sound | None:
        if name not in self._sounds:
            path = _find_file(SOUNDS_DIR, name)
            self._sounds[name] = pygame.mixer.Sound(path) if path else None
        return self._sounds[name]


def _find_file(folder: Path, name: str) -> Path | None:
    for extension in AUDIO_EXTENSIONS:
        path = folder / f"{name}{extension}"
        if path.exists():
            return path
    return None
