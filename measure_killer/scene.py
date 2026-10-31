"""Scenes are the screens of the game: title menu, gameplay, pause menu and so on.

The scenes sit on a stack.
Only the top scene gets input and updates.
An overlay scene, like the pause menu, lets the scenes below it draw first.
"""

import pygame


class Scene:
    # Set this to True for overlays, so the scene below stays visible.
    draws_below = False
    # Gameplay hides the mouse pointer because it draws its own crosshair.
    shows_cursor = True

    def __init__(self, app):
        self.app = app

    def handle_event(self, event: pygame.event.Event) -> None:
        pass

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        pass

    def on_resume(self) -> None:
        """Called when the scene above this one closes."""


class SceneStack:
    def __init__(self):
        self._scenes: list[Scene] = []

    @property
    def top(self) -> Scene | None:
        return self._scenes[-1] if self._scenes else None

    def push(self, scene: Scene) -> None:
        self._scenes.append(scene)

    def pop(self) -> None:
        self._scenes.pop()
        if self.top:
            self.top.on_resume()

    def replace_all(self, scene: Scene) -> None:
        self._scenes = [scene]

    def draw(self, surface: pygame.Surface) -> None:
        first = len(self._scenes) - 1
        while first > 0 and self._scenes[first].draws_below:
            first -= 1
        for scene in self._scenes[first:]:
            scene.draw(surface)
