DEFAULT_STATS = {"STR": 1, "DEX": 1, "INT": 1, "WIS": 1, "CHA": 1}

def new_character(name: str, personality: str) -> dict:
    return {
        "name": name,
        "personality": personality,
        "hp": 10,
        "hp_max": 10,
        "gold": 10,
        "state": "в порядке",
        "stats": dict(DEFAULT_STATS),
    }

def apply_delta(char: dict, delta: dict):
    if "hp_delta" in delta:
        char["hp"] = max(0, min(char["hp_max"], char["hp"] + int(delta["hp_delta"])))
    if "gold_delta" in delta:
        char["gold"] = max(0, char["gold"] + int(delta["gold_delta"]))
    for key in ("state", "personality", "name"):
        if delta.get(key):
            char[key] = delta[key]
