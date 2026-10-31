"""The hero, Measure Killer. He cuts the unused measures with his sword and throws fireballs at them."""

import math
from dataclasses import dataclass, field

import pygame

from measure_killer.animation import Animation, mirrored
from measure_killer.assets import Assets
from measure_killer.constants import GRAVITY, HERO_GREEN, TILE
from measure_killer.game import combat
from measure_killer.game.camera import Camera
from measure_killer.game.physics import Body, approach
from measure_killer.game.projectiles import FIRE_COLORS, Fireball

# The hero sheets are horizontal strips of square frames, seen from a 3/4 view facing east.
# The frame size is the height of the strip, and the number of frames is read from its width.
# The sword strips are bigger than the others, so the blade has room.
SPRITES = {
    "idle": "characters/measure_killer/idle.png",
    "walk": "characters/measure_killer/walk.png",
    "cast": "characters/measure_killer/cast.png",
    "jump": "characters/measure_killer/jump.png",
    "slash": "characters/measure_killer/sword_side.png",
}
# The jump strip holds one pose each for going up, coming down and landing. These are their frames.
JUMP_RISE = (0,)
JUMP_FALL = (1,)
JUMP_LAND = (2,)
FEET_MARGIN = 2  # the sprite's feet end this many pixel rows above the bottom of the frame
IDLE_FRAME = 96
IDLE_FPS = 5  # a slow breath
WALK_FPS = 10
JUMP_FPS = 8
LAND_TIME = 0.15


@dataclass(frozen=True)
class Action:
    """A one-shot move: how long it plays, and which frame of its strip lands the hit or the throw.

    Some frames show for longer, like the anticipation before a swing and the hit itself.
    Each frame lasts as many ticks as its entry in holds says, and every frame past the end of holds lasts one tick.
    """

    duration: float
    hit_frame: int
    holds: tuple[int, ...] = ()


ACTIONS = {
    "cast": Action(0.45, hit_frame=4),
    # The swing has three frames: a long anticipation, a fast smear, and the hit, which is held for impact.
    "slash": Action(0.4, hit_frame=2, holds=(5, 1, 2)),
}
CAST_POINT = (90, 54)  # where the fireball leaves his thrown hand, in pixels inside the idle-sized frame
SWORD_DAMAGE = 35.0
SWORD_POWER = 2  # cuts dirt, leaves, crates, platforms, wood and dark rock, see materials.py
SLASH_REACH = 48  # how far in front of him the swing hits enemies
LUNGE_SPEED = 300.0  # the swing carries him forward this fast
LUNGE_TIME = 0.12  # the lunge ends when the blade lands
MAX_ENERGY = 5  # fireball charges
RECHARGE_TIME = 2.0  # seconds per charge
TURN_DEAD_ZONE = 6  # the mouse must pass the middle of the hero by this many pixels to turn him around
WIDTH, HEIGHT = 30, 58
RUN_SPEED = 230.0
GROUND_ACCEL = 2400.0
AIR_ACCEL = 1500.0
FRICTION = 2800.0
JUMP_SPEED = 600.0
COYOTE_TIME = 0.1  # you can still jump this long after running off a ledge
JUMP_BUFFER = 0.12  # a jump pressed this long before landing still counts
MAX_HEALTH = 100
HURT_COOLDOWN = 0.9
RESPAWN_SHIELD = 2.0
DEBRIS = ((43, 43, 43), (70, 70, 70), HERO_GREEN)


@dataclass
class PlayerInput:
    """What the player asks the hero to do this frame."""

    move: int = 0
    jump_pressed: bool = False
    jump_held: bool = False
    drop: bool = False
    attack_pressed: bool = False
    fire_held: bool = False
    fire_pressed: bool = False
    aim: pygame.Vector2 = field(default_factory=pygame.Vector2)


