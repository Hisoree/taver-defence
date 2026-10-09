"""Small helpers: lerp, distance, way-point interpolation, color tinting."""
from __future__ import annotations

import math
import pygame

Vec2 = tuple[float, float]


def dist(a: Vec2, b: Vec2) -> float:
    return math.hypot(b[0] - a[0], b[1] - a[1])


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def clamp(x: float, lo: float, hi: float) -> float:
    if x < lo:
        return lo
    if x > hi:
        return hi
    return x


def point_to_segment_distance(p: Vec2, a: Vec2, b: Vec2) -> float:
    """Shortest distance from point p to segment a-b."""
    ax, ay = a
    bx, by = b
    px, py = p
    dx = bx - ax
    dy = by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    t = ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)
    t = clamp(t, 0.0, 1.0)
    near_x = lerp(ax, bx, t)
    near_y = lerp(ay, by, t)
    return math.hypot(px - near_x, py - near_y)


def nearest_point_on_path(pos: Vec2, waypoints: list[Vec2]) -> Vec2:
    """Closest point on the polyline defined by waypoints."""
    best = waypoints[0]
    best_d = math.inf
    seg_a = waypoints[0]
    for seg_b in waypoints[1:]:
        d = point_to_segment_distance(pos, seg_a, seg_b)
        if d < best_d:
            best_d = d
            # closest point on this segment
            ax, ay = seg_a
            bx, by = seg_b
            dx = bx - ax
            dy = by - ay
            if dx == 0 and dy == 0:
                best = seg_a
            else:
                px, py = pos
                t = clamp(((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy), 0.0, 1.0)
                best = (lerp(ax, bx, t), lerp(ay, by, t))
        seg_a = seg_b
    return best


def hex_points(center: Vec2, radius: float, n: int = 6) -> list[Vec2]:
    cx, cy = center
    out = []
    for i in range(n):
        a = math.tau * i / n - math.pi / 2
        out.append((cx + radius * math.cos(a), cy + radius * math.sin(a)))
    return out


def tint_color(base: pygame.Color, factor: float) -> pygame.Color:
    return pygame.Color(
        int(base.r * factor),
        int(base.g * factor),
        int(base.b * factor),
        base.a,
    )


def hex_to_color(h: int) -> pygame.Color:
    return pygame.Color(h)
