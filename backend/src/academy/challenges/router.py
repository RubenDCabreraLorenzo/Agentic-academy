"""Challenge routes (contracts/openapi.yaml "Challenges")."""

from __future__ import annotations

import uuid
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Body, Response
from pydantic import BaseModel, Field

from academy.auth.dependencies import CurrentLearner, Db
from academy.challenges import service

router = APIRouter()


class SubmissionBody(BaseModel):
    submission_id: uuid.UUID
    kind: Literal["visible_run", "submission"]
    files: dict[str, str] = Field(max_length=50)


@router.get("/challenges/{challenge_id}")
def detail(challenge_id: str, learner: CurrentLearner, db: Db) -> dict[str, Any]:
    return service.get_detail(db, learner.account.id, challenge_id)


@router.put("/challenges/{challenge_id}/workspace", status_code=204)
def workspace(
    challenge_id: str,
    files: Annotated[dict[str, str], Body(max_length=50)],
    learner: CurrentLearner,
    db: Db,
) -> Response:
    service.save_workspace(db, learner.account.id, challenge_id, files)
    return Response(status_code=204)


@router.post("/challenges/{challenge_id}/hints")
def hint(challenge_id: str, learner: CurrentLearner, db: Db) -> dict[str, Any]:
    return service.reveal_hint(db, learner.account.id, challenge_id)


@router.post("/challenges/{challenge_id}/submissions", status_code=202)
def submit(
    challenge_id: str, body: SubmissionBody, learner: CurrentLearner, db: Db
) -> dict[str, Any]:
    return service.create_submission(
        db, learner.account.id, challenge_id, body.submission_id, body.kind, body.files
    )


@router.get("/challenges/{challenge_id}/submissions")
def submissions(challenge_id: str, learner: CurrentLearner, db: Db) -> list[dict[str, Any]]:
    return service.list_submissions(db, learner.account.id, challenge_id)


@router.get("/submissions/{submission_id}")
def submission(submission_id: uuid.UUID, learner: CurrentLearner, db: Db) -> dict[str, Any]:
    return service.get_submission(db, learner.account.id, submission_id)
