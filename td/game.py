"""Main game scene: the play loop, grid, path, towers, enemies, projectiles, HUD, menus, shop."""
from __future__ import annotations

import math
import random
from typing import Any, Dict, List, Optional

import pygame
import pygame.locals as pg

from td.settings import (
    WIDTH, HEIGHT, TILE, COLS, ROWS,
    FIELD_LEFT, FIELD_TOP, FIELD_RIGHT, FIELD_BOTTOM,
    GRID_COLS, GRID_ROWS, PLACE_MARGIN,
    BG, PANEL, GOLD_COLOR, TEXT_DARK, TEXT_MUTED, ACCENT,
    TOWER_TEMPLATES, ENEMY_TEMPLATES, STARTING_GOLD, STARTING_LIVES,
)
from td.path import Path
from td.entities import Enemy, Tower, Projectile, Particle, spawn_hit_particles, spawn_death_particles, dist
from td.waves import Spawner, WaveTimeline, make_infinite_timeline
from td.levels import LEVELS, build_timeline, tower_config_from_type, enemy_template_from_type
from td.menu import MainMenu, HUD, level_complete_screen, game_over_screen, Button
from td.shop import ShopScreen
from td.save import load_into_scene, autosave

Vec2 = tuple[float, float]


class GameScene:
    def __init__(
        self,
        screen: pygame.Surface,
        base_path: Any,
        level_index: int | None = None,
        infinite: bool = False,
    ) -> None:
        self.screen = screen
        self.base_path = base_path

        self.level_index = level_index
        self.infinite = infinite
        self.infinite_wave_index = 0

        # build level data
        if level_index is not None:
            data = LEVELS[level_index]
            self.level_name = data["name"]
            self.mode_name = f"Level {level_index + 1}"
            self.starting_gold = data.get("starting_gold", STARTING_GOLD)
            self.starting_lives = data.get("starting_lives", STARTING_LIVES)
            self.tower_order = list(data.get("tower_shop", ["rapid"]))
            self.timeline = build_timeline(data["waves"])
        else:
            self.level_name = "Infinite"
            self.mode_name = "Infinite Mode"
            self.starting_gold = 220
            self.starting_lives = 20
            self.tower_order = ["rapid", "cannon", "sniper", "frost"]
            # infinite uses a base timeline built from level 3 as a template,
            # but re-created each wave cycle via make_infinite_timeline.
            self._infinite_base_events = LEVELS[2]["waves"]
            self.timeline = build_timeline(self._infinite_base_events)

        # appliquer le thème du niveau (couleurs du fond, field, grille, path)
        from td.settings import LEVEL_THEMES
        if level_index is not None:
            self.theme_index = int(data.get("theme", 0))
        else:
            self.theme_index = 5  # Nuit / Cosmos pour infinite
        self.theme = dict(LEVEL_THEMES.get(self.theme_index, LEVEL_THEMES[0]))

        # path + grid
        self.path = Path(self._level_waypoints(data=data) if level_index is not None else self._infinite_waypoints())
        self.reserved_cells = self.path.grid_cells_for_path(GRID_COLS, GRID_ROWS)

        # state
        self.gold = self.starting_gold
        self.lives = self.starting_lives
        self.max_lives = self.starting_lives
        self.score = 0
        self.wave_text = "Preparing"
        self.wave_progress = 0.0

        self.towers: List[Tower] = []
        self.enemies: List[Enemy] = []
        self.projectiles: List[Projectile] = []
        self.particles: List[Particle] = []

        self.spawner = Spawner(self.timeline)
        self.spawned_this_wave = 0
        self.killed_this_wave = 0
        self._wave_active = False
        self._wave_start_clock = 0.0
        self._between_waves_timer = 0.0
        self._game_over = False
        self._level_complete = False
        self._paused = False
        self._endedScreen: Optional[EndScreen] = None
        self._return_to_menu = False
        self._advance_level = False
        self._active_boosts: Dict[str, float] = {}

        # tower placement
        self.placing_tower_type: Optional[str] = None
        self.hovered_cell: Optional[tuple[int, int]] = None
        self.hovered_tower_type: Optional[str] = None
        self.show_range_on: Optional[Tower] = None
        self.selected_tower: Optional[Tower] = None
        self.shop: Optional[ShopScreen] = None
        self.shop_open = False

        # enemy waypoints cache (pixel coords)
        self._waypoints = self.path.waypoints
        self._path_total = self.path.total_length

        # input state
        self._mouse_pos = (0.0, 0.0)
        self._click_pos = (0.0, 0.0)
        self._mouse_down = False

        # subsidy for infinite mode: extra gold every few waves
        self._infinite_gold_bonus = 0

    # ------------------------------------------------------------------
    # Waypoints
    # ------------------------------------------------------------------
    def _level_waypoints(self, data: Dict[str, Any]) -> List[Vec2]:
        # waypoints are already stored as pixel coords by _w() in levels.py
        return list(data["waypoints"])

    def _infinite_waypoints(self) -> List[Vec2]:
        # A longer, more complex path for infinite mode
        # The path winds through the field multiple times for a longer journey
        return [
            (FIELD_LEFT + 1 * TILE + TILE / 2, FIELD_TOP + 2 * TILE + TILE / 2),
            (FIELD_LEFT + 1 * TILE + TILE / 2, FIELD_TOP + 7 * TILE + TILE / 2),
            (FIELD_LEFT + 5 * TILE + TILE / 2, FIELD_TOP + 7 * TILE + TILE / 2),
            (FIELD_LEFT + 5 * TILE + TILE / 2, FIELD_TOP + 2 * TILE + TILE / 2),
            (FIELD_LEFT + 9 * TILE + TILE / 2, FIELD_TOP + 2 * TILE + TILE / 2),
            (FIELD_LEFT + 9 * TILE + TILE / 2, FIELD_TOP + 7 * TILE + TILE / 2),
            (FIELD_LEFT + 13 * TILE + TILE / 2, FIELD_TOP + 7 * TILE + TILE / 2),
            (FIELD_LEFT + 13 * TILE + TILE / 2, FIELD_TOP + 3 * TILE + TILE / 2),
            (FIELD_LEFT + 16 * TILE + TILE / 2, FIELD_TOP + 3 * TILE + TILE / 2),
            (FIELD_LEFT + 16 * TILE + TILE / 2, FIELD_TOP + 10 * TILE + TILE / 2),
            (FIELD_LEFT + 12 * TILE + TILE / 2, FIELD_TOP + 10 * TILE + TILE / 2),
            (FIELD_LEFT + 12 * TILE + TILE / 2, FIELD_TOP + 5 * TILE + TILE / 2),
            (FIELD_LEFT + 8 * TILE + TILE / 2, FIELD_TOP + 5 * TILE + TILE / 2),
            (FIELD_LEFT + 8 * TILE + TILE / 2, FIELD_TOP + 11 * TILE + TILE / 2),
            (FIELD_LEFT + 4 * TILE + TILE / 2, FIELD_TOP + 11 * TILE + TILE / 2),
            (FIELD_LEFT + 4 * TILE + TILE / 2, FIELD_TOP + 7 * TILE + TILE / 2),
            (FIELD_LEFT + 1 * TILE + TILE / 2, FIELD_TOP + 7 * TILE + TILE / 2),
        ]

    # ------------------------------------------------------------------
    # Reset / start
    # ------------------------------------------------------------------
    def reset(self, load_save: bool = False) -> None:
        self.gold = self.starting_gold
        self.lives = self.starting_lives
        self.score = 0
        self.towers.clear()
        self.enemies.clear()
        self.projectiles.clear()
        self.particles.clear()
        self.spawned_this_wave = 0
        self.killed_this_wave = 0
        self._wave_active = False
        self._wave_start_clock = 0.0
        self._between_waves_timer = 0.0
        self._game_over = False
        self._level_complete = False
        self._endedScreen = None
        self._return_to_menu = False
        self._advance_level = False
        self.placing_tower_type = None
        self.selected_tower = None
        self.show_range_on = None
        self._infinite_gold_bonus = 0
        self.wave_progress = 0.0
        self._active_boosts: Dict[str, float] = {}

        if self.infinite:
            self.infinite_wave_index = 0
            self.timeline = self._build_infinite_timeline()
        else:
            self.timeline = build_timeline(self._level_data()["waves"])

        self.path = Path(self._waypoints)
        self.reserved_cells = self.path.grid_cells_for_path(GRID_COLS, GRID_ROWS)
        self.spawner = Spawner(self.timeline)
        self.wave_text = "Preparing"
        self._start_next_wave()

    def _level_data(self) -> Dict[str, Any]:
        if self.level_index is not None:
            return LEVELS[self.level_index]
        return LEVELS[2]

    def _apply_theme_background(self, surface: pygame.Surface) -> None:
        """Remplit l'écran et le field avec les couleurs du thème."""
        t = self.theme
        bg = tuple(int(c) for c in t.get("bg", (20, 24, 30)))
        field = tuple(int(c) for c in t.get("field", (26, 30, 36)))
        pygame.draw.rect(surface, bg, (0, 0, WIDTH, HEIGHT))
        pygame.draw.rect(
            surface,
            field,
            (FIELD_LEFT, FIELD_TOP, FIELD_RIGHT - FIELD_LEFT, FIELD_BOTTOM - FIELD_TOP),
        )

    def _draw_grid_themed(self, surface: pygame.Surface) -> None:
        t = self.theme
        grid = tuple(int(c) for c in t.get("grid", (40, 46, 56)))
        for c in range(GRID_COLS + 1):
            x = FIELD_LEFT + c * TILE
            pygame.draw.line(surface, grid, (x, FIELD_TOP), (x, FIELD_BOTTOM), 1)
        for r in range(GRID_ROWS + 1):
            y = FIELD_TOP + r * TILE
            pygame.draw.line(surface, grid, (FIELD_LEFT, y), (FIELD_RIGHT, y), 1)


    def _load_save_if_any(self, base_path) -> None:
        if not load_into_scene(base_path, self):
            return
        self._mark_save_loaded()
        # ne pas reset() après load; les tours/or/vie sont déjà dans la scène
        # re-définir la timeline selon le niveau chargé
        if self.infinite:
            self.infinite_wave_index = 0
            self.timeline = self._build_infinite_timeline()
        else:
            self.timeline = build_timeline(self._level_data()["waves"])
        self.spawner = Spawner(self.timeline)
        self._wave_active = False
        self._wave_start_clock = 0.0
        self._between_waves_timer = 0.0
        self._game_over = False
        self._level_complete = False
        self._endedScreen = None
        self._return_to_menu = False
        self._advance_level = False
        self.placing_tower_type = None
        self.selected_tower = None
        self.show_range_on = None
        self._infinite_gold_bonus = 0
        self.shop_open = False
        self.shop = None
        self.wave_text = "Preparing"
        self.wave_progress = 0.0
        self.path = Path(self._waypoints)
        self.reserved_cells = self.path.grid_cells_for_path(GRID_COLS, GRID_ROWS)
        self._start_next_wave()

    def _save_loaded(self) -> bool:
        return self._save_loaded

    def _mark_save_loaded(self) -> None:
        self._save_loaded = True

    def _start_next_wave(self) -> None:
        if self.infinite:
            self.timeline = self._build_infinite_timeline()
            self.spawner = Spawner(self.timeline)
            self.infinite_wave_index += 1
            # bonus gold every 3rd wave
            if (self.infinite_wave_index - 1) % 3 == 0:
                self._infinite_gold_bonus = 15 + (self.infinite_wave_index // 3) * 5
                self.gold += self._infinite_gold_bonus
            wave_label = f"Infinite Wave {self.infinite_wave_index}"
        else:
            self.spawner = Spawner(self.timeline)
            wave_label = "Wave 1"

        self.wave_text = wave_label
        self.wave_progress = 0.0
        self.spawned_this_wave = 0
        self.killed_this_wave = 0
        self._wave_active = True
        self._wave_start_clock = 0.0
        # give a little starting gold for infinite
        if self.infinite:
            self.gold += 10

    # ------------------------------------------------------------------
    def set_paused(self, paused: bool) -> None:
        self._paused = paused

    def open_shop(self) -> None:
        if self.shop is None:
            self.shop = ShopScreen(
                self.gold,
                self._buy_tower_from_shop,
                self._buy_boost_from_shop,
                self._close_shop,
            )
        else:
            self.shop.set_gold(self.gold)
        self.shop_open = True

    def _close_shop(self) -> None:
        self.shop_open = False

    def _buy_tower_from_shop(self, ttype: str) -> None:
        cfg = tower_config_from_type(ttype)
        cost = int(cfg.get('cost', 0))
        if self.gold >= cost:
            self.gold -= cost
            # met타워 배치 상태로 전환할 수도 있지만, 외부 구매 시에는 바로 배치를 유도하지 않음
            # 여기서는 단순히 소비만 반영
            pass

    def _buy_boost_from_shop(self, bcfg: dict) -> None:
        cost = int(bcfg.get('cost', 0))
        if self.gold >= cost:
            self.gold -= cost
            stat = bcfg.get('stat', '')
            dur = float(bcfg.get('duration', 0.0))
            if stat == 'damage_mult':
                self._active_boosts['damage_mult'] = dur
            elif stat == 'range_mult':
                self._active_boosts['range_mult'] = dur
            elif stat == 'fire_rate_mult':
                self._active_boosts['fire_rate_mult'] = dur

    def _active_boosts(self):
        return self._active_boosts

    # ------------------------------------------------------------------
    # Input helpers
    # ------------------------------------------------------------------
    def cell_from_pos(self, pos: Vec2) -> Optional[tuple[int, int]]:
        x, y = pos
        c = int((x - FIELD_LEFT) / TILE)
        r = int((y - FIELD_TOP) / TILE)
        if 0 <= c < GRID_COLS and 0 <= r < GRID_ROWS:
            return (c, r)
        return None

    def cell_center(self, cell: tuple[int, int]) -> Vec2:
        c, r = cell
        return (FIELD_LEFT + c * TILE + TILE / 2, FIELD_TOP + r * TILE + TILE / 2)

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------
    def update(self, dt: float) -> None:
        if self._paused:
            return
        if self._game_over or self._level_complete:
            self._update_particles(dt)
            return

        if self._wave_active and self.spawner.finished and len(self.enemies) == 0:
            # wave cleared
            self._wave_active = False
            self.wave_text = "Wave cleared!"
            self._between_waves_timer = 2.0
            self._give_wave_clear_bonus()

        if self._between_waves_timer > 0:
            self._between_waves_timer -= dt
            if self._between_waves_timer <= 0:
                if not self.infinite:
                    # check if timeline fully done
                    if self.spawner.finished or self.spawner.clock >= self.timeline.duration + 1.0:
                        self._end_level(True)
                        return
                self._start_next_wave()

        # spawner
        if self._wave_active:
            self.spawner.update(dt, self._do_spawn)
            # progress estimate
        if self.timeline.duration > 0:
            self.wave_progress = min(1.0, self.spawner.clock / max(0.1, self.timeline.duration))

        # enemies
        for e in self.enemies:
            if not e.is_dead() and not e.reached_end:
                e.advance(dt, self._path_total)

        # towers
        for t in self.towers:
            t._enemies_near = self.enemies
            proj = t.update(dt, self.enemies)
            if proj is not None:
                self.projectiles.append(proj)
            self._expire_boosts(dt)

        # projectiles
        for p in self.projectiles:
            if p.update(dt):
                continue
        self.projectiles = [p for p in self.projectiles if p.alive]

        # enemies that reached the end
        for e in self.enemies:
            if e.reached_end and not e.is_dead():
                self.lives -= 1
                self.wave_text = "Lives lost!"
                e._done = True
                if self.lives <= 0:
                    self.lives = 0
                    self._end_level(False)

        # remove dead enemies, collect rewards
        dead: List[Enemy] = []
        for e in self.enemies:
            if e.is_dead():
                if not e.reached_end:
                    # killed
                    self.gold += int(e.reward)
                    self.score += int(e.reward * 2)
                    self.killed_this_wave += 1
                    self.particles.extend(spawn_death_particles((e.x, e.y), e.color, 14))
                dead.append(e)
        self.enemies = [e for e in self.enemies if e not in dead]

        # particles
        self._update_particles(dt)

        # hover logic
        self._update_hover()

    def _update_particles(self, dt: float) -> None:
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.alive()]

    def _give_wave_clear_bonus(self) -> None:
        bonus = 5 + self.killed_this_wave // 3
        self.gold += bonus
        self.wave_text = f"Wave cleared! +{bonus} gold"

    def _end_level(self, won: bool) -> None:
        if self._level_complete or self._game_over:
            return
        if self.infinite:
            # infinite never ends; just keep going
            self._wave_active = False
            self._between_waves_timer = 1.5
            self.wave_text = "Wave cleared!"
            return

        # save before showing end screen (so reload restore towers/gold etc.)
        if self._save_loaded:
            autosave(self.base_path, self)

        if won:
            self._level_complete = True
            self._endedScreen = level_complete_screen(
                self._retry,
                self._back_to_menu,
                self._next_level if self.level_index is not None and self.level_index + 1 < len(LEVELS) else None,
            )
            self.wave_text = "Level complete!"
        else:
            self._game_over = True
            self._endedScreen = game_over_screen(self._retry, self._back_to_menu)
            self.wave_text = "Game over"

    def _expire_boosts(self, dt: float) -> None:
        for k in list(self._active_boosts.keys()):
            v = self._active_boosts[k]
            if v > 0:
                nv = v - dt
                if nv <= 0:
                    del self._active_boosts[k]
                else:
                    self._active_boosts[k] = nv

    def _do_spawn(self, enemy_type: str, hp: float, speed: float, reward: float) -> None:
        t = enemy_template_from_type(enemy_type)
        color = pygame.Color(t.get("color", (255, 255, 255)))
        radius = float(t.get("radius", 9))
        hp = max(1.0, hp)
        e = Enemy(
            path=self.path,
            enemy_type=enemy_type,
            max_hp=hp,
            speed=speed,
            reward=reward,
            color=color,
            radius=radius,
            waypoints=self._waypoints,
        )
        e.reset_progress()
        # start a little before the first waypoint
        start = self.path.place_enemy_at_distance(0, radius + 8)
        e.pos[0], e.pos[1] = start
        e.set_progress(0.0)
        self.enemies.append(e)
        self.spawned_this_wave += 1

    def _update_hover(self) -> None:
        mx, my = self._mouse_pos
        cell = self.cell_from_pos((mx, my))
        self.hovered_cell = cell
        # shop hover
        self.hovered_tower_type = None
        if cell is None:
            # check tower shop hover
            for t in self.tower_order:
                cfg = TOWER_TEMPLATES[t]
                cost = int(cfg.get("cost", 0))
                left = WIDTH - 210
                top = 70
                y = top + 34 + self.tower_order.index(t) * 94
                btn = pg.Rect(left, y, 180, 84)
                if btn.collidepoint(int(mx), int(my)):
                    if self.gold >= cost:
                        self.hovered_tower_type = t
                    break

    # ------------------------------------------------------------------
    # Input handling
    # ------------------------------------------------------------------
    def handle_click(self, pos: Vec2, button: int = 1) -> None:
        if self._endedScreen is not None:
            action = self._endedScreen.handle_click(pos)
            if action:
                kind, val = action
                if kind == "retry":
                    self._retry()
                elif kind == "menu":
                    self._back_to_menu()
            return

        if self.shop_open and self.shop is not None:
            action = self.shop.handle_click(pos)
            if action is not None:
                return
            # le clic est hors du shop => on traite comme un clic normal

        mx, my = pos

        # bouton shop (coin supérieur droit, hors panneau droit)
        shop_btn = pg.Rect(WIDTH - 60, 12, 44, 36)
        if shop_btn.collidepoint(int(mx), int(my)):
            if self.shop_open:
                self._close_shop()
            else:
                self.open_shop()
            return
        # débogage placement
        if self.placing_tower_type is not None:
            pass  # on continue le placement plus bas

        # clique sur le panneau droit (boutique de tours rapides)
        left = WIDTH - 210
        top = 70
        for t in self.tower_order:
            cfg = TOWER_TEMPLATES[t]
            cost = int(cfg.get("cost", 0))
            y = top + 34 + self.tower_order.index(t) * 94
            btn = pg.Rect(left, y, 180, 84)
            if btn.collidepoint(int(mx), int(my)):
                if self.gold >= cost:
                    if self.placing_tower_type == t:
                        self.placing_tower_type = None
                    else:
                        self.placing_tower_type = t
                        self.selected_tower = None
                        self.show_range_on = None
                return

        # map click (recalculer hovered_cell depuis pos)
        cell = self.cell_from_pos((mx, my))
        self.hovered_cell = cell
        if cell is None:
            if self.placing_tower_type is not None:
                self.placing_tower_type = None
            self.selected_tower = None
            self.show_range_on = None
            return

        c, r = cell
        if self.placing_tower_type is not None:
            if self.path.can_place_at(c, r, self.reserved_cells):
                cfg = tower_config_from_type(self.placing_tower_type)
                cost = int(cfg.get("cost", 0))
                if self.gold >= cost:
                    self.gold -= cost
                    t = Tower(c, r, self.placing_tower_type, cfg, FIELD_LEFT, FIELD_TOP, TILE)
                    self.towers.append(t)
                    self.placing_tower_type = None
                    self.selected_tower = t
                    self.show_range_on = t

            if self.placing_tower_type is not None:
                self.placing_tower_type = None
            return

        for t in reversed(self.towers):
            if dist((mx, my), t.center) <= TILE * 0.6:
                self.selected_tower = t
                self.show_range_on = t
                self.placing_tower_type = None
                return

        self.selected_tower = None
        self.show_range_on = None

    def handle_right_click(self, pos: Vec2) -> None:
        # cancel placement / deselect
        self.placing_tower_type = None
        self.selected_tower = None
        self.show_range_on = None

    def handle_key(self, key: int) -> None:
        if key == pg.K_ESCAPE:
            if self.shop_open:
                self._close_shop()
                return
        if key == pg.K_b and self.selected_tower is not None:
            self._upgrade_selected_tower()

    def _upgrade_selected_tower(self) -> None:
        t = self.selected_tower
        if t is None:
            return
        cost = t.upgrade_cost()
        if self.gold >= cost:
            self.gold -= cost
            t.upgrade()

    def handle_hover(self, pos: Vec2) -> None:
        self._mouse_pos = (float(pos[0]), float(pos[1]))

    # ------------------------------------------------------------------
    # Render
    # ------------------------------------------------------------------
    def draw(self) -> None:
        self.screen.fill(BG)

        # field background (thème)
        self._apply_theme_background(self.screen)
        # grid (thème)
        self._draw_grid_themed(self.screen)

        # scroll edge decoration
        pygame.draw.line(self.screen, (56, 62, 72), (FIELD_RIGHT, FIELD_TOP), (FIELD_RIGHT, FIELD_BOTTOM), 1)
        pygame.draw.line(self.screen, (56, 62, 72), (FIELD_LEFT, FIELD_BOTTOM), (FIELD_RIGHT, FIELD_BOTTOM), 1)

        # path (thème)
        t = self.theme
        fill = tuple(int(c) for c in t.get("path_fill", (52, 58, 66)))
        edge = tuple(int(c) for c in t.get("path_edge", (96, 104, 118)))
        pygame.draw.lines(self.screen, fill, False, self.path.waypoints, 26)
        pygame.draw.lines(self.screen, edge, False, self.path.waypoints, 4)
        for wp in self.path.waypoints:
            pygame.draw.circle(self.screen, (150, 160, 174), (int(wp[0]), int(wp[1])), 4)

        # reserved cells hint (subtle)
        self._draw_reserved_hint(self.screen)

        # towers
        for t in self.towers:
            show = (t is self.show_range_on) or (t is self.selected_tower)
            t.draw(self.screen, show_range=show)

        # enemies
        for e in self.enemies:
            e.draw(self.screen)

        # projectiles
        for p in self.projectiles:
            p.draw(self.screen)

        # particles
        for p in self.particles:
            p.draw(self.screen)

        # placement preview
        if self.placing_tower_type is not None and self.hovered_cell is not None:
            self._draw_placement_preview(self.screen)

        # HUD
        self._draw_hud(self.screen)

        # end screen overlay
        if self._endedScreen is not None:
            self._endedScreen.draw(self.screen)

    def _draw_grid(self, surface: pygame.Surface) -> None:
        for c in range(GRID_COLS + 1):
            x = FIELD_LEFT + c * TILE
            pygame.draw.line(surface, (40, 46, 56), (x, FIELD_TOP), (x, FIELD_BOTTOM), 1)
        for r in range(GRID_ROWS + 1):
            y = FIELD_TOP + r * TILE
            pygame.draw.line(surface, (40, 46, 56), (FIELD_LEFT, y), (FIELD_RIGHT, y), 1)

    def _draw_reserved_hint(self, surface: pygame.Surface) -> None:
        for c, r in self.reserved_cells:
            x = FIELD_LEFT + c * TILE
            y = FIELD_TOP + r * TILE
            pygame.draw.rect(surface, (50, 56, 64), (x, y, TILE, TILE), width=0)
            pygame.draw.rect(surface, (56, 62, 70), (x, y, TILE, TILE), width=1)

    def _draw_placement_preview(self, surface: pygame.Surface) -> None:
        c, r = self.hovered_cell
        cx, cy = self.cell_center((c, r))
        cfg = TOWER_TEMPLATES[self.placing_tower_type]
        cost = int(cfg.get("cost", 0))
        can_afford = self.gold >= cost
        can_place = self.path.can_place_at(c, r, self.reserved_cells)
        color = cfg.get("color", (200, 200, 200))
        if not can_afford:
            color = (90, 70, 70)
        if not can_place:
            color = (90, 70, 70)

        # range preview
        pygame.draw.circle(surface, (120, 160, 220), (int(cx), int(cy)), int(cfg.get("range", 100)), width=1)
        # tower preview
        r2 = int(TILE * 0.42)
        pygame.draw.circle(surface, color, (int(cx), int(cy)), r2)
        pygame.draw.circle(surface, (20, 24, 30), (int(cx), int(cy)), r2 + 3, width=2)
        if not can_afford or not can_place:
            # red border
            pygame.draw.circle(surface, (255, 80, 80), (int(cx), int(cy)), r2 + 5, width=2)

    def _draw_hud(self, surface: pygame.Surface) -> None:
        hud = HUD()
        hp_info = f"{self.lives}/{self.max_lives}"
        wave_info = self.wave_text
        hud.draw_topbar(
            surface,
            self.gold,
            self.lives,
            self.max_lives,
            wave_info,
            self.score,
            self._paused,
            self.mode_name,
            self.level_name,
        )
        hud.draw_tower_shop(
            surface,
            self.tower_order,
            self.gold,
            self._mouse_pos,
            self.hovered_tower_type,
        )
        hud.draw_wave_progress(surface, self.wave_progress)

    # ------------------------------------------------------------------
    # Transitions
    # ------------------------------------------------------------------
    def _retry(self) -> None:
        self.reset()

    def _back_to_menu(self) -> None:
        self._return_to_menu = True

    def _next_level(self) -> None:
        self._advance_level = True

    def _save_game(self) -> None:
        autosave(self.base_path, self)




