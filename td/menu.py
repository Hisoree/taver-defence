"""Menus: main menu, HUD, pause, level complete, game over."""
from __future__ import annotations

import math
import pygame
import pygame.locals as pg
from td.settings import WIDTH, HEIGHT, BG, PANEL, PANEL_LIGHT, GRID_LINE, TEXT_DARK, TEXT_MUTED, ACCENT, ACCENT_GREEN, ACCENT_RED, ACCENT_ORANGE, GOLD_COLOR, TOWER_TEMPLATES
from td.levels import THEME_NAMES


Vec2 = tuple[float, float]


def make_surface(size):
    return pygame.Surface(size, pygame.SRCALPHA)


class Button:
    def __init__(self, rect, label, color=ACCENT, text_color=(20, 24, 30), hover_color=None, font_size=22):
        self.rect = rect
        self.label = label
        self.color = color
        self.hover_color = hover_color or tuple(min(255, c + 28) for c in color)
        self.text_color = text_color
        self.font = pygame.font.SysFont("consolas", font_size, bold=True)
        self.hover = False
        self.action = None

    def set_action(self, fn):
        self.action = fn

    def update(self, mouse_pos):
        self.hover = self.rect.collidepoint(int(mouse_pos[0]), int(mouse_pos[1]))

    def draw(self, surface):
        col = self.hover_color if self.hover else self.color
        pygame.draw.rect(surface, col, self.rect, border_radius=10)
        pygame.draw.rect(surface, (255, 255, 255), self.rect, width=2, border_radius=10)
        txt = self.font.render(self.label, True, self.text_color)
        tx = self.rect.x + (self.rect.width - txt.get_width()) / 2
        ty = self.rect.y + (self.rect.height - txt.get_height()) / 2
        surface.blit(txt, (tx, ty))

    def contains(self, pos):
        return self.rect.collidepoint(int(pos[0]), int(pos[1]))


class MainMenu:
    def __init__(self, levels):
        self.levels = levels
        self.buttons = []
        self._build_buttons()

    def _build_buttons(self):
        cx = WIDTH // 2
        y = 220
        play = Button(pg.Rect(cx - 120, y, 240, 52), "JOUER", ACCENT_GREEN, font_size=26)
        play.set_action(lambda: ("play", None))
        self.buttons.append(play)
        y += 64
        inf = Button(pg.Rect(cx - 120, y, 240, 52), "MODE INFINI", ACCENT_ORANGE, font_size=22)
        inf.set_action(lambda: ("infinite", None))
        self.buttons.append(inf)
        y += 64
        levels_btn = Button(pg.Rect(cx - 120, y, 240, 52), "NIVEAUX (6)", ACCENT, font_size=22)
        levels_btn.set_action(lambda: ("levels", None))
        self.buttons.append(levels_btn)
        y += 64
        quit_btn = Button(pg.Rect(cx - 80, y, 160, 46), "QUITTER", ACCENT_RED, font_size=22)
        quit_btn.set_action(lambda: ("quit", None))
        self.buttons.append(quit_btn)

    def handle_click(self, pos):
        for b in self.buttons:
            if b.contains(pos):
                return b.action()
        return None

    def update(self, mouse_pos):
        for b in self.buttons:
            b.update(mouse_pos)

    def draw(self, surface):
        surface.fill(BG)
        big = pygame.font.SysFont("consolas", 56, bold=True)
        sub = pygame.font.SysFont("consolas", 20)
        title = big.render("TOWER DEFENSE", True, ACCENT)
        surface.blit(title, (WIDTH / 2 - title.get_width() / 2, 70))
        sub_txt = sub.render("build defend survive", True, TEXT_MUTED)
        surface.blit(sub_txt, (WIDTH / 2 - sub_txt.get_width() / 2, 135))
        rect = pg.Rect(WIDTH / 2 - 220, 190, 440, 330)
        pygame.draw.rect(surface, PANEL, rect, border_radius=16)
        pygame.draw.rect(surface, GRID_LINE, rect, width=2, border_radius=16)
        for b in self.buttons:
            b.draw(surface)
        footer = sub.render("Place des tours - Defend la voie", True, TEXT_MUTED)
        surface.blit(footer, (WIDTH / 2 - footer.get_width() / 2, 550))


