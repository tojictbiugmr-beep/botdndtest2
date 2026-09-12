from config import MAX_EVENTS, EVENTS_CTX, MAX_HISTORY
from character import CLASSES, apply_delta


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
        world["world"]["progress"] = _safe_int(w["progress"], world["world"].get("progress", 0))

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

    ev = mem.get("event")
    if ev:
        push_event(world, ev.get("what", ""), ev.get("result", ""))


def build_context(world: dict) -> str:
    lines = []
    w = world["world"]
    lines.append(f"МИР: {w['setting']} | тон: {w['tone']}")
    lines.append(f"MILESTONE: {w['milestone'] or '—'} ({w['progress']}%)")
    lines.append(f"РЕЖИМ: {w['mode']}")

    c = world["character"]
    cls = CLASSES.get(c.get("cls"), {})
    lines.append(
        f"ИГРОК: {c.get('name','?')} — {cls.get('name','')}. "
        f"Описание: {c.get('personality','')}. "
        f"HP {c.get('hp',0)}/{c.get('hp_max',0)}, золото {c.get('gold',0)}, "
        f"состояние: {c.get('state','')}"
    )

    if world["npcs"]:
        lines.append("NPC:")
        for name, d in world["npcs"].items():
            lines.append(f"  • {name}: {d['char']} | отношение: {d['attitude']}")

    if world["events"]:
        lines.append("ПОСЛЕДНИЕ СОБЫТИЯ:")
        for e in world["events"][-EVENTS_CTX:]:
            lines.append(f"  • {e['what']} → {e['result']}")

    return "\n".join(lines)
