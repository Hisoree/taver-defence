"""Shared constants for the Tower Defense game."""
from __future__ import annotations

import pygame

# ---------------------------------------------------------------------------
# Screen / timing
# ---------------------------------------------------------------------------
WIDTH = 1100
HEIGHT = 700
FPS = 60

# ---------------------------------------------------------------------------
# Grid
# ---------------------------------------------------------------------------
TILE = 40
COLS = WIDTH // TILE
ROWS = HEIGHT // TILE

FIELD_LEFT = 40
FIELD_TOP = 60
FIELD_RIGHT = WIDTH - 220
FIELD_BOTTOM = HEIGHT - 60

GRID_COLS = (FIELD_RIGHT - FIELD_LEFT) // TILE
GRID_ROWS = (FIELD_BOTTOM - FIELD_TOP) // TILE
PLACE_MARGIN = 1

# ---------------------------------------------------------------------------
# Level themes (6 themes, one per level)
# ---------------------------------------------------------------------------
LEVEL_THEMES = {
    0: {  # Terre / Brume — fond sombre, chemin gris marron
        'bg': (20, 24, 30),
        'field': (26, 30, 36),
        'grid': (40, 46, 56),
        'path_fill': (52, 58, 66),
        'path_edge': (96, 104, 118),
        'accent': (86, 156, 255),
    },
    1: {  # Glace / Neige
        'bg': (18, 22, 34),
        'field': (22, 34, 46),
        'grid': (36, 52, 72),
        'path_fill': (60, 80, 108),
        'path_edge': (140, 180, 220),
        'accent': (120, 200, 255),
    },
    2: {  # Feu / Lave
        'bg': (28, 14, 10),
        'field': (40, 18, 12),
        'grid': (64, 30, 20),
        'path_fill': (90, 40, 20),
        'path_edge': (255, 120, 40),
        'accent': (255, 140, 60),
    },
    3: {  # Poison / Vert toxique
        'bg': (14, 24, 16),
        'field': (22, 40, 24),
        'grid': (36, 60, 36),
        'path_fill': (50, 80, 50),
        'path_edge': (120, 220, 120),
        'accent': (120, 255, 120),
    },
    4: {  # Nuage / Ciel
        'bg': (20, 28, 40),
        'field': (30, 38, 52),
        'grid': (46, 54, 72),
        'path_fill': (70, 86, 110),
        'path_edge': (180, 200, 240),
        'accent': (140, 180, 255),
    },
    5: {  # Nuit / Cosmos
        'bg': (10, 8, 20),
        'field': (18, 16, 30),
        'grid': (30, 26, 50),
        'path_fill': (48, 40, 80),
        'path_edge': (160, 140, 255),
        'accent': (160, 120, 255),
    },
}

# ---------------------------------------------------------------------------
# Colors (override by theme at runtime, defaults here)
# ---------------------------------------------------------------------------
BG = (20, 24, 30)
PANEL = (28, 33, 40)
PANEL_LIGHT = (40, 46, 56)
GRID_LINE = (38, 44, 54)
PATH_FILL = (52, 58, 66)
PATH_EDGE = (90, 98, 110)
GOLD_COLOR = (255, 213, 79)
LIVES_COLOR = (255, 97, 97)
TEXT_DARK = (230, 234, 240)
TEXT_MUTED = (150, 160, 174)
ACCENT = (86, 156, 255)
ACCENT_GREEN = (86, 213, 120)
ACCENT_RED = (255, 97, 97)
ACCENT_ORANGE = (255, 163, 69)
ENEMY_BASIC = (255, 120, 120)
ENEMY_FAST = (255, 213, 90)
ENEMY_TANK = (190, 130, 255)
ENEMY_BOSS = (255, 70, 110)
ENEMY_FLYER = (255, 180, 60)
ENEMY_BLOAT = (120, 200, 255)
ENEMY_BONE = (220, 220, 220)
ENEMY_SHADOW = (80, 80, 120)
TOW1_COLOR = (86, 190, 255)
TOW2_COLOR = (255, 170, 70)
TOW3_COLOR = (120, 255, 150)
TOW4_COLOR = (200, 130, 255)

# ---------------------------------------------------------------------------
# Projectile & combat defaults
# ---------------------------------------------------------------------------
PROJECTILE_SPEED = 420
PROJECTILE_RADIUS = 4
SHOT_COOLDOWN_MIN = 0.18

# ---------------------------------------------------------------------------
# Economy
# ---------------------------------------------------------------------------
STARTING_GOLD = 200
STARTING_LIVES = 20

