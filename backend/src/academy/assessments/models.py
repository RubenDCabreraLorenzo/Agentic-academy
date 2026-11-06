"""AssessmentAttempt (data-model §2.6)."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from academy.db.session import Base

AttemptStatus = Enum("in_progress", "submitted", name="attempt_status", create_type=False)


class AssessmentAttempt(Base):
    __tablename__ = "assessment_attempt"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("account.id", ondelete="CASCADE"))
    knowledge_check_id: Mapped[str] = mapped_column(String)
    module_id: Mapped[str] = mapped_column(String)
    content_version: Mapped[str] = mapped_column(String)
    bundle_version: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(AttemptStatus, default="in_progress")
    answers: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    question_order: Mapped[list[str]] = mapped_column(JSONB)
    score: Mapped[Decimal | None] = mapped_column(Numeric(4, 3))
    passed: Mapped[bool | None] = mapped_column(Boolean)
    per_objective: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
