"""Entities: enemies, towers, projectiles, particles."""
from __future__ import annotations

import math
import random
from typing import List, Optional, Tuple

import pygame

from td.settings import PROJECTILE_SPEED, PROJECTILE_RADIUS, SHOT_COOLDOWN_MIN
from td.helpers import dist, lerp, clamp, hex_points

Vec2 = Tuple[float, float]


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------
class Entity:
    """Anything with a position and radius on the field."""

    def __init__(self, pos: Vec2, radius: float) -> None:
        self.pos = list(pos)
        self.radius = radius

    @property
    def x(self) -> float:
        return self.pos[0]

    @property
    def y(self) -> float:
        return self.pos[1]

    def draw(self, surface: pygame.Surface) -> None:
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Enemy
# ---------------------------------------------------------------------------
class Enemy(Entity):
    """An enemy travels along a path defined by waypoints.

    It supports HP, speed, rewards, slow effects, and optionally a boss
    pulsing aura.
    """

    def __init__(
        self,
        path: "Path",
        enemy_type: str,
        max_hp: float,
        speed: float,
        reward: float,
        color: pygame.Color,
        radius: float,
        waypoints: list[Vec2],
        slow_timer: float = 0.0,
        slow_factor: float = 1.0,
    ) -> None:
        super().__init__((waypoints[0][0], waypoints[0][1]), radius)
        self.path = path
        self.enemy_type = enemy_type
        self.max_hp = max_hp
        self.hp = max_hp
        self.speed = speed
        self.reward = reward
        self.color = color
        self.waypoints = waypoints
        self._done = False
        self.slow_timer = slow_timer
        self.slow_factor = slow_factor
        self.hit_flash = 0.0
        self.reached_end = False

    def update(self, dt: float) -> None:
        if self._done:
            return
        if self.hp <= 0:
            self._done = True
            return

        self.hit_flash = max(0.0, self.hit_flash - dt)
        if self.slow_timer > 0:
            self.slow_timer -= dt

    def reset_progress(self) -> None:
        self._progress = 0.0

    def set_progress(self, d: float) -> None:
        self._progress = d

    def progress(self) -> float:
        return self._progress

    def advance(self, dt: float, path_total: float) -> bool:
        """Move along path by dt*speed, return True if reached the end."""
        if self._done or self.hp <= 0:
            self._done = True
            return True
        effective_speed = self.speed * self.slow_factor if self.slow_timer > 0 else self.speed
        move = effective_speed * dt
        self._progress += move
        if self._progress >= path_total:
            self._progress = path_total
            self._done = True
            self.reached_end = True
            return True
        # update position
        self._set_pos_from_progress()
        return False

    def _set_pos_from_progress(self) -> None:
        d = self._progress
        if d <= 0:
            self.pos[0], self.pos[1] = self.waypoints[0]
            return
        acc = 0.0
        for i in range(len(self.waypoints) - 1):
            seg = dist(self.waypoints[i], self.waypoints[i + 1])
            if acc + seg >= d:
                frac = (d - acc) / seg
                ax, ay = self.waypoints[i]
                bx, by = self.waypoints[i + 1]
                self.pos[0] = ax + (bx - ax) * frac
                self.pos[1] = ay + (by - ay) * frac
                return
            acc += seg
        self.pos[0], self.pos[1] = self.waypoints[-1]

    def take_damage(self, amount: float, slow: float = 0.0, slow_dur: float = 0.0) -> bool:
        """Apply damage; return True if killed."""
        if self._done:
            return False
        self.hp -= amount
        self.hit_flash = 0.12
        if slow > 0:
            self.slow_timer = slow_dur
            self.slow_factor = 1.0 - slow
        if self.hp <= 0:
            self.hp = 0
            self._done = True
            return True
        return False

    def is_dead(self) -> bool:
        return self._done

    def draw(self, surface: pygame.Surface) -> None:
        x, y = int(self.pos[0]), int(self.pos[1])
        r = self.radius

        # body
        base = self.color
        if self.hit_flash > 0:
            base = pygame.Color(255, 255, 255)
        if getattr(self, 'shadow', False):
            pygame.draw.circle(surface, (40, 40, 60), (x, y), int(r * 1.6), width=2)
            pygame.draw.circle(surface, base, (x, y), int(r), width=0)
        else:
            pygame.draw.circle(surface, base, (x, y), int(r), width=0)

        # fighter - ailes
        if getattr(self, 'fly', False):
            for angle in (0.4, -0.4):
                ex = x + math.cos(pygame.time.get_ticks() / 150 + angle) * r * 1.8
                ey = y + math.sin(pygame.time.get_ticks() / 150 + angle) * r * 0.6
                pygame.draw.circle(surface, (255, 200, 100), (int(ex), int(ey)), int(r * 0.5))


        # boss aura
        if self.enemy_type == "boss":
            pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() / 200)
            pygame.draw.circle(
                surface,
                pygame.Color(255, 70, 110),
                (x, y),
                int(r + 4 + pulse * 5),
                width=2,
            )

        # hp bar
        bw = r * 2.6
        bh = 4
        bx = x - bw / 2
        by = y - r - 8
        ratio = max(0.0, self.hp / self.max_hp)
        pygame.draw.rect(surface, (60, 60, 60), (bx, by, bw, bh))
        col = (86, 213, 120) if ratio > 0.5 else (255, 163, 69)
        if ratio < 0.25:
            col = (255, 97, 97)
        pygame.draw.rect(surface, col, (bx, by, bw * ratio, bh))

        # dead marker
        if self._done and self.hp <= 0:
            pygame.draw.circle(surface, (255, 255, 255), (x, y), int(r * 0.4))

        # bloat aura
        if self.enemy_type == 'bloat':
            pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() / 300)
            pygame.draw.circle(surface, pygame.Color(120, 220, 255), (x, y), int(r + 3 + pulse * 4), width=2)

        # skeleton glow
        if self.enemy_type == 'skull':
            pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() / 180)
            pygame.draw.circle(surface, pygame.Color(240, 240, 200), (x, y), int(r + 2 + pulse * 3), width=2)


