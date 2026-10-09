"""Sauvegarde JSON dans le dossier du jeu (relatif à main.py ou au .exe)."""
from __future__ import annotations

import json
import pathlib

SAVE_NAME = "towerdefense_save.json"


def _save_path(base_path: pathlib.Path) -> pathlib.Path:
    # Si base_path pointe vers un fichier (main.py dans le dev), on écrit à côté.
    if base_path.is_file():
        return base_path.parent / SAVE_NAME
    # Sinon on considère que c'est un répertoire (répertoire du .exe quand frozen).
    return base_path / SAVE_NAME


def load_save(base_path: pathlib.Path) -> dict:
    p = _save_path(base_path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_game(base_path: pathlib.Path, data: dict) -> None:
    p = _save_path(base_path)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def autosave(base_path: pathlib.Path, scene) -> None:
    data = {
        "level_index": scene.level_index if scene.level_index is not None else -1,
        "gold": scene.gold,
        "lives": scene.lives,
        "score": scene.score,
        "towers": [
            {
                "type": t.tower_type,
                "col": t.col,
                "row": t.row,
                "level": getattr(t, "level", 1),
            }
            for t in scene.towers
        ],
        "active_boosts": list(getattr(scene, "active_boosts", {}).keys()),
        "infinite": getattr(scene, "infinite", False),
        "infinite_wave": getattr(scene, "infinite_wave_index", 0),
    }
    save_game(base_path, data)


def load_into_scene(base_path: pathlib.Path, scene) -> bool:
    data = load_save(base_path)
    if not data:
        return False

    if scene.infinite and not data.get("infinite", False):
        return False

    if "gold" in data:
        scene.gold = data["gold"]
    if "lives" in data:
        scene.lives = data["lives"]
    if "score" in data:
        scene.score = data["score"]
    if "towers" in data:
        from td.settings import TOWER_TEMPLATES, FIELD_LEFT, FIELD_TOP, TILE
        from td.entities import Tower

        for tdata in data["towers"]:
            cfg = dict(TOWER_TEMPLATES.get(tdata.get("type", "rapid"), {}))
            t = Tower(
                tdata.get("col", 0),
                tdata.get("row", 0),
                tdata.get("type", "rapid"),
                cfg,
                FIELD_LEFT,
                FIELD_TOP,
                TILE,
            )
            t.level = tdata.get("level", 1)
            scene.towers.append(t)
    if "active_boosts" in data:
        scene.active_boosts = {
            k: scene.active_boosts.get(k, 0.0) for k in data["active_boosts"]
        }
    return True
