content = open('td/game.py', 'r', encoding='utf-8').read()

# Ajouter import pour les nouveaux modules
content = content.replace(
    'from td.menu import MainMenu, HUD, level_complete_screen, game_over_screen',
    'from td.menu import MainMenu, HUD, level_complete_screen, game_over_screen\nfrom td.shop import ShopScreen\nfrom td.save import autosave, load_save_into_scene\nfrom td.settings import LEVEL_THEMES'
)

# Ajouter champs dans __init__
content = content.replace(
    '        self._infinite_gold_bonus = 0\n\n    # ------------------------------------------------------------------\n    # Waypoints',
    '        self._infinite_gold_bonus = 0\n        self._theme = None\n        self._active_boosts = {}\n        self._permanent_boosts = []\n        self._shop_screen: ShopScreen | None = None\n        self._money_pickups = []\n        self._next_pickup_id = 0\n        self.FIELD_LEFT = FIELD_LEFT\n        self.FIELD_TOP = FIELD_TOP\n        self.TILE = TILE\n\n    # ------------------------------------------------------------------\n    # Waypoints'
)

# Modifier _level_waypoints pour utiliser les waypoints tels quels
content = content.replace(
    '    def _level_waypoints(self, data: Dict[str, Any]) -> List[Vec2]:\n        # waypoints are already stored as pixel coords by _w() in levels.py\n        return list(data["waypoints"])',
    '    def _level_waypoints(self, data: Dict[str, Any]) -> List[Vec2]:\n        return list(data["waypoints"])'
)

# Ajouter application du thème dans __init__
content = content.replace(
    '        self._waypoints = self.path.waypoints\n        self._path_total = self.path.total_length\n\n        # input state',
    '        self._waypoints = self.path.waypoints\n        self._path_total = self.path.total_length\n\n        # appliquer le theme\n        if self.level_index is not None:\n            self._theme = LEVEL_THEMES.get(self.level_index, LEVEL_THEMES[0])\n        else:\n            self._theme = LEVEL_THEMES[4]  # nuage pour infini\n        # input state'
)

# Ajouter load save dans reset
content = content.replace(
    '        self.wave_text = "Preparing"\n        self._start_next_wave()',
    '        self.wave_text = "Preparing"\n        # charger la sauvegarde si dispo\n        if not self.infinite and self.level_index is not None:\n            load_save_into_scene(self.base_path, self)\n        self._start_next_wave()'
)

# Ajouter open_shop et update_boost_methods avant _update_particles
content = content.replace(
    '    def _update_particles(self, dt: float) -> None:',
    '    def open_shop(self):\n        self._shop_screen = ShopScreen(self.gold, self._on_buy_tower, self._on_buy_boost)\n\n    def close_shop(self):\n        if self._shop_screen is not None:\n            self.gold = self._shop_screen.gold\n            self._shop_screen = None\n            autosave(self.base_path, self)\n\n    def _on_buy_tower(self, ttype):\n        # ouverture du shop a deja deduit l'or, on place juste la tour selectionnee\n        self.placing_tower_type = ttype\n\n    def _on_buy_boost(self, bcfg):\n        stat = bcfg.get("stat", "")\n        if stat == "damage_mult":\n            self._active_boosts["damage_mult"] = bcfg.get("duration", 0)\n        elif stat == "range_mult":\n            self._active_boosts["range_mult"] = bcfg.get("duration", 0)\n        elif stat == "fire_rate_mult":\n            self._active_boosts["fire_rate_mult"] = bcfg.get("duration", 0)\n        elif stat == "fire_rate_mult_life":\n            if "fire_rate_mult_life" not in self._permanent_boosts:\n                self._permanent_boosts.append("fire_rate_mult_life")\n        self._update_boost_display()\n\n    def _update_boost_display(self):\n        if self._shop_screen is not None:\n            self._shop_screen.gold = self.gold\n            self._shop_screen._build_content()\n\n    def update_boosts(self, dt: float):\n        # mettre a jour les boosts temporaires\n        to_remove = []\n        for k, remaining in self._active_boosts.items():\n            if remaining > 0:\n                self._active_boosts[k] = remaining - dt\n                if self._active_boosts[k] <= 0:\n                    to_remove.append(k)\n        for k in to_remove:\n            del self._active_boosts[k]\n\n    def get_damage_mult(self) -> float:\n        mult = 1.0\n        if "damage_mult" in self._active_boosts or "damage_mult" in self._permanent_boosts:\n            mult *= 1.25\n        return mult\n\n    def get_range_mult(self) -> float:\n        mult = 1.0\n        if "range_mult" in self._active_boosts or "range_mult" in self._permanent_boosts:\n            mult *= 1.3\n        return mult\n\n    def get_fire_rate_mult(self) -> float:\n        mult = 1.0\n        if "fire_rate_mult" in self._active_boosts:\n            mult *= 0.7\n        if "fire_rate_mult_life" in self._permanent_boosts:\n            mult *= 0.85\n        return mult\n\n    def _update_particles(self, dt: float) -> None:'
)

