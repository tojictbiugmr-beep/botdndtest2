from dice import roll_d20, roll_expr
from character import CLASSES, check_level_up, CHARGES_PER_FIGHT


def player_defense(char: dict) -> int:
    return 10 + char["stats"].get("DEX", 0) + char.get("armor_bonus", 0)


def _guess_xp(hp: int) -> int:
    if hp >= 40:
        return 150   # босс
    if hp >= 30:
        return 70    # мини-босс
    if hp >= 20:
        return 45    # сильный
    if hp >= 12:
        return 20    # средний
    return 8         # слабый


def _attack_roll(mod: int, target_def: int) -> dict:
    d = roll_d20()
    total = d + mod
    crit = (d == 20)
    miss = (d == 1)
    hit = crit or (not miss and total >= target_def)
    return {"d20": d, "mod": mod, "total": total,
            "vs": target_def, "hit": hit, "crit": crit}


def _damage(expr: str, crit: bool, stat_mod: int, dmg_bonus: int = 0) -> dict:
    base, rolls = roll_expr(expr)
    extra_rolls = []
    if crit:
        extra, extra_rolls = roll_expr(expr)
    else:
        extra = 0
    total = base + extra + stat_mod + dmg_bonus
    return {
        "expr": expr,
        "rolls": rolls,
        "extra_rolls": extra_rolls,
        "dice_sum": base + extra,
        "stat_mod": stat_mod,
        "dmg_bonus": dmg_bonus,
        "total": total,
        "crit": crit,
    }


def _fmt_damage(d: dict) -> str:
    if d["extra_rolls"]:
        head = f"{d['expr']}+{d['expr']} → {d['rolls']}+{d['extra_rolls']}"
    else:
        head = f"{d['expr']} → {d['rolls']}"
    return (f"{head} = {d['dice_sum']} + {d['stat_mod']}"
            + (f" + {d['dmg_bonus']}" if d["dmg_bonus"] else "")
            + f" = {d['total']}")


def start_combat(world: dict, enemies: list[dict]):
    world["combat"] = {
        "active": True,
        "enemies": [
            {
                "name": e.get("name", "Враг"),
                "hp": int(e.get("hp", 8)),
                "hp_max": int(e.get("hp", 8)),
                "defense": int(e.get("defense", 12)),
                "attack_stat": int(e.get("attack_stat", 2)),
                "damage": e.get("damage", "1d4"),
                "xp": int(e.get("xp") or _guess_xp(int(e.get("hp", 8)))),
            }
            for e in enemies
        ],
        "log": [],
    }


def combat_over(world: dict) -> bool:
    c = world.get("combat") or {}
    if not c.get("active"):
        return True
    if not c.get("enemies"):
        return True
    return world["character"]["hp"] <= 0


def _kill_enemy(world: dict, enemy: dict) -> str:
    char = world["character"]
    xp = enemy.get("xp", 8)
    char["xp"] = char.get("xp", 0) + xp
    world["combat"]["enemies"].remove(enemy)
    return f"☠️ {enemy['name']} повержен. +{xp} XP"


def player_attack(world: dict) -> str:
    c = world.get("combat") or {}
    if not c.get("enemies"):
        return "Врагов нет."

    char = world["character"]
    enemy = c["enemies"][0]
    cls = CLASSES.get(char.get("cls"), CLASSES["warrior"])
    stat = cls["attack_stat"]
    mod = char["stats"].get(stat, 0)
    dmg_bonus = char.get("dmg_bonus", 0)

    r = _attack_roll(mod, enemy["defense"])
    lines = [
        f"⚔️ Ты атакуешь {enemy['name']} ({stat}):",
        f"🎲 d20={r['d20']} + {mod} = {r['total']} vs {r['vs']}",
    ]

    if not r["hit"]:
        lines.append("Промах.")
        return "\n".join(lines)

    d = _damage(cls["damage"], r["crit"], mod, dmg_bonus)
    enemy["hp"] = max(0, enemy["hp"] - d["total"])
    tag = " 💥 КРИТ!" if r["crit"] else ""
    lines.append(f"Урон{tag}: {_fmt_damage(d)}")
    lines.append(f"{enemy['name']}: HP {enemy['hp']}/{enemy['hp_max']}")

    if enemy["hp"] <= 0:
        lines.append(_kill_enemy(world, enemy))

    return "\n".join(lines)