class _MoneyPickup:
    def __init__(self, pos, amount, pick_id):
        self.pos = list(pos)
        self.amount = amount
        self.pick_id = pick_id
        self.alive_flag = True
        self.life = 8.0
        self.float_offset = random.uniform(0, math.pi * 2)
        self.size = 10

    def update(self, dt):
        self.life -= dt
        self.float_offset += dt * 3

    def draw(self, surface):
        if not self.alive_flag or self.life <= 0:
            return
        x, y = int(self.pos[0]), int(self.pos[1] + math.sin(self.float_offset) * 3)
        # glow
        pygame.draw.circle(surface, (255, 213, 79, 80), (x, y), self.size + 4, width=0)
        # or
        pygame.draw.circle(surface, GOLD_COLOR, (x, y), self.size, width=0)
        pygame.draw.circle(surface, (255, 255, 255), (x - 2, y - 2), self.size // 3, width=0)
        # amount text
        font = pygame.font.SysFont('consolas', 10, bold=True)
        txt = font.render('+' + str(self.amount), True, (20, 24, 30))
        surface.blit(txt, (x - txt.get_width() // 2, y - txt.get_height() // 2 - 12))

    def contains(self, pos):
        if not self.alive_flag:
            return False
        return math.hypot(pos[0] - self.pos[0], pos[1] - self.pos[1]) < self.size + 10

    def alive(self):
        return self.alive_flag and self.life > 0


def dist(a: Vec2, b: Vec2) -> float:
    return math.hypot(b[0] - a[0], b[1] - a[1])
