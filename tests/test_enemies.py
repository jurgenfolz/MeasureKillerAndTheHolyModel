"""The unused measure: its thrown keys."""

import pygame

from measure_killer.constants import DT
from measure_killer.game.enemies import UnusedMeasure
from measure_killer.game.projectiles import ThrownKey
from tests.test_player import make_world


def test_a_thrown_key_breaks_a_block_on_the_third_hit(assets, audio):
    world = make_world(["            ", "    P1  D1  ", "D1D1D1D1D1D1"], assets, audio)
    for hit in range(3):
        world.add_projectile(ThrownKey(100, 48, pygame.Vector2(1, 0), assets))
        for _ in range(30):
            world.update(DT, player_input())
        if hit < 2:
            assert round(world.tilemap.damage_ratio(4, 1), 3) == round((hit + 1) / 3, 3)
    assert world.tilemap.get(4, 1) is None


def test_a_measure_throws_a_key_partway_through_its_throw(assets, audio):
    world = make_world(["                ", "P1          M1  ", "D1D1D1D1D1D1D1D1"], assets, audio)
    measure = world.enemies[0]
    assert isinstance(measure, UnusedMeasure)
    measure.face(world.player.center.x)
    measure.start_throw()
    for _ in range(60):
        world.update(DT, player_input())
        if any(isinstance(p, ThrownKey) for p in world.projectiles):
            break
    else:
        raise AssertionError("no key was thrown")
    key = next(p for p in world.projectiles if isinstance(p, ThrownKey))
    assert key.vel.x < 0  # toward the hero on the left


def player_input():
    from measure_killer.game.player import PlayerInput
    return PlayerInput()
