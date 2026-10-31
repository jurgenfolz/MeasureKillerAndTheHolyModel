"""The hero: aiming and throwing fireballs."""

import pygame

from measure_killer.constants import DT
from measure_killer.game.level import LevelData, Spawn, split_row
from measure_killer.game.player import PlayerInput
from measure_killer.game.world import World


def make_world(rows: list[str], assets, audio) -> World:
    """Build a small world from text rows. "P1" is the hero, "M1" a measure, the other codes are the same as in a level file."""
    kinds = {"P1": "player", "M1": "measure"}
    spawns = [
        Spawn(0, kinds[code], x, y) for y, row in enumerate(rows) for x, code in enumerate(split_row(row)) if code in kinds
    ]
    return World(LevelData("test", "sky", "level", rows, spawns), assets, audio)


def test_the_hero_does_not_flicker_when_aiming_just_above_him(assets, audio):
    """The mouse sits between his middle and his hands. Turning by the hands would flip him every frame."""
    world = make_world(["        ", "    P1  ", "D1D1D1D1"], assets, audio)
    player = world.player
    facings = []
    for _ in range(20):
        aim = player.center + (10, -200)
        world.update(DT, PlayerInput(aim=aim))
        facings.append(player.facing)
    assert set(facings) == {1}


def test_the_hero_turns_around_when_the_mouse_passes_him(assets, audio):
    world = make_world(["        ", "    P1  ", "D1D1D1D1"], assets, audio)
    world.update(DT, PlayerInput(aim=world.player.center - (100, 0)))
    assert world.player.facing == -1


def test_a_fireball_at_a_wall_you_touch_hits_that_wall(assets, audio):
    """The hands reach out, so they poke through the wall. The fireball must still hit the wall."""
    world = make_world(["            ", "        D1  ", "    P1  D1  ", "D1D1D1D1D1D1"], assets, audio)
    player = world.player
    for _ in range(40):
        world.update(DT, PlayerInput(move=1, aim=player.center + (300, 0)))
    assert player.body.hit_wall == 1
    aim = pygame.Vector2(1000, player.hands.y)
    world.update(DT, PlayerInput(fire_pressed=True, fire_held=True, aim=aim))
    # The fireball leaves his hands partway through the cast animation, so wait for the whole cast.
    for _ in range(40):
        world.update(DT, PlayerInput(aim=aim))
    # The fireball bursts at the wall and breaks the blocks there in one hit.
    assert world.tilemap.get(4, 1) is None or world.tilemap.get(4, 2) is None


def test_the_sword_cuts_a_block_in_two_swings(assets, audio):
    world = make_world(["        ", "    P1D1", "D1D1D1D1"], assets, audio)
    player = world.player
    aim = player.center + (300, 0)
    for swing in range(2):
        world.update(DT, PlayerInput(attack_pressed=True, aim=aim))
        # The blade lands after a wind-up, so wait for the whole swing.
        for _ in range(40):
            world.update(DT, PlayerInput(aim=aim))
        if swing == 0:
            assert world.tilemap.damage_ratio(3, 1) == 0.5
    assert world.tilemap.get(3, 1) is None

