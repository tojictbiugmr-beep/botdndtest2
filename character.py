CLASSES = {
    "warrior": {
        "name": "Воин", "hp_base": 20,
        "stats": {"STR": 3, "DEX": 1, "INT": 0, "WIS": 1, "CHA": 0},
        "attack_stat": "STR", "damage": "2d4",
        "skill": {"name": "Круговой замах",
                  "desc": "Бьёт всех врагов, урон -15%"},
        "desc": "Много HP, тяжёлые удары.",
    },
    "rogue": {
        "name": "Плут", "hp_base": 16,
        "stats": {"STR": 1, "DEX": 3, "INT": 1, "WIS": 1, "CHA": 1},
        "attack_stat": "DEX", "damage": "2d4",
        "skill": {"name": "Серия ударов",
                  "desc": "Бьёт всех врагов, урон -15%"},
        "desc": "Ловкий, точные удары.",
    },
    "mage": {
        "name": "Маг", "hp_base": 14,
        "stats": {"STR": 0, "DEX": 1, "INT": 3, "WIS": 1, "CHA": 1},
        "attack_stat": "INT", "damage": "2d6",
        "skill": {"name": "Комета",
                  "desc": "Бьёт всех врагов, урон -15%"},
        "desc": "Хрупкий, но бьёт магией больно.",
    },
}

MAX_LEVEL = 5
XP_TO_REACH = {2: 20, 3: 50, 4: 100, 5: 180}
CHARGES_PER_FIGHT = 2


def level_bonus(level: int) -> tuple[int, int, int]:
    """(hp_bonus, dmg_bonus, armor_bonus) для уровня."""
    hp_bonus = (level - 1) * 3
    dmg_bonus = (level - 1) * 2
    armor_bonus = 0
    if level >= 2:
        armor_bonus += 1
    if level >= 4:
        armor_bonus += 1
    return hp_bonus, dmg_bonus, armor_bonus


def new_character(name: str, personality: str, cls_key: str) -> dict:
    cls = CLASSES.get(cls_key, CLASSES["warrior"])
    hp_bonus, dmg_bonus, armor_bonus = level_bonus(1)
    hp_max = cls["hp_base"] + hp_bonus
    return {
        "name": name,
        "personality": personality,
        "cls": cls_key,
        "level": 1,
        "xp": 0,
        "hp": hp_max,
        "hp_max": hp_max,
        "gold": 10,
        "state": "в порядке",
        "stats": dict(cls["stats"]),
        "dmg_bonus": dmg_bonus,
        "armor_bonus": armor_bonus,
        "charges": CHARGES_PER_FIGHT,
        "charges_max": CHARGES_PER_FIGHT,
    }


def check_level_up(char: dict) -> list[str]:
    """Проверяет и применяет ап. Возвращает сообщения."""
    msgs = []
    while char.get("level", 1) < MAX_LEVEL:
        next_lvl = char["level"] + 1
        need = XP_TO_REACH[next_lvl]
        if char.get("xp", 0) < need:
            break

        char["level"] = next_lvl
        cls = CLASSES.get(char["cls"], CLASSES["warrior"])
        hp_bonus, dmg_bonus, armor_bonus = level_bonus(next_lvl)
        new_hp_max = cls["hp_base"] + hp_bonus
        char["hp_max"] = new_hp_max
        char["hp"] = new_hp_max
        char["dmg_bonus"] = dmg_bonus
        char["armor_bonus"] = armor_bonus

        armor_str = f", броня +{armor_bonus}" if armor_bonus else ""
        msgs.append(
            f"🎉 Уровень {next_lvl}! HP {new_hp_max}, урон +{dmg_bonus}{armor_str}"
        )
    return msgs


def apply_delta(char: dict, delta: dict):
    if "hp_delta" in delta:
        char["hp"] = max(0, min(char["hp_max"], char["hp"] + int(delta["hp_delta"])))
    if "gold_delta" in delta:
        char["gold"] = max(0, char["gold"] + int(delta["gold_delta"]))
    for key in ("state", "personality", "name"):
        if delta.get(key):
            char[key] = delta[key]
