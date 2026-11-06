"""Progress routes (contracts/openapi.yaml "Progress")."""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Query, Response
from pydantic import BaseModel

from academy.auth.dependencies import CurrentLearner, Db
from academy.progress import reset, service

router = APIRouter()


class ResetBody(BaseModel):
    confirm: Literal["RESET"]


@router.get("/me/dashboard")
def dashboard(learner: CurrentLearner, db: Db) -> dict[str, Any]:
    return service.dashboard(db, learner.account.id)


@router.get("/me/competencies")
def competencies(
    learner: CurrentLearner, db: Db, path_id: str | None = Query(default=None, alias="pathId")
) -> list[dict[str, Any]]:
    return service.competency_view(db, learner.account.id, path_id)


@router.delete("/me/paths/{path_id}/progress", status_code=204)
def reset_progress(path_id: str, body: ResetBody, learner: CurrentLearner, db: Db) -> Response:
    reset.reset_path(db, learner.account.id, path_id)
    return Response(status_code=204)
