CLASSES = {
    "warrior": {
        "name": "Воин", "hp_max": 14,
        "stats": {"STR": 3, "DEX": 1, "INT": 0, "WIS": 1, "CHA": 0},
        "attack_stat": "STR", "damage": "1d8",
        "desc": "Много HP, тяжёлые удары.",
    },
    "mage": {
        "name": "Маг", "hp_max": 8,
        "stats": {"STR": 0, "DEX": 1, "INT": 3, "WIS": 1, "CHA": 1},
        "attack_stat": "INT", "damage": "1d10",
        "desc": "Хрупкий, но бьёт магией больно.",
    },
    "rogue": {
        "name": "Плут", "hp_max": 10,
        "stats": {"STR": 1, "DEX": 3, "INT": 1, "WIS": 1, "CHA": 1},
        "attack_stat": "DEX", "damage": "1d6",
        "desc": "Ловкий, точные удары.",
    },
    "cleric": {
        "name": "Жрец", "hp_max": 12,
        "stats": {"STR": 1, "DEX": 0, "INT": 1, "WIS": 3, "CHA": 1},
        "attack_stat": "WIS", "damage": "1d6",
        "desc": "Крепкая вера, бьёт и лечит.",
    },
}

def new_character(name: str, personality: str, cls_key: str) -> dict:
    cls = CLASSES.get(cls_key, CLASSES["warrior"])
    return {
        "name": name,
        "personality": personality,
        "cls": cls_key,
        "hp": cls["hp_max"],
        "hp_max": cls["hp_max"],
        "gold": 10,
        "state": "в порядке",
        "stats": dict(cls["stats"]),
    }

def apply_delta(char: dict, delta: dict):
    if "hp_delta" in delta:
        char["hp"] = max(0, min(char["hp_max"], char["hp"] + int(delta["hp_delta"])))
    if "gold_delta" in delta:
        char["gold"] = max(0, char["gold"] + int(delta["gold_delta"]))
    for key in ("state", "personality", "name"):
        if delta.get(key):
            char[key] = delta[key]
