"""Reads level files.

A level is a JSON file in resources/levels.
Its "map" is a list of text rows, and every two characters are one tile.
A tile code is a letter and a digit, like "D1": the letter says what it is and the digit which variant.
Two spaces (or two dots) are air.
Materials have their codes in materials.py, and everything else is in SPAWN_LEGEND below.
The file also holds the level's name, its look, its music and its dialogs.
"""

import json
from dataclasses import dataclass, field

from measure_killer.constants import LEVELS_DIR
from measure_killer.game.dialog import DialogLine
from measure_killer.game.materials import MATERIALS, Material

LEVEL_FILES = ("level1.json",)
CODE_WIDTH = 2  # characters per tile in a map row

# Codes that place something in the level. Materials have their own codes, see materials.py.
SPAWN_LEGEND = {
    "P1": "player",
    "N1": "pedro",
    "M1": "measure",
    "h1": "health",
    "k1": "checkpoint",
    "E1": "exit",
    "H1": "holy_model",
}
EMPTY = ("  ", "..")


@dataclass(frozen=True)
class Spawn:
    id: int
    kind: str
    x: int
    y: int


@dataclass(frozen=True)
class Trigger:
    """When the hero walks past column x, a conversation starts or the hero says something."""

    name: str
    x: int
    dialog: str | None = None
    say: str | None = None


@dataclass
class LevelData:
    name: str
    theme: str
    music: str
    rows: list[str]
    spawns: list[Spawn]
    dialogs: dict[str, list[DialogLine]] = field(default_factory=dict)
    start_dialog: str | None = None
    triggers: list[Trigger] = field(default_factory=list)

    def build_cells(self) -> list[list[Material | None]]:
        """Return a fresh terrain grid. Each call gives a new copy, so a restarted level is whole again."""
        return [[MATERIALS.get(code) for code in split_row(row)] for row in self.rows]


def split_row(row: str) -> list[str]:
    """Cut a map row into tile codes of two characters each."""
    return [row[i : i + CODE_WIDTH] for i in range(0, len(row), CODE_WIDTH)]


def level_count() -> int:
    return len(LEVEL_FILES)


def load_level(index: int) -> LevelData:
    path = LEVELS_DIR / LEVEL_FILES[index]
    with open(path, encoding="utf-8") as file:
        data = json.load(file)
    width = max(len(row) for row in data["map"])
    width += width % CODE_WIDTH  # round up, so the last tile of the widest row is whole
    rows = [row.ljust(width) for row in data["map"]]
    spawns = []
    for y, row in enumerate(rows):
        for x, code in enumerate(split_row(row)):
            if code in SPAWN_LEGEND:
                spawns.append(Spawn(len(spawns), SPAWN_LEGEND[code], x, y))
            elif code not in MATERIALS and code not in EMPTY:
                raise ValueError(f"{path.name}: unknown tile code {code!r} at column {x}, row {y}")
    if sum(s.kind == "player" for s in spawns) != 1:
        raise ValueError(f"{path.name}: the map needs exactly one 'P1' for the hero")
    dialogs = {
        name: [DialogLine(line["speaker"], line["text"]) for line in lines]
        for name, lines in data.get("dialogs", {}).items()
    }
    triggers = [
        Trigger(t.get("name", f"trigger{i}"), int(t["x"]), t.get("dialog"), t.get("say"))
        for i, t in enumerate(data.get("triggers", []))
    ]
    return LevelData(
        name=data["name"],
        theme=data.get("theme", "sky"),
        music=data.get("music", "level"),
        rows=rows,
        spawns=spawns,
        dialogs=dialogs,
        start_dialog=data.get("start_dialog"),
        triggers=triggers,
    )
