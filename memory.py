from config import MAX_EVENTS, EVENTS_CTX, MAX_HISTORY
from character import CLASSES, apply_delta, format_personality
from inventory import add_item, remove_item

MAX_RECENT_ACTIONS = 5


def new_world(user_id: int) -> dict:
    return {
        "user_id": user_id,
        "world": {
            "setting": "",
            "tone": "",
            "description": "",
            "milestone": "",
            "progress": 0,
            "mode": "AMBIENT",
            "final": "",
            "boss_defeated": False,
            "epilogue_turns": 0,
            "final_reached": False,
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

    # final — только при первом заполнении, не перезаписываем
    if w.get("final") and not world["world"].get("final"):
        world["world"]["final"] = w["final"]

    # description — тоже только один раз (игрок задал при старте)
    if w.get("description") and not world["world"].get("description"):
        world["world"]["description"] = w["description"]

    if "boss_defeated" in w and w["boss_defeated"] is not None:
        world["world"]["boss_defeated"] = bool(w["boss_defeated"])

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
    lines.append(f"СЕТТИНГ: {w.get('setting', '') or '—'}")
    lines.append(f"ТОН: {w.get('tone', '') or '—'}")

    desc = w.get("description", "")
    if desc:
        lines.append(f"МИР (задан игроком): {desc}")

    lines.append(f"MILESTONE: {w['milestone'] or '—'} ({w['progress']}%)")
    lines.append(f"РЕЖИМ: {w['mode']}")

    final = w.get("final", "")
    if final:
        lines.append(f"ФИНАЛ (скрыт от игрока, вести к нему): {final}")

    if w.get("final_reached"):
        lines.append("СТАТУС: ИСТОРИЯ ЗАВЕРШЕНА")
    elif w.get("epilogue_turns", 0) > 0:
        lines.append(
            f"СТАТУС: ЭПИЛОГ, осталось {w['epilogue_turns']} ходов до конца. "
            f"Раскрывай последствия, веди к финальной точке."
        )
    elif w.get("boss_defeated"):
        lines.append("СТАТУС: босс повержен, начинается эпилог")
    else:
        lines.append("СТАТУС: основной сюжет")

    c = world["character"]
    cls = CLASSES.get(c.get("cls"), {})
    lines.append(
        f"ИГРОК (служебные данные, NPC их не знают): "
        f"{c.get('name','?')} — {cls.get('name','')}, ур. {c.get('level',1)}. "
        f"HP {c.get('hp',0)}/{c.get('hp_max',0)}, "
        f"золото {c.get('gold',0)}, состояние: {c.get('state','')}"
    )

    # Характер — отдельным блоком
    p = c.get("personality")
    if p:
        lines.append("")
        lines.append("ХАРАКТЕР ПЕРСОНАЖА (используй в каждой сцене — привычку, манеру, страх, мотив):")
        if isinstance(p, dict):
            if p.get("archetype"):
                lines.append(f"  • Архетип: {p['archetype']}")
            if p.get("habits"):
                lines.append(f"  • Привычки: {p['habits']}")
            if p.get("manner"):
                lines.append(f"  • Манера: {p['manner']}")
            if p.get("fears"):
                lines.append(f"  • Страхи: {p['fears']}")
            if p.get("motivation"):
                lines.append(f"  • Мотив: {p['motivation']}")
            if p.get("notes"):
                lines.append(f"  • Доп.: {p['notes']}")
        else:
            lines.append(f"  • {p}")

    inv = c.get("inventory", [])
    if inv:
        lines.append("")
        lines.append("ИНВЕНТАРЬ (у игрока):")
        for it in inv:
            qty = it.get("qty", 1)
            qty_str = f" ×{qty}" if qty > 1 else ""
            desc = f" — {it['desc']}" if it.get("desc") else ""
            lines.append(f"  • {it['name']}{qty_str}{desc}")

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
