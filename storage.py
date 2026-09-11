import json
import os
from config import DATA_DIR

def _path(user_id: int) -> str:
    os.makedirs(DATA_DIR, exist_ok=True)
    return os.path.join(DATA_DIR, f"{user_id}.json")

def load(user_id: int) -> dict | None:
    p = _path(user_id)
    if not os.path.exists(p):
        return None
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def save(user_id: int, world: dict):
    with open(_path(user_id), "w", encoding="utf-8") as f:
        json.dump(world, f, ensure_ascii=False, indent=2)
