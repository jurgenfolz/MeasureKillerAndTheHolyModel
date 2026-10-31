"""Where the game keeps its files on the player's computer, and how it writes them safely.

Settings and saves never go inside the game folder.
A Steam install folder can be read-only, and an update would wipe the files.
Each operating system has its own place for user files, so we use that.
Set the MEASURE_KILLER_HOME environment variable to keep everything in one folder instead (handy for tests).
"""

import json
import os
import sys
from pathlib import Path

from measure_killer.constants import APP_DIR_NAME


def _override_dir() -> Path | None:
    value = os.environ.get("MEASURE_KILLER_HOME")
    return Path(value) if value else None


def config_dir() -> Path:
    """Return the folder for the settings file."""
    override = _override_dir()
    if override:
        return override / "config"
    if sys.platform == "win32":
        return Path(os.environ.get("APPDATA", Path.home())) / APP_DIR_NAME
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_DIR_NAME
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / APP_DIR_NAME


def saves_dir() -> Path:
    """Return the folder for save games."""
    override = _override_dir()
    if override:
        return override / "saves"
    if sys.platform == "win32":
        return Path(os.environ.get("APPDATA", Path.home())) / APP_DIR_NAME / "saves"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_DIR_NAME / "saves"
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / APP_DIR_NAME / "saves"


def write_json_atomic(path: Path, data: dict) -> None:
    """Write data as JSON so that a crash never leaves a half-written file.

    The data goes to a temporary file first.
    Then the temporary file replaces the real one in a single step.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(path.name + ".tmp")
    with open(temp_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)
        file.flush()
        os.fsync(file.fileno())
    os.replace(temp_path, path)


def read_json(path: Path) -> dict | None:
    """Return the JSON object in the file, or None when the file does not exist.

    It raises ValueError when the file is damaged or is not a JSON object.
    """
    if not path.exists():
        return None
    try:
        with open(path, encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"Cannot read {path.name}: {error}") from error
    if not isinstance(data, dict):
        raise ValueError(f"{path.name} does not hold a JSON object")
    return data
