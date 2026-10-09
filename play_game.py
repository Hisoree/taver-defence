"""
Automated in-game smoke test.

Loads Level 1, simulates a simple placement over time using a fake mouse
position, runs the loop until a terminal state is reached, and asserts that
the game actually ends (win or lose) rather than running forever.

Runs headless via SDL_VIDEODRIVER=dummy.
"""
import os
import sys
import pathlib
import time
import traceback

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
from td.controller import App
from td.levels import LEVELS
from td.settings import TOWER_TEMPLATES

FPS = 60
TIMEOUT_SEC = 60


def main() -> int:
    pygame.init()
    try:
        screen = pygame.display.set_mode((1100, 700), pygame.NOFRAME)
    except Exception as exc:
        print("could not create dummy display:", exc)
        return 2

    app = App(HERE)
    app.state = "playing"
    app.scene = None
    from td.game import GameScene

    app.scene = GameScene(screen, HERE, level_index=0, infinite=False)
    app.scene.reset()

    start = time.time()
    frame_count = 0
    hover_switch_at = -1.0
    hover_pos = (0.0, 0.0)

    # Simple autonomous placement policy: every so often move the fake
    # cursor to a different grid cell. If we're not currently placing a
    # tower type, try to pick the cheapest affordable one. If we are
    # placing, attempt to put it on the current hovered cell.
    # Spread towers along row 2/4 (above/below the row-3 path) so they
    # cover the whole path. Also try row 5 for the turn at col 12.
    cells = [(3, 2), (6, 2), (9, 2), (3, 4), (6, 4), (9, 4),
             (11, 4), (11, 5), (10, 5), (8, 5)]

    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return 0

        now_dt = app.clock.tick(FPS) / 1000.0
        frame_count += 1
        now = time.time() - start

        if now - hover_switch_at > 0.35:
            idx = int(now * 0.5) % len(cells)
            c, r = cells[idx]
            mx = 40 + c * 40 + 20
            my = 60 + r * 40 + 20
            hover_pos = (float(mx), float(my))
            hover_switch_at = now

        app.scene.handle_hover(hover_pos)
        app.scene.update(now_dt)

        scene = app.scene
        if scene.placing_tower_type is None:
            for t in scene.tower_order:
                cost = int(TOWER_TEMPLATES[t].get("cost", 0))
                if scene.gold >= cost:
                    scene.placing_tower_type = t
                    break
        if scene.placing_tower_type is not None:
            cell = scene.cell_from_pos(hover_pos)
            if cell is not None:
                c, r = cell
                if scene.path.can_place_at(c, r, scene.reserved_cells):
                    # don't stack towers on the same cell
                    if not any(t.col == c and t.row == r for t in scene.towers):
                        cost = int(
                            TOWER_TEMPLATES[scene.placing_tower_type].get("cost", 0)
                        )
                        if scene.gold >= cost:
                            scene.handle_click(hover_pos, 1)
                            scene.placing_tower_type = None

        app.scene.draw()

        if app.scene._game_over or app.scene._level_complete:
            elapsed = time.time() - start
            print(
                f"play smoke ok: {frame_count} frames, {elapsed:.1f}s, "
                f"game_over={app.scene._game_over}, complete={app.scene._level_complete}"
            )
            return 0

        if time.time() - start > TIMEOUT_SEC:
            print("play smoke FAILED: timeout before reaching terminal state")
            s = app.scene
            print(
                f"alive enemies={len(s.enemies)} towers={len(s.towers)} "
                f"gold={s.gold} lives={s.lives}"
            )
            return 3


if __name__ == "__main__":
    try:
        rc = main()
    except Exception:
        traceback.print_exc()
        rc = 4
    sys.exit(rc)
