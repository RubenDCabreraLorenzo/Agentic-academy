"""Knowledge-check routes (contracts/openapi.yaml "Knowledge checks")."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from academy.assessments import service
from academy.auth.dependencies import CurrentLearner, Db

router = APIRouter()


class StartBody(BaseModel):
    attempt_id: uuid.UUID


class AnswerBody(BaseModel):
    selected: list[str] | None = Field(default=None, max_length=50)
    pairs: dict[str, str] | None = None

    def as_dict(self) -> dict[str, Any]:
        return self.model_dump(exclude_none=True)


class SubmitBody(BaseModel):
    confirm_unanswered: bool = False


@router.post("/knowledge-checks/{check_id}/attempts", status_code=201)
def start(check_id: str, body: StartBody, learner: CurrentLearner, db: Db) -> dict[str, Any]:
    return service.start_attempt(db, learner.account.id, check_id, body.attempt_id)


@router.get("/knowledge-checks/{check_id}/attempts/history")
def attempt_history(check_id: str, learner: CurrentLearner, db: Db) -> list[dict[str, Any]]:
    return service.history(db, learner.account.id, check_id)


@router.put("/attempts/{attempt_id}/answers/{question_id}")
def answer(
    attempt_id: uuid.UUID, question_id: str, body: AnswerBody, learner: CurrentLearner, db: Db
) -> dict[str, Any]:
    return service.save_answer(db, learner.account.id, attempt_id, question_id, body.as_dict())


@router.post("/attempts/{attempt_id}/submit")
def submit(
    attempt_id: uuid.UUID, learner: CurrentLearner, db: Db, body: SubmitBody | None = None
) -> dict[str, Any]:
    return service.submit_attempt(
        db, learner.account.id, attempt_id, (body or SubmitBody()).confirm_unanswered
    )
