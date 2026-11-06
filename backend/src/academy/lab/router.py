"""Laboratory routes (contracts/openapi.yaml "Laboratory")."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from academy.auth.dependencies import CurrentLearner, Db
from academy.lab import service

router = APIRouter()


@router.get("/lab/scenarios/{scenario_id}")
def scenario(
    scenario_id: str,
    learner: CurrentLearner,
    db: Db,
    variant: str | None = Query(default=None, max_length=80),
) -> dict[str, Any]:
    return service.get_scenario(db, learner.account.id, scenario_id, variant)
