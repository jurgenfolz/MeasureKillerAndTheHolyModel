"""The terrain grid and bodies that move on it."""

from measure_killer.constants import DT, TILE
from measure_killer.game.level import split_row
from measure_killer.game.materials import MATERIALS
from measure_killer.game.physics import Body
from measure_killer.game.tilemap import TileHit, TileMap


def make_map(*rows: str) -> TileMap:
    """Build a map from text rows, with the same tile codes as a level file."""
    return TileMap([[MATERIALS.get(code) for code in split_row(row)] for row in rows])


def middle_of(x: int, y: int) -> tuple[float, float]:
    return ((x + 0.5) * TILE, (y + 0.5) * TILE)


# Damage


def test_a_weak_shot_bounces_off_hard_rock():
    tm = make_map("R1")
    assert tm.damage(0, 0, power=1) == TileHit.DEFLECTED
    assert tm.get(0, 0) is not None


def test_enough_hits_destroy_a_block():
    tm = make_map("D1")
    results = [tm.damage(0, 0, power=1) for _ in range(3)]
    assert results == [TileHit.DAMAGED, TileHit.DAMAGED, TileHit.DESTROYED]
    assert tm.get(0, 0) is None
    assert tm.destroyed_cells() == [[0, 0]]


def test_broken_dirt_leaves_a_wall_and_loses_its_grass():
    tm = make_map("    ", "D1D1")
    assert tm.grass[1][0]
    tm.destroy(0, 1)
    assert tm.walls[1][0] is not None
    assert not tm.grass[1][0]


def test_grass_grows_only_on_top():
    tm = make_map("D1", "D1")
    assert tm.grass[0][0]
    assert not tm.grass[1][0]


# Line of sight


def test_a_ray_stops_at_the_first_block():
    tm = make_map("    R1  R1")
    hit = tm.raycast(*middle_of(0, 0), *middle_of(4, 0))
    assert hit is not None
    assert hit.cell == (2, 0)
    assert hit.normal == (-1, 0)


def test_you_can_see_through_air_and_platforms_but_not_dirt():
    assert make_map("          ").line_of_sight(*middle_of(0, 0), *middle_of(4, 0))
    assert make_map("    B1    ").line_of_sight(*middle_of(0, 0), *middle_of(4, 0))
    assert not make_map("    D1    ").line_of_sight(*middle_of(0, 0), *middle_of(4, 0))


# Bodies


def fall(tm: TileMap, body: Body, seconds: float = 1.0) -> None:
    for _ in range(round(seconds / DT)):
        body.move(tm, DT)


def test_a_body_lands_on_the_ground():
    tm = make_map("      ", "      ", "      ", "D1D1D1")
    body = Body(TILE, 0, 20, 20)
    fall(tm, body)
    assert body.on_ground
    assert body.rect.bottom == 3 * TILE


def test_a_body_lands_on_a_platform():
    tm = make_map("      ", "      ", "  B1  ", "      ")
    body = Body(TILE + 6, 0, 20, 20)
    fall(tm, body)
    assert body.on_ground
    assert body.rect.bottom == 2 * TILE


def test_a_body_jumps_up_through_a_platform():
    tm = make_map("      ", "      ", "  B1  ", "      ", "D1D1D1")
    body = Body(TILE + 6, 4 * TILE - 20, 20, 20)
    body.vel.y = -700
    for _ in range(10):
        body.move(tm, DT)
    assert body.rect.bottom < 2 * TILE
