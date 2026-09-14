import json
import os
from config import DATA_DIR


def _path(user_id: int) -> str:
    os.makedirs(DATA_DIR, exist_ok=True)
    return os.path.join(DATA_DIR, f"{user_id}.json")


def _migrate(world: dict) -> dict:
    if not world:
        return world

    char = world.get("character") or {}
    if char:
        from character import CHARGES_PER_FIGHT, level_bonus
        char.setdefault("charges", CHARGES_PER_FIGHT)
        char.setdefault("charges_max", CHARGES_PER_FIGHT)
        char.setdefault("level", 1)
        char.setdefault("xp", 0)
        char.setdefault("shards", 0)
        _, dmg, armor = level_bonus(char.get("level", 1))
        char.setdefault("dmg_bonus", dmg)
        char.setdefault("armor_bonus", armor)
        char.setdefault("inventory", [])

    if "combat" not in world or not isinstance(world.get("combat"), dict):
        world["combat"] = {"active": False, "enemies": [], "log": []}

    world.setdefault("recent_actions", [])
    world.setdefault("pending", None)

    return world


def load(user_id: int) -> dict | None:
    p = _path(user_id)
    if not os.path.exists(p):
        return None
    with open(p, "r", encoding="utf-8") as f:
        return _migrate(json.load(f))


def save(user_id: int, world: dict):
    with open(_path(user_id), "w", encoding="utf-8") as f:
        json.dump(world, f, ensure_ascii=False, indent=2)