class LevelSelectMenu:
    def __init__(self, levels):
        self.levels = levels
        self.buttons = []
        self.scroll = 0.0
        self._build_buttons()

    def _build_buttons(self):
        cx = WIDTH // 2
        y = 200
        title_btn = Button(pg.Rect(cx - 120, y, 240, 46), "NIVEAUX", ACCENT, font_size=22)
        title_btn.set_action(lambda: ("back", None))
        self.buttons.append(title_btn)
        y += 64
        for i, lv in enumerate(self.levels):
            theme = THEME_NAMES[lv.get("theme", 0)]
            label = f"Level {i + 1}: {lv['name']} [{theme}]"
            btn = Button(pg.Rect(cx - 160, y, 320, 44), label, ACCENT_GREEN, font_size=19)
            btn.set_action(lambda idx=i: ("level", idx))
            self.buttons.append(btn)
            y += 50
        y += 20
        inf_btn = Button(pg.Rect(cx - 120, y, 240, 46), "RETOUR AU MENU", ACCENT, font_size=18)
        inf_btn.set_action(lambda: ("back", None))
        self.buttons.append(inf_btn)

    def handle_click(self, pos):
        for b in self.buttons:
            if b.contains(pos):
                return b.action()
        return None

    def update(self, mouse_pos):
        for b in self.buttons:
            b.update(mouse_pos)

    def draw(self, surface):
        surface.fill(BG)
        big = pygame.font.SysFont("consolas", 40, bold=True)
        title = big.render("SELECTION DES NIVEAUX", True, ACCENT)
        surface.blit(title, (WIDTH / 2 - title.get_width() / 2, 50))
        rect = pg.Rect(WIDTH / 2 - 200, 180, 400, 440)
        pygame.draw.rect(surface, PANEL, rect, border_radius=16)
        pygame.draw.rect(surface, GRID_LINE, rect, width=2, border_radius=16)
        for b in self.buttons:
            b.draw(surface)


