"""Shared test setup.

Tests run pygame without a window and without a sound card, so they also work on a build server.
Settings and saves go to a temporary folder, so tests never touch the player's real files.
"""

import os

# SDL reads these when pygame starts, so they must be set first.
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame
import pytest

from measure_killer.assets import Assets
from measure_killer.audio import Audio


@pytest.fixture(scope="session", autouse=True)
def hidden_display():
    """Open a tiny hidden display. Images cannot load before a display exists."""
    pygame.display.init()
    pygame.font.init()
    pygame.display.set_mode((1, 1))
    yield
    pygame.quit()


@pytest.fixture(autouse=True)
def game_home(tmp_path, monkeypatch):
    """Point settings and saves at a fresh temporary folder for each test."""
    monkeypatch.setenv("MEASURE_KILLER_HOME", str(tmp_path))
    return tmp_path


@pytest.fixture(scope="session")
def assets(hidden_display) -> Assets:
    return Assets()


@pytest.fixture
def audio() -> Audio:
    """Return audio that stays silent. The sound mixer is never started in tests."""
    return Audio(music_volume=0, sfx_volume=0)
