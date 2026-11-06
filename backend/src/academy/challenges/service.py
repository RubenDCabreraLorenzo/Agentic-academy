"""Challenges (US4; FR-021–FR-025, FR-022c, FR-041, FR-045b).

The API only queues work: learner code never runs on the API host (runner protocol §0). A
submission and its job are created in one transaction; the runner claims jobs through restricted
database functions.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import delete, func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from academy.challenges.files import InvalidFilesError, validate_files
from academy.challenges.models import (
    ChallengeSubmission,
    ChallengeWorkspace,
    HintUsage,
    SubmissionJob,
)
from academy.config import get_settings
from academy.content.registry import Bundle, get_registry
from academy.progress import derivation
from academy.progress.evidence import Evidence, EvidenceItem, gather, register_provider
from academy.shared.errors import ProblemError
from academy.shared.health import evaluation_available
from academy.shared.hooks import on_before_account_delete

MAX_QUEUE = 200
DELAYED_AFTER = timedelta(minutes=5)
FINAL = {"passed", "failed", "stopped", "error", "cancelled"}


def _now() -> datetime:
    return datetime.now(UTC)


def _challenge(bundle: Bundle, challenge_id: str) -> dict[str, Any]:
    ch = bundle.challenge(challenge_id)
    if ch is None:
        raise ProblemError(404, "not_found", "Challenge not found")
    return ch


def _passed(db: Session, account_id: uuid.UUID, challenge_id: str) -> bool:
    return bool(
        db.scalar(
            select(func.count())
            .select_from(ChallengeSubmission)
            .where(
                ChallengeSubmission.account_id == account_id,
                ChallengeSubmission.challenge_id == challenge_id,
                ChallengeSubmission.kind == "submission",
                ChallengeSubmission.status == "passed",
            )
        )
    )


def _hints_revealed(db: Session, account_id: uuid.UUID, challenge_id: str) -> int:
    row = db.get(HintUsage, (account_id, challenge_id))
    return row.hints_revealed if row else 0


def get_detail(db: Session, account_id: uuid.UUID, challenge_id: str) -> dict[str, Any]:
    bundle = get_registry().current()
    ch = _challenge(bundle, challenge_id)
    workspace = db.get(ChallengeWorkspace, (account_id, challenge_id))
    revealed = _hints_revealed(db, account_id, challenge_id)
    passed = _passed(db, account_id, challenge_id)
    comps = bundle.competencies
    attempts = db.scalar(
        select(func.count())
        .select_from(ChallengeSubmission)
        .where(
            ChallengeSubmission.account_id == account_id,
            ChallengeSubmission.challenge_id == challenge_id,
            ChallengeSubmission.attempt_number.is_not(None),
        )
    )
    return {
        "id": ch["id"],
        "version": ch["version"],
        "lang": ch["lang"],
        "last_reviewed": ch["last_reviewed"],
        "deprecation": ch.get("deprecation"),
        "title": ch["title"],
        "module_id": ch["module_id"],
        "difficulty_rank": ch["difficulty_rank"],
        "scenario_markdown": ch["scenario"],
        "problem_markdown": ch["problem"],
        "expected_outcome_markdown": ch["expected_outcome"],
        "instructions_markdown": ch["instructions"],
        "criteria": [
            {"id": c["id"], "description": c["description"], "mandatory": c["mandatory"]}
            for c in ch["criteria"]
        ],
        "competencies": [
            {"id": c, "title": comps[c]["title"], "level": comps[c]["level"]}
            for c in ch["competencies"]
            if c in comps
        ],
        "files": workspace.files if workspace else ch["starter_files"],
        "starter_files": ch["starter_files"],
        "tests": ch["tests"],
        "hints_revealed": ch["hints"][:revealed],
        "hints_total": len(ch["hints"]),
        "attempts": attempts or 0,
        "passed": passed,
        "reference_explanation_markdown": ch["reference_explanation"] if passed else None,
        "limits": ch["limits"],
        "evaluation_enabled": get_settings().challenges_enabled,
    }


def save_workspace(
    db: Session, account_id: uuid.UUID, challenge_id: str, files: dict[str, str]
) -> None:
    ch = _challenge(get_registry().current(), challenge_id)
    try:
        validate_files(files, ch["tests"])
    except InvalidFilesError as exc:
        status = 413 if "256 KB" in str(exc) else 400
        raise ProblemError(status, "invalid_submission_files", str(exc)) from exc
    stmt = insert(ChallengeWorkspace).values(
        account_id=account_id, challenge_id=challenge_id, files=files
    )
    db.execute(
        stmt.on_conflict_do_update(
            index_elements=["account_id", "challenge_id"],
            set_={"files": files, "updated_at": func.now()},
        )
    )


def reveal_hint(db: Session, account_id: uuid.UUID, challenge_id: str) -> dict[str, Any]:
    ch = _challenge(get_registry().current(), challenge_id)
    hints = ch["hints"]
    row = db.get(HintUsage, (account_id, challenge_id), with_for_update=True)
    if row is None:
        row = HintUsage(account_id=account_id, challenge_id=challenge_id, hints_revealed=0)
        db.add(row)
    if row.hints_revealed >= len(hints):
        raise ProblemError(409, "no_more_hints", "All hints have been revealed")
    row.hints_revealed += 1
    db.flush()
    return {
        "index": row.hints_revealed,
        "total": len(hints),
        "markdown": hints[row.hints_revealed - 1],
    }


def _queue_position(db: Session, sub: ChallengeSubmission) -> int | None:
    if sub.status != "queued":
        return None
    job = db.get(SubmissionJob, sub.id)
    if job is None:
        return None
    ahead = db.scalar(
        select(func.count())
        .select_from(SubmissionJob)
        .join(ChallengeSubmission, ChallengeSubmission.id == SubmissionJob.submission_id)
        .where(
            ChallengeSubmission.status == "queued", SubmissionJob.available_at < job.available_at
        )
    )
    return int(ahead or 0) + 1


def submission_view(db: Session, sub: ChallengeSubmission) -> dict[str, Any]:
    return {
        "submission_id": str(sub.id),
        "challenge_id": sub.challenge_id,
        "kind": sub.kind,
        "attempt_number": sub.attempt_number,
        "status": sub.status,
        "queue_position": _queue_position(db, sub),
        "delayed": sub.status == "queued" and _now() - sub.queued_at > DELAYED_AFTER,
        "stop_reason": sub.stop_reason,
        "criteria_results": sub.criteria_results or [],
        "output_excerpt": sub.output_excerpt or "",
        "files": sub.files,
        "hints_used": sub.hints_used,
        "version": sub.content_version,
        "queued_at": sub.queued_at.isoformat() if sub.queued_at else None,
        "finished_at": sub.finished_at.isoformat() if sub.finished_at else None,
    }


def _unavailable(detail: str) -> ProblemError:
    return ProblemError(
        503, "evaluation_unavailable", "Code evaluation is unavailable right now", detail
    )


def create_submission(
    db: Session,
    account_id: uuid.UUID,
    challenge_id: str,
    submission_id: uuid.UUID,
    kind: str,
    files: dict[str, str],
) -> dict[str, Any]:
    existing = db.get(ChallengeSubmission, submission_id)
    if existing is not None:  # idempotent retry of the same request
        if existing.account_id != account_id:
            raise ProblemError(409, "conflict", "Submission id already used")
        return submission_view(db, existing)
    bundle = get_registry().current()
    ch = _challenge(bundle, challenge_id)
    try:
        validate_files(files, ch["tests"])
    except InvalidFilesError as exc:
        raise ProblemError(400, "invalid_submission_files", str(exc)) from exc
    # The code is kept in the workspace whatever happens next (spec edge case), so it is
    # committed before any refusal below.
    save_workspace(db, account_id, challenge_id, files)
    db.commit()
    if not get_settings().challenges_enabled:
        raise _unavailable("Challenge evaluation is not enabled yet")
    if not evaluation_available(db):
        raise _unavailable("No evaluation worker is available; your code is saved, try again later")
    queued = db.scalar(
        select(func.count())
        .select_from(ChallengeSubmission)
        .where(ChallengeSubmission.status == "queued")
    )
    if (queued or 0) >= MAX_QUEUE:
        raise _unavailable(
            "The evaluation queue is full; your code is saved, try again in a few minutes"
        )
    active = db.scalar(
        select(func.count())
        .select_from(ChallengeSubmission)
        .where(
            ChallengeSubmission.account_id == account_id,
            ChallengeSubmission.status.in_(("queued", "running")),
        )
    )
    if active:
        raise ProblemError(429, "run_in_progress", "Wait for your current run to finish")
    sub = ChallengeSubmission(
        id=submission_id,
        account_id=account_id,
        challenge_id=challenge_id,
        module_id=ch["module_id"],
        content_version=ch["version"],
        bundle_version=bundle.version,
        kind=kind,
        files=files,
        status="queued",
        hints_used=_hints_revealed(db, account_id, challenge_id),
    )
    db.add(sub)
    db.flush()
    db.add(SubmissionJob(submission_id=submission_id, limits=ch["limits"]))
    db.flush()
    db.refresh(sub)
    return submission_view(db, sub)


def list_submissions(db: Session, account_id: uuid.UUID, challenge_id: str) -> list[dict[str, Any]]:
    subs = db.scalars(
        select(ChallengeSubmission)
        .where(
            ChallengeSubmission.account_id == account_id,
            ChallengeSubmission.challenge_id == challenge_id,
        )
        .order_by(ChallengeSubmission.queued_at.desc())
    ).all()
    return [submission_view(db, s) for s in subs]


def get_submission(db: Session, account_id: uuid.UUID, submission_id: uuid.UUID) -> dict[str, Any]:
    sub = db.get(ChallengeSubmission, submission_id)
    if sub is None or sub.account_id != account_id:
        raise ProblemError(404, "not_found", "Submission not found")
    view = submission_view(db, sub)
    if sub.status == "passed" and sub.kind == "submission":
        bundle = get_registry().current()
        ev = gather(db, account_id)
        states = derivation.competency_states(bundle.data, ev)
        ch = bundle.challenge(sub.challenge_id) or {"competencies": []}
        view["competencies_demonstrated"] = [
            c for c in ch["competencies"] if states.get(c) and states[c].status == "demonstrated"
        ]
    return view


@on_before_account_delete
def _cancel_jobs(db: Session, account_id: uuid.UUID) -> None:
    db.execute(
        update(ChallengeSubmission)
        .where(ChallengeSubmission.account_id == account_id, ChallengeSubmission.status == "queued")
        .values(status="cancelled", finished_at=_now())
    )
    db.execute(
        delete(SubmissionJob).where(
            SubmissionJob.submission_id.in_(
                select(ChallengeSubmission.id).where(ChallengeSubmission.account_id == account_id)
            )
        )
    )


@register_provider
def _evidence(db: Session, account_id: uuid.UUID, ev: Evidence) -> None:
    rows = db.execute(
        select(
            ChallengeSubmission.id,
            ChallengeSubmission.challenge_id,
            ChallengeSubmission.module_id,
            ChallengeSubmission.content_version,
            ChallengeSubmission.kind,
            ChallengeSubmission.status,
            ChallengeSubmission.finished_at,
        ).where(ChallengeSubmission.account_id == account_id)
    ).all()
    for row in rows:
        key = ("challenge", row.challenge_id)
        ev.attempted.add(key)
        ev.active_modules.add(row.module_id)
        if row.kind == "submission" and row.status == "passed" and row.finished_at is not None:
            prev = ev.passed.get(key)
            if prev is None or row.finished_at < prev.at:
                ev.passed[key] = EvidenceItem(
                    "challenge", row.challenge_id, row.content_version, str(row.id), row.finished_at
                )
