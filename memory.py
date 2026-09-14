from config import MAX_EVENTS, EVENTS_CTX, MAX_HISTORY
from character import CLASSES, apply_delta
from inventory import add_item, remove_item

MAX_RECENT_ACTIONS = 5


def new_world(user_id: int) -> dict:
    return {
        "user_id": user_id,
        "world": {
            "setting": "",
            "tone": "",
            "milestone": "",
            "progress": 0,
            "mode": "AMBIENT",
        },
        "character": {},
        "npcs": {},
        "events": [],
        "archive": [],
        "history": [],
        "pending": None,
        "combat": {"active": False, "enemies": [], "log": []},
        "recent_actions": [],
    }


def push_event(world: dict, what: str, result: str):
    if not what:
        return
    world["events"].append({"what": what, "result": result or ""})
    if len(world["events"]) > MAX_EVENTS:
        world["archive"].extend(world["events"][:-MAX_EVENTS])
        world["events"] = world["events"][-MAX_EVENTS:]


def push_history(world: dict, role: str, content: str):
    world["history"].append({"role": role, "content": content})
    if len(world["history"]) > MAX_HISTORY:
        world["history"] = world["history"][-MAX_HISTORY:]


def push_recent_action(world: dict, text: str):
    """Факт действия через интерфейс (инвентарь и т.п.). Показывается мастеру 1-2 хода."""
    if not text:
        return
    world.setdefault("recent_actions", []).append(text)
    if len(world["recent_actions"]) > MAX_RECENT_ACTIONS:
        world["recent_actions"] = world["recent_actions"][-MAX_RECENT_ACTIONS:]


def clear_recent_actions(world: dict):
    """Вызывается после ответа мастера — он уже увидел факты."""
    world["recent_actions"] = []


def _safe_int(value, default: int = 0) -> int:
    try:
        return int(float(str(value).replace("%", "").strip()))
    except (ValueError, TypeError):
        return default


def apply_memory(world: dict, mem: dict):
    if not mem:
        return

    w = mem.get("world") or {}
    for k in ("setting", "tone", "milestone", "mode"):
        if w.get(k):
            world["world"][k] = w[k]

    if "progress" in w and w["progress"] is not None:
        world["world"]["progress"] = _safe_int(
            w["progress"], world["world"].get("progress", 0)
        )

    if mem.get("character"):
        apply_delta(world["character"], mem["character"])

    for name, data in (mem.get("npc_add") or {}).items():
        world["npcs"][name] = {
            "char": data.get("char", ""),
            "attitude": data.get("attitude", ""),
        }

    for name, data in (mem.get("npc_update") or {}).items():
        if name in world["npcs"]:
            for k in ("char", "attitude"):
                if data.get(k):
                    world["npcs"][name][k] = data[k]
        else:
            world["npcs"][name] = {
                "char": data.get("char", ""),
                "attitude": data.get("attitude", ""),
            }

    for item in (mem.get("inventory_add") or []):
        if isinstance(item, dict):
            add_item(world["character"], item)

    for name in (mem.get("inventory_remove") or []):
        if isinstance(name, str):
            remove_item(world["character"], name)

    ev = mem.get("event")
    if ev:
        push_event(world, ev.get("what", ""), ev.get("result", ""))


def build_context(world: dict) -> str:
    lines = []

    lines.append("=== ПАМЯТЬ МАСТЕРА (не знания NPC) ===")

    w = world["world"]
    lines.append(f"МИР: {w['setting']} | тон: {w['tone']}")
    lines.append(f"MILESTONE: {w['milestone'] or '—'} ({w['progress']}%)")
    lines.append(f"РЕЖИМ: {w['mode']}")

    c = world["character"]
    cls = CLASSES.get(c.get("cls"), {})
    lines.append(
        f"ИГРОК (служебные данные, NPC их не знают): "
        f"{c.get('name','?')} — {cls.get('name','')}, ур. {c.get('level',1)}. "
        f"Описание (для отыгрыша): {c.get('personality','')}. "
        f"HP {c.get('hp',0)}/{c.get('hp_max',0)}, "
        f"золото {c.get('gold',0)}, состояние: {c.get('state','')}"
    )

    inv = c.get("inventory", [])
    if inv:
        lines.append("ИНВЕНТАРЬ (у игрока):")
        for it in inv:
            qty = it.get("qty", 1)
            qty_str = f" ×{qty}" if qty > 1 else ""
            desc = f" — {it['desc']}" if it.get("desc") else ""
            lines.append(f"  • {it['name']}{qty_str}{desc}")

    # Факты действий через интерфейс (использование зелий и т.п.)
    recent = world.get("recent_actions") or []
    if recent:
        lines.append("")
        lines.append("ПОСЛЕДНИЕ ДЕЙСТВИЯ ЧЕРЕЗ ИНТЕРФЕЙС (уже выполнено кодом):")
        for act in recent:
            lines.append(f"  • {act}")

    if world["npcs"]:
        lines.append("")
        lines.append("ИЗВЕСТНЫЕ NPC (мастер знает о них; сами NPC знают только то,")
        lines.append("что видели/слышали лично. Отношение — к игроку, знает только мастер):")
        for name, d in world["npcs"].items():
            lines.append(f"  • {name}: {d['char']} | отношение к игроку: {d['attitude']}")

    if world["events"]:
        lines.append("")
        lines.append("ПОСЛЕДНИЕ СОБЫТИЯ (что произошло в мире — НЕ то, что знают все):")
        for e in world["events"][-EVENTS_CTX:]:
            lines.append(f"  • {e['what']} → {e['result']}")

    lines.append("=== КОНЕЦ ПАМЯТИ МАСТЕРА ===")

    return "\n".join(lines)
