import re
import httpx
from config import YANDEX_API_KEY, YANDEX_FOLDER_ID

MAX_CHARS = 4900
TTS_URL = "https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize"


def clean_text(text: str) -> str:
    text = re.sub(r"[*_`#]", "", text)
    text = re.sub(
        r"[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F000-\U0001F2FF]",
        "",
        text,
    )
    text = re.sub(r"\s+", " ", text).strip()
    return text


async def synthesize(text: str, voice: str = "alena"):
    if not YANDEX_API_KEY or not YANDEX_FOLDER_ID:
        raise RuntimeError("YANDEX_API_KEY или YANDEX_FOLDER_ID не заданы")

    cleaned = clean_text(text)
    if not cleaned:
        raise RuntimeError("Пустой текст для озвучки")

    truncated = False
    if len(cleaned) > MAX_CHARS:
        cleaned = cleaned[:MAX_CHARS]
        truncated = True

    headers = {"Authorization": f"Api-Key {YANDEX_API_KEY}"}
    data = {
        "text": cleaned,
        "lang": "ru-RU",
        "voice": voice,
        "format": "oggopus",
        "folderId": YANDEX_FOLDER_ID,
        "speed": "1.0",
    }

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(TTS_URL, headers=headers, data=data)
        if r.status_code != 200:
            raise RuntimeError(f"SpeechKit {r.status_code}: {r.text[:200]}")
        return r.content, truncated
