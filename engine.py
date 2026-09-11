import json
from llm import ask_master
from memory import build_context, apply_memory, push_history
from dice import resolve

async def process_action(world: dict, user_input: str) -> dict:
    """
    Возвращает:
      {"type": "text", "text": "..."}                        — обычный ответ
      {"type": "check", "text": "...", "check": {...}}       — нужен бросок
    """
    ctx = build_context(world)
    data = await ask_master(ctx, world["history"], user_input)

    narrative = data.get("narrative", "").strip() or "..."
    memory = data.get("memory") or {}
    check = data.get("check")

    push_history(world, "user", user_input)
    push_history(world, "assistant", json.dumps(data, ensure_ascii=False))

    if check:
        # сохраняем отложенную проверку
        world["pending"] = {"check": check, "memory": memory, "narrative": narrative}
        return {"type": "check", "text": narrative, "check": check}

    # обычный ход — сразу применяем память
    apply_memory(world, memory)
    return {"type": "text", "text": narrative}


def resolve_check(world: dict, d20_data: dict) -> dict:
    """
    Игрок нажал «бросить». Применяем память и выбираем ветку success/fail.
    """
    pending = world.get("pending")
    if not pending:
        return {"type": "text", "text": "Нечего бросать."}

    check = pending["check"]
    stat = check.get("stat", "DEX")
    diff = int(check.get("difficulty", 12))
    mod = int(world["character"]["stats"].get(stat, 0))

    roll = resolve(mod, diff)
    branch = check.get("success" if roll["success"] else "fail", "")
    result_text = f"{pending['narrative']}\n\n🎲 {stat}: d20={roll['d20']} + {mod} = {roll['total']} vs {diff} → {'УСПЕХ' if roll['success'] else 'ПРОВАЛ'}\n\n{branch}"

    apply_memory(world, pending["memory"])
    # фиксируем факт броска в истории как ход игрока
    push_history(world, "user", f"[бросок {stat}: {roll['total']} vs {diff} — {'успех' if roll['success'] else 'провал'}]")

    world["pending"] = None
    return {"type": "text", "text": result_text, "roll": roll}
