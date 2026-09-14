import json
import logging
from openai import AsyncOpenAI
from config import GROQ_KEY, GROQ_URL, MODEL
from prompts import SYSTEM_PROMPT, context_block

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
        temperature=0.8,
        max_tokens=2000,
        response_format={"type": "json_object"},
    )
    content = resp.choices[0].message.content
    finish = resp.choices[0].finish_reason
    if finish == "length":
        logging.warning("LLM hit max_tokens — ответ обрезан")
    return _extract_json(content)
