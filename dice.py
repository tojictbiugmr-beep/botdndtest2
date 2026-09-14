import random
import re

_DICE_RE = re.compile(r"(\d*)d(\d+)([+-]\d+)?")


def roll_d20() -> int:
    return random.randint(1, 20)


def roll_expr(expr: str) -> tuple:
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
    crit_success = (d == 20)
    crit_fail = (d == 1)

    if crit_success:
        success = True
    elif crit_fail:
        success = False
    else:
        success = total >= difficulty

    return {
        "d20": d,
        "mod": stat_mod,
        "total": total,
        "difficulty": difficulty,
        "success": success,
        "crit_success": crit_success,
        "crit_fail": crit_fail,
    }
