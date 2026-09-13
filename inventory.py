import random
from dice import roll_expr

MAX_POTION_STACK = 10

ITEM_EMOJI = {
    "weapon": "🗡",
    "armor": "🛡",
    "potion": "🧪",
    "misc": "📦",
    "torch": "🔥",
    "lighter": "✨",
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


def find_item(char: dict, name: str) -> dict | None:
    for it in char.get("inventory", []):
        if it["name"] == name:
            return it
    return None


def use_potion(char: dict, idx: int) -> str:
    """Возвращает строку с результатом."""
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
        q_names = {0: "обычное", 1: "🟢 зелёное", 2: "🟣 фиолетовое", 3: "🟡 золотое"}
        bonus = item.get("attack_bonus", 0)
        lines.append(f"Атака: +{bonus}  |  Качество: {q_names.get(q, '—')}")
    elif item.get("type") == "armor":
        q = item.get("quality", 0)
        q_names = {0: "обычное", 1: "🟢 зелёное", 2: "🟣 фиолетовое", 3: "🟡 золотое"}
        bonus = item.get("defense_bonus", 0)
        lines.append(f"Защита: +{bonus}  |  Качество: {q_names.get(q, '—')}")
    elif item.get("type") == "potion":
        if item.get("heal"):
            lines.append(f"Восстанавливает: {item['heal']} HP")

    return "\n".join(lines)
