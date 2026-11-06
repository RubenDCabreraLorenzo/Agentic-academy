"""Reference solution (validator only; never shipped to learners)."""

import math


def apply_temperature(scores: dict[str, float], temperature: float) -> dict[str, float]:
    if temperature <= 0:
        raise ValueError("temperature must be greater than 0")
    if not scores:
        raise ValueError("scores must not be empty")
    scaled = {token: score / temperature for token, score in scores.items()}
    top = max(scaled.values())
    exps = {token: math.exp(value - top) for token, value in scaled.items()}
    total = sum(exps.values())
    return {token: value / total for token, value in exps.items()}


def most_likely(scores: dict[str, float]) -> str:
    return max(scores, key=scores.__getitem__)
