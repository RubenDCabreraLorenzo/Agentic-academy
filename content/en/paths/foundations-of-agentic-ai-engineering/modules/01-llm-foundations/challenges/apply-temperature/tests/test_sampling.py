import math

import pytest

from sampling import apply_temperature, most_likely

SCORES = {"refund": 2.0, "replacement": 1.0, "apology": 0.5}


def test_probabilities_sum_to_one():
    probs = apply_temperature(SCORES, 1.0)
    assert set(probs) == set(SCORES)
    assert math.isclose(sum(probs.values()), 1.0, rel_tol=1e-9)
    assert all(0 < p < 1 for p in probs.values())


def test_lower_temperature_sharpens():
    cold = apply_temperature(SCORES, 0.2)["refund"]
    normal = apply_temperature(SCORES, 1.0)["refund"]
    hot = apply_temperature(SCORES, 5.0)["refund"]
    assert cold > normal > hot
    assert cold > 0.99


@pytest.mark.parametrize("temperature", [0, -1.0])
def test_invalid_temperature_rejected(temperature):
    with pytest.raises(ValueError):
        apply_temperature(SCORES, temperature)
    with pytest.raises(ValueError):
        apply_temperature({}, 1.0)


def test_large_scores_do_not_overflow():
    probs = apply_temperature({"a": 1000.0, "b": 999.0}, 0.5)
    assert math.isclose(sum(probs.values()), 1.0)
    assert probs["a"] > probs["b"]


def test_most_likely_is_greedy_choice():
    assert most_likely(SCORES) == "refund"
