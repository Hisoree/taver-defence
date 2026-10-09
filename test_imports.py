import sys
import pathlib

base = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(base))

from td.settings import WIDTH, HEIGHT, TILE, FIELD_LEFT, FIELD_TOP, GRID_COLS, GRID_ROWS
from td.path import Path
from td.entities import Enemy, Tower, Projectile, Particle
from td.waves import Spawner, WaveTimeline, make_infinite_timeline
from td.levels import LEVELS, build_timeline, tower_config_from_type, enemy_template_from_type
import pygame

def main() -> int:
    # path + reserved cells
    lv = LEVELS[0]
    waypoints = [(FIELD_LEFT + c * TILE + TILE/2, FIELD_TOP + r * TILE + TILE/2) for c,r in lv["waypoints"]]
    path = Path(waypoints)
    reserved = path.grid_cells_for_path(GRID_COLS, GRID_ROWS)
    if not path.can_place_at(0,0,reserved):
        print("cell (0,0) is placeable (expected)")
    # spawner smoke
    tl = build_timeline(lv["waves"])
    spawner = Spawner(tl)
    log = []
    def sp(type_, hp, spd, rew):
        log.append((type_, hp, spd, rew))
    dt = 0.016
    guard = 0
    while not spawner.finished and guard < 2000:
        spawner.update(dt, sp)
        guard += 1
    print(f"spawner finished={spawner.finished} events_emitted={len(log)} guard={guard}")
    # enemy movement smoke
    t = enemy_template_from_type("basic")
    e = Enemy(path, "basic", t["hp"], t["speed"], t["reward"], pygame.Color(t["color"]), t["radius"], waypoints)
    e.reset_progress()
    guard = 0
    while not e.reached_end and guard < 4000:
        e.advance(dt, path.total_length)
        guard += 1
    print(f"enemy reached_end={e.reached_end} progress={e.progress():.0f}/{path.total_length:.0f} guard={guard}")
    # tower smoke
    cfg = tower_config_from_type("rapid")
    tp = Tower(1,1,"rapid",cfg,FIELD_LEFT,FIELD_TOP,TILE)
    tp._enemies_near = [e]
    p = tp.update(0.5, [e])
    print(f"tower fired={p is not None}")
    print("OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
