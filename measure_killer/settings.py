"""Player settings: screen resolution, fullscreen and volume."""

from dataclasses import asdict, dataclass

from measure_killer.storage import config_dir, read_json, write_json_atomic

SETTINGS_FILE = "settings.json"


@dataclass
class Settings:
    resolution: tuple[int, int] = (1280, 720)
    fullscreen: bool = False
    music_volume: float = 0.5
    sfx_volume: float = 0.8


def load_settings() -> Settings:
    """Read the settings file, and use the default for any value that is missing or wrong."""
    defaults = Settings()
    try:
        data = read_json(config_dir() / SETTINGS_FILE) or {}
    except ValueError:
        return defaults
    return Settings(
        resolution=_read_resolution(data.get("resolution"), defaults.resolution),
        fullscreen=bool(data.get("fullscreen", defaults.fullscreen)),
        music_volume=_read_volume(data.get("music_volume"), defaults.music_volume),
        sfx_volume=_read_volume(data.get("sfx_volume"), defaults.sfx_volume),
    )


def save_settings(settings: Settings) -> None:
    data = asdict(settings)
    data["resolution"] = list(settings.resolution)
    write_json_atomic(config_dir() / SETTINGS_FILE, data)


def _read_resolution(value, default: tuple[int, int]) -> tuple[int, int]:
    if isinstance(value, list) and len(value) == 2 and all(isinstance(v, int) and v >= 320 for v in value):
        return (value[0], value[1])
    return default


def _read_volume(value, default: float) -> float:
    if isinstance(value, (int, float)):
        return min(1.0, max(0.0, float(value)))
    return default