# Ajouter money pickups dans update (apres projectiles)
content = content.replace(
    '        # projectiles\n        for p in self.projectiles:\n            if p.update(dt):\n                continue\n        self.projectiles = [p for p in self.projectiles if p.alive]\n\n        # enemies that reached the end',
    '        # projectiles\n        for p in self.projectiles:\n            if p.update(dt):\n                continue\n        self.projectiles = [p for p in self.projectiles if p.alive]\n\n        # money pickups\n        for mp in self._money_pickups:\n            mp.update(dt)\n        self._money_pickups = [mp for mp in self._money_pickups if mp.alive()]\n\n        # enemies that reached the end'
)

# Ajouter spawn money pickups dans _do_spawn (une chance de 15% de spawn un pickup)
content = content.replace(
    '        e.set_progress(0.0)\n        self.enemies.append(e)\n        self.spawned_this_wave += 1',
    '        e.set_progress(0.0)\n        self.enemies.append(e)\n        self.spawned_this_wave += 1\n        # chance de spawn un money pickup\n        if random.random() < 0.15:\n            self._spawn_money_pickup()'
)

# Ajouter methode _spawn_money_pickup avant _update_hover
content = content.replace(
    '    def _update_hover(self, pos: Vec2) -> None:',
    '    def _spawn_money_pickup(self):\n        # spawn un pickup d\'or aléatoire dans la field\n        c = random.randint(1, GRID_COLS - 2)\n        r = random.randint(1, GRID_ROWS - 2)\n        cx = FIELD_LEFT + c * TILE + TILE / 2\n        cy = FIELD_TOP + r * TILE + TILE / 2\n        amount = random.randint(5, 15)\n        self._money_pickups.append(_MoneyPickup((cx, cy), amount, self._next_pickup_id))\n        self._next_pickup_id += 1\n\n    def _update_hover(self, pos: Vec2) -> None:'
)

# Modifier handle_click pour gerer le shop
content = content.replace(
    '    def handle_click(self, pos: Vec2, button: int = 1) -> None:\n        if self._endedScreen is not None:',
    '    def handle_click(self, pos: Vec2, button: int = 1) -> None:\n        # Si on clique sur un money pickup\n        for mp in self._money_pickups:\n            if mp.contains(pos):\n                self.gold += mp.amount\n                mp.alive_flag = False\n                self._update_boost_display()\n                autosave(self.base_path, self)\n                return\n        if self._shop_screen is not None:\n            action = self._shop_screen.handle_click(pos)\n            if action:\n                kind, val = action\n                if kind == "close":\n                    self.close_shop()\n                return\n        if self._endedScreen is not None:'
)

# Modifier le menu shop pour utiliser les boosts
content = content.replace(
    '        # shop click (right panel)\n        left = WIDTH - 210\n        top = 70\n        for t in self.tower_order:',
    '        # Bouton Magasin (en haut a droite)\n        shop_btn_rect = pg.Rect(WIDTH - 100, 12, 70, 28)\n        if shop_btn_rect.collidepoint(int(mx), int(my)):\n            if self._shop_screen is None:\n        
