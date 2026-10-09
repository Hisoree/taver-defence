import sys
import json
import pathlib
import subprocess
import time
import datetime
import shutil
import os

HERE = pathlib.Path(__file__).resolve().parent
EXE = HERE / "dist" / "TowerDefense.exe"
PYTHON = HERE / ".venv" / "Scripts" / "python.exe"
REBUILD = HERE / "build_exe.py"

PROTOCOL = HERE / "delivery_protocol.json"

errors = []
start = datetime.datetime.now()


def check(cond, msg):
    if not cond:
        errors.append(msg)


def _ensure_no_running_exe() -> None:
    try:
        import psutil

        for p in psutil.process_iter(["name"]):
            if p.info["name"] and p.info["name"].lower().endswith("towerdefense.exe"):
                try:
                    p.terminate()
                except Exception:
                    pass
        time.sleep(1.8)
    except Exception:
        pass


def _force_remove_dir(path: pathlib.Path) -> None:
    if not path.exists():
        return
    if path.is_dir():
        for root, dirs, files in os.walk(str(path), topdown=False):
            for name in files:
                fp = os.path.join(root, name)
                for _ in range(3):
                    try:
                        os.unlink(fp)
                        break
                    except OSError:
                        time.sleep(0.5)
            for name in dirs:
                dp = os.path.join(root, name)
                for _ in range(3):
                    try:
                        os.rmdir(dp)
                        break
                    except OSError:
                        time.sleep(0.5)
        for _ in range(5):
            try:
                os.rmdir(str(path))
                return
            except OSError:
                time.sleep(0.6)
        raise RuntimeError(f"could not remove {path}")


# 1. EXE exists
check(EXE.exists(), f"EXE missing: {EXE}")
exe_size = EXE.stat().st_size if EXE.exists() else 0
check(exe_size > 5_000_000, f"EXE too small ({exe_size} bytes)")

# 2. Make sure no TowerDefense.exe is still running before we rebuild.
_ensure_no_running_exe()

# 3. Source files present
src = [
    HERE / "main.py",
    HERE / "td" / "__init__.py",
    HERE / "td" / "settings.py",
    HERE / "td" / "helpers.py",
    HERE / "td" / "path.py",
    HERE / "td" / "entities.py",
    HERE / "td" / "waves.py",
    HERE / "td" / "levels.py",
    HERE / "td" / "menu.py",
    HERE / "td" / "game.py",
    HERE / "td" / "controller.py",
    HERE / "build_exe.py",
]
for p in src:
    check(p.exists(), f"missing source: {p.relative_to(HERE)}")

# 4. Rebuild via build script (uses the same command the user would run)
rebuild = subprocess.run(
    [str(PYTHON), str(REBUILD)],
    cwd=str(HERE),
    capture_output=True,
    text=True,
    timeout=240,
)
check(
    rebuild.returncode == 0,
    f"rebuild failed (exit {rebuild.returncode}):\n{rebuild.stdout[-1500:]}\n{rebuild.stderr[-1500:]}",
)
check((HERE / "dist" / "TowerDefense.exe").exists(), "rebuild did not produce EXE")

# 5. EXE launch smoke: start, wait, confirm alive, then close
proc = subprocess.Popen([str(EXE)], cwd=str(HERE), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
alive = False
for _ in range(50):
    time.sleep(0.1)
    if proc.poll() is not None:
        out, err = proc.communicate(timeout=1)
        break
    alive = True
    break
check(alive, "EXE exited immediately on launch")
if proc.poll() is None:
    proc.terminate()
    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=3)
exitcode = proc.returncode if proc.returncode is not None else "killed"

# 6. Log
log = {
    "checked_at": start.isoformat(),
    "exe_path": str(EXE),
    "exe_size_bytes": exe_size,
    "exe_launched": alive,
    "exe_exit": exitcode,
    "rebuild_exit": rebuild.returncode,
    "errors": errors,
}
PROTOCOL.write_text(json.dumps(log, indent=2) + "\n", encoding="utf-8")

if errors:
    print("VERIFICATION FAILED:")
    for e in errors:
        print(" -", e)
    sys.exit(1)
print("VERIFICATION PASSED")
print(json.dumps(log, indent=2))
sys.exit(0)
