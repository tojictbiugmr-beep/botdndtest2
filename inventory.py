from dice import roll_expr

MAX_POTION_STACK = 10

UPGRADE_COSTS = {0: 8, 1: 20, 2: 45}
QUALITY_NAMES = {
    0: "обычное",
    1: "🟢 зелёное",
    2: "🟣 фиолетовое",
    3: "🟡 золотое",
}

ITEM_EMOJI = {
    "weapon": "🗡",
    "armor": "🛡",
    "potion": "🧪",
    "misc": "📦",
    "torch": "🔥",
}


def add_item(char: dict, item: dict):
    inv = char.setdefault("inventory", [])
    name = (item.get("name") or "").strip()
    if not name:
        return
    itype = item.get("type", "misc")
    for it in inv:
        if it["name"] == name and it.get("type") == itype:
            cap = MAX_POTION_STACK if itype == "potion" else 99
            it["qty"] = min(cap, it.get("qty", 1) + item.get("qty", 1))
            if item.get("desc") and not it.get("desc"):
                it["desc"] = item["desc"]
            return
    item.setdefault("qty", 1)
    item.setdefault("type", itype)
    inv.append(item)


def remove_item(char: dict, name: str, qty: int = 1) -> bool:
    inv = char.get("inventory", [])
    for it in list(inv):
        if it["name"] == name:
            it["qty"] = it.get("qty", 1) - qty
            if it["qty"] <= 0:
                inv.remove(it)
            return True
    return False


def find_item(char: dict, name: str):
    for it in char.get("inventory", []):
        if it["name"] == name:
            return it
    return None


def use_potion(char: dict, idx: int) -> str:
    inv = char.get("inventory", [])
    if idx < 0 or idx >= len(inv):
        return "Предмет не найден."

    item = inv[idx]
    if item.get("type") != "potion":
        return "Это нельзя использовать так."

    heal_expr = item.get("heal")
    if not heal_expr:
        return "Зелье без эффекта."

    amount, rolls = roll_expr(heal_expr)
    before = char["hp"]
    char["hp"] = min(char["hp_max"], char["hp"] + amount)
    healed = char["hp"] - before

    item["qty"] = item.get("qty", 1) - 1
    if item["qty"] <= 0:
        inv.remove(item)

    return (
        f"🧪 {item['name']}: {heal_expr} → {rolls} = {amount}\n"
        f"❤️ HP: {before} → {char['hp']}/{char['hp_max']} (+{healed})"
    )


def can_upgrade(item: dict) -> bool:
    if item.get("type") not in ("weapon", "armor"):
        return False
    return item.get("quality", 0) < 3


def upgrade_cost(item: dict):
    return UPGRADE_COSTS.get(item.get("quality", 0))


def upgrade_item(char: dict, idx: int) -> str:
    inv = char.get("inventory", [])
    if idx < 0 or idx >= len(inv):
        return "Предмет не найден."

    item = inv[idx]
    if not can_upgrade(item):
        return "Этот предмет нельзя улучшить."

    cost = upgrade_cost(item)
    shards = char.get("shards", 0)
    if shards < cost:
        return f"🔹 Не хватает осколков: нужно {cost}, у тебя {shards}."

    char["shards"] = shards - cost
    item["quality"] = item.get("quality", 0) + 1

    if item["type"] == "weapon":
        item["attack_bonus"] = item.get("attack_bonus", 0) + 1
        stat_name = "атаке"
    else:
        item["defense_bonus"] = item.get("defense_bonus", 0) + 1
        stat_name = "защите"

    q_name = QUALITY_NAMES.get(item["quality"], "—")
    return (
        f"⚒ {item['name']} улучшен до {q_name}!\n"
        f"+1 к {stat_name}. Осталось осколков: {char['shards']} 🔹"
    )


def format_item_line(item: dict) -> str:
    emoji = ITEM_EMOJI.get(item.get("type"), "📦")
    qty = item.get("qty", 1)
    qty_str = f" ×{qty}" if qty > 1 else ""
    return f"{emoji} {item['name']}{qty_str}"


def item_info(item: dict) -> str:
    emoji = ITEM_EMOJI.get(item.get("type"), "📦")
    lines = [f"{emoji} {item['name']}"]
    if item.get("desc"):
        lines.append(item["desc"])

    if item.get("type") == "weapon":
        q = item.get("quality", 0)
        bonus = item.get("attack_bonus", 0)
        lines.append(f"Атака: +{bonus}  |  Качество: {QUALITY_NAMES.get(q, '—')}")
    elif item.get("type") == "armor":
        q = item.get("quality", 0)
        bonus = item.get("defense_bonus", 0)
        lines.append(f"Защита: +{bonus}  |  Качество: {QUALITY_NAMES.get(q, '—')}")
    elif item.get("type") == "potion":
        if item.get("heal"):
            lines.append(f"Восстанавливает: {item['heal']} HP")

    if can_upgrade(item):
        cost = upgrade_cost(item)
        lines.append(f"⚒ Следующее улучшение: {cost} 🔹")

    return "\n".join(lines)
