"""
Headless smoke test: instantiates App and runs the loop for a few seconds
without a display (using a pygame NULL driver), then reports success.

Because Pygame needs a video driver, we set SDL_VIDEODRIVER=dummy so the
window creation doesn't fail in a headless environment.
"""
import os
import sys
import pathlib
import time
import traceback

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))


def main() -> int:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

    import pygame
    from td.controller import App
    from td.levels import LEVELS

    pygame.init()
    try:
        screen = pygame.display.set_mode((1100, 700), pygame.NOFRAME)
    except Exception as exc:
        print("could not create dummy display:", exc)
        return 2

    app = App(HERE)
    # force straight into game for the smoke test
    app.state = "playing"
    app.scene = app.scene if app.scene is not None else None
    from td.game import GameScene
    app.scene = GameScene(screen, HERE, level_index=0, infinite=False)
    app.scene.reset()

    start = time.time()
    deadline = start + 4.0
    frame_count = 0
    while time.time() < deadline:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return 0
        dt = app.clock.tick(60) / 1000.0
        app.scene.handle_hover((300, 300))
        app.scene.update(dt)
        app.scene.draw()
        frame_count += 1
        if app.scene._game_over or app.scene._level_complete:
            print(f"smoke test reached end state after {frame_count} frames")
            break

    print(f"smoke test ok: {frame_count} frames in {time.time()-start:.2f}s, game_over={app.scene._game_over}, complete={app.scene._level_complete}")
    return 0


if __name__ == "__main__":
    try:
        rc = main()
    except Exception:
        traceback.print_exc()
        rc = 3
    sys.exit(rc)
