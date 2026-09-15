CLASSES = {
    "warrior": {
        "name": "Воин", "hp_base": 20,
        "stats": {"STR": 3, "DEX": 1, "INT": 0, "WIS": 1, "CHA": 0},
        "attack_stat": "STR", "damage": "2d4",
        "skill": {"name": "Круговой замах",
                  "desc": "Бьёт всех врагов, урон -15%"},
        "desc": "Много HP, тяжёлые удары.",
        "start_inventory": [
            {"name": "Двуручный меч", "type": "weapon", "quality": 0,
             "attack_bonus": 0, "desc": "Тяжёлое оружие ближнего боя"},
            {"name": "Тяжёлая броня", "type": "armor", "quality": 0,
             "defense_bonus": 0, "desc": "Массивный доспех"},
            {"name": "Слабое зелье лечения", "type": "potion", "qty": 1,
             "heal": "1d4+3", "desc": "Восстанавливает 1d4+3 HP"},
            {"name": "Факел", "type": "torch", "qty": 1,
             "desc": "Освещает путь в темноте"},
            {"name": "Огниво", "type": "misc", "qty": 1,
             "desc": "Для розжига огня"},
        ],
    },
    "rogue": {
        "name": "Плут", "hp_base": 16,
        "stats": {"STR": 1, "DEX": 3, "INT": 1, "WIS": 1, "CHA": 1},
        "attack_stat": "DEX", "damage": "2d4",
        "skill": {"name": "Серия ударов",
                  "desc": "Бьёт всех врагов, урон -15%"},
        "desc": "Ловкий, точные удары.",
        "start_inventory": [
            {"name": "Парные кинжалы", "type": "weapon", "quality": 0,
             "attack_bonus": 0, "desc": "Быстрые клинки"},
            {"name": "Лёгкий доспех", "type": "armor", "quality": 0,
             "defense_bonus": 0, "desc": "Кожаный доспех"},
            {"name": "Слабое зелье лечения", "type": "potion", "qty": 1,
             "heal": "1d4+3", "desc": "Восстанавливает 1d4+3 HP"},
            {"name": "Факел", "type": "torch", "qty": 1,
             "desc": "Освещает путь в темноте"},
            {"name": "Огниво", "type": "misc", "qty": 1,
             "desc": "Для розжига огня"},
        ],
    },
    "mage": {
        "name": "Маг", "hp_base": 14,
        "stats": {"STR": 0, "DEX": 1, "INT": 3, "WIS": 1, "CHA": 1},
        "attack_stat": "INT", "damage": "2d6",
        "skill": {"name": "Комета",
                  "desc": "Бьёт всех врагов, урон -15%"},
        "desc": "Хрупкий, но бьёт магией больно.",
        "start_inventory": [
            {"name": "Посох", "type": "weapon", "quality": 0,
             "attack_bonus": 0, "desc": "Проводник магии"},
            {"name": "Мантия", "type": "armor", "quality": 0,
             "defense_bonus": 0, "desc": "Ткань, пропитанная чарами"},
            {"name": "Слабое зелье лечения", "type": "potion", "qty": 1,
             "heal": "1d4+3", "desc": "Восстанавливает 1d4+3 HP"},
            {"name": "Факел", "type": "torch", "qty": 1,
             "desc": "Освещает путь в темноте"},
            {"name": "Огниво", "type": "misc", "qty": 1,
             "desc": "Для розжига огня"},
        ],
    },
}


