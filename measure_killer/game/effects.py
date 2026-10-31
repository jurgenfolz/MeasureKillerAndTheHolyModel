"""Visual effects: flying debris, blood, guts, sparks, embers, explosions, flying bodies and floating text.

Effects never change the game rules.
They only make hits and explosions feel strong.
"""

import math
import random
from dataclasses import dataclass

import pygame

from measure_killer.animation import Animation
from measure_killer.assets import Assets
from measure_killer.constants import TILE
from measure_killer.game.camera import Camera
from measure_killer.game.tilemap import TileMap
from measure_killer.ui.text import outlined

MAX_PARTICLES = 1200
WHITE_HOT = (255, 255, 230)
BLOOD = ((120, 8, 20), (170, 15, 25), (210, 30, 40), (90, 5, 15))
GUTS = ((150, 20, 40), (110, 10, 30), (200, 60, 90), (175, 95, 125))
BODY_GRAVITY = 1300.0
Color = tuple[int, int, int]


@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    color: Color
    size: int
    gravity: float = 900.0
    bounces: bool = True
    age: float = 0.0


@dataclass
class FloatingText:
    x: float
    y: float
    image: pygame.Surface
    life: float = 1.1
    age: float = 0.0


@dataclass
class FlyingBody:
    """A dead enemy knocked off its feet. It spins through the air and bleeds, then it is gone."""

    x: float
    y: float
    vx: float
    vy: float
    image: pygame.Surface
    spin: float  # degrees per second
    angle: float = 0.0
    life: float = 2.2
    age: float = 0.0


@dataclass
class SpriteEffect:
    x: float
    y: float
    animation: Animation
    age: float = 0.0


