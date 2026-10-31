"""Save slots and the settings file."""

import json

import pytest

from measure_killer.saves import SAVE_VERSION, SaveError, SaveManager
from measure_killer.settings import Settings, load_settings, save_settings

GAME_STATE = {"level_index": 1, "level_name": "Level 2 - Mines", "playtime": 42.5, "world": {"deleted": 3}}


@pytest.fixture
def saves(tmp_path) -> SaveManager:
    return SaveManager(tmp_path / "saves")


def test_a_saved_game_reads_back_the_same(saves):
    saves.write("slot1", GAME_STATE)
    data = saves.read("slot1")
    assert data["version"] == SAVE_VERSION
    assert {key: data[key] for key in GAME_STATE} == GAME_STATE
    assert saves.info("slot1").status == "ok"


def test_an_empty_slot(saves):
    assert saves.info("slot2").status == "empty"
    with pytest.raises(SaveError):
        saves.read("slot2")


def test_a_damaged_file_does_not_crash(saves):
    saves.write("slot1", GAME_STATE)
    (saves.directory / "slot1.json").write_text("{ not json", encoding="utf-8")
    assert saves.info("slot1").status == "damaged"
    with pytest.raises(SaveError):
        saves.read("slot1")


def test_a_save_from_a_newer_game_is_refused(saves):
    saves.write("slot1", GAME_STATE)
    path = saves.directory / "slot1.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["version"] = SAVE_VERSION + 1
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(SaveError):
        saves.read("slot1")


def test_an_unknown_slot_name_is_refused(saves):
    with pytest.raises(ValueError):
        saves.write("../../escape", GAME_STATE)


def test_settings_without_a_file_use_the_defaults():
    assert load_settings() == Settings()


def test_settings_read_back_the_same():
    settings = Settings(resolution=(1920, 1080), fullscreen=True, music_volume=0.2, sfx_volume=0.4)
    save_settings(settings)
    assert load_settings() == settings


def test_bad_settings_fall_back_to_safe_values(game_home):
    path = game_home / "config" / "settings.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"resolution": "huge", "music_volume": 7, "sfx_volume": -1}), encoding="utf-8")
    settings = load_settings()
    assert settings.resolution == Settings().resolution
    assert (settings.music_volume, settings.sfx_volume) == (1.0, 0.0)
