"""Path model: waypoints + reserved cells mask for tower placement."""
from __future__ import annotations

import math
from typing import List, Tuple

import pygame

from td.settings import FIELD_LEFT, FIELD_TOP, TILE, PLACE_MARGIN
from td.helpers import dist, hex_points

Vec2 = Tuple[float, float]


class Path:
    """A path is an ordered list of waypoints in pixel coords.

    Enemies travel from waypoints[0] -> ... -> waypoints[-1].
    """

    def __init__(self, waypoints: list[Vec2]) -> None:
        if len(waypoints) < 2:
            raise ValueError("A path needs at least 2 waypoints.")
        self.waypoints = list(waypoints)

        # Precompute segment lengths and cumulative lengths for fast
        # position lookup by distance along the path.
        self._seg_lengths: list[float] = []
        self._cumulative: list[float] = [0.0]
        acc = 0.0
        for i in range(len(self.waypoints) - 1):
            d = dist(self.waypoints[i], self.waypoints[i + 1])
            self._seg_lengths.append(d)
            acc += d
            self._cumulative.append(acc)
        self.total_length = acc

    # ------------------------------------------------------------------
    # Position along the path
    # ------------------------------------------------------------------
    def position_at_distance(self, d: float) -> Vec2:
        """Point on the path at signed distance d from the start (clamped)."""
        if not self.total_length:
            return self.waypoints[0]
        d = max(0.0, min(d, self.total_length))
        # find segment
        for i in range(len(self._seg_lengths)):
            if d <= self._cumulative[i + 1]:
                seg_d = d - self._cumulative[i]
                frac = seg_d / self._seg_lengths[i]
                ax, ay = self.waypoints[i]
                bx, by = self.waypoints[i + 1]
                return (ax + (bx - ax) * frac, ay + (by - ay) * frac)
        return self.waypoints[-1]

    def place_enemy_at_distance(self, d: float, margin: float) -> Vec2:
        """Return a start position just before the path start (so enemies
        appear off-screen / outside the field)."""
        if d <= 0:
            # Place a little before the first waypoint along the first segment
            # direction, or just at the start if degenerate.
            if len(self.waypoints) >= 2:
                ax, ay = self.waypoints[0]
                bx, by = self.waypoints[1]
                dx, dy = bx - ax, by - ay
                l = math.hypot(dx, dy) or 1.0
                return (ax - dx / l * margin, ay - dy / l * margin)
            return self.waypoints[0]
        return self.position_at_distance(d)

    # ------------------------------------------------------------------
    # Grid / placement helpers
    # ------------------------------------------------------------------
    def cell_center(self, col: int, row: int) -> Vec2:
        return (FIELD_LEFT + col * TILE + TILE / 2, FIELD_TOP + row * TILE + TILE / 2)

    def grid_cells_for_path(self, cols: int, rows: int) -> set[tuple[int, int]]:
        """All grid cells whose centers fall within PLACE_MARGIN cells of the path.

        These cells are reserved and cannot receive towers.
        """
        reserved: set[tuple[int, int]] = set()
        margin_cells = PLACE_MARGIN
        # Use a fine sampling along the path to mark nearby cells.
        steps = max(2, int(self.total_length / (TILE * 0.5)))
        for k in range(steps + 1):
            d = self.total_length * k / steps
            px, py = self.position_at_distance(d)
            c = int((px - FIELD_LEFT) / TILE)
            r = int((py - FIELD_TOP) / TILE)
            for dc in range(-margin_cells, margin_cells + 1):
                for dr in range(-margin_cells, margin_cells + 1):
                    nc, nr = c + dc, r + dr
                    if 0 <= nc < cols and 0 <= nr < rows:
                        reserved.add((nc, nr))
        return reserved

    def can_place_at(self, col: int, row: int, reserved: set[tuple[int, int]]) -> bool:
        return (col, row) not in reserved

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------
    def draw(self, surface: pygame.Surface) -> None:
        if not self.waypoints:
            return
        # filled soft path
        pygame.draw.lines(surface, (52, 58, 66), False, self.waypoints, 26)
        # edge
        pygame.draw.lines(surface, (96, 104, 118), False, self.waypoints, 4)
        # waypoints
        for wp in self.waypoints:
            pygame.draw.circle(surface, (150, 160, 174), (int(wp[0]), int(wp[1])), 4)

    def draw_direction_dots(self, surface: pygame.Surface) -> None:
        """Small dots along the path to visualize direction for debugging."""
        for i in range(0, len(self.waypoints) - 1, 2):
            a = self.waypoints[i]
            b = self.waypoints[i + 1]
            mx = (a[0] + b[0]) / 2
            my = (a[1] + b[1]) / 2
            pygame.draw.circle(surface, (200, 210, 224), (int(mx), int(my)), 3)
