"""``GET /api/v1/health``: database, content bundle and evaluation availability."""

from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from academy.config import get_settings
from academy.content.registry import ContentUnavailableError, get_registry
from academy.db.session import get_db

router = APIRouter()


class Health(BaseModel):
    database: Literal["ok", "unavailable"]
    content_bundle_version: str | None
    evaluation: Literal["available", "unavailable"]
    challenges_enabled: bool


def evaluation_available(db: Session) -> bool:
    """A runner heartbeat newer than 30 s (runner protocol §1)."""
    try:
        exists = db.execute(text("SELECT to_regclass('runner_worker') IS NOT NULL")).scalar()
        if not exists:
            return False
        return bool(
            db.execute(
                text(
                    "SELECT EXISTS (SELECT 1 FROM runner_worker "
                    "WHERE last_heartbeat_at > now() - interval '30 seconds')"
                )
            ).scalar()
        )
    except Exception:
        return False


@router.get("/health")
def health(db: Annotated[Session, Depends(get_db)]) -> Health:
    try:
        db.execute(text("SELECT 1"))
        database: Literal["ok", "unavailable"] = "ok"
    except Exception:
        database = "unavailable"
    try:
        version: str | None = get_registry().current().version
    except ContentUnavailableError:
        version = None
    available = database == "ok" and evaluation_available(db)
    return Health(
        database=database,
        content_bundle_version=version,
        evaluation="available" if available else "unavailable",
        challenges_enabled=get_settings().challenges_enabled,
    )
