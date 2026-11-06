"""Content views and the derived last position (data-model §2.4–2.5)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, func, select
from sqlalchemy.dialects.postgresql import UUID, insert
from sqlalchemy.orm import Mapped, Session, mapped_column

from academy.db.session import Base

ContentType = Enum("module", "lesson", name="content_type", create_type=False)


class ContentView(Base):
    __tablename__ = "content_view"

    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("account.id", ondelete="CASCADE"), primary_key=True
    )
    content_type: Mapped[str] = mapped_column(ContentType, primary_key=True)
    content_id: Mapped[str] = mapped_column(String, primary_key=True)
    content_version: Mapped[str] = mapped_column(String)
    path_id: Mapped[str] = mapped_column(String)
    module_id: Mapped[str] = mapped_column(String)
    first_viewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_viewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


def record_view(
    db: Session,
    account_id: uuid.UUID,
    content_type: str,
    content_id: str,
    version: str,
    path_id: str,
    module_id: str,
) -> None:
    stmt = insert(ContentView).values(
        account_id=account_id,
        content_type=content_type,
        content_id=content_id,
        content_version=version,
        path_id=path_id,
        module_id=module_id,
    )
    db.execute(
        stmt.on_conflict_do_update(
            index_elements=["account_id", "content_type", "content_id"],
            set_={"last_viewed_at": func.now(), "content_version": version},
        )
    )


def viewed_modules(db: Session, account_id: uuid.UUID) -> set[str]:
    return set(db.scalars(select(ContentView.module_id).where(ContentView.account_id == account_id)))


@dataclass(frozen=True)
class Position:
    path_id: str
    module_id: str
    lesson_id: str | None
    updated_at: datetime


def last_position(db: Session, account_id: uuid.UUID) -> Position | None:
    """Most recent activity wins (multi-device edge case)."""
    row = db.execute(
        select(ContentView)
        .where(ContentView.account_id == account_id)
        .order_by(ContentView.last_viewed_at.desc(), ContentView.content_type.desc())
        .limit(1)
    ).scalar_one_or_none()
    if row is None:
        return None
    lesson = row.content_id if row.content_type == "lesson" else None
    return Position(row.path_id, row.module_id, lesson, row.last_viewed_at)
