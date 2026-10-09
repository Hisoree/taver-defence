import pathlib

here = pathlib.Path('.')

# ============================================================
# td/levels.py — corrigé
# ============================================================
(here / 'td' / 'levels.py').write_text('''\"\"\"Level definitions.\"\"\"
from __future__ import annotations

from typing import Any, Dict, List

from td.settings import FIELD_LEFT, FIELD_TOP

Vec2 = tuple[float, float]

THEME_NAMES = ['Terre · Brume', 'Glace · Neige', 'Feu · Lave', 'Poison · Toxique', 'Nuage · Ciel', 'Nuit · Cosmos']

def _w(*cells):
    out = []
    for c, r in cells:
        out.append((FIELD_LEFT + c * 40 + 20, FIELD_TOP + r * 40 + 20))
    return out

LEVEL1 = {'name': 'Premier Pas', 'theme': 0, 'waypoints': _w((1,3),(12,3),(12,9),(9,9)), 'starting_gold': 180, 'starting_lives': 20, 'tower_shop': ['rapid','cannon'], 'waves': [{'when':1.0,'count':5,'type':'basic','interval':0.8},{'when':3.0,'count':6,'type':'basic','interval':0.6},{'when':5.5,'count':4,'type':'fast','interval':0.5},{'when':8.0,'count':7,'type':'basic','interval':0.5},{'when':11.0,'count':5,'type':'tank','interval':0.9},{'when':14.0,'count':8,'type':'basic','interval':0.4},{'when':17.0,'count':6,'type':'fighter','interval':0.35},{'when':20.0,'count':5,'type':'tank','interval':0.8}]}

LEVEL2 = {'name': 'Zigzag', 'theme': 1, 'waypoints': _w((1,2),(1,8),(6,8),(6,3),(11,3),(11,9),(14,9)), 'starting_gold': 200, 'starting_lives': 18, 'tower_shop': ['rapid','cannon','sniper','frost'], 'waves': [{'when':1.0,'count':6,'type':'basic','interval':0.7},{'when':3.0,'count':7,'type':'fast','interval':0.5},{'when':5.5,'count':5,'type':'basic','interval':0.6},{'when':8.0,'count':7,'type':'fighter','interval':0.4},{'when':11.0,'count':4,'type':'tank','interval':1.0},{'when':13.5,'count':9,'type':'fast','interval':0.4},{'when':16.5,'count':6,'type':'basic','interval':0.4},{'when':19.5,'count':5,'type':'tank','interval':0.8},{'when':22.0,'count':11,'type':'fighter','interval':0.35},{'when':25.0,'count':5,'type':'tank','interval':0.7},{'when':28.0,'count':8,'type':'fast','interval':0.3}]}

LEVEL3 = {'name': 'Marais Toxique', 'theme': 3, 'waypoints': _w((1,2),(1,6),(5,6),(5,2),(9,2),(9,6),(13,6),(13,2),(16,2),(16,9),(12,9)), 'starting_gold': 240, 'starting_lives': 20, 'tower_shop': ['rapid','cannon','sniper','frost'], 'waves': [{'when':1.0,'count':7,'type':'basic','interval':0.6},{'when':3.5,'count':8,'type':'fast','interval':0.45},{'when':6.5,'count':6,'type':'basic','interval':0.5},{'when':9.5,'count':5,'type':'skull','interval':0.8},{'when':12.5,'count':9,'type':'basic','interval':0.4},{'when':15.5,'count':7,'type':'fast','interval':0.35},{'when':19.0,'count':6,'type':'tank','interval':0.8},{'when':22.5,'count':11,'type':'basic','interval':0.35},{'when':26.0,'count':5,'type':'tank','interval':0.7},{'when':29.5,'count':13,'type':'fast','interval':0.3},{'when':33.0,'count':7,'type':'tank','interval':0.6},{'when':37.0,'count':10,'type':'skull','interval':0.28}]}

LEVEL4 = {'name': 'Zone de Lave', 'theme': 2, 'waypoints': _w((1,4),(4,4),(4,1),(12,1),(12,4),(12,8),(8,8),(8,10),(5,10),(5,6),(2,6)), 'starting_gold': 220, 'starting_lives': 18, 'tower_shop': ['rapid','cannon','sniper','frost'], 'waves': [{'when':1.0,'count':6,'type':'basic','interval':0.6},{'when':3.0,'count':7,'type':'fast','interval':0.45},{'when':5.5,'count':6,'type':'basic','interval':0.5},{'when':8.5,'count':4,'type':'bloat','interval':1.0},{'when':11.5,'count':10,'type':'basic','interval':0.4},{'when':14.5,'count':8,'type':'fast','interval':0.35},{'when':18.0,'count':6,'type':'tank','interval':0.8},{'when':21.5,'count':12,'type':'basic','interval':0.35},{'when':25.0,'count':5,'type':'bloat','interval':0.7},{'when':28.5,'count':14,'type':'fast','interval':0.3},{'when':32.0,'count':7,'type':'tank','interval':0.6},{'when':36.0,'count':10,'type':'basic','interval':0.28},{'when':40.0,'count':6,'type':'fast','interval':0.25}]}

LEVEL5 = {'name': 'Fortresse des Cieux', 'theme': 4, 'waypoints': _w((1,2),(1,8),(5,8),(5,4),(9,4),(9,9),(13,9),(13,3),(17,3),(17,10),(14,10),(14,6),(10,6),(10,11),(6,11)), 'starting_gold': 280, 'starting_lives': 20, 'tower_shop': ['rapid','cannon','sniper','frost'], 'waves': [{'when':1.0,'count':15,'type':'basic','interval':0.5},{'when':4.5,'count':18,'type':'fast','interval':0.35},{'when':8.5,'count':12,'type':'basic','interval':0.4},{'when':12.5,'count':15,'type':'fighter','interval':0.3},{'when':17.0,'count':10,'type':'tank','interval':0.7},{'when':21.5,'count':20,'type':'basic','interval':0.3},{'when':26.5,'count':8,'type':'bloat','interval':0.6},{'when':31.5,'count':25,'type':'fast','interval':0.25},{'when':37.0,'count':15,'type':'tank','interval':0.5},{'when':43.0,'count':30,'type':'basic','interval':0.22},{'when':49.5,'count':10,'type':'bloat','interval':0.45}]}

LEVEL6 = {'name': 'Apocalypse Nocturne', 'theme': 5, 'waypoints': _w((1,3),(1,9),(7,9),(7,4),(12,4),(12,10),(16,10),(16,2),(20,2),(20,8),(17,8),(17,5),(13,5),(13,11),(9,11),(9,6),(5,6),(5,10),(1,10)), 'starting_gold': 350, 'starting_lives': 22, 'tower_shop': ['rapid','cannon','sniper','frost'], 'waves': [{'when':1.0,'count':18,'type':'basic','interval':0.45},{'when':3.5,'count':20,'type':'fast','interval':0.3},{'when':6.5,'count':15,'type':'basic','interval':0.35},{'when':9.5,'count':12,'type':'tank','interval':0.6},{'when':12.5,'count':22,'type':'fighter','interval':0.25},{'when':15.5,'count':18,'type':'basic','interval':0.3},{'when':18.5,'count':10,'type':'skull','interval':0.5},{'when':21.5,'count':28,'type':'fast','interval':0.2},{'when':25.0,'count':20,'type':'basic','interval':0.25},{'when':28.5,'count':15,'type':'tank','interval':0.45},{'when':32.0,'count':35,'type':'shadow','interval':0.18},{'when':36.5,'count':12,'type':'tank','interval':0.4},{'when':41.0,'count':40,'type':'fast','interval':0.15},{'when':46.0,'count':25,'type':'basic','interval':0.2}]}

LEVELS = [LEVEL1, LEVEL2, LEVEL3, LEVEL4, LEVEL5, LEVEL6]

def build_timeline(waves):
    from td.waves import WaveTimeline
    return WaveTimeline.from_events(waves)

def tower_config_from_type(t):
    from td.settings import TOWER_TEMPLATES
    return dict(TOWER_TEMPLATES[t])

def enemy_template_from_type(t):
    from td.settings import ENEMY_TEMPLATES
    return dict(ENEMY_TEMPLATES[t])
''', encoding='utf-8')

