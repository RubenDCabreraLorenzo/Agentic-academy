"""Knowledge-check attempts (US2; FR-016–FR-019, FR-041, FR-051).

An attempt is pinned to the bundle version current when it started; it is scored with that
version even if newer content is published meanwhile. Once a question has received feedback its
answer is locked; learners improve by starting a new attempt (unlimited retries, best score kept).
"""

from __future__ import annotations

import random
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from academy.assessments.models import AssessmentAttempt
from academy.assessments.scoring import is_correct, score_attempt
from academy.content.registry import Bundle, get_registry
from academy.progress import derivation
from academy.progress.evidence import Evidence, EvidenceItem, gather, register_provider
from academy.shared.errors import ProblemError


def _now() -> datetime:
    return datetime.now(UTC)


def _lesson_link(module_id: str, anchor: str) -> dict[str, str]:
    lesson_id, _, frag = anchor.partition("#")
    return {"module_id": module_id, "lesson_id": lesson_id, "anchor": frag}


def _bundle_and_check(attempt: AssessmentAttempt) -> tuple[Bundle, dict[str, Any]]:
    bundle = get_registry().get(attempt.bundle_version)
    check = bundle.knowledge_check(attempt.knowledge_check_id)
    if check is None:  # pragma: no cover - bundles are immutable
        raise ProblemError(500, "content_missing", "Knowledge check version is not available")
    return bundle, check


def _present_question(q: dict[str, Any], rng: random.Random) -> dict[str, Any]:
    out: dict[str, Any] = {"id": q["id"], "type": q["type"], "prompt_markdown": q["prompt"]}
    if q["type"] in ("single_choice", "multiple_choice"):
        out["options"] = [{"id": o["id"], "text": o["text"]} for o in q["options"]]
    elif q["type"] == "ordering":
        items = [{"id": i["id"], "text": i["text"]} for i in q["items"]]
        shuffled = items[:]
        for _ in range(10):
            rng.shuffle(shuffled)
            if shuffled != items:
                break
        out["items"] = shuffled
    elif q["type"] == "matching":
        out["left"] = [{"id": i["id"], "text": i["text"]} for i in q["left"]]
        right = [{"id": i["id"], "text": i["text"]} for i in q["right"]]
        rng.shuffle(right)
        out["right"] = right
    return out


def _attempt_view(attempt: AssessmentAttempt) -> dict[str, Any]:
    bundle, check = _bundle_and_check(attempt)
    module = bundle.module(check["module_id"]) or {"objectives": []}
    by_id = {q["id"]: q for q in check["questions"]}
    rng = random.Random(str(attempt.id))  # noqa: S311 - presentation shuffle, not security
    assessed = {q["objective_id"] for q in check["questions"]}
    return {
        "attempt_id": str(attempt.id),
        "knowledge_check_id": attempt.knowledge_check_id,
        "module_id": check["module_id"],
        "version": attempt.content_version,
        "status": attempt.status,
        "pass_threshold": check["pass_threshold"],
        "objectives": [o["statement"] for o in module["objectives"] if o["id"] in assessed],
        "questions": [_present_question(by_id[qid], rng) for qid in attempt.question_order],
        "saved_answers": attempt.answers,
        "feedback": {qid: _feedback(check, by_id[qid], a) for qid, a in attempt.answers.items()},
    }


def _feedback(check: dict[str, Any], q: dict[str, Any], answer: dict[str, Any]) -> dict[str, Any]:
    return {
        "correct": is_correct(q, answer),
        "explanation_markdown": q["explanation"],
        "lesson_link": _lesson_link(check["module_id"], q["lesson_anchor"]),
    }


def _get_owned(
    db: Session, account_id: uuid.UUID, attempt_id: uuid.UUID, lock: bool = False
) -> AssessmentAttempt:
    stmt = select(AssessmentAttempt).where(
        AssessmentAttempt.id == attempt_id, AssessmentAttempt.account_id == account_id
    )
    if lock:
        stmt = stmt.with_for_update()
    attempt = db.scalar(stmt)
    if attempt is None:
        raise ProblemError(404, "not_found", "Attempt not found")
    return attempt


def start_attempt(
    db: Session, account_id: uuid.UUID, check_id: str, attempt_id: uuid.UUID
) -> dict[str, Any]:
    existing = db.scalar(
        select(AssessmentAttempt).where(
            AssessmentAttempt.account_id == account_id,
            AssessmentAttempt.knowledge_check_id == check_id,
            AssessmentAttempt.status == "in_progress",
        )
    )
    if existing is not None:
        return _attempt_view(existing)
    same_id = db.get(AssessmentAttempt, attempt_id)
    if same_id is not None:
        if same_id.account_id != account_id:
            raise ProblemError(409, "conflict", "Attempt id already used")
        return _attempt_view(same_id)
    bundle = get_registry().current()
    check = bundle.knowledge_check(check_id)
    if check is None:
        raise ProblemError(404, "not_found", "Knowledge check not found")
    order = [q["id"] for q in check["questions"]]
    random.Random(str(attempt_id)).shuffle(order)  # noqa: S311 - presentation shuffle
    attempt = AssessmentAttempt(
        id=attempt_id,
        account_id=account_id,
        knowledge_check_id=check_id,
        module_id=check["module_id"],
        content_version=check["version"],
        bundle_version=bundle.version,
        status="in_progress",
        answers={},
        question_order=order,
    )
    db.add(attempt)
    try:
        db.flush()
    except IntegrityError as exc:  # concurrent start from another tab
        db.rollback()
        raise ProblemError(
            409, "conflict", "An attempt is already in progress; reload to resume"
        ) from exc
    return _attempt_view(attempt)


