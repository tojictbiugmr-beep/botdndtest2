import os

BOT_TOKEN   = os.getenv("BOT_TOKEN")
GROQ_KEY    = os.getenv("GROQ_API_KEY")
GROQ_URL    = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
MODEL       = os.getenv("MODEL", "groq/compound-mini")
DATA_DIR    = os.getenv("DATA_DIR", "data")

MAX_EVENTS   = 20      # активных событий
EVENTS_CTX   = 5       # сколько отдаём в LLM
MAX_HISTORY  = 10      # сообщений истории в контексте
