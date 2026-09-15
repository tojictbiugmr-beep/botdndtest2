import json
import os
from config import DATA_DIR


def _path(user_id: int) -> str:
    os.makedirs(DATA_DIR, exist_ok=True)
    return os.path.join(DATA_DIR, f"{user_id}.json")


def _migrate_personality(p):
    """Старый характер (строка) → dict. Новый dict возвращает как есть."""
    if isinstance(p, dict):
        # Дополняем отсутствующие поля
        for k in ("archetype", "habits", "manner", "fears",
                  "motivation", "conflict", "notes"):
            p.setdefault(k, "")
        return p
    if isinstance(p, str):
        return {
            "archetype": "",
            "habits": "",
            "manner": "",
            "fears": "",
            "motivation": "",
            "conflict": "",
            "notes": p,
        }
    return {
        "archetype": "",
        "habits": "",
        "manner": "",
        "fears": "",
        "motivation": "",
        "conflict": "",
        "notes": "",
    }


def _migrate(world: dict) -> dict:
    if not world:
        return world

    # Мир — новые поля
    w = world.get("world")
    if not isinstance(w, dict):
        w = {}
        world["world"] = w
    w.setdefault("setting", "")
    w.setdefault("tone", "")
    w.setdefault("description", "")
    w.setdefault("milestone", "")
    w.setdefault("progress", 0)
    w.setdefault("mode", "AMBIENT")
    w.setdefault("final", "")
    w.setdefault("boss_defeated", False)
    w.setdefault("epilogue_turns", 0)
    w.setdefault("final_reached", False)

    # Персонаж
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
        char["personality"] = _migrate_personality(char.get("personality"))

    if "combat" not in world or not isinstance(world.get("combat"), dict):
        world["combat"] = {"active": False, "enemies": [], "log": []}

    world.setdefault("recent_actions", [])
    world.setdefault("pending", None)
    world.setdefault("npcs", {})
    world.setdefault("events", [])
    world.setdefault("archive", [])
    world.setdefault("history", [])

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
