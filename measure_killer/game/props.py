"""Things in a level that are neither the hero nor an enemy: pickups, checkpoints, the exit, the Holy Model and the Developer."""

import math
import random

import pygame

from measure_killer.animation import Animation, mirrored
from measure_killer.assets import Assets
from measure_killer.constants import HERO_GREEN
from measure_killer.game.camera import Camera
from measure_killer.game.physics import Body

HEAL_AMOUNT = 35


class Prop:
    """Something placed in the level. Its feet sit on (x, y)."""

    def __init__(self, spawn_id: int | None, x: float, y: float):
        self.spawn_id = spawn_id
        self.alive = True
        self.age = random.uniform(0, 3)

    def update(self, world, dt: float) -> None:
        self.age += dt

    def draw(self, surface: pygame.Surface, camera: Camera) -> None:
        pass


class Pickup(Prop):
    """A small item that falls to the ground and is collected on touch."""

    SIZE = 24

    def __init__(self, spawn_id: int | None, x: float, y: float, image: pygame.Surface):
        super().__init__(spawn_id, x, y)
        self.image = image
        self.body = Body(x - self.SIZE / 2, y - self.SIZE, self.SIZE, self.SIZE)

    def update(self, world, dt: float) -> None:
        super().update(world, dt)
        self.body.vel.x *= 0.92
        self.body.move(world.tilemap, dt)
        player = world.player
        if player.alive and self.body.rect.colliderect(player.body.rect) and self.collect(world):
            self.alive = False
            world.audio.play("pickup")

    def collect(self, world) -> bool:
        """Give the item to the hero. Return False to leave it lying there."""
        return True

    def draw(self, surface: pygame.Surface, camera: Camera) -> None:
        bob = math.sin(self.age * 3) * 3
        rect = self.body.rect
        x, y = camera.to_screen(rect.centerx, rect.bottom - self.image.get_height() / 2 + bob - 4)
        surface.blit(self.image, self.image.get_rect(center=(x, y)))


class HealthPickup(Pickup):
    def __init__(self, spawn_id, x, y, assets: Assets):
        super().__init__(spawn_id, x, y, assets.image("items/health.png"))

    def collect(self, world) -> bool:
        if not world.player.heal(HEAL_AMOUNT):
            return False
        world.effects.float_text(*world.player.speech_anchor, "+COFFEE", HERO_GREEN)
        return True


class Checkpoint(Prop):
    def __init__(self, spawn_id, x, y, assets: Assets):
        super().__init__(spawn_id, x, y)
        self.frames = assets.frames("items/checkpoint.png", 32, 64)
        self.rect = pygame.FRect(x - 16, y - 64, 32, 64)
        self.active = False

    @property
    def respawn_point(self) -> tuple[float, float]:
        return (self.rect.centerx, self.rect.bottom)

    def update(self, world, dt: float) -> None:
        super().update(world, dt)
        player = world.player
        if not self.active and player.alive and self.rect.colliderect(player.body.rect):
            self.active = True
            world.reach_checkpoint(self)

    def draw(self, surface: pygame.Surface, camera: Camera) -> None:
        surface.blit(self.frames[1 if self.active else 0], camera.to_screen(self.rect.x, self.rect.y))


class ExitPortal(Prop):
    def __init__(self, spawn_id, x, y, assets: Assets):
        super().__init__(spawn_id, x, y)
        self.animation = Animation(assets.frames("items/exit_portal.png", 64, 96), fps=8)
        self.position = (x - 32, y - 96)
        self.trigger = pygame.FRect(x - 19, y - 82, 38, 72)
        self.used = False

    def update(self, world, dt: float) -> None:
        super().update(world, dt)
        if not self.used and world.player.alive and self.trigger.colliderect(world.player.body.rect):
            self.used = True
            world.finish_level()

    def draw(self, surface: pygame.Surface, camera: Camera) -> None:
        surface.blit(self.animation.frame(self.age), camera.to_screen(*self.position))


class HolyModel(Prop):
    """The goal of the whole game. It floats and glows."""

    def __init__(self, spawn_id, x, y, assets: Assets):
        super().__init__(spawn_id, x, y)
        self.animation = Animation(assets.frames("items/holy_model.png", 96, 96), fps=8)
        self.center = pygame.Vector2(x, y - 56)
        self.trigger = pygame.FRect(0, 0, 60, 70)
        self.trigger.center = self.center
        self.found = False

    @property
    def speech_anchor(self) -> pygame.Vector2:
        return self.center - (0, 50)

    def update(self, world, dt: float) -> None:
        super().update(world, dt)
        if not self.found and world.player.alive and self.trigger.colliderect(world.player.body.rect):
            self.found = True
            world.find_holy_model()

    def draw(self, surface: pygame.Surface, camera: Camera) -> None:
        frame = self.animation.frame(self.age)
        bob = math.sin(self.age * 1.6) * 5
        surface.blit(frame, frame.get_rect(center=camera.to_screen(self.center.x, self.center.y + bob)))


class Pedro(Prop):
    """The Power BI Developer, the hero's master. He talks and looks at the hero."""

    def __init__(self, spawn_id, x, y, assets: Assets):
        super().__init__(spawn_id, x, y)
        frames = assets.frames("characters/pedro.png", 48, 64)
        self.animation = Animation(frames, fps=3)
        self.animation_left = Animation(mirrored(frames), fps=3)
        self.feet = pygame.Vector2(x, y)
        self.facing = 1

    @property
    def speech_anchor(self) -> pygame.Vector2:
        return self.feet - (0, 62)

    def update(self, world, dt: float) -> None:
        super().update(world, dt)
        self.facing = 1 if world.player.center.x >= self.feet.x else -1

    def draw(self, surface: pygame.Surface, camera: Camera) -> None:
        animation = self.animation if self.facing > 0 else self.animation_left
        offset = 23 if self.facing > 0 else 24
        surface.blit(animation.frame(self.age), camera.to_screen(self.feet.x - offset, self.feet.y - 64))


PROP_TYPES = {
    "health": HealthPickup,
    "checkpoint": Checkpoint,
    "exit": ExitPortal,
    "holy_model": HolyModel,
    "pedro": Pedro,
}


def make_prop(kind: str, spawn_id: int | None, x: float, y: float, assets: Assets) -> Prop:
    return PROP_TYPES[kind](spawn_id, x, y, assets)

