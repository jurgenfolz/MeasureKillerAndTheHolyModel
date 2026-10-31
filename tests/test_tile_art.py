"""Checks on the tileset art that the terrain uses."""

import pytest

from measure_killer.constants import ART_TILE
from measure_killer.game.materials import DIRT, TILESET_PATH


@pytest.mark.parametrize("cell", DIRT.top_tiles)
def test_grass_tiles_join_without_gaps(assets, cell):
    """Grass is drawn without a backing color. A see-through side would show the sky as a gap between two blocks."""
    sheet = assets.image(TILESET_PATH)
    tile = sheet.subsurface((cell[0] * ART_TILE, cell[1] * ART_TILE, ART_TILE, ART_TILE))
    for x in (0, ART_TILE - 1):
        clear_rows = [y for y in range(ART_TILE) if tile.get_at((x, y)).a == 0]
        assert not clear_rows, f"tile {cell} is see-through at column {x}, rows {clear_rows}"
