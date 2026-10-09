"""Application controller: menu -> game -> menu loop."""
from __future__ import annotations

import pygame
import pygame.locals as pg

from td.settings import WIDTH, HEIGHT, FPS, BG
from td.levels import LEVELS
from td.menu import MainMenu, LevelSelectMenu
from td.game import GameScene


class App:
    def __init__(self, base_path: Any) -> None:
        self.base_path = base_path
        pygame.init()
        pygame.display.set_caption("Tower Defense")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 18)

        self.main_menu = MainMenu(LEVELS)
        self.scene: GameScene | None = None
        self.state = "menu"  # "menu" | "playing" | "levels"
        self.level_menu: LevelSelectMenu | None = None
        self.mouse_pos = (0.0, 0.0)
        self.mouse_down = False
        self.pressed_btn: int | None = None

    def run(self) -> None:
        while True:
            dt = self.clock.tick(FPS) / 1000.0
            self._handle_events()
            self._update(dt)
            self._draw()

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------
    def _handle_events(self) -> None:
        for ev in pygame.event.get():
            if ev.type == pg.QUIT:
                pygame.quit()
                raise SystemExit
            if ev.type == pg.KEYDOWN:
                if ev.key == pg.K_ESCAPE:
                    if self.state == "playing" and self.scene is not None:
                        self.scene.set_paused(not self.scene._paused)
                    elif self.state == "playing" and self.scene is not None and self.scene._paused:
                        self.scene.set_paused(False)
                    else:
                        pygame.quit()
                        raise SystemExit
                if ev.key == pg.K_p and self.state == "playing" and self.scene is not None:
                    self.scene.set_paused(not self.scene._paused)
                if ev.key == pg.K_r and self.state == "playing" and self.scene is not None:
                    if self.scene._game_over or self.scene._level_complete:
                        self.scene._retry()
            if ev.type == pg.MOUSEMOTION:
                self.mouse_pos = (float(ev.pos[0]), float(ev.pos[1]))
            if ev.type == pg.MOUSEBUTTONDOWN:
                self.mouse_down = True
                self.pressed_btn = ev.button
                self.mouse_pos = (float(ev.pos[0]), float(ev.pos[1]))
            if ev.type == pg.MOUSEBUTTONUP:
                self.mouse_down = False
                if ev.button in (1, 3):
                    self.mouse_pos = (float(ev.pos[0]), float(ev.pos[1]))
                    self._handle_click(ev.button, self.mouse_pos)
                self.pressed_btn = None

    def _handle_click(self, button: int, pos: tuple[float, float]) -> None:
        if self.state == "menu":
            action = self.main_menu.handle_click(pos)
            if action:
                kind, val = action
                if kind == "play":
                    self._start_game(level_index=0, infinite=False)
                elif kind == "infinite":
                    self._start_game(level_index=None, infinite=True)
                elif kind == "levels":
                    self.level_menu = LevelSelectMenu(LEVELS)
                    self.state = "levels"
                elif kind == "quit":
                    pygame.quit()
                    raise SystemExit
        elif self.state == "levels" and self.level_menu is not None:
            action = self.level_menu.handle_click(pos)
            if action:
                kind, val = action
                if kind == "level":
                    self._start_game(level_index=val, infinite=False)
                elif kind == "back":
                    self.level_menu = None
                    self.state = "menu"
        elif self.state == "playing" and self.scene is not None:
            if button == 1:
                self.scene.handle_click(pos, 1)
            elif button == 3:
                self.scene.handle_right_click(pos)
            if self.scene._return_to_menu:
                self._back_to_menu()
            if self.scene._advance_level:
                self._start_game(self.scene.level_index + 1, False)

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------
    def _update(self, dt: float) -> None:
        if self.state == "menu":
            self.main_menu.update(self.mouse_pos)
        elif self.state == "levels" and self.level_menu is not None:
            self.level_menu.update(self.mouse_pos)
        elif self.state == "playing" and self.scene is not None:
            self.scene.handle_hover(self.mouse_pos)
            self.scene.update(dt)

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------
    def _draw(self) -> None:
        self.screen.fill(BG)
        if self.state == "menu":
            self.main_menu.draw(self.screen)
        elif self.state == "levels" and self.level_menu is not None:
            self.level_menu.draw(self.screen)
        elif self.state == "playing" and self.scene is not None:
            self.scene.draw()
        pygame.display.flip()

    # ------------------------------------------------------------------
    # Transitions
    # ------------------------------------------------------------------
    def _start_game(self, level_index: int | None, infinite: bool) -> None:
        self.scene = GameScene(self.screen, self.base_path, level_index=level_index, infinite=infinite)
        self.scene.reset()
        self.state = "playing"

    def _back_to_menu(self) -> None:
        self.scene = None
        self.state = "menu"
        self.main_menu = MainMenu(LEVELS)
