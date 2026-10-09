"""
Build script for Tower Defense.

Produces a single standalone .exe via PyInstaller. Run with the project venv:
    .venv/Scripts/python.exe build_exe.py

The output lands in dist/ as TowerDefense.exe.
"""
import os
import sys
import time
import shutil
import pathlib
import subprocess
import json

HERE = pathlib.Path(__file__).resolve().parent


def _rmtree(path: pathlib.Path) -> None:
    if not path.exists():
        return
    for attempt in range(3):
        try:
            shutil.rmtree(path)
            return
        except OSError:
            if attempt >= 2:
                raise
            time.sleep(0.4)


def main() -> int:
    python = pathlib.Path(sys.executable)
    if not python.name.lower().endswith("python.exe"):
        print("Please run this script with the project Python (the venv python).")
        return 2

    dist = HERE / "dist"
    build = HERE / "build"

    for d in (dist, build):
        if d.exists():
            print(f"Removing existing {d}...")
            _rmtree(d)

    # Windows uses ; as the add-data separator.
    add_data = f"{HERE / 'td'};td"

    cmd = [
        str(python),
        "-m",
        "PyInstaller",
        "--clean",
        "--onefile",
        "--windowed",
        "--name",
        "TowerDefense",
        "--add-data",
        add_data,
        str(HERE / "main.py"),
    ]

    print("Running:", " ".join(cmd))
    proc = subprocess.run(cmd, cwd=str(HERE), check=False)
    if proc.returncode != 0:
        print("PyInstaller failed.")
        return proc.returncode

    exe = dist / "TowerDefense.exe"
    if exe.exists():
        size = exe.stat().st_size
        print(f"\nBuilt: {exe}  ({size // 1024} KB)")
        print("You can run it directly; it does not need Python installed.")
    else:
        print("Unexpected: no .exe produced in dist/.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