ARCHETYPES = {
    "hermit": {
        "name": "Затворник",
        "emoji": "🌲",
        "habits": "держит дистанцию, избегает толпы, молчит, пока не спросят",
        "manner": "говорит тихо и редко, отвечает односложно, не смотрит в глаза",
        "fears": "внимание чужих, шумные сборища, привязанность",
        "motivation": "сохранить независимость от кого-либо",
        "conflict": "боится людей, но не может жить без них — ищет одиночества и тайно страдает от него",
    },
    "fugitive": {
        "name": "Скрытный",
        "emoji": "🌑",
        "habits": "постоянно оглядывается, держится у выходов, спит чутко",
        "manner": "уклончив, говорит расплывчато, меняет тему",
        "fears": "быть узнанным, прошлое, вопросы о себе",
        "motivation": "скрыться от того, что гонится следом",
        "conflict": "бежит от прошлого, но всё, что делает, напоминает ему о нём",
    },
    "adventurer": {
        "name": "Азартный",
        "emoji": "🎲",
        "habits": "не сидит на месте, первым идёт в неизвестность",
        "manner": "громкий, весёлый, шутит, перебивает, любит внимание",
        "fears": "скука, однообразие, остаться один",
        "motivation": "найти яркое событие и наживу",
        "conflict": "ищет приключений ради острых ощущений, но глубоко внутри боится, что ничего не значит без них",
    },
    "avenger": {
        "name": "Непреклонный",
        "emoji": "🔥",
        "habits": "всегда настороже, ведёт счёт долгам, не забывает обид",
        "manner": "холоден, резок, не улыбается, говорит коротко",
        "fears": "не успеть, умереть раньше, чем расплатится",
        "motivation": "отомстить за то, что отняли",
        "conflict": "жаждет мести, но понимает, что она не вернёт утраченное — и это его разрывает",
    },
    "seeker": {
        "name": "Любознательный",
        "emoji": "📖",
        "habits": "рассматривает мелочи, задаёт вопросы, всё запоминает",
        "manner": "любопытен, говорит сбивчиво, отвлекается на детали",
        "fears": "невежество, тайна без ответа, ошибка в выводах",
        "motivation": "докопаться до правды любой ценой",
        "conflict": "хочет знать всё, но боится того, что может найти",
    },
    "romantic": {
        "name": "Мечтатель",
        "emoji": "✨",
        "habits": "замечает красоту вокруг, говорит образами, вздыхает",
        "manner": "мягок, галантен, преувеличенно вежлив, сентиментален",
        "fears": "быть осмеянным, отвергнутым, серым и обычным",
        "motivation": "найти великое чувство или великое дело",
        "conflict": "верит в высокое, но мир вокруг жесток и не соответствует его идеалам",
    },
    "soldier": {
        "name": "Стойкий",
        "emoji": "⛰️",
        "habits": "встаёт рано, всё делает по порядку, не жалуется",
        "manner": "лаконичен, чётко формулирует, держит осанку",
        "fears": "потерять контроль, подвести своих, трусость",
        "motivation": "исполнить долг и искупить прошлое",
        "conflict": "привык подчиняться приказам, но всё чаще сомневается, кому и зачем служит",
    },
    "jester": {
        "name": "Насмешник",
        "emoji": "🎭",
        "habits": "ищет повод для смеха, избегает серьёзных тем",
        "manner": "болтлив, шутит некстати, обаятелен, легко сходится",
        "fears": "тишина, серьёзный разговор, собственная боль",
        "motivation": "развлечься и не дать тоске взять верх",
        "conflict": "смешит других, чтобы не слышать собственный страх — маска приросла к лицу",
    },
}


MAX_LEVEL = 5
XP_TO_REACH = {2: 20, 3: 50, 4: 100, 5: 180}
CHARGES_PER_FIGHT = 2


def level_bonus(level: int) -> tuple:
    hp_bonus = (level - 1) * 3
    dmg_bonus = (level - 1) * 2
    armor_bonus = 0
    if level >= 2:
        armor_bonus += 1
    if level >= 4:
        armor_bonus += 1
    return hp_bonus, dmg_bonus, armor_bonus


def new_personality(archetype_key: str = "", habits: str = "",
                    manner: str = "", fears: str = "",
                    motivation: str = "", notes: str = "") -> dict:
    """Собирает dict характера. archetype_key — ключ из ARCHETYPES или пусто."""
    arch_name = ""
    conflict = ""
    if archetype_key in ARCHETYPES:
        a = ARCHETYPES[archetype_key]
        arch_name = a["name"]
        conflict = a.get("conflict", "")
        if not habits:
            habits = a["habits"]
        if not manner:
            manner = a["manner"]
        if not fears:
            fears = a["fears"]
        if not motivation:
            motivation = a["motivation"]

    return {
        "archetype": arch_name,
        "habits": habits or "",
        "manner": manner or "",
        "fears": fears or "",
        "motivation": motivation or "",
        "conflict": conflict,
        "notes": notes or "",
    }


def new_character(name: str, personality, cls_key: str) -> dict:
    """personality — dict или строка (для совместимости)."""
    if isinstance(personality, str):
        personality = new_personality(notes=personality)
    elif not isinstance(personality, dict):
        personality = new_personality()

    cls = CLASSES.get(cls_key, CLASSES["warrior"])
    hp_bonus, dmg_bonus, armor_bonus = level_bonus(1)
    hp_max = cls["hp_base"] + hp_bonus
    inventory = [dict(it) for it in cls.get("start_inventory", [])]
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
        "shards": 0,
        "inventory": inventory,
    }


def check_level_up(char: dict) -> list:
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


def format_personality(p) -> str:
    """Форматирует характер для вывода в контекст мастера."""
    if not p:
        return "—"
    if isinstance(p, str):
        return p
    parts = []
    if p.get("archetype"):
        parts.append(f"Архетип: {p['archetype']}")
    if p.get("habits"):
        parts.append(f"Привычки: {p['habits']}")
    if p.get("manner"):
        parts.append(f"Манера: {p['manner']}")
    if p.get("fears"):
        parts.append(f"Страхи: {p['fears']}")
    if p.get("motivation"):
        parts.append(f"Мотив: {p['motivation']}")
    if p.get("conflict"):
        parts.append(f"Конфликт: {p['conflict']}")
    if p.get("notes"):
        parts.append(f"Доп.: {p['notes']}")
    return " | ".join(parts) if parts else "—"


def apply_delta(char: dict, delta: dict):
    if "hp_delta" in delta:
        char["hp"] = max(0, min(char["hp_max"], char["hp"] + int(delta["hp_delta"])))
    if "gold_delta" in delta:
        char["gold"] = max(0, char["gold"] + int(delta["gold_delta"]))
    for key in ("state", "name"):
        if delta.get(key):
            char[key] = delta[key]
    # personality от LLM игнорируем — характер меняет только игрок через интерфейс
