"""Progress derivation rules (data-model §2.12, FR-036, FR-037)."""

from __future__ import annotations

from datetime import UTC, datetime

from academy.progress import derivation
from academy.progress.evidence import Evidence, EvidenceItem

T = datetime(2026, 1, 1, tzinfo=UTC)
BUNDLE = {
    "competencies": [{"id": "c1", "title": "C1", "level": "foundational"}, {"id": "c2", "title": "C2", "level": "foundational"}],
    "paths": {"p": {"id": "p", "modules": ["m1", "m2"]}},
    "modules": {
        "m1": {
            "id": "m1", "path_id": "p", "title": "M1", "competencies": ["c1"], "prerequisites": [],
            "objectives": [{"id": "o1", "statement": "S", "competencies": ["c1"]}],
            "knowledge_check_id": "k1", "challenge_ids": ["ch1"],
        },
        "m2": {
            "id": "m2", "path_id": "p", "title": "M2", "competencies": ["c2"], "prerequisites": ["c1", "m1"],
            "objectives": [{"id": "o2", "statement": "S2", "competencies": ["c2"]}],
            "knowledge_check_id": "k2", "challenge_ids": [],
        },
    },
    "knowledge_checks": {
        "k1": {"id": "k1", "module_id": "m1", "questions": [{"id": "q", "objective_id": "o1"}]},
        "k2": {"id": "k2", "module_id": "m2", "questions": [{"id": "q", "objective_id": "o2"}]},
    },
    "challenges": {"ch1": {"id": "ch1", "module_id": "m1", "competencies": ["c1"]}},
}


def item(kind: str, item_id: str) -> EvidenceItem:
    return EvidenceItem(kind, item_id, "1.0.0", "r", T)


def test_nothing_done() -> None:
    ev = Evidence()
    states = derivation.competency_states(BUNDLE, ev)
    assert states["c1"].status == "not_started"
    assert derivation.module_status(BUNDLE["modules"]["m1"], ev) == "not_started"


def test_viewing_content_is_activity_not_evidence() -> None:
    ev = Evidence(active_modules={"m1"})
    assert derivation.competency_states(BUNDLE, ev)["c1"].status == "in_progress"
    assert derivation.module_status(BUNDLE["modules"]["m1"], ev) == "in_progress"
    assert not derivation.objective_demonstrated(BUNDLE["modules"]["m1"], ev)


def test_check_demonstrates_objectives_but_not_competency_or_completion() -> None:
    ev = Evidence(passed={("knowledge_check", "k1"): item("knowledge_check", "k1")})
    ev.attempted.add(("knowledge_check", "k1"))
    m1 = BUNDLE["modules"]["m1"]
    assert derivation.objective_demonstrated(m1, ev)
    assert derivation.pending_objectives(m1, ev) == []
    assert derivation.competency_states(BUNDLE, ev)["c1"].status == "in_progress"
    assert derivation.module_status(m1, ev) == "in_progress"


def test_check_and_challenge_demonstrate_and_complete() -> None:
    ev = Evidence(
        passed={
            ("knowledge_check", "k1"): item("knowledge_check", "k1"),
            ("challenge", "ch1"): item("challenge", "ch1"),
        }
    )
    state = derivation.competency_states(BUNDLE, ev)["c1"]
    assert state.status == "demonstrated" and len(state.evidence) == 2
    assert derivation.module_status(BUNDLE["modules"]["m1"], ev) == "completed"
    assert not derivation.path_completed(BUNDLE, BUNDLE["paths"]["p"], ev)


def test_module_without_challenges_completes_with_check() -> None:
    ev = Evidence(passed={("knowledge_check", "k2"): item("knowledge_check", "k2")})
    assert derivation.module_status(BUNDLE["modules"]["m2"], ev) == "completed"


def test_missing_prerequisites() -> None:
    ev = Evidence()
    missing = derivation.missing_prerequisites(BUNDLE, BUNDLE["modules"]["m2"], ev)
    assert missing == [
        {"id": "c1", "title": "C1", "taught_in_module": "m1"},
        {"id": "m1", "title": "M1", "taught_in_module": "m1"},
    ]
