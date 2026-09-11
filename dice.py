import random
import re

_DICE_RE = re.compile(r"(\d*)d(\d+)([+-]\d+)?")

def roll_d20() -> int:
    return random.randint(1, 20)

def roll_expr(expr: str) -> tuple[int, list[int]]:
    """'2d6+3' → (сумма, броски)."""
    m = _DICE_RE.fullmatch(expr.strip().lower())
    if not m:
        return 0, []
    n = int(m.group(1) or 1)
    d = int(m.group(2))
    mod = int(m.group(3) or 0)
    rolls = [random.randint(1, d) for _ in range(n)]
    return sum(rolls) + mod, rolls

def resolve(stat_mod: int, difficulty: int) -> dict:
    d = roll_d20()
    total = d + stat_mod
    return {
        "d20": d, "mod": stat_mod, "total": total,
        "difficulty": difficulty,
        "success": total >= difficulty,
    }
