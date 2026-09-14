import json
from llm import ask_master
from memory import (
    build_context,
    apply_memory,
    push_history,
    clear_recent_actions,
)
from dice import resolve
from combat import start_combat


def _safe_int(value, default: int = 0) -> int:
    try:
        return int(float(str(value).replace("%", "").strip()))
    except (ValueError, TypeError):
        return default


async def process_action(world: dict, user_input: str) -> dict:
    ctx = build_context(world)
    data = await ask_master(ctx, world["history"], user_input)

    print("LLM RAW:", json.dumps(data, ensure_ascii=False)[:1000])

    narrative = data.get("narrative", "").strip() or "..."
    memory = data.get("memory") or {}
    check = data.get("check")
    start_c = data.get("start_combat")

    push_history(world, "user", user_input)

    short = {"narrative": narrative, "memory": memory}
    push_history(world, "assistant", json.dumps(short, ensure_ascii=False))

    if check:
        world["pending"] = {"check": check, "memory": memory, "narrative": narrative}
        clear_recent_actions(world)
        return {"type": "check", "text": narrative, "check": check}

    apply_memory(world, memory)

    if start_c and start_c.get("enemies"):
        start_combat(world, start_c["enemies"])
        clear_recent_actions(world)
        return {"type": "combat", "text": narrative}

    clear_recent_actions(world)
    return {"type": "text", "text": narrative}


def resolve_check(world: dict) -> dict:
    pending = world.get("pending")
    if not pending:
        return {"type": "text", "text": "Нечего бросать."}

    check = pending["check"]
    stat = check.get("stat", "DEX")
    diff = _safe_int(check.get("difficulty", 12), 12)
    mod = _safe_int(world["character"]["stats"].get(stat, 0), 0)

    roll = resolve(mod, diff)

    if roll.get("crit_success"):
        verdict = "КРИТ. УСПЕХ"
    elif roll.get("crit_fail"):
        verdict = "КРИТ. ПРОВАЛ"
    elif roll["success"]:
        verdict = "УСПЕХ"
    else:
        verdict = "ПРОВАЛ"

    branch_raw = check.get("success" if roll["success"] else "fail")
    if not branch_raw or isinstance(branch_raw, bool):
        branch = (
            "Тебе удаётся сделать задуманное."
            if roll["success"]
            else "Что-то идёт не так — последствия могут быть тяжёлыми."
        )
    else:
        branch = str(branch_raw).strip()

    result_text = (
        f"🎲 {stat}: d20={roll['d20']} + {mod} = {roll['total']} vs {diff} "
        f"→ {verdict}\n\n{branch}"
    )

    apply_memory(world, pending["memory"])

    # Пишем результат броска в историю как ответ мастера,
    # чтобы LLM на следующем ходу видела, что именно было сказано
    push_history(world, "assistant", result_text)

    world["pending"] = None
    return {"type": "text", "text": result_text, "roll": roll}