class Effects:
    def __init__(self, assets: Assets, font: pygame.font.Font):
        self.font = font
        self.particles: list[Particle] = []
        self.texts: list[FloatingText] = []
        self.sprites: list[SpriteEffect] = []
        self.bodies: list[FlyingBody] = []
        self._explosion = Animation(assets.frames("effects/explosion.png", 64, 64, scale=2.5), fps=16, loop=False)
        self._fire_burst = Animation(assets.frames("effects/fire_burst.png", 32, 32, scale=2), fps=18, loop=False)

    def debris(self, x: float, y: float, colors: tuple[Color, ...], count: int = 8, speed: float = 170) -> None:
        for _ in range(count):
            angle = random.uniform(math.pi * 1.05, math.pi * 1.95)
            power = random.uniform(0.3, 1.0) * speed
            self._add(Particle(
                x + random.uniform(-8, 8), y + random.uniform(-8, 8),
                math.cos(angle) * power, math.sin(angle) * power,
                life=random.uniform(0.6, 1.3), color=random.choice(colors), size=random.choice((3, 4, 4, 6)),
            ))

    def blood(self, x: float, y: float, count: int = 12, speed: float = 240) -> None:
        """Blood sprays out in every direction. The drops bounce and stay around for a while."""
        for _ in range(count):
            angle = random.uniform(0, math.tau)
            power = random.uniform(0.2, 1.0) * speed
            self._add(Particle(
                x + random.uniform(-6, 6), y + random.uniform(-10, 10),
                math.cos(angle) * power, math.sin(angle) * power - speed * 0.4,
                life=random.uniform(1.2, 3.5), color=random.choice(BLOOD), size=random.choice((2, 3, 3, 4, 5)),
            ))

    def guts(self, x: float, y: float, count: int = 14, speed: float = 320) -> None:
        """Chunks fly out of a dead enemy. They bounce and lie around for a long while."""
        for _ in range(count):
            angle = random.uniform(0, math.tau)
            power = random.uniform(0.3, 1.0) * speed
            self._add(Particle(
                x + random.uniform(-8, 8), y + random.uniform(-10, 10),
                math.cos(angle) * power, math.sin(angle) * power - speed * 0.5,
                life=random.uniform(2.5, 5.0), color=random.choice(GUTS), size=random.choice((5, 6, 7, 8, 9)),
            ))

    def flying_body(self, image: pygame.Surface, x: float, y: float, velocity: pygame.Vector2) -> None:
        self.bodies.append(FlyingBody(x, y, velocity.x, velocity.y, image, spin=random.choice((-1, 1)) * random.uniform(400, 800)))

    def sparks(self, x: float, y: float, normal: tuple[float, float], count: int = 5) -> None:
        base = math.atan2(normal[1], normal[0]) if normal != (0, 0) else -math.pi / 2
        for _ in range(count):
            angle = base + random.uniform(-0.9, 0.9)
            power = random.uniform(120, 320)
            self._add(Particle(
                x, y, math.cos(angle) * power, math.sin(angle) * power,
                life=random.uniform(0.12, 0.3), color=random.choice(((255, 236, 140), (255, 190, 80), WHITE_HOT)),
                size=2, gravity=600, bounces=False,
            ))

    def wants_trail(self) -> bool:
        """Return True on some frames, so a flying thing leaves a loose trail instead of a solid line."""
        return random.random() < 0.6

    def ember(self, x: float, y: float, colors: tuple[Color, ...]) -> None:
        """Leave a small glowing piece that drifts up and fades fast."""
        self._add(Particle(
            x + random.uniform(-3, 3), y + random.uniform(-3, 3), random.uniform(-30, 30), random.uniform(-70, -20),
            life=random.uniform(0.15, 0.4), color=random.choice(colors), size=random.choice((2, 3)), gravity=0, bounces=False,
        ))

    def explosion(self, x: float, y: float) -> None:
        self.sprites.append(SpriteEffect(x, y, self._explosion))
        self.debris(x, y, ((255, 220, 120), (255, 150, 60), (90, 80, 80)), count=24, speed=420)
        self.sparks(x, y, (0, -1), count=14)

    def fire_burst(self, x: float, y: float) -> None:
        """A fireball bursting: a small fire explosion with embers flying out."""
        self.sprites.append(SpriteEffect(x, y, self._fire_burst))
        self.sparks(x, y, (0, -1), count=10)
        for _ in range(6):
            self.ember(x, y, ((255, 236, 140), (255, 160, 50), (230, 80, 30)))

    def float_text(self, x: float, y: float, text: str, color: Color) -> None:
        image = outlined(self.font, text, color)
        self.texts.append(FloatingText(x - image.get_width() / 2, y, image))

    def update(self, dt: float, tilemap: TileMap) -> None:
        alive = []
        for p in self.particles:
            p.age += dt
            if p.age >= p.life:
                continue
            p.vy += p.gravity * dt
            nx, ny = p.x + p.vx * dt, p.y + p.vy * dt
            if p.bounces and tilemap.is_solid(int(nx // TILE), int(ny // TILE)):
                p.vx *= 0.5
                p.vy = -p.vy * 0.3
            else:
                p.x, p.y = nx, ny
            alive.append(p)
        self.particles = alive
        for text in self.texts:
            text.age += dt
            text.y -= 34 * dt
        self.texts = [t for t in self.texts if t.age < t.life]
        for sprite in self.sprites:
            sprite.age += dt
        self.sprites = [s for s in self.sprites if not s.animation.finished(s.age)]
        for body in self.bodies:
            body.age += dt
            body.vy += BODY_GRAVITY * dt
            body.x += body.vx * dt
            body.y += body.vy * dt
            body.angle += body.spin * dt
            if random.random() < 0.7:
                self.blood(body.x, body.y, count=1, speed=60)
        self.bodies = [b for b in self.bodies if b.age < b.life]

    def draw(self, surface: pygame.Surface, camera: Camera) -> None:
        ox, oy = camera.offset
        for p in self.particles:
            surface.fill(p.color, (p.x - ox, p.y - oy, p.size, p.size))
        for sprite in self.sprites:
            frame = sprite.animation.frame(sprite.age)
            surface.blit(frame, frame.get_rect(center=(sprite.x - ox, sprite.y - oy)))
        for body in self.bodies:
            image = pygame.transform.rotate(body.image, body.angle)
            surface.blit(image, image.get_rect(center=(body.x - ox, body.y - oy)))
        for text in self.texts:
            text.image.set_alpha(int(255 * min(1.0, 2 * (1 - text.age / text.life))))
            surface.blit(text.image, (text.x - ox, text.y - oy))

    def _add(self, particle: Particle) -> None:
        if len(self.particles) < MAX_PARTICLES:
            self.particles.append(particle)
