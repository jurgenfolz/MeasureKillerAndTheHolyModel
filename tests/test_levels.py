"""Checks on the level files and on whole running levels."""

import json
import random

import pygame
import pytest

from measure_killer.constants import DT, SCREEN_SIZE
from measure_killer.game.level import level_count, load_level, split_row
from measure_killer.game.player import PlayerInput
from measure_killer.game.world import World

LEVELS = range(level_count())


@pytest.mark.parametrize("index", LEVELS)
def test_every_dialog_a_level_names_exists(index):
    """A typo in a dialog name makes the game skip that conversation without a word."""
    level = load_level(index)
    named = [level.start_dialog] + [t.dialog for t in level.triggers]
    missing = [name for name in named if name and name not in level.dialogs]
    assert not missing


@pytest.mark.parametrize("index", LEVELS)
def test_every_conversation_can_be_clicked_through(index, assets, audio):
    """The game can draw right after a click, before its next update, so each step must leave something to draw."""
    world = World(load_level(index), assets, audio)
    screen = pygame.Surface(SCREEN_SIZE)
    for name, lines in world.level.dialogs.items():
        world.start_conversation(name)
        # Each line takes at most two clicks: one shows the whole text, one goes on.
        for _ in range(2 * len(lines)):
            world.advance_conversation()
            world.draw(screen)
        assert world.conversation is None, f"conversation {name!r} did not end"


@pytest.mark.parametrize("index", LEVELS)
def test_a_level_plays_without_crashing(index, assets, audio):
    """Play the level for a while with scripted input, and draw some frames.

    This catches crashes in code that only runs during play, like a fireball hitting a wall.
    """
    random.seed(index)
    world = World(load_level(index), assets, audio)
    world.begin()
    screen = pygame.Surface(SCREEN_SIZE)
    for frame in range(20 * 60):
        if world.conversation is not None:
            world.advance_conversation()
        player = world.player
        inp = PlayerInput(
            move=1 if frame % 400 < 300 else -1,
            jump_pressed=frame % 50 == 0,
            jump_held=frame % 50 < 20,
            attack_pressed=frame % 25 == 0,
            fire_held=True,
            fire_pressed=frame % 15 == 0,
            aim=player.center + (300 * player.facing, 40),
        )
        world.update(DT, inp)
        if frame % 10 == 0:
            world.draw(screen)


def test_a_saved_level_comes_back_the_same(assets, audio):
    world = World(load_level(0), assets, audio)
    world.begin()
    x, y = next((x, y) for y, row in enumerate(world.level.rows) for x, code in enumerate(split_row(row)) if code == "D1")
    world.tilemap.destroy(x, y)
    world.deleted = 4
    world.player.health = 55
    snapshot = json.loads(json.dumps(world.snapshot()))  # the same trip a save file makes

    restored = World(load_level(0), assets, audio)
    restored.restore(snapshot)
    assert restored.tilemap.destroyed_cells() == [[x, y]]
    assert restored.deleted == 4
    assert restored.player.health == 55
