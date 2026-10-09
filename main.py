"""
Tower Defense - main entry point.
Runs the game directly, or can be bundled with PyInstaller into a single .exe.
"""
import sys
import pathlib

def main() -> None:
    # When bundled with PyInstaller, resources live next to the .exe.
    if getattr(sys, "frozen", False):
        base = pathlib.Path(sys.executable).parent
    else:
        base = pathlib.Path(__file__).resolve().parent

    from td.controller import App

    app = App(base)
    app.run()


if __name__ == "__main__":
    main()
