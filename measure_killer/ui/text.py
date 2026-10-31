"""Text helpers. The pixel font looks sharp only without anti-aliasing, so every render here turns it off."""

import pygame

from measure_killer.constants import INK, SOFT_WHITE

Color = tuple[int, int, int]


def outlined(font: pygame.font.Font, text: str, color: Color = SOFT_WHITE, outline: Color = INK) -> pygame.Surface:
    """Render text with a 1 px dark outline, so it reads on any background."""
    back = font.render(text, False, outline)
    image = pygame.Surface((back.get_width() + 2, back.get_height() + 2), pygame.SRCALPHA)
    for dx, dy in ((0, 1), (2, 1), (1, 0), (1, 2), (2, 2)):
        image.blit(back, (dx, dy))
    image.blit(font.render(text, False, color), (1, 1))
    return image


def draw_text(
    surface: pygame.Surface,
    font: pygame.font.Font,
    text: str,
    pos: tuple[float, float],
    color: Color = SOFT_WHITE,
    anchor: str = "topleft",
) -> pygame.Rect:
    """Draw outlined text. The anchor names the point of the text box that lands on pos, like "center"."""
    image = outlined(font, text, color)
    rect = image.get_rect(**{anchor: (round(pos[0]), round(pos[1]))})
    surface.blit(image, rect)
    return rect


def wrap(font: pygame.font.Font, text: str, max_width: int) -> list[str]:
    """Split text into lines that fit max_width. A newline in the text always starts a new line."""
    lines = []
    for paragraph in text.split("\n"):
        line = ""
        for word in paragraph.split(" "):
            candidate = f"{line} {word}" if line else word
            if font.size(candidate)[0] <= max_width or not line:
                line = candidate
            else:
                lines.append(line)
                line = word
        lines.append(line)
    return lines
