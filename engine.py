import json
import re
from llm import ask_master
from memory import build_context, apply_memory, push_history
from dice import resolve
from combat import start_combat


CHECK_WORDS = re.compile(
    r"(брос|проверк|d20|кубик|испытани|сложност)",
    re.IGNORECASE,
)

COMBAT_WORDS = re.compile(
    r"\b(атак|удар|бьёт|бьют|ранит|кров|меча|клинк|стрел|кинжал|замах"
    r"|бросился|напал|схватк|драк|выстрел|попал|промах)\w*",
    re.IGNORECASE,
)


async def process_action(world: dict, user_input: str) -> dict:
    ctx = build_context(world)
    data = await ask_master(ctx, world["history"], user_input)

    print("LLM RAW:", json.dumps(data, ensure_ascii=False)[:1000])

    narrative = data.get("narrative", "").strip() or "..."
    memory = data.get("memory") or {}
    check = data.get("check")
    start_c = data.get("start_combat")

    push_history(world, "user", user_input)
    push_history(world, "assistant", json.dumps(data, ensure_ascii=False))

    # 1) Проверка от LLM
    if check:
        world["pending"] = {"check": check, "memory": memory, "narrative": narrative}
        return {"type": "check", "text": narrative, "check": check}

    apply_memory(world, memory)

    # 2) Бой от LLM
    if start_c and start_c.get("enemies"):
        start_combat(world, start_c["enemies"])
        return {"type": "combat", "text": narrative}

    # 3) ФОЛБЭК: LLM просит бросок в тексте, но забыл check
    if CHECK_WORDS.search(narrative) and not world.get("combat", {}).get("active"):
        fallback_check = {
            "stat": "DEX",
            "difficulty": 12,
            "reason": "авто",
            "success": "Ты справляешься.",
            "fail": "Что-то идёт не так.",
        }
        world["pending"] = {
            "check": fallback_check,
            "memory": memory,
            "narrative": narrative,
        }
        print("FALLBACK CHECK triggered")
        return {"type": "check", "text": narrative, "check": fallback_check}

    # 4) ФОЛБЭК: LLM описывает бой в тексте, но забыл start_combat
    if COMBAT_WORDS.search(narrative) and not world.get("combat", {}).get("active"):
        fallback_enemies = [
            {"name": "Враг", "hp": 8, "defense": 11,
             "attack_stat": 1, "damage": "1d4"}
        ]
        start_combat(world, fallback_enemies)
        print("FALLBACK COMBAT triggered")
        return {"type": "combat", "text": narrative}

    return {"type": "text", "text": narrative}


def resolve_check(world: dict, d20_data: dict) -> dict:
    pending = world.get("pending")
    if not pending:
        return {"type": "text", "text": "Нечего бросать."}

    check = pending["check"]
    stat = check.get("stat", "DEX")
    try:
    diff = int(str(check.get("difficulty", 12)).replace("%", "").strip())
except (ValueError, TypeError):
    diff = 12
    mod = int(world["character"]["stats"].get(stat, 0))

    roll = resolve(mod, diff)
    branch = check.get("success" if roll["success"] else "fail", "")

    result_text = (
        f"🎲 {stat}: d20={roll['d20']} + {mod} = {roll['total']} vs {diff} "
        f"→ {'УСПЕХ' if roll['success'] else 'ПРОВАЛ'}\n\n{branch}"
    )

    apply_memory(world, pending["memory"])
    push_history(
        world, "user",
        f"[бросок {stat}: {roll['total']} vs {diff} — "
        f"{'успех' if roll['success'] else 'провал'}]"
    )

    world["pending"] = None
    return {"type": "text", "text": result_text, "roll": roll}
