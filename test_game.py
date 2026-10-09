"""Quick automated sanity test: import + instantiate the core objects + run a short simulated frame sequence."""
import sys
import pathlib
import traceback

def main() -> int:
    base = pathlib.Path(__file__).resolve().parent
    sys.path.insert(0, str(base))

    problems = []
    from td.settings import WIDTH, HEIGHT, TILE, FIELD_LEFT, FIELD_TOP, GRID_COLS, GRID_ROWS
    from td.path import Path
    from td.entities import Enemy, Tower, Projectile, Particle
    from td.waves import Spawner, WaveTimeline, make_infinite_timeline
    from td.levels import LEVELS, build_timeline, tower_config_from_type, enemy_template_from_type

    # 1) level data sanity
    for i, lv in enumerate(LEVELS):
        if len(lv["waypoints"]) < 2:
            problems.append(f"Level {i+1} has <2 waypoints")
        for w in lv["waves"]:
            if w["type"] not in enemy_template_from_type(w["type"]):
                problems.append(f"Level {i+1} unknown enemy type {w['type']}")

    # 2) path + reserved cells
    lv = LEVELS[0]
    waypoints = [(FIELD_LEFT + c * TILE + TILE/2, FIELD_TOP + r * TILE + TILE/2) for c,r in lv["waypoints"]]
    path = Path(waypoints)
    reserved = path.grid_cells_for_path(GRID_COLS, GRID_ROWS)
    if not path.can_place_at(0,0,reserved):
        problems.append("Level 1 cell (0,0) unexpectedly reserved")

    # 3) spawner
    tl = build_timeline(lv["waves"])
    spawner = Spawner(tl)
    spawn_log = []
    def spawn(type_, hp, spd, rew):
        spawn_log.append((type_, hp, spd, rew))
    dt = 0.016
    while not spawner.finished:
        spawner.update(dt, spawn)
        if len(spawn_log) > 200:
            problems.append("spawner did not finish in time")
            break

    # 4) enemy movement along path
    t = enemy_template_from_type("basic")
    e = Enemy(path, "basic", t["hp"], t["speed"], t["reward"], __import__("pygame").Color(t["color"]), t["radius"], waypoints)
    e.reset_progress()
    for _ in range(200):
        reached = e.advance(dt, path.total_length)
        if reached:
            break
    if not e.reached_end and e.progress() < path.total_length - 1:
        problems.append("enemy did not reach end in reasonable steps")

    # 5) tower placement + fire
    cfg = tower_config_from_type("rapid")
    tp = Tower(1, 1, "rapid", cfg, FIELD_LEFT, FIELD_TOP, TILE)
    tp._enemies_near = [e]
    proj = tp.update(0.5, [e])
    if proj is None:
        problems.append("tower did not fire when enemy in range")

    # 6) projectile
    p = Projectile((tp.x, tp.y), e, 500, 12, 0, 0, 0, __import__("pygame").Color(cfg["color"]), tp)
    removed = False
    for _ in range(300):
        if p.update(dt):
            removed = True
            break
    if not removed:
        problems.append("projectile never removed")

    # 7) particles
    parts = [Particle((100,100),(10,10),__import__("pygame").Color(255,0,0),0.5,3)]
    for _ in range(60):
        for p in parts:
            p.update(dt)
        parts = [p for p in parts if p.alive()]
    if not parts:
        pass

    if problems:
        print("FAIL:")
        for pb in problems:
            print("  -", pb)
        return 1
    print("OK: all core objects constructed and run without error")
    return 0

if __name__ == "__main__":
    try:
        rc = main()
    except Exception as exc:
        print("CRASH:", exc)
        traceback.print_exc()
        rc = 3
    sys.exit(rc)
