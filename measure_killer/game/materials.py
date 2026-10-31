"""Terrain materials: what each block is made of and how hard it is to break.

The hero's sword has a power value, see player.py.
It can only cut a block when its power is at least the block's toughness, and it takes two cuts.
A fireball breaks any block in one hit.
"""

from dataclasses import dataclass

TILESET_PATH = "Tiles/Assets/Assets.png"

Cell = tuple[int, int]  # (column, row) of a 16 px tile in the tileset image
Color = tuple[int, int, int]


@dataclass(frozen=True)
class Material:
    key: str  # the two-character code that places this material in a level map, see level.py
    name: str
    hp: float
    toughness: int
    tiles: tuple[Cell, ...]  # one variant is picked per block, so the ground does not look repeated
    debris: tuple[Color, ...]
    top_tiles: tuple[Cell, ...] = ()  # used when the block has open air above it at level start
    one_way: bool = False  # a thin platform that you can jump up through
    hurts: int = 0  # damage when you touch it
    leaves_wall: bool = True  # a broken block leaves a dark wall behind it
    see_through: bool = False  # the art has holes, so it is drawn without a backing color


DIRT = Material(
    key="D1",
    name="dirt",
    hp=3,
    toughness=1,
    tiles=((2, 2), (3, 2), (4, 2), (3, 3), (2, 12), (3, 12), (4, 12), (3, 13)),
    # Only middle pieces. The end pieces of the tileset have a see-through side, which shows as a gap in a row.
    top_tiles=((3, 0), (9, 0)),
    debris=((160, 91, 83), (118, 66, 62), (75, 44, 54), (122, 190, 48)),
)
LEAVES = Material(
    key="L1",
    name="leaves",
    hp=1,
    toughness=1,
    tiles=((2, 16), (3, 16), (2, 17), (3, 17), (4, 17), (3, 18)),
    top_tiles=((3, 15),),
    debris=((20, 75, 19), (62, 137, 32), (122, 190, 48)),
    leaves_wall=False,
)
WOOD = Material(
    key="W1",
    name="wood",
    hp=4,
    toughness=2,
    tiles=((7, 8), (8, 8), (9, 8), (7, 9), (8, 9), (9, 9), (7, 10), (8, 10), (9, 10)),
    debris=((196, 120, 84), (160, 91, 63), (110, 60, 48)),
    leaves_wall=False,
)
CRATE = Material(
    key="X1",
    name="crate",
    hp=2,
    toughness=1,
    tiles=((6, 3),),
    debris=((160, 91, 83), (118, 66, 62), (196, 120, 84)),
    leaves_wall=False,
)
ROCK = Material(
    key="R1",
    name="dark rock",
    hp=6,
    toughness=2,
    tiles=((13, 13), (12, 14), (13, 14), (13, 15), (12, 15)),
    debris=((92, 58, 66), (64, 40, 50), (40, 26, 34)),
)
CRYSTAL = Material(
    key="C1",
    name="crystal",
    hp=8,
    toughness=4,
    tiles=((22, 5), (21, 6), (22, 6), (23, 6), (22, 7)),
    debris=((120, 70, 160), (88, 48, 120), (170, 120, 210)),
)
SPIKES = Material(
    key="S1",
    name="spikes",
    hp=4,
    toughness=4,
    tiles=((11, 8),),
    debris=((170, 160, 160), (110, 100, 104)),
    hurts=20,
    leaves_wall=False,
    see_through=True,
)
PLATFORM = Material(
    key="B1",
    name="platform",
    hp=2,
    toughness=1,
    tiles=((7, 17), (8, 17)),
    debris=((196, 120, 84), (160, 91, 63)),
    one_way=True,
    leaves_wall=False,
    see_through=True,
)

MATERIALS: dict[str, Material] = {m.key: m for m in (DIRT, LEAVES, WOOD, CRATE, ROCK, CRYSTAL, SPIKES, PLATFORM)}

# Small plants that grow on grass. Each entry is a list of tileset cells drawn side by side.
DECORATIONS: tuple[tuple[Cell, ...], ...] = (
    ((13, 0),),
    ((14, 0),),
    ((15, 0),),
    ((17, 2),),
    ((18, 2),),
    ((13, 2),),
    ((14, 2), (15, 2)),
)
