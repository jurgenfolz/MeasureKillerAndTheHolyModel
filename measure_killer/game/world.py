"""One running level: the terrain, the hero, the enemies, the props and everything that flies around.

The world also answers questions for the things inside it, like "can this enemy see the hero?".
"""

import math
import random
from collections.abc import Callable

import pygame

from measure_killer.assets import Assets
from measure_killer.audio import Audio
from measure_killer.constants import DANGER_RED, GOLD, TILE
from measure_killer.game import combat
from measure_killer.game.backdrop import Backdrop
from measure_killer.game.camera import Camera
from measure_killer.game.dialog import Barks, Conversation
from measure_killer.game.effects import Effects
from measure_killer.game.enemies import ENEMY_TYPES, Enemy
from measure_killer.game.level import LevelData
from measure_killer.game.materials import Material
from measure_killer.game.player import Player, PlayerInput
from measure_killer.game.props import Checkpoint, Pedro, HolyModel, Prop, make_prop
from measure_killer.game.tile_renderer import TileRenderer
from measure_killer.game.tilemap import TileMap

RESPAWN_DELAY = 2.2
ENEMY_HEALTH_DROP = 0.2
AIM_LOOKAHEAD = 0.25  # the camera leans this share of the way toward the mouse


class World:
    def __init__(self, level: LevelData, assets: Assets, audio: Audio):
        self.level = level
        self.assets = assets
        self.audio = audio
        self.tilemap = TileMap(level.build_cells())
        self.tiles = TileRenderer(self.tilemap, assets)
        self.backdrop = Backdrop(level.theme, assets)
        self.camera = Camera(self.tilemap.pixel_width, self.tilemap.pixel_height)
        self.effects = Effects(assets, assets.font(8))
        self.barks = Barks(assets.font(8))
        self.enemies: list[Enemy] = []
        self.props: list[Prop] = []
        self.projectiles: list = []
        self.player: Player | None = None
        self._spawn_level()
        self.checkpoint = self.player.body.rect.midbottom
        self.conversation: Conversation | None = None
        self._after_conversation: Callable[[], None] | None = None
        self.fired_triggers: set[str] = set()
        self.removed_spawns: set[int] = set()
        self.deleted = 0
        self.outcome: str | None = None  # becomes "level_complete" or "victory"
        self.autosave_requested = False
        self.respawn_timer = 0.0
        self._hinted: set[str] = set()
        self.camera.snap_to(self.player.center)

    def begin(self) -> None:
        """Start a fresh level."""
        if self.level.start_dialog:
            self.fired_triggers.add("start")
            self.start_conversation(self.level.start_dialog)

    # The main loop

    def update(self, dt: float, inp: PlayerInput) -> None:
        if self.conversation is not None:
            self._update_conversation(dt)
            return
        self.player.update(self, inp, dt)
        for enemy in self.enemies:
            enemy.update(self, dt)
        for prop in self.props:
            prop.update(self, dt)
        for projectile in self.projectiles:
            projectile.update(self, dt)
        self._remove_finished()
        self.effects.update(dt, self.tilemap)
        self.barks.update(dt)
        self._check_triggers()
        if not self.player.alive:
            self.respawn_timer -= dt
            if self.respawn_timer <= 0:
                self.player.respawn(*self.checkpoint)
        self.camera.follow(self._camera_target(inp), dt)

    def _update_conversation(self, dt: float) -> None:
        # The hero stands still while people talk, but he still breathes and stays on the ground.
        self.player.update(self, PlayerInput(aim=self.player.center + (self.player.facing * 100, 0)), dt)
        self.conversation.update(dt)
        self.effects.update(dt, self.tilemap)
        self.camera.follow(self.player.center, dt)

    def _remove_finished(self) -> None:
        for thing in [*self.enemies, *self.props]:
            if not thing.alive and thing.spawn_id is not None:
                self.removed_spawns.add(thing.spawn_id)
        self.enemies = [e for e in self.enemies if e.alive]
        self.props = [p for p in self.props if p.alive]
        self.projectiles = [p for p in self.projectiles if p.alive]

    def _check_triggers(self) -> None:
        hero_x = self.player.center.x
        for trigger in self.level.triggers:
            if trigger.name in self.fired_triggers or hero_x < trigger.x * TILE:
                continue
            self.fired_triggers.add(trigger.name)
            if trigger.dialog:
                self.start_conversation(trigger.dialog)
            elif trigger.say:
                self.say(self.player, trigger.say, 3.5)

    def _camera_target(self, inp: PlayerInput) -> pygame.Vector2:
        center = self.player.center
        lean = (inp.aim - center) * AIM_LOOKAHEAD
        if lean.length() > 120:
            lean.scale_to_length(120)
        return center + lean

    # Questions and requests from the things inside the world

    def can_see_player(self, enemy: Enemy) -> bool:
        """An enemy sees the hero when he is in range, in front of it, and no block is in the way."""
        player = self.player
        if not player.alive:
            return False
        eye = enemy.eye
        delta = player.center - eye
        if delta.length_squared() > enemy.SIGHT_RANGE ** 2:
            return False
        if not enemy.alerted and delta.x * enemy.facing < -24:
            return False
        return any(self.tilemap.line_of_sight(eye.x, eye.y, p.x, p.y) for p in (player.center, player.head))

    def first_enemy_on_line(self, start: pygame.Vector2, end: pygame.Vector2, skip: set[int]) -> tuple[Enemy | None, float]:
        best, best_distance = None, math.inf
        for enemy in self.enemies:
            if not enemy.alive or id(enemy) in skip:
                continue
            distance = combat.segment_hits_rect(start, end, enemy.body.rect)
            if distance is not None and distance < best_distance:
                best, best_distance = enemy, distance
        return best, best_distance

    def add_projectile(self, projectile) -> None:
        self.projectiles.append(projectile)

    def drop_pickup(self, kind: str, x: float, y: float) -> None:
        pickup = make_prop(kind, None, x, y + 12, self.assets)
        pickup.body.vel.update(random.uniform(-60, 60), -240)
        self.props.append(pickup)

    def say(self, speaker, text: str, duration: float = 3.0) -> None:
        self.barks.say(speaker, text, duration)

    def start_conversation(self, name: str, then: Callable[[], None] | None = None) -> None:
        lines = self.level.dialogs.get(name)
        if not lines:
            if then:
                then()
            return
        self.barks.clear()
        self.conversation = Conversation(lines, self.assets.font(8), self.audio)
        self._after_conversation = then

    def advance_conversation(self) -> None:
        if self.conversation is None:
            return
        self.conversation.advance()
        #! Close a finished conversation right away. The game can draw before its next update, and drawing needs a line to show.
        if self.conversation.finished:
            self.conversation = None
            then, self._after_conversation = self._after_conversation, None
            if then:
                then()

    def on_enemy_killed(self, enemy: Enemy, direction: pygame.Vector2, source: str) -> None:
        """An enemy died. Killed by the sword, its body flies off in the direction of the blow."""
        self.deleted += 1
        x, y = enemy.body.rect.center
        self.effects.blood(x, y, count=110, speed=400)
        self.effects.guts(x, y)
        self.effects.debris(x, y, enemy.DEBRIS, count=22, speed=300)
        if source == "sword":
            self.effects.flying_body(enemy.image, x, y, direction * 540 + (0, -380))
        self.effects.float_text(x, enemy.body.rect.top - 12, "DELETED!", DANGER_RED)
        self.audio.play("enemy_die")
        self.camera.shake(3)
        if random.random() < ENEMY_HEALTH_DROP:
            self.drop_pickup("health", x, y)

    def on_sword_deflected(self, material: Material) -> None:
        """The first time the sword is too weak for a material, the hero says so."""
        if material.name in self._hinted:
            return
        self._hinted.add(material.name)
        self.say(self.player, f"This {material.name} is too hard for my sword. A fireball should do it!", 3.5)

    def on_player_died(self) -> None:
        self.respawn_timer = RESPAWN_DELAY
        self.barks.clear()

    def reach_checkpoint(self, checkpoint: Checkpoint) -> None:
        self.checkpoint = checkpoint.respawn_point
        self.audio.play("checkpoint")
        self.effects.float_text(checkpoint.rect.centerx, checkpoint.rect.top - 10, "CHECKPOINT - SAVED", GOLD)
        self.autosave_requested = True

    def finish_level(self) -> None:
        self.audio.play("level_complete")
        self.outcome = "level_complete"

    def find_holy_model(self) -> None:
        self.audio.play("level_complete")
        self.start_conversation("holy_model", then=self._win)

    def _win(self) -> None:
        self.outcome = "victory"

    # Drawing

    def draw(self, surface: pygame.Surface) -> None:
        camera = self.camera
        self.backdrop.draw(surface, camera)
        self.tiles.draw(surface, camera)
        view = camera.view_rect(margin=64)
        for prop in self.props:
            prop.draw(surface, camera)
        for enemy in self.enemies:
            if view.colliderect(enemy.body.rect):
                enemy.draw(surface, camera)
        self.player.draw(surface, camera)
        for projectile in self.projectiles:
            projectile.draw(surface, camera)
        self.effects.draw(surface, camera)
        self.barks.draw(surface, camera)
        if self.conversation is not None:
            speaker = self._speaker(self.conversation.speaker)
            anchor = camera.to_screen(*speaker.speech_anchor) if speaker else None
            self.conversation.draw(surface, anchor)

    def _speaker(self, name: str):
        if name == "player":
            return self.player
        wanted = {"pedro": Pedro, "holy_model": HolyModel}.get(name)
        return next((p for p in self.props if wanted and isinstance(p, wanted)), None)

    # Building the level and save games

    def _spawn_level(self) -> None:
        for spawn in self.level.spawns:
            x, y = (spawn.x + 0.5) * TILE, (spawn.y + 1) * TILE
            if spawn.kind == "player":
                self.player = Player(x, y, self.assets)
            elif spawn.kind in ENEMY_TYPES:
                self.enemies.append(ENEMY_TYPES[spawn.kind](spawn.id, x, y, self.assets))
            else:
                self.props.append(make_prop(spawn.kind, spawn.id, x, y, self.assets))

    def snapshot(self) -> dict:
        """Return everything a save game needs to rebuild this level as it is now."""
        return {
            "player": self.player.to_dict(),
            "checkpoint": list(self.checkpoint),
            "destroyed": self.tilemap.destroyed_cells(),
            "removed": sorted(self.removed_spawns),
            "active_checkpoints": [p.spawn_id for p in self.props if isinstance(p, Checkpoint) and p.active],
            "fired_triggers": sorted(self.fired_triggers),
            "deleted": self.deleted,
        }

    def restore(self, data: dict) -> None:
        """Rebuild the level from a snapshot. It raises KeyError, TypeError or ValueError when the data is wrong."""
        for x, y in data["destroyed"]:
            self.tilemap.destroy(int(x), int(y))
        self.removed_spawns = {int(i) for i in data["removed"]}
        self.enemies = [e for e in self.enemies if e.spawn_id not in self.removed_spawns]
        self.props = [p for p in self.props if p.spawn_id not in self.removed_spawns]
        active = set(data["active_checkpoints"])
        for prop in self.props:
            if isinstance(prop, Checkpoint) and prop.spawn_id in active:
                prop.active = True
        self.checkpoint = (float(data["checkpoint"][0]), float(data["checkpoint"][1]))
        self.fired_triggers = set(data["fired_triggers"])
        self.deleted = int(data["deleted"])
        self.player.load(data["player"])
        self.camera.snap_to(self.player.center)
