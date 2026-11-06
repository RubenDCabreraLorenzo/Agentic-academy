"""Challenge workspaces, hints, submissions, jobs and runner workers (data-model §2.7–2.10)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from academy.db.session import Base

SubmissionKind = Enum("visible_run", "submission", name="submission_kind", create_type=False)
SubmissionStatus = Enum(
    "queued",
    "running",
    "passed",
    "failed",
    "stopped",
    "error",
    "cancelled",
    name="submission_status",
    create_type=False,
)
StopReason = Enum(
    "timeout",
    "memory",
    "output_limit",
    "forbidden_operation",
    name="stop_reason",
    create_type=False,
)


class ChallengeWorkspace(Base):
    __tablename__ = "challenge_workspace"

    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("account.id", ondelete="CASCADE"), primary_key=True
    )
    challenge_id: Mapped[str] = mapped_column(String, primary_key=True)
    files: Mapped[dict[str, str]] = mapped_column(JSONB)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class HintUsage(Base):
    __tablename__ = "hint_usage"

    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("account.id", ondelete="CASCADE"), primary_key=True
    )
    challenge_id: Mapped[str] = mapped_column(String, primary_key=True)
    hints_revealed: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ChallengeSubmission(Base):
    __tablename__ = "challenge_submission"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("account.id", ondelete="CASCADE"))
    challenge_id: Mapped[str] = mapped_column(String)
    module_id: Mapped[str] = mapped_column(String)
    content_version: Mapped[str] = mapped_column(String)
    bundle_version: Mapped[str] = mapped_column(String)
    kind: Mapped[str] = mapped_column(SubmissionKind)
    attempt_number: Mapped[int | None] = mapped_column(Integer)
    files: Mapped[dict[str, str]] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(SubmissionStatus, default="queued")
    stop_reason: Mapped[str | None] = mapped_column(StopReason)
    criteria_results: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB)
    output_excerpt: Mapped[str | None] = mapped_column(Text)
    hints_used: Mapped[int] = mapped_column(Integer, default=0)
    queued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class SubmissionJob(Base):
    __tablename__ = "submission_job"

    submission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("challenge_submission.id", ondelete="CASCADE"),
        primary_key=True,
    )
    available_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    worker_id: Mapped[str | None] = mapped_column(String)
    lease_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    infra_attempts: Mapped[int] = mapped_column(Integer, default=0)
    limits: Mapped[dict[str, Any]] = mapped_column(JSONB)


class RunnerWorker(Base):
    __tablename__ = "runner_worker"

    worker_id: Mapped[str] = mapped_column(String, primary_key=True)
    capacity: Mapped[int] = mapped_column(Integer)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_heartbeat_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
