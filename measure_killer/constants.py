"""Values that the whole game shares.

The game draws everything on a small canvas of SCREEN_SIZE pixels.
The display then scales that canvas up to the window size the player picked.
"""

from pathlib import Path

GAME_TITLE = "Measure Killer and The Holy Model"
APP_DIR_NAME = "MeasureKiller"

SCREEN_SIZE = (960, 540)
SCREEN_W, SCREEN_H = SCREEN_SIZE
FPS = 60
DT = 1 / FPS

# The tileset art is 16 px per tile and the game draws it at 2x.
ART_TILE = 16
ART_SCALE = 2
TILE = ART_TILE * ART_SCALE

GRAVITY = 1500.0
MAX_FALL_SPEED = 900.0

ROOT_DIR = Path(__file__).resolve().parent.parent
RESOURCES_DIR = ROOT_DIR / "resources"
LEVELS_DIR = RESOURCES_DIR / "levels"
SOUNDS_DIR = RESOURCES_DIR / "sounds"
MUSIC_DIR = RESOURCES_DIR / "music"
FONTS_DIR = RESOURCES_DIR / "fonts"

# Colors
INK = (27, 27, 36)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
POWER_BI_YELLOW = (242, 200, 17)
HERO_GREEN = (168, 208, 44)
DANGER_RED = (230, 57, 70)
GOLD = (255, 214, 92)
SOFT_WHITE = (240, 240, 232)
GREY = (150, 150, 160)
