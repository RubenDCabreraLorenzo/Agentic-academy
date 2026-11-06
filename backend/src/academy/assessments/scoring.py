"""Pure scoring rules (data-model §1.6).

Each question scores 0 or 1: single choice = the correct option; multiple choice = all and only the
correct options; ordering = exact order; matching = every pair. Score = correct / total; passed ⇔
score ≥ threshold of the version the attempt started on.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


def is_correct(question: dict[str, Any], answer: dict[str, Any] | None) -> bool:
    if not isinstance(answer, dict):
        return False
    qtype = question["type"]
    if qtype in ("single_choice", "multiple_choice"):
        selected = answer.get("selected")
        if not isinstance(selected, list) or len(selected) != len(set(selected)):
            return False
        return set(selected) == set(question["correct"])
    if qtype == "ordering":
        selected = answer.get("selected")
        return isinstance(selected, list) and selected == [i["id"] for i in question["items"]]
    if qtype == "matching":
        pairs = answer.get("pairs")
        return isinstance(pairs, dict) and pairs == question["pairs"]
    return False


@dataclass(frozen=True)
class Score:
    score: float
    passed: bool
    correct: dict[str, bool]
    per_objective: dict[str, tuple[int, int]]


def score_attempt(check: dict[str, Any], answers: dict[str, Any]) -> Score:
    questions = check["questions"]
    correct = {q["id"]: is_correct(q, answers.get(q["id"])) for q in questions}
    per_objective: dict[str, tuple[int, int]] = {}
    for q in questions:
        ok, total = per_objective.get(q["objective_id"], (0, 0))
        per_objective[q["objective_id"]] = (ok + int(correct[q["id"]]), total + 1)
    value = round(sum(correct.values()) / len(questions), 3) if questions else 0.0
    return Score(value, value >= float(check["pass_threshold"]), correct, per_objective)