def save_answer(
    db: Session,
    account_id: uuid.UUID,
    attempt_id: uuid.UUID,
    question_id: str,
    answer: dict[str, Any],
) -> dict[str, Any]:
    attempt = _get_owned(db, account_id, attempt_id, lock=True)
    if attempt.status != "in_progress":
        raise ProblemError(409, "attempt_submitted", "This attempt has already been submitted")
    _bundle, check = _bundle_and_check(attempt)
    question = next((q for q in check["questions"] if q["id"] == question_id), None)
    if question is None:
        raise ProblemError(404, "not_found", "Question not found")
    if question_id in attempt.answers:
        if attempt.answers[question_id] == answer:  # idempotent replay of the same answer
            return _feedback(check, question, answer)
        raise ProblemError(
            409, "already_answered", "This question was already answered in this attempt"
        )
    attempt.answers = {**attempt.answers, question_id: answer}
    return _feedback(check, question, answer)


def _best_score(db: Session, account_id: uuid.UUID, check_id: str) -> float | None:
    scores = db.scalars(
        select(AssessmentAttempt.score).where(
            AssessmentAttempt.account_id == account_id,
            AssessmentAttempt.knowledge_check_id == check_id,
            AssessmentAttempt.status == "submitted",
        )
    ).all()
    values = [float(s) for s in scores if s is not None]
    return max(values) if values else None


def _result(db: Session, attempt: AssessmentAttempt) -> dict[str, Any]:
    bundle, check = _bundle_and_check(attempt)
    module = bundle.module(check["module_id"]) or {"objectives": [], "competencies": []}
    by_q = {q["id"]: q for q in check["questions"]}
    per = attempt.per_objective or {}
    threshold = float(check["pass_threshold"])
    weak = []
    for obj in module["objectives"]:
        ok, total = per.get(obj["id"], [0, 0])
        if total and ok / total < threshold:
            first = next(q for q in check["questions"] if q["objective_id"] == obj["id"])
            weak.append(
                {
                    "id": obj["id"],
                    "statement": obj["statement"],
                    "lesson_link": _lesson_link(check["module_id"], first["lesson_anchor"]),
                }
            )
    current = get_registry().current()
    ev = gather(db, attempt.account_id)
    states = derivation.competency_states(current.data, ev)
    return {
        "attempt_id": str(attempt.id),
        "version": attempt.content_version,
        "submitted_at": attempt.submitted_at.isoformat() if attempt.submitted_at else None,
        "score": float(attempt.score or 0),
        "passed": bool(attempt.passed),
        "best_score": _best_score(db, attempt.account_id, attempt.knowledge_check_id),
        "questions": [
            {"question_id": qid, **_feedback(check, by_q[qid], attempt.answers.get(qid, {}))}
            for qid in attempt.question_order
        ],
        "weak_objectives": weak,
        "objectives_demonstrated": [o["id"] for o in module["objectives"]]
        if attempt.passed
        else [],
        "competencies_demonstrated": [
            c
            for c in module["competencies"]
            if states.get(c) and states[c].status == "demonstrated"
        ],
    }


def submit_attempt(
    db: Session, account_id: uuid.UUID, attempt_id: uuid.UUID, confirm_unanswered: bool
) -> dict[str, Any]:
    attempt = _get_owned(db, account_id, attempt_id, lock=True)
    if attempt.status == "submitted":
        return _result(db, attempt)
    _bundle, check = _bundle_and_check(attempt)
    missing = [q["id"] for q in check["questions"] if q["id"] not in attempt.answers]
    if missing and not confirm_unanswered:
        raise ProblemError(
            422,
            "unanswered_questions",
            "Some questions are unanswered",
            extra={"unanswered": missing},
        )
    result = score_attempt(check, attempt.answers)
    attempt.status = "submitted"
    attempt.score = Decimal(str(result.score))
    attempt.passed = result.passed
    attempt.per_objective = {k: list(v) for k, v in result.per_objective.items()}
    attempt.submitted_at = _now()
    db.flush()
    return _result(db, attempt)


def history(db: Session, account_id: uuid.UUID, check_id: str) -> list[dict[str, Any]]:
    attempts = db.scalars(
        select(AssessmentAttempt)
        .where(
            AssessmentAttempt.account_id == account_id,
            AssessmentAttempt.knowledge_check_id == check_id,
            AssessmentAttempt.status == "submitted",
        )
        .order_by(AssessmentAttempt.submitted_at.desc())
    ).all()
    return [_result(db, a) for a in attempts]


@register_provider
def _evidence(db: Session, account_id: uuid.UUID, ev: Evidence) -> None:
    rows = db.execute(
        select(
            AssessmentAttempt.id,
            AssessmentAttempt.knowledge_check_id,
            AssessmentAttempt.module_id,
            AssessmentAttempt.content_version,
            AssessmentAttempt.passed,
            AssessmentAttempt.submitted_at,
            AssessmentAttempt.started_at,
        ).where(AssessmentAttempt.account_id == account_id)
    ).all()
    for row in rows:
        key = ("knowledge_check", row.knowledge_check_id)
        ev.attempted.add(key)
        ev.active_modules.add(row.module_id)
        if row.passed and row.submitted_at is not None:
            prev = ev.passed.get(key)
            if prev is None or row.submitted_at < prev.at:
                ev.passed[key] = EvidenceItem(
                    "knowledge_check",
                    row.knowledge_check_id,
                    row.content_version,
                    str(row.id),
                    row.submitted_at,
                )