class HUD:
    def __init__(self):
        self.gold_label = ""
        self.lives_label = ""
        self.wave_label = ""

    def draw_topbar(self, surface, gold, lives, max_lives, wave_text, score, paused, mode_name, level_name):
        font = pygame.font.SysFont("consolas", 20, bold=True)
        small = pygame.font.SysFont("consolas", 16)
        # gauche: or + vie
        g_txt = font.render(f"{gold} or", True, GOLD_COLOR)
        surface.blit(g_txt, (12, 10))
        l_txt = font.render(f"{lives}/{max_lives}", True, ACCENT_RED if lives < max_lives * 0.4 else TEXT_DARK)
        surface.blit(l_txt, (12, 34))
        # droite: vague + score
        w_txt = small.render(wave_text, True, TEXT_DARK)
        surface.blit(w_txt, (WIDTH - 16 - w_txt.get_width(), 14))
        sc_txt = small.render(f"Score: {score}", True, TEXT_MUTED)
        surface.blit(sc_txt, (WIDTH - 16 - sc_txt.get_width(), 36))
        # mode + niveau
        mode_small = pygame.font.SysFont("consolas", 14)
        m_txt = mode_small.render(f"{mode_name} · {level_name}", True, TEXT_MUTED)
        surface.blit(m_txt, (WIDTH - 16 - m_txt.get_width(), 8))
        # pause badge
        if paused:
            pause_font = pygame.font.SysFont("consolas", 22, bold=True)
            p_txt = pause_font.render("PAUSE (P)", True, TEXT_MUTED)
            surface.blit(p_txt, (WIDTH // 2 - p_txt.get_width() // 2, 12))

    def draw_tower_shop(self, surface, tower_order, gold, mouse_pos, hovered_tower_type):
        left = WIDTH - 210
        top = 70
        title_font = pygame.font.SysFont("consolas", 18, bold=True)
        ttl = title_font.render("BOURSE DE TOURS", True, TEXT_MUTED)
        surface.blit(ttl, (left + 4, top - 2))
        for idx, ttype in enumerate(tower_order):
            cfg = TOWER_TEMPLATES[ttype]
            cost = int(cfg.get("cost", 0))
            y = top + 34 + idx * 94
            can_afford = gold >= cost
            color = cfg.get("color", (200, 200, 200))
            if not can_afford:
                color = (90, 70, 70)
            # icône
            r = 26
            cx_btn = left + 24
            cy_btn = y + 42
            pygame.draw.circle(surface, color, (cx_btn, cy_btn), r)
            pygame.draw.circle(surface, (20, 24, 30), (cx_btn, cy_btn), r + 3, width=2)
            # label
            lab = f"{cfg.get('name', ttype)} — {cost} or"
            lab_font = pygame.font.SysFont("consolas", 16, bold=True)
            l_txt = lab_font.render(lab, True, TEXT_DARK if can_afford else (150, 100, 100))
            surface.blit(l_txt, (left + 60, y + 10))
            # hover highlight
            btn = pg.Rect(left, y, 180, 84)
            if btn.collidepoint(int(mouse_pos[0]), int(mouse_pos[1])):
                pygame.draw.rect(surface, (60, 66, 76), btn, width=2)
            # selection
            if hovered_tower_type == ttype:
                pygame.draw.rect(surface, ACCENT, btn, width=2)

    def draw_wave_progress(self, surface, progress):
        if progress <= 0:
            return
        bar_w = 180
        bar_h = 8
        x = WIDTH // 2 - bar_w // 2
        y = 60
        pygame.draw.rect(surface, (40, 46, 56), (x, y, bar_w, bar_h), border_radius=4)
        pygame.draw.rect(surface, ACCENT, (x, y, int(bar_w * progress), bar_h), border_radius=4)
        f = pygame.font.SysFont("consolas", 12)
        p_txt = f.render(f"{int(progress * 100)}%", True, TEXT_MUTED)
        surface.blit(p_txt, (x + bar_w + 6, y + 2))


def level_complete_screen(retry_fn, menu_fn, next_fn):
    class EndScreen:
        def __init__(self, retry_fn, menu_fn, next_fn):
            self.retry_fn = retry_fn
            self.menu_fn = menu_fn
            self.next_fn = next_fn
            self.buttons = []
            cx = WIDTH // 2
            y = 340
            nxt = Button(pg.Rect(cx - 110, y, 220, 50), "NIVEAU SUIVANT", ACCENT_GREEN, font_size=20)
            if next_fn is None:
                nxt.set_action(lambda: ("menu", None))
                nxt.label = "RETOUR AU MENU"
            else:
                nxt.set_action(lambda: ("next", None))
            self.buttons.append(nxt)
            y += 64
            ret = Button(pg.Rect(cx - 110, y, 220, 50), "REJOUER", ACCENT_ORANGE, font_size=20)
            ret.set_action(lambda: ("retry", None))
            self.buttons.append(ret)
            y += 64
            mnu = Button(pg.Rect(cx - 110, y, 220, 50), "MENU PRINCIPAL", ACCENT_RED, font_size=18)
            mnu.set_action(lambda: ("menu", None))
            self.buttons.append(mnu)

        def handle_click(self, pos):
            for b in self.buttons:
                if b.contains(pos):
                    if b.label == "NIVEAU SUIVANT" and self.next_fn is not None:
                        return ("next", None)
                    if b.label == "RETOUR AU MENU":
                        return ("menu", None)
                    if b.label == "REJOUER":
                        return ("retry", None)
                    if b.label == "MENU PRINCIPAL":
                        return ("menu", None)
            return None

        def draw(self, surface):
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            surface.blit(overlay, (0, 0))
            big = pygame.font.SysFont("consolas", 48, bold=True)
            txt = big.render("NIVEAU TERMINÉ", True, ACCENT_GREEN)
            surface.blit(txt, (WIDTH / 2 - txt.get_width() / 2, 120))
            for b in self.buttons:
                b.draw(surface)

    return EndScreen(retry_fn, menu_fn, next_fn)


def game_over_screen(retry_fn, menu_fn):
    class EndScreen:
        def __init__(self, retry_fn, menu_fn):
            self.retry_fn = retry_fn
            self.menu_fn = menu_fn
            cx = WIDTH // 2
            y = 340
            self.buttons = []
            ret = Button(pg.Rect(cx - 110, y, 220, 50), "REJOUER", ACCENT_ORANGE, font_size=20)
            ret.set_action(lambda: ("retry", None))
            self.buttons.append(ret)
            y += 64
            mnu = Button(pg.Rect(cx - 110, y, 220, 50), "MENU PRINCIPAL", ACCENT_RED, font_size=18)
            mnu.set_action(lambda: ("menu", None))
            self.buttons.append(mnu)

        def handle_click(self, pos):
            for b in self.buttons:
                if b.contains(pos):
                    if b.label == "REJOUER":
                        return ("retry", None)
                    if b.label == "MENU PRINCIPAL":
                        return ("menu", None)
            return None

        def draw(self, surface):
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            surface.blit(overlay, (0, 0))
            big = pygame.font.SysFont("consolas", 48, bold=True)
            txt = big.render("GAME OVER", True, ACCENT_RED)
            surface.blit(txt, (WIDTH / 2 - txt.get_width() / 2, 120))
            for b in self.buttons:
                b.draw(surface)

    return EndScreen(retry_fn, menu_fn)
