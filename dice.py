import random

def roll_d20() -> int:
    return random.randint(1, 20)

def resolve(stat_mod: int, difficulty: int) -> dict:
    d = roll_d20()
    total = d + stat_mod
    return {
        "d20": d,
        "mod": stat_mod,
        "total": total,
        "difficulty": difficulty,
        "success": total >= difficulty,
    }
