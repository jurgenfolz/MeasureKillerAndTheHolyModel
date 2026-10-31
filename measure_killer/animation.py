"""A simple frame animation."""

import pygame


class Animation[Frame]:
    """Picks a frame by time. A frame can be an image, or the number of a frame in a sprite sheet."""

    def __init__(self, frames: list[Frame], fps: float, loop: bool = True, holds: tuple[int, ...] | None = None):
        """Each frame shows for one tick of the fps, or for as many ticks as its entry in holds says."""
        self.frames = frames
        self.fps = fps
        self.loop = loop
        self.holds = holds or (1,) * len(frames)

    @property
    def ticks(self) -> int:
        return sum(self.holds)

    @property
    def duration(self) -> float:
        return self.ticks / self.fps

    def frame(self, time: float) -> Frame:
        """Return the frame to show after the animation has run for this many seconds."""
        tick = int(time * self.fps)
        if self.loop:
            tick %= self.ticks
        else:
            tick = min(tick, self.ticks - 1)
        for frame, hold in zip(self.frames, self.holds):
            tick -= hold
            if tick < 0:
                return frame
        return self.frames[-1]

    def start_of(self, index: int) -> float:
        """Return when the frame at this index starts to show, in seconds from the start."""
        return sum(self.holds[:index]) / self.fps

    def finished(self, time: float) -> bool:
        return not self.loop and time >= self.duration


def mirrored(frames: list[pygame.Surface]) -> list[pygame.Surface]:
    """Return the frames flipped left to right. All sprites face right, so this makes them face left."""
    return [pygame.transform.flip(frame, True, False) for frame in frames]
