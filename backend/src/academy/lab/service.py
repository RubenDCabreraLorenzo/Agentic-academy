"""Laboratory scenarios (US5; FR-026–FR-034). Recordings are served as-is and replayed in the
browser; no model is called. Visits are recorded as exploration only and are never evidence."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, delete, func
from sqlalchemy.dialects.postgresql import UUID, insert
from sqlalchemy.orm import Mapped, Session, mapped_column

from academy.content.registry import get_registry
from academy.db.session import Base
from academy.shared.errors import ProblemError
from academy.shared.hooks import PathScope, on_reset_path


class LabVisit(Base):
    __tablename__ = "lab_visit"

    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("account.id", ondelete="CASCADE"), primary_key=True
    )
    scenario_id: Mapped[str] = mapped_column(String, primary_key=True)
    variant_id: Mapped[str] = mapped_column(String, primary_key=True)
    first_viewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_viewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


def get_scenario(
    db: Session, account_id: uuid.UUID, scenario_id: str, variant_id: str | None
) -> dict[str, Any]:
    doc = get_registry().current().lab_scenario(scenario_id)
    if doc is None:
        raise ProblemError(404, "not_found", "Laboratory scenario not found")
    variants = {v["id"] for v in doc["variants"]}
    variant = variant_id if variant_id in variants else doc["variants"][0]["id"]
    stmt = insert(LabVisit).values(
        account_id=account_id, scenario_id=scenario_id, variant_id=variant
    )
    db.execute(
        stmt.on_conflict_do_update(
            index_elements=["account_id", "scenario_id", "variant_id"],
            set_={"last_viewed_at": func.now()},
        )
    )
    return doc


@on_reset_path
def _reset(db: Session, account_id: uuid.UUID, scope: PathScope) -> None:
    db.execute(
        delete(LabVisit).where(
            LabVisit.account_id == account_id, LabVisit.scenario_id.in_(scope.lab_ids)
        )
    )
