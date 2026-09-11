from dice import roll_d20, roll_expr
from character import CLASSES

def player_defense(char: dict) -> int:
    return 10 + char["stats"].get("DEX", 0)

def _attack_roll(mod: int, target_def: int) -> dict:
    d = roll_d20()
    total = d + mod
    crit = (d == 20)
    miss = (d == 1)
    hit = crit or (not miss and total >= target_def)
    return {"d20": d, "mod": mod, "total": total,
            "vs": target_def, "hit": hit, "crit": crit}

def _damage(expr: str, crit: bool) -> tuple[int, list[int]]:
    dmg, rolls = roll_expr(expr)
    if crit:
        d2, r2 = roll_expr(expr)
        return dmg + d2, rolls + r2
    return dmg, rolls

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
                "damage": e.get("damage", "1d6"),
            }
            for e in enemies
        ],
        "log": [],
    }

def combat_over(world: dict) -> bool:
    c = world.get("combat")
    if not c or not c.get("active"):
        return True
    if not c["enemies"]:
        return True
    return world["character"]["hp"] <= 0

def player_attack(world: dict) -> str:
    c = world["combat"]
    char = world["character"]
    enemy = c["enemies"][0]
    cls = CLASSES[char["cls"]]
    stat = cls["attack_stat"]
    mod = char["stats"].get(stat, 0)
    r = _attack_roll(mod, enemy["defense"])

    lines = [f"⚔️ Ты атакуешь {enemy['name']} ({stat}):"]
    lines.append(f"🎲 d20={r['d20']} + {mod} = {r['total']} vs {r['vs']}")

    if not r["hit"]:
        lines.append("Промах.")
    else:
        dmg, rolls = _damage(cls["damage"], r["crit"])
        enemy["hp"] = max(0, enemy["hp"] - dmg)
        tag = " 💥 КРИТ!" if r["crit"] else ""
        lines.append(f"Урон: {cls['damage']} → {rolls} = {dmg}{tag}")
        lines.append(f"{enemy['name']}: HP {enemy['hp']}/{enemy['hp_max']}")

        if enemy["hp"] <= 0:
            lines.append(f"☠️ {enemy['name']} повержен.")
            c["enemies"].pop(0)

    return "\n".join(lines)

def enemy_turn(world: dict) -> str:
    c = world["combat"]
    if not c["enemies"]:
        return ""
    char = world["character"]
    enemy = c["enemies"][0]
    r = _attack_roll(enemy["attack_stat"], player_defense(char))

    lines = [f"🗡 {enemy['name']} атакует:"]
    lines.append(f"🎲 d20={r['d20']} + {r['attack_stat']} = {r['total']} vs {r['vs']}")
    if not r["hit"]:
        lines.append("Мимо.")
    else:
        dmg, rolls = _damage(enemy["damage"], r["crit"])
        char["hp"] = max(0, char["hp"] - dmg)
        lines.append(f"Урон: {enemy['damage']} → {rolls} = {dmg}")
        lines.append(f"Твоё HP: {char['hp']}/{char['hp_max']}")

    return "\n".join(lines)

def end_combat(world: dict) -> str:
    c = world.get("combat") or {}
    enemies = c.get("enemies") or []
    if not enemies:
        summary = "Бой окончен. Все враги повержены."
    else:
        summary = "Бой прерван."
    world["combat"] = {"active": False, "enemies": [], "log": []}
    return summary

def status_line(world: dict) -> str:
    c = world.get("combat") or {}
    if not c.get("active") or not c["enemies"]:
        return ""
    e = c["enemies"][0]
    ch = world["character"]
    return (
        f"❤️ Ты: {ch['hp']}/{ch['hp_max']}  |  "
        f"👹 {e['name']}: {e['hp']}/{e['hp_max']}"
    )
