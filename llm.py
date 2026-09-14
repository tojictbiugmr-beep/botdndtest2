import json
import logging
from openai import AsyncOpenAI
from config import GROQ_KEY, GROQ_URL, MODEL
from prompts import SYSTEM_PROMPT, context_block, CHECK_RESULT_PROMPT

_client = AsyncOpenAI(api_key=GROQ_KEY, base_url=GROQ_URL)


def _extract_json(text: str) -> dict:
    if not text:
        return {}
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].lstrip()
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        text = text[start:end + 1]
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        logging.warning("Bad JSON from LLM: %s", text[:300])
        return {}


async def ask_master(memory_text: str, history: list, user_input: str) -> dict:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": context_block(memory_text)},
        *history,
        {"role": "user", "content": user_input},
    ]
    resp = await _client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.95,
        max_tokens=1500,
        response_format={"type": "json_object"},
    )
    content = resp.choices[0].message.content
    finish = resp.choices[0].finish_reason
    if finish == "length":
        logging.warning("LLM hit max_tokens — ответ обрезан")
    return _extract_json(content)


async def ask_check_result(check: dict, roll: dict, verdict: str, ctx: str) -> dict:
    """Второй запрос — сцена после крита или сюжетной проверки.
    Возвращает полный dict, как ask_master."""
    prompt = CHECK_RESULT_PROMPT.format(
        reason=check.get("reason", "рискованное действие"),
        stat=check.get("stat", "DEX"),
        difficulty=roll.get("difficulty", 12),
        d20=roll.get("d20", 0),
        mod=roll.get("mod", 0),
        total=roll.get("total", 0),
        verdict=verdict,
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": context_block(ctx)},
        {"role": "user", "content": prompt},
    ]

    resp = await _client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=1,
        max_tokens=1500,
        response_format={"type": "json_object"},
    )
    return _extract_json(resp.choices[0].message.content)
