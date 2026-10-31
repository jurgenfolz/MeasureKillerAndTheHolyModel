"""Save games: one autosave slot and three manual slots.

Each slot is one JSON file in the saves folder (see storage.py).
Every file has a version number, so later versions of the game can still read old saves.
A damaged file never crashes the game: the slot just shows as damaged.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from measure_killer.storage import read_json, write_json_atomic

SAVE_VERSION = 1
AUTOSAVE_SLOT = "autosave"
MANUAL_SLOTS = ("slot1", "slot2", "slot3")
ALL_SLOTS = (AUTOSAVE_SLOT, *MANUAL_SLOTS)
REQUIRED_KEYS = ("level_index", "level_name", "world", "playtime")


class SaveError(Exception):
    """A save file exists but the game cannot use it."""


@dataclass
class SlotInfo:
    slot: str
    status: str  # "ok", "empty" or "damaged"
    level_name: str = ""
    saved_at: datetime | None = None

    @property
    def title(self) -> str:
        return "AUTOSAVE" if self.slot == AUTOSAVE_SLOT else f"SLOT {self.slot[-1]}"


class SaveManager:
    def __init__(self, directory: Path):
        self.directory = directory

    def write(self, slot: str, game_state: dict) -> None:
        data = {"version": SAVE_VERSION, "saved_at": datetime.now().isoformat(timespec="seconds"), **game_state}
        write_json_atomic(self._path(slot), data)

    def read(self, slot: str) -> dict:
        """Return the saved game state, or raise SaveError."""
        try:
            data = read_json(self._path(slot))
        except ValueError as error:
            raise SaveError(str(error)) from error
        if data is None:
            raise SaveError("The slot is empty")
        version = data.get("version")
        if not isinstance(version, int) or version > SAVE_VERSION:
            raise SaveError("The save comes from a newer version of the game")
        missing = [key for key in REQUIRED_KEYS if key not in data]
        if missing:
            raise SaveError(f"The save is missing: {', '.join(missing)}")
        return data

    def info(self, slot: str) -> SlotInfo:
        if not self._path(slot).exists():
            return SlotInfo(slot, "empty")
        try:
            data = self.read(slot)
            saved_at = datetime.fromisoformat(data["saved_at"])
        except (SaveError, KeyError, TypeError, ValueError):
            return SlotInfo(slot, "damaged")
        return SlotInfo(slot, "ok", str(data["level_name"]), saved_at)

    def latest_slot(self) -> str | None:
        """Return the slot with the newest usable save, or None."""
        usable = [info for info in map(self.info, ALL_SLOTS) if info.status == "ok"]
        if not usable:
            return None
        return max(usable, key=lambda info: info.saved_at).slot

    def _path(self, slot: str) -> Path:
        if slot not in ALL_SLOTS:
            raise ValueError(f"Unknown save slot: {slot}")
        return self.directory / f"{slot}.json"
