import json
from openai import AsyncOpenAI
from config import GROQ_KEY, GROQ_URL, MODEL
from prompts import SYSTEM_PROMPT, context_block

_client = AsyncOpenAI(api_key=GROQ_KEY, base_url=GROQ_URL)


def _extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].lstrip()
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        text = text[start:end + 1]
    return json.loads(text)


async def ask_master(memory_text: str, history: list[dict], user_input: str) -> dict:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": context_block(memory_text)},
        *history,
        {"role": "user", "content": user_input},
    ]
    resp = await _client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=1.0,
        max_tokens=2000,
        response_format={"type": "json_object"},
    )
    return _extract_json(resp.choices[0].message.content)
