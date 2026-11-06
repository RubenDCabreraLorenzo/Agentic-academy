"""Catalog and content routes (contracts/openapi.yaml "Catalog & content")."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from academy.auth.dependencies import CurrentLearner, Db, OptionalLearner
from academy.catalog import service

router = APIRouter()


@router.get("/catalog")
def catalog() -> list[dict[str, Any]]:
    return service.list_catalog()


@router.get("/paths/{path_id}")
def path_detail(path_id: str, db: Db, learner: OptionalLearner) -> dict[str, Any]:
    return service.get_path(path_id, db, learner.account.id if learner else None)


@router.get("/modules/{module_id}")
def module_detail(
    module_id: str,
    db: Db,
    learner: CurrentLearner,
    lesson: str | None = Query(default=None, max_length=80),
) -> dict[str, Any]:
    return service.get_module(module_id, db, learner.account.id, lesson)