# ---------------------------------------------------------------------------
# Tower
# ---------------------------------------------------------------------------
class Tower(Entity):
    """A placed tower that targets enemies and fires projectiles.

    Fires at the nearest enemy in range. Supports splash, slow, etc.
    """

    def __init__(
        self,
        col: int,
        row: int,
        tower_type: str,
        config: dict,
        grid_left: float,
        grid_top: float,
        tile: float,
    ) -> None:
        cx = grid_left + col * tile + tile / 2
        cy = grid_top + row * tile + tile / 2
        super().__init__((cx, cy), tile * 0.42)
        self.col = col
        self.row = row
        self.tower_type = tower_type
        self.config = dict(config)
        self.range = float(self.config["range"])
        self.damage = float(self.config["damage"])
        self.fire_rate = max(SHOT_COOLDOWN_MIN, float(self.config["fire_rate"]))
        self.splash = float(self.config.get("splash", 0))
        self.slow = float(self.config.get("slow", 0))
        self.slow_dur = float(self.config.get("slow_duration", 0))
        self.level = 1
        self.projectile_speed = float(self.config.get("projectile_speed", PROJECTILE_SPEED))
        self._boost_remaining_s = 0.0
        self.color = pygame.Color(self.config["color"])
        self.name = str(self.config.get("name", tower_type))
        self.cost = int(self.config.get("cost", 0))
        self.cooldown = 0.0
        self.angle = 0.0
        self.target: Optional[Enemy] = None

        # visual glow
        self.glow = 0.0

    @property
    def center(self) -> Vec2:
        return (self.pos[0], self.pos[1])

    def find_target(self, enemies: List[Enemy]) -> Optional[Enemy]:
        best: Optional[Enemy] = None
        best_d = float("inf")
        cx, cy = self.center
        for e in enemies:
            if e.is_dead() or e.reached_end:
                continue
            d = dist((e.x, e.y), (cx, cy))
            if d <= self.range and d < best_d:
                best_d = d
                best = e
        self.target = best
        return best

    _enemies_near: List[Enemy] = []  # set by game scene for splash lookups

    def update(self, dt: float, enemies: List[Enemy]) -> Optional["Projectile"]:
        self.cooldown = max(0.0, self.cooldown - dt)
        self.glow = max(0.0, self.glow - dt)

        target = self.find_target(enemies)
        if target is not None:
            tx, ty = target.pos
            self.angle = math.atan2(ty - self.y, tx - self.x)
            if self.cooldown <= 0:
                self.cooldown = self.fire_rate
                self.glow = 0.18
                return self._fire(target)
        return None

    # ---- boosts & upgrades -------------------------------------------------
    def _apply_boost(self, key: str, remaining: float, dt: float) -> None:
        if remaining <= 0:
            return

    def upgrade_cost(self) -> int:
        return 60 + (self.level - 1) * 40

    def upgrade(self) -> None:
        self.level += 1

    def effective_damage(self) -> float:
        base = self.damage * (1.0 + 0.25 * (self.level - 1))
        if getattr(self, '_boost_remaining_s', 0) > 0:
            base *= getattr(self, '_boost_active_mult', 1.0)
        return base

    def effective_range(self) -> float:
        base = self.range * (1.0 + 0.20 * (self.level - 1))
        if getattr(self, '_boost_remaining_s', 0) > 0:
            base *= getattr(self, '_boost_active_mult', 1.0)
        return base

    def effective_fire_rate(self) -> float:
        return self.fire_rate

    def _fire(self, target: Enemy) -> "Projectile":
        return Projectile(
            pos=(self.pos[0], self.pos[1]),
            target=target,
            speed=self.projectile_speed,
            damage=self.damage,
            splash=self.splash,
            slow=self.slow,
            slow_dur=self.slow_dur,
            color=self.color,
            owner=self,
        )

    def draw(self, surface: pygame.Surface, show_range: bool = False) -> None:
        x, y = int(self.pos[0]), int(self.pos[1])
        r = int(self.radius)

        # range circle
        if show_range:
            pygame.draw.circle(
                surface,
                pygame.Color(120, 160, 220),
                (x, y),
                int(self.range),
                width=2,
            )
            pygame.draw.circle(
                surface,
                pygame.Color(80, 120, 180),
                (x, y),
                int(self.range),
                width=1,
            )

        # body
        shape = str(self.config.get("shape", "circle"))
        if shape == "square":
            sz = r * 1.7
            pygame.draw.rect(surface, self.color, (x - sz / 2, y - sz / 2, sz, sz), border_radius=4)
        elif shape == "diamond":
            pts = [(x, y - r * 1.4), (x + r * 1.4, y), (x, y + r * 1.4), (x - r * 1.4, y)]
            pygame.draw.polygon(surface, self.color, pts)
        elif shape == "hex":
            pts = hex_points((x, y), r * 1.3, 6)
            pygame.draw.polygon(surface, self.color, pts, width=0)
        else:
            pygame.draw.circle(surface, self.color, (x, y), r)

        # base ring
        pygame.draw.circle(surface, (20, 24, 30), (x, y), r + 3, width=2)

        # barrel
        barrel_len = r * 1.5
        bx = x + math.cos(self.angle) * barrel_len
        by = y + math.sin(self.angle) * barrel_len
        pygame.draw.line(surface, (220, 224, 230), (x, y), (bx, by), width=max(2, r // 3))

        # glow
        if self.glow > 0:
            glow = pygame.Color(255, 255, 200)
            glow.a = int(90 * self.glow * 5)
            pygame.draw.circle(surface, glow, (x, y), r + 6, width=3)

        # selection highlight
        pygame.draw.circle(surface, (255, 255, 255), (x, y), r + 5, width=2)

        # level badge
        lvl = getattr(self, 'level', 1)
        if lvl > 1:
            pygame.draw.circle(surface, (255, 255, 255), (x + r - 2, y - r + 2), 4, width=0)
            f2 = pygame.font.SysFont('consolas', 9, bold=True)
            lb = f2.render(str(lvl), True, (20, 24, 30))
            surface.blit(lb, (x + r - lb.get_width() - 2, y - r - 2))


# ---------------------------------------------------------------------------
# Projectile
# ---------------------------------------------------------------------------
class Projectile(Entity):
    """A projectile tracks a target enemy and explodes on arrival."""

    def __init__(
        self,
        pos: Vec2,
        target: Enemy,
        speed: float,
        damage: float,
        splash: float,
        slow: float,
        slow_dur: float,
        color: pygame.Color,
        owner: Tower,
    ) -> None:
        super().__init__(pos, PROJECTILE_RADIUS)
        self.target = target
        self.speed = speed
        self.damage = damage
        self.splash = splash
        self.slow = slow
        self.slow_dur = slow_dur
        self.color = color
        self.owner = owner
        self.alive = True
        self.trail: list[Vec2] = []
        self.max_trail = 6

    def update(self, dt: float) -> bool:
        """Move toward target. Returns True if should be removed."""
        if not self.alive:
            return True
        if self.target.is_dead() or self.target.reached_end:
            self.alive = False
            return True

        tx, ty = self.target.pos
        dx = tx - self.x
        dy = ty - self.y
        d = math.hypot(dx, dy)
        if d < self.radius + self.target.radius:
            self._explode((self.x, self.y))
            return True
        step = self.speed * dt
        if step >= d:
            self.pos[0] = tx
            self.pos[1] = ty
            self._explode((self.x, self.y))
            return True
        self.pos[0] += dx / d * step
        self.pos[1] += dy / d * step
        # trail
        self.trail.append((self.x, self.y))
        if len(self.trail) > self.max_trail:
            self.trail.pop(0)
        return False

    def _explode(self, pos: Vec2) -> None:
        self.alive = False
        # direct hit
        if not self.target.is_dead():
            self.target.take_damage(self.damage, self.slow, self.slow_dur)
        # splash
        if self.splash > 0:
            cx, cy = pos
            r = self.splash
            for e in self.owner._enemies_near:
                if e is self.target:
                    continue
                if dist((e.x, e.y), (cx, cy)) <= r and not e.is_dead():
                    e.take_damage(self.damage * 0.5, self.slow, self.slow_dur)

    def draw(self, surface: pygame.Surface) -> None:
        if not self.alive:
            return
        x, y = int(self.x), int(self.y)
        # trail
        for i, p in enumerate(self.trail):
            a = int(120 * (i + 1) / len(self.trail))
            c = self.color
            c.a = a
            pygame.draw.circle(surface, c, (int(p[0]), int(p[1])), 2)
        # core
        pygame.draw.circle(surface, self.color, (x, y), int(self.radius))
        pygame.draw.circle(surface, (255, 255, 255), (x, y), int(self.radius * 0.5))


# ---------------------------------------------------------------------------
# Particle
# ---------------------------------------------------------------------------
class Particle:
    """A tiny visual effect with life and velocity."""

    def __init__(self, pos: Vec2, vel: Vec2, color: pygame.Color, life: float, size: float) -> None:
        self.pos = list(pos)
        self.vel = list(vel)
        self.color = color
        self.life = life
        self.max_life = life
        self.size = size

    def update(self, dt: float) -> None:
        self.pos[0] += self.vel[0] * dt
        self.pos[1] += self.vel[1] * dt
        self.vel[0] *= 0.92
        self.vel[1] *= 0.92
        self.life -= dt

    def draw(self, surface: pygame.Surface) -> None:
        if self.life <= 0:
            return
        a = int(255 * clamp(self.life / self.max_life, 0.0, 1.0))
        c = self.color
        c.a = a
        pygame.draw.circle(surface, c, (int(self.pos[0]), int(self.pos[1])), int(self.size))

    def alive(self) -> bool:
        return self.life > 0


def spawn_hit_particles(pos: Vec2, color: pygame.Color, n: int = 8) -> List[Particle]:
    out = []
    for _ in range(n):
        a = random.random() * math.tau
        s = random.uniform(40, 120)
        out.append(
            Particle(
                pos,
                (math.cos(a) * s, math.sin(a) * s),
                color,
                random.uniform(0.2, 0.5),
                random.uniform(2, 4),
            )
        )
    return out


def spawn_death_particles(pos: Vec2, color: pygame.Color, n: int = 16) -> List[Particle]:
    out = []
    for _ in range(n):
        a = random.random() * math.tau
        s = random.uniform(60, 180)
        out.append(
            Particle(
                pos,
                (math.cos(a) * s, math.sin(a) * s),
                color,
                random.uniform(0.4, 0.9),
                random.uniform(2, 5),
            )
        )
    return out
