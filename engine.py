import json
import logging
import re
from llm import ask_master, ask_check_result
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


def _get_prev_narratives(history: list, n: int = 3) -> list:
    """Достаёт narrative из последних n ответов ассистента."""
    prev = []
    for h in history:
        if h.get("role") != "assistant":
            continue
        content = h.get("content", "")
        try:
            d = json.loads(content)
            txt = d.get("narrative", "")
        except Exception:
            txt = content
        if txt:
            prev.append(txt)
    return prev[-n:]


def _anti_repeat(text: str, history: list) -> str:
    """Срезает предложения, дублирующие прошлые ответы. Сохраняет абзацы."""
    if not text or not history:
        return text

    # Литеральные \n → настоящие переносы (модель иногда так возвращает)
    text = text.replace("\\r\\n", "\n").replace("\\n", "\n").replace("\\r", "\n")

    prev = _get_prev_narratives(history, n=3)
    if not prev:
        return text

    paragraphs = text.split("\n\n")
    out_paras = []

    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        sents = re.split(r'(?<=[.!?…])\s+', p)
        kept = []
        for s in sents:
            s = s.strip()
            if not s:
                continue
            if len(s) > 30:
                head = s[:40].lower()
                if any(head in pv.lower() for pv in prev):
                    continue
            kept.append(s)
        if kept:
            out_paras.append(" ".join(kept))
        else:
            # Если все предложения абзаца — дубли, оставляем его целиком
            out_paras.append(p)

    if not out_paras:
        return text

    return "\n\n".join(out_paras)


def _update_epilogue(world: dict):
    """Обновляет счётчик эпилога. Вызывается один раз за ход."""
    w = world["world"]
    if w.get("final_reached"):
        return
    if w.get("boss_defeated") and w.get("epilogue_turns", 0) == 0:
        w["epilogue_turns"] = 5
        return
    if w.get("epilogue_turns", 0) > 0:
        w["epilogue_turns"] -= 1
        if w["epilogue_turns"] == 0:
            w["final_reached"] = True


async def process_action(world: dict, user_input: str) -> dict:
    ctx = build_context(world)
    data = await ask_master(ctx, world["history"], user_input)

    print("LLM RAW:", json.dumps(data, ensure_ascii=False)[:1000])

    narrative_raw = data.get("narrative", "").strip()
    memory = data.get("memory") or {}
    check = data.get("check")
    start_c = data.get("start_combat")

    # При check narrative пустая — не подставляем "..."
    narrative = narrative_raw or ("" if check else "...")

    # Анти-повтор: срезаем дубли из прошлых ответов + сохраняем абзацы
    if narrative:
        narrative = _anti_repeat(narrative, world["history"])

    push_history(world, "user", user_input)

    if narrative:
        short = {"narrative": narrative, "memory": memory}
        push_history(world, "assistant", json.dumps(short, ensure_ascii=False))

    if check:
        stat = check.get("stat", "DEX")
        diff = _safe_int(check.get("difficulty", 12), 12)
        header = f"🎲 Требуется проверка: {stat} (сл. {diff})"
        world["pending"] = {"check": check, "memory": memory, "narrative": ""}
        clear_recent_actions(world)
        return {"type": "check", "text": header, "check": check}

    apply_memory(world, memory)
    _update_epilogue(world)

    if start_c and start_c.get("enemies"):
        start_combat(world, start_c["enemies"])
        clear_recent_actions(world)
        return {"type": "combat", "text": narrative}

    clear_recent_actions(world)
    return {"type": "text", "text": narrative}


async def resolve_check(world: dict) -> dict:
    pending = world.get("pending")
    if not pending:
        return {"type": "text", "text": "Нечего бросать."}

    check = pending["check"]
    stat = check.get("stat", "DEX")
    diff = _safe_int(check.get("difficulty", 12), 12)
    mod = _safe_int(world["character"]["stats"].get(stat, 0), 0)

    roll = resolve(mod, diff)

    roll["difficulty"] = diff
    roll["mod"] = mod

    crit_success = roll.get("crit_success", False)
    crit_fail = roll.get("crit_fail", False)

    if crit_success:
        verdict = "КРИТ. УСПЕХ"
    elif crit_fail:
        verdict = "КРИТ. ПРОВАЛ"
    elif roll["success"]:
        verdict = "УСПЕХ"
    else:
        verdict = "ПРОВАЛ"

    roll_line = (
        f"🎲 {stat}: d20={roll['d20']} + {mod} = {roll['total']} vs {diff} "
        f"→ {verdict}"
    )

    apply_memory(world, pending["memory"])

    # ВСЕГДА полная сцена после броска
    ctx = build_context(world)
    try:
        data = await ask_check_result(check, roll, verdict, ctx)
    except Exception:
        logging.exception("check result LLM error")
        data = None

    if data:
        narrative = data.get("narrative", "").strip() or "..."
        narrative = _anti_repeat(narrative, world["history"])

        memory = data.get("memory") or {}
        new_check = data.get("check")
        new_combat = data.get("start_combat")

        apply_memory(world, memory)
        _update_epilogue(world)

        result_text = f"{roll_line}\n\n{narrative}"
        push_history(world, "assistant", result_text)
        world["pending"] = None

        if new_check:
            world["pending"] = {
                "check": new_check,
                "memory": {},
                "narrative": "",
            }
            return {"type": "check", "text": result_text, "check": new_check}

        if new_combat and new_combat.get("enemies"):
            start_combat(world, new_combat["enemies"])
            return {"type": "combat", "text": result_text}

        return {"type": "text", "text": result_text, "roll": roll}

    # Fallback, если второй запрос упал
    branch_raw = check.get("success" if roll["success"] else "fail")
    branch = str(branch_raw).strip() if branch_raw else (
        "Тебе удаётся сделать задуманное."
        if roll["success"]
        else "Что-то идёт не так — последствия могут быть тяжёлыми."
    )
    result_text = f"{roll_line}\n\n{branch}"

    push_history(world, "assistant", result_text)
    world["pending"] = None
    return {"type": "text", "text": result_text, "roll": roll}