class Player:
    def __init__(self, x: float, y: float, assets: Assets):
        """Place the hero with his feet centered on (x, y)."""
        self.assets = assets
        self.body = Body(x - WIDTH / 2, y - HEIGHT, WIDTH, HEIGHT)
        self._animations = _load_animations(assets)
        self.health = float(MAX_HEALTH)
        self.energy = MAX_ENERGY
        self.recharge = 0.0
        self.facing = 1
        self.aim_angle = 0.0
        self.alive = True
        self.hurt_timer = 0.0
        self.action: str | None = None  # the one-shot action that plays right now, a key of ACTIONS
        self.action_time = 0.0
        self.action_hit = 0.0  # when the hit or the throw of the action happens, in seconds from its start
        self.action_fired = False
        self.pose = "idle"
        self.pose_time = 0.0  # how long the current pose has shown
        self.land_timer = 0.0
        self.coyote = 0.0
        self.jump_buffer = 0.0

    @property
    def center(self) -> pygame.Vector2:
        return pygame.Vector2(self.body.rect.center)

    @property
    def head(self) -> pygame.Vector2:
        return pygame.Vector2(self.body.rect.centerx, self.body.rect.top + 8)

    @property
    def speech_anchor(self) -> pygame.Vector2:
        return pygame.Vector2(self.body.rect.centerx, self.body.rect.top - 6)

    @property
    def recharge_share(self) -> float:
        """Return how far the next fireball charge has come back, from 0 to 1."""
        return 0.0 if self.energy >= MAX_ENERGY else self.recharge / RECHARGE_TIME

    @property
    def hands(self) -> pygame.Vector2:
        """Return where a fireball leaves his hands, in world pixels. It mirrors when he faces left."""
        x, y = CAST_POINT
        rect = self.body.rect
        side = (x + 0.5 - IDLE_FRAME / 2) * self.facing
        return pygame.Vector2(rect.centerx + side, rect.bottom - (IDLE_FRAME - FEET_MARGIN) + y + 0.5)

    def update(self, world, inp: PlayerInput, dt: float) -> None:
        if not self.alive:
            return
        self.hurt_timer -= dt
        self._recharge(dt)
        self._move(world, inp, dt)
        self._aim(inp)
        if inp.attack_pressed:
            self._start_action("slash")
        if inp.fire_pressed or inp.fire_held:
            self._try_cast(world, inp.fire_pressed)
        self._update_action(world, dt)
        for material in self.body.touched:
            if material.hurts:
                self.hurt(world, material.hurts, -self.facing)
        if self.body.rect.top > world.tilemap.pixel_height + 64:
            self.die(world)
        self._track_pose(dt)

    def _track_pose(self, dt: float) -> None:
        """Keep the pose up to date. A pose change restarts its animation."""
        pose = self._pose_name()
        if pose != self.pose:
            self.pose = pose
            self.pose_time = 0.0
        else:
            self.pose_time += dt

    def _move(self, world, inp: PlayerInput, dt: float) -> None:
        body = self.body
        if inp.move == 0 and body.on_ground:
            accel = FRICTION
        else:
            accel = GROUND_ACCEL if body.on_ground else AIR_ACCEL
        body.vel.x = approach(body.vel.x, inp.move * RUN_SPEED, accel * dt)
        if self.action == "slash" and self.action_hit - LUNGE_TIME <= self.action_time < self.action_hit:
            body.vel.x = self.facing * LUNGE_SPEED
        self.coyote = COYOTE_TIME if body.on_ground else self.coyote - dt
        self.jump_buffer = JUMP_BUFFER if inp.jump_pressed else self.jump_buffer - dt
        if self.jump_buffer > 0 and self.coyote > 0:
            body.vel.y = -JUMP_SPEED
            self.coyote = self.jump_buffer = 0.0
            world.audio.play("jump")
        if body.vel.y < 0 and not inp.jump_held:
            # Letting go of jump early makes a short hop.
            body.vel.y += GRAVITY * 1.2 * dt
        was_on_ground = body.on_ground
        fall_speed = body.vel.y
        body.move(world.tilemap, dt, drop_through=inp.drop)
        if body.on_ground and not was_on_ground and fall_speed > 350:
            self.land_timer = LAND_TIME
            world.audio.play("land")
        self.land_timer -= dt

    def _aim(self, inp: PlayerInput) -> None:
        # Turn around by the middle of the hero, not by the hands.
        # Turning moves the hands to his other side, so the hands would make him flip back and forth.
        # He does not turn around in the middle of an attack or a throw.
        side = inp.aim.x - self.body.rect.centerx
        if abs(side) > TURN_DEAD_ZONE and self.action is None:
            self.facing = 1 if side > 0 else -1
        delta = inp.aim - self.hands
        if delta.length_squared() > 16:
            self.aim_angle = math.atan2(delta.y, delta.x)

    # The sword

    def _slash(self, world) -> None:
        """A wide swing in front of him. It cuts the two blocks in front of him, so he can walk on."""
        rect = self.body.rect
        # The box covers his own body too, because the lunge can carry him into the enemy before the blade lands.
        box = pygame.FRect(rect.left if self.facing > 0 else rect.left - SLASH_REACH, rect.top, rect.width + SLASH_REACH, rect.height)
        column = int((rect.centerx + self.facing * (rect.width / 2 + 12)) // TILE)
        cells = {(column, int((rect.top + 10) // TILE)), (column, int((rect.bottom - 10) // TILE))}
        self._sword_hit(world, box, pygame.Vector2(self.facing, -0.4), cells, SWORD_DAMAGE)

    def _sword_hit(self, world, box: pygame.FRect, push: pygame.Vector2, cells: set, damage: float) -> None:
        world.audio.play("sword")
        hit_something = False
        for enemy in world.enemies:
            if enemy.alive and enemy.body.rect.colliderect(box):
                enemy.take_hit(world, damage, push, source="sword")
                hit_something = True
        for x, y in cells:
            hit_something |= combat.cut_tile(world, x, y, SWORD_POWER)
        if hit_something:
            world.camera.shake(3)

    # Fireballs

    def _recharge(self, dt: float) -> None:
        if self.energy >= MAX_ENERGY:
            self.recharge = 0.0
            return
        self.recharge += dt
        if self.recharge >= RECHARGE_TIME:
            self.recharge -= RECHARGE_TIME
            self.energy += 1

    def _try_cast(self, world, pressed: bool) -> None:
        if self.action is not None:
            return
        if self.energy <= 0:
            if pressed:
                world.audio.play("empty")
            return
        self.energy -= 1
        self._start_action("cast")

    def _cast_sparks(self, world) -> None:
        hands = self.hands
        for _ in range(2):
            world.effects.ember(hands.x, hands.y, FIRE_COLORS)

    def _throw(self, world) -> None:
        hands = self.hands
        #! The hands reach out, so they can poke through a wall. Then the fireball starts inside the hero, so it hits that wall.
        center = self.center
        start = center if world.tilemap.raycast(center.x, center.y, hands.x, hands.y) else hands
        world.add_projectile(Fireball(start.x, start.y, self.aim_angle, self.assets))
        world.audio.play("cast")
        world.camera.shake(1.5)

    # One-shot actions

    def _start_action(self, name: str) -> None:
        """Start a one-shot action. Nothing starts while another one plays."""
        if self.action is not None:
            return
        self.action = name
        self.action_time = 0.0
        self.action_hit = self._animations[name][0].start_of(ACTIONS[name].hit_frame)
        self.action_fired = False

    def _update_action(self, world, dt: float) -> None:
        if self.action is None:
            return
        self.action_time += dt
        if self.action == "cast":
            self._cast_sparks(world)
        if not self.action_fired and self.action_time >= self.action_hit:
            self.action_fired = True
            {"cast": self._throw, "slash": self._slash}[self.action](world)
        if self.action_time >= ACTIONS[self.action].duration:
            self.action = None

    # Health

    def heal(self, amount: float) -> bool:
        if self.health >= MAX_HEALTH:
            return False
        self.health = min(MAX_HEALTH, self.health + amount)
        return True

    def hurt(self, world, amount: float, push_x: float) -> None:
        if not self.alive or self.hurt_timer > 0 or amount <= 0:
            return
        self.health -= amount
        self.hurt_timer = HURT_COOLDOWN
        self.body.vel.x = 260 if push_x >= 0 else -260
        self.body.vel.y = min(self.body.vel.y, -250)
        world.audio.play("player_hurt")
        world.camera.shake(5)
        if self.health <= 0:
            self.die(world)

    def die(self, world) -> None:
        if not self.alive:
            return
        self.alive = False
        self.health = 0
        x, y = self.body.rect.center
        world.effects.explosion(x, y)
        world.effects.debris(x, y, DEBRIS, count=30, speed=380)
        world.audio.play("explosion")
        world.on_player_died()

    def respawn(self, x: float, y: float) -> None:
        self.body.rect.midbottom = (x, y)
        self.body.vel.update(0, 0)
        self.health = float(MAX_HEALTH)
        self.energy = MAX_ENERGY
        self.action = None
        self.alive = True
        self.hurt_timer = RESPAWN_SHIELD

    # Drawing

    def draw(self, surface: pygame.Surface, camera: Camera) -> None:
        if not self.alive:
            return
        if self.hurt_timer > 0 and int(self.hurt_timer * 20) % 2 == 0:
            return
        frame = self._frame()
        width, height = frame.get_size()
        rect = self.body.rect
        surface.blit(frame, camera.to_screen(rect.centerx - width / 2, rect.bottom - (height - FEET_MARGIN)))

    def _frame(self) -> pygame.Surface:
        """Return the hero image that shows right now."""
        right, left = self._animations[self.pose]
        animation = right if self.facing > 0 else left
        time = self.pose_time
        # Walking away from where you aim plays the walk cycle backwards.
        if self.pose == "walk" and self.body.vel.x * self.facing < 0:
            time = -time
        return animation.frame(time)

    def _pose_name(self) -> str:
        if self.action is not None:
            return self.action
        if not self.body.on_ground:
            return "jump" if self.body.vel.y < 0 else "fall"
        if self.land_timer > 0:
            return "land"
        if abs(self.body.vel.x) > 20:
            return "walk"
        return "idle"

    def to_dict(self) -> dict:
        return {"x": self.body.rect.centerx, "y": self.body.rect.bottom, "health": self.health}

    def load(self, data: dict) -> None:
        """Restore the hero from a save game."""
        self.body.rect.midbottom = (float(data["x"]), float(data["y"]))
        self.health = min(float(data["health"]), MAX_HEALTH)


def _load_animations(assets: Assets) -> dict[str, tuple[Animation, Animation]]:
    """Load every pose as two animations: one facing right, one facing left."""
    strips = {name: assets.strip(path) for name, path in SPRITES.items()}
    jump = strips["jump"]
    poses = {
        "idle": (strips["idle"], IDLE_FPS, True, None),
        "walk": (strips["walk"], WALK_FPS, True, None),
        "jump": (_pick(jump, JUMP_RISE), JUMP_FPS, False, None),
        "fall": (_pick(jump, JUMP_FALL), JUMP_FPS, False, None),
        "land": (_pick(jump, JUMP_LAND), len(JUMP_LAND) / LAND_TIME, False, None),
    }
    for name, action in ACTIONS.items():
        frames = strips[name]
        # A strip that is too short, like a placeholder, gets as many of the holds as fit.
        holds = (action.holds + (1,) * len(frames))[: len(frames)]
        poses[name] = (frames, sum(holds) / action.duration, False, holds)
    return {
        name: (Animation(frames, fps, loop, holds), Animation(mirrored(frames), fps, loop, holds))
        for name, (frames, fps, loop, holds) in poses.items()
    }


def _pick(frames: list[pygame.Surface], indexes: tuple[int, ...]) -> list[pygame.Surface]:
    """Return the frames at these indexes. A strip that is too short, like a placeholder, gives its last frame."""
    return [frames[min(i, len(frames) - 1)] for i in indexes]


def standing_hero(assets: Assets, aim: float) -> Player:
    """Return a hero who stands on the ground. The title screen and the window icon show him."""
    hero = Player(0, 0, assets)
    hero.body.on_ground = True
    hero.aim_angle = aim
    return hero