# ============================================================
# td/shop.py — NEW (écran shop séparé)
# ============================================================
(here / 'td' / 'shop.py').write_text('''\"\"\"Shop écran séparé : onglets Tours + Boosts.\"\"\"
from __future__ import annotations

import pygame
import pygame.locals as pg

from td.settings import WIDTH, HEIGHT, BG, PANEL, PANEL_LIGHT, GRID_LINE, TEXT_DARK, TEXT_MUTED, ACCENT, ACCENT_GREEN, ACCENT_RED, ACCENT_ORANGE, GOLD_COLOR, TOWER_TEMPLATES, BOOSTS
from td.menu import Button

Vec2 = tuple[float, float]


class ShopScreen:
    def __init__(self, gold: int, on_buy_tower, on_buy_boost):
        self.gold = gold
        self.on_buy_tower = on_buy_tower
        self.on_buy_boost = on_buy_boost
        self.tab = 'towers'  # 'towers' or 'boosts'
        self.buttons = []
        self._build_tabs()
        self._build_content()

    def _build_tabs(self):
        cx = WIDTH // 2
        y = 170
        self.tab_buttons = []
        tb1 = Button(pg.Rect(cx - 130, y, 120, 44), 'TOURS', ACCENT, font_size=20)
        tb1.set_action(lambda: self._set_tab('towers'))
        self.tab_buttons.append(tb1)
        tb2 = Button(pg.Rect(cx + 10, y, 120, 44), 'BOOSTS', ACCENT_ORANGE, font_size=20)
        tb2.set_action(lambda: self._set_tab('boosts'))
        self.tab_buttons.append(tb2)

    def _set_tab(self, tab):
        self.tab = tab
        self._build_content()

    def _build_content(self):
        self.content_buttons = []
        cx = WIDTH // 2
        if self.tab == 'towers':
            y = 230
            for ttype, cfg in TOWER_TEMPLATES.items():
                cost = int(cfg.get('cost', 0))
                label = f\"{cfg.get('name', ttype)} — {cost} or\"
                btn = Button(pg.Rect(cx - 160, y, 320,
