from __future__ import annotations

from academy.assessments.scoring import is_correct, score_attempt

CHECK = {
    "pass_threshold": 0.7,
    "questions": [
        {"id": "s", "type": "single_choice", "objective_id": "o1", "correct": ["a"], "options": [{"id": "a"}, {"id": "b"}]},
        {"id": "m", "type": "multiple_choice", "objective_id": "o1", "correct": ["a", "b"], "options": [{"id": "a"}, {"id": "b"}, {"id": "c"}]},
        {"id": "o", "type": "ordering", "objective_id": "o2", "items": [{"id": "x"}, {"id": "y"}, {"id": "z"}]},
        {"id": "t", "type": "matching", "objective_id": "o2", "pairs": {"l1": "r1", "l2": "r2"}},
    ],
}
Q = {q["id"]: q for q in CHECK["questions"]}


def test_single_choice() -> None:
    assert is_correct(Q["s"], {"selected": ["a"]})
    assert not is_correct(Q["s"], {"selected": ["b"]})
    assert not is_correct(Q["s"], {"selected": ["a", "b"]})


def test_multiple_choice_requires_all_and_only_correct() -> None:
    assert is_correct(Q["m"], {"selected": ["b", "a"]})
    assert not is_correct(Q["m"], {"selected": ["a"]})
    assert not is_correct(Q["m"], {"selected": ["a", "b", "c"]})


def test_ordering_requires_exact_order() -> None:
    assert is_correct(Q["o"], {"selected": ["x", "y", "z"]})
    assert not is_correct(Q["o"], {"selected": ["y", "x", "z"]})


def test_matching_requires_all_pairs() -> None:
    assert is_correct(Q["t"], {"pairs": {"l1": "r1", "l2": "r2"}})
    assert not is_correct(Q["t"], {"pairs": {"l1": "r1"}})
    assert not is_correct(Q["t"], {"pairs": {"l1": "r2", "l2": "r1"}})


def test_missing_or_malformed_answers_are_incorrect() -> None:
    assert not is_correct(Q["s"], None)
    assert not is_correct(Q["s"], {"selected": "a"})
    assert not is_correct(Q["t"], {"pairs": ["l1"]})


def test_score_threshold_and_per_objective() -> None:
    answers = {"s": {"selected": ["a"]}, "m": {"selected": ["a", "b"]}, "o": {"selected": ["x", "y", "z"]}, "t": {"pairs": {}}}
    result = score_attempt(CHECK, answers)
    assert result.score == 0.75 and result.passed
    assert result.per_objective == {"o1": (2, 2), "o2": (1, 2)}
    failing = score_attempt(CHECK, {"s": {"selected": ["a"]}})
    assert failing.score == 0.25 and not failing.passed
    assert score_attempt({**CHECK, "pass_threshold": 0.75}, answers).passed  # boundary is inclusive