# ---------------------------------------------------------------------------
# Towers
# ---------------------------------------------------------------------------
TOWER_TEMPLATES = {
    'rapid': {
        'name': 'Rapid',
        'cost': 50,
        'damage': 12,
        'range': 150,
        'fire_rate': 0.16,
        'color': TOW1_COLOR,
        'projectile_speed': 520,
        'splash': 0,
        'slow': 0,
        'shape': 'circle',
    },
    'cannon': {
        'name': 'Cannon',
        'cost': 110,
        'damage': 38,
        'range': 170,
        'fire_rate': 0.85,
        'color': TOW2_COLOR,
        'projectile_speed': 360,
        'splash': 55,
        'slow': 0,
        'shape': 'square',
    },
    'sniper': {
        'name': 'Sniper',
        'cost': 180,
        'damage': 75,
        'range': 300,
        'fire_rate': 1.1,
        'color': TOW3_COLOR,
        'projectile_speed': 700,
        'splash': 0,
        'slow': 0,
        'shape': 'diamond',
    },
    'frost': {
        'name': 'Frost',
        'cost': 130,
        'damage': 8,
        'range': 160,
        'fire_rate': 0.5,
        'color': TOW4_COLOR,
        'projectile_speed': 460,
        'splash': 0,
        'slow': 0.45,
        'slow_duration': 1.6,
        'shape': 'hex',
    },
}

# ---------------------------------------------------------------------------
# Boosts (achetables dans le shop)
# ---------------------------------------------------------------------------
BOOSTS = {
    'damage_boost': {
        'name': 'Attaque +25%',
        'cost': 80,
        'desc': 'Dégâts x1.25 pendant 15s',
        'duration': 15.0,
        'stat': 'damage_mult',
        'value': 1.25,
    },
    'range_boost': {
        'name': 'Portée +30%',
        'cost': 70,
        'desc': 'Portée x1.3 pendant 15s',
        'duration': 15.0,
        'stat': 'range_mult',
        'value': 1.3,
    },
    'fire_boost': {
        'name': 'Croissance +30%',
        'cost': 90,
        'desc': 'Cadence x1.3 pendant 15s',
        'duration': 15.0,
        'stat': 'fire_rate_mult',
        'value': 0.7,  # divise la cadence par 1.3
    },
    'rapid_fire': {
        'name': 'Feu rapide permanent',
        'cost': 150,
        'desc': 'Cadence x0.85 à vie',
        'duration': 0.0,
        'stat': 'fire_rate_mult_life',
        'value': 0.85,
    },
    'max_hp_boost': {
        'name': '+20% PV ennemis',
        'cost': 0,
        'desc': 'Bientôt disponible',
        'duration': 0.0,
        'stat': None,
        'value': 0.0,
        'locked': True,
    },
}

# ---------------------------------------------------------------------------
# Enemies
# ---------------------------------------------------------------------------
ENEMY_TEMPLATES = {
    'basic': {
        'name': 'Scout',
        'hp': 40,
        'speed': 55,
        'reward': 5,
        'color': ENEMY_BASIC,
        'radius': 9,
    },
    'fast': {
        'name': 'Coureur',
        'hp': 22,
        'speed': 95,
        'reward': 6,
        'color': ENEMY_FAST,
        'radius': 7,
    },
    'tank': {
        'name': 'Cuirassé',
        'hp': 140,
        'speed': 38,
        'reward': 12,
        'color': ENEMY_TANK,
        'radius': 13,
    },
    'boss': {
        'name': 'Boss',
        'hp': 420,
        'speed': 30,
        'reward': 35,
        'color': ENEMY_BOSS,
        'radius': 18,
    },
    'fighter': {
        'name': 'Aviateur',
        'hp': 60,
        'speed': 130,
        'reward': 10,
        'color': ENEMY_FLYER,
        'radius': 8,
        'fly': True,
    },
    'bloat': {
        'name': 'Géant vert',
        'hp': 280,
        'speed': 25,
        'reward': 22,
        'color': ENEMY_BLOAT,
        'radius': 19,
    },
    'skull': {
        'name': 'Squelette',
        'hp': 90,
        'speed': 72,
        'reward': 14,
        'color': ENEMY_BONE,
        'radius': 10,
        'slow_resist': 0.5,
    },
    'shadow': {
        'name': 'Ombre',
        'hp': 55,
        'speed': 60,
        'reward': 9,
        'color': ENEMY_SHADOW,
        'radius': 9,
        'shadow': True,
    },
}