def player_skill(world: dict) -> str:
    c = world.get("combat") or {}
    if not c.get("enemies"):
        return "Врагов нет."

    char = world["character"]
    if char.get("charges", 0) <= 0:
        return "Нет зарядов скилла."

    cls = CLASSES.get(char.get("cls"), CLASSES["warrior"])
    stat = cls["attack_stat"]
    mod = char["stats"].get(stat, 0)
    dmg_bonus = char.get("dmg_bonus", 0)
    skill_name = cls["skill"]["name"]

    # Один d20 на всех, DC = максимальная защита в группе
    target_def = max(e["defense"] for e in c["enemies"])
    r = _attack_roll(mod, target_def)

    char["charges"] = char.get("charges", 0) - 1

    lines = [
        f"🌀 {skill_name} ({stat}):",
        f"🎲 d20={r['d20']} + {mod} = {r['total']} vs {target_def}",
    ]

    if not r["hit"]:
        lines.append("Скилл ушёл в молоко — никто не пострадал.")
        return "\n".join(lines)

    # Урон как обычная атака, но -15%, при крите х2
    d = _damage(cls["damage"], False, mod, dmg_bonus)
    base = d["total"]
    after15 = int(base * 0.85)
    final = after15 * 2 if r["crit"] else after15
    tag = " 💥 КРИТ!" if r["crit"] else ""
    lines.append(
        f"Урон по всем{tag}: {d['expr']} → {d['rolls']} = {d['dice_sum']} + "
        f"{mod}" + (f" + {dmg_bonus}" if dmg_bonus else "") +
        f" = {base} × 0.85 = {after15}" + (f" × 2 = {final}" if r["crit"] else "")
    )

    for enemy in list(c["enemies"]):
        enemy["hp"] = max(0, enemy["hp"] - final)
        lines.append(f"  {enemy['name']}: HP {enemy['hp']}/{enemy['hp_max']}")
        if enemy["hp"] <= 0:
            lines.append("  " + _kill_enemy(world, enemy))

    return "\n".join(lines)


def enemy_turn(world: dict) -> str:
    c = world.get("combat") or {}
    if not c.get("enemies"):
        return ""

    char = world["character"]
    lines = []

    for enemy in list(c["enemies"]):
        if char["hp"] <= 0:
            break
        r = _attack_roll(enemy["attack_stat"], player_defense(char))
        lines.append(
            f"🗡 {enemy['name']}: d20={r['d20']} + {enemy['attack_stat']} "
            f"= {r['total']} vs {r['vs']}"
        )

        if not r["hit"]:
            lines.append("  Мимо.")
            continue

        d = _damage(enemy["damage"], r["crit"], enemy["attack_stat"], 0)
        char["hp"] = max(0, char["hp"] - d["total"])
        tag = " 💥 КРИТ!" if r["crit"] else ""
        lines.append(f"  Урон{tag}: {_fmt_damage(d)}")
        lines.append(f"  Твоё HP: {char['hp']}/{char['hp_max']}")

    return "\n".join(lines)


def end_combat(world: dict) -> str:
    c = world.get("combat") or {}
    enemies = c.get("enemies") or []
    if not enemies:
        summary = "Бой окончен. Все враги повержены."
    else:
        summary = "Бой прерван."

    char = world["character"]
    char["hp"] = char["hp_max"]
    char["charges"] = char.get("charges_max", CHARGES_PER_FIGHT)

    msgs = check_level_up(char)

    world["combat"] = {"active": False, "enemies": [], "log": []}
    return summary, msgs


def status_line(world: dict) -> str:
    c = world.get("combat") or {}
    if not c.get("active") or not c["enemies"]:
        return ""
    ch = world["character"]
    enemies = "  ".join(
        f"👹 {e['name']}: {e['hp']}/{e['hp_max']}" for e in c["enemies"]
    )
    return (
        f"❤️ Ты: {ch['hp']}/{ch['hp_max']}  "
        f"| 🌀 {ch.get('charges', 0)}  |  {enemies}"
    )
