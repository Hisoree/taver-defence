"""Shop écran séparé (UTF-8 propre), avec portefeuille et deux onglets Tours / Boosts."""
from __future__ import annotations

import pygame
import pygame.locals as pg

from td.settings import WIDTH, HEIGHT, PANEL, GRID_LINE, ACCENT, ACCENT_GREEN, ACCENT_RED, ACCENT_ORANGE, TOWER_TEMPLATES, BOOSTS
from td.menu import Button


class ShopScreen:
    """Écran de magasin modal: onglets Tours / Boosts, achat validé par callbacks."""

    def __init__(self, gold: int, on_buy_tower, on_buy_boost, on_close):
        self.gold = gold
        self.on_buy_tower = on_buy_tower
        self.on_buy_boost = on_buy_boost
        self.on_close = on_close
        self.tab = "towers"
        self.tab_buttons: list[Button] = []
        self.content_buttons: list[Button] = []
        self._gold_label = "0 or"
        self._build_tabs()
        self._build_content()
        self._refresh_gold_label()

    # ------------------------------------------------------------------
    def _refresh_gold_label(self) -> None:
        self._gold_label = f"{self.gold} or"

    def set_gold(self, gold: int) -> None:
        self.gold = int(gold)
        self._refresh_gold_label()

    def gold_label(self) -> str:
        return self._gold_label

    # ------------------------------------------------------------------
    def _build_tabs(self) -> None:
        cx = WIDTH // 2
        y = 170
        tb1 = Button(
            pg.Rect(cx - 130, y, 120, 44),
            "TOURS",
            ACCENT,
            font_size=20,
        )
        tb1.set_action(lambda: self._set_tab("towers"))
        self.tab_buttons.append(tb1)

        tb2 = Button(
            pg.Rect(cx + 10, y, 120, 44),
            "BOOSTS",
            ACCENT_ORANGE,
            font_size=20,
        )
        tb2.set_action(lambda: self._set_tab("boosts"))
        self.tab_buttons.append(tb2)

    def _set_tab(self, tab: str) -> None:
        self.tab = tab
        self._build_content()

    def _build_content(self) -> None:
        self.content_buttons = []
        cx = WIDTH // 2
        if self.tab == "towers":
            y = 230
            for ttype, cfg in TOWER_TEMPLATES.items():
                cost = int(cfg.get("cost", 0))
                name = str(cfg.get("name", ttype))
                label = f"{name} — {cost} or"
                btn = Button(
                    pg.Rect(cx - 160, y, 320, 50),
                    label,
                    ACCENT,
                    font_size=19,
                )
                btn.set_action(lambda t=ttype, c=cost: self._buy_tower(t, c))
                self.content_buttons.append(btn)
                y += 58
        else:
            y = 230
            for btype, bcfg in BOOSTS.items():
                if bcfg.get("locked"):
                    label = f"{bcfg.get('name', btype)} — Bientôt disponible"
                    btn = Button(
                        pg.Rect(cx - 160, y, 320, 50),
                        label,
                        (90, 90, 90),
                        font_size=19,
                    )
                    btn.set_action(lambda: None)
                    self.content_buttons.append(btn)
                    y += 58
                    continue
                cost = int(bcfg.get("cost", 0))
                desc = str(bcfg.get("desc", ""))
                name = str(bcfg.get("name", btype))
                label = f"{name} — {cost} or — {desc}"
                btn = Button(
                    pg.Rect(cx - 160, y, 320, 50),
                    label,
                    ACCENT_GREEN,
                    font_size=19,
                )
                btn.set_action(lambda b=bcfg, c=cost: self._buy_boost(b, c))
                self.content_buttons.append(btn)
                y += 58

    # ------------------------------------------------------------------
    def _buy_tower(self, ttype: str, cost: int) -> None:
        if self.gold >= cost:
            self.gold -= cost
            self._refresh_gold_label()
            self.on_buy_tower(ttype)

    def _buy_boost(self, bcfg: dict, cost: int) -> None:
        if self.gold >= cost:
            self.gold -= cost
            self._refresh_gold_label()
            self.on_buy_boost(bcfg)

    # ------------------------------------------------------------------
    def handle_click(self, pos) -> None:
        for b in self.tab_buttons:
            if b.contains(pos):
                b.action()
                return None
        for b in self.content_buttons:
            if b.contains(pos):
                b.action()
                return None
        if self.close_button().contains(pos):
            self.close_button().action()
        return None

    def close_button(self) -> Button:
        if not hasattr(self, "_close_button") or self._close_button is None:
            self._close_button = Button(
                pg.Rect(WIDTH // 2 - 80, HEIGHT - 90, 160, 46),
                "FERMER",
                ACCENT_RED,
                font_size=20,
            )
            self._close_button.set_action(lambda: self.on_close())
        return self._close_button

    def handle_hover(self, pos) -> None:
        for b in self.tab_buttons + self.content_buttons + [self.close_button()]:
            b.update(pos)

    def draw(self, surface) -> None:
        overlay = pg.Surface((WIDTH, HEIGHT), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        surface.blit(overlay, (0, 0))

        cx = WIDTH // 2
        panel = pg.Rect(cx - 180, 140, 360, HEIGHT - 280)
        pygame.draw.rect(surface, PANEL, panel, border_radius=16)
        pygame.draw.rect(surface, GRID_LINE, panel, width=2, border_radius=16)

        font = pygame.font.SysFont("consolas", 26, bold=True)
        title = font.render("MAGASIN", True, ACCENT)
        surface.blit(title, (cx - title.get_width() // 2, 150))

        for b in self.tab_buttons:
            b.draw(surface)
        for b in self.content_buttons:
            b.draw(surface)
        self.close_button().draw(surface)
