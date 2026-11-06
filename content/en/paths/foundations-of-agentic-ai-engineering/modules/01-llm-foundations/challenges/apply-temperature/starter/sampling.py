"""Convert model scores into sampling probabilities."""

import math


def apply_temperature(scores: dict[str, float], temperature: float) -> dict[str, float]:
    """Return token -> probability after scaling scores by the temperature (softmax)."""
    raise NotImplementedError("implement apply_temperature")


def most_likely(scores: dict[str, float]) -> str:
    """Return the token greedy decoding would choose."""
    raise NotImplementedError("implement most_likely")
