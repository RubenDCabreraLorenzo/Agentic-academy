"""FastAPI dependencies for the current learner."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session as DbSession

from academy.auth.models import Account, Session
from academy.auth.sessions import SESSION_COOKIE, resolve_session
from academy.db.session import get_db
from academy.shared.errors import ProblemError


@dataclass(frozen=True)
class Learner:
    account: Account
    session: Session

    @property
    def id(self):  # type: ignore[no-untyped-def]
        return self.account.id


def optional_learner(request: Request, db: Annotated[DbSession, Depends(get_db)]) -> Learner | None:
    resolved = resolve_session(db, request.cookies.get(SESSION_COOKIE))
    if resolved is None:
        return None
    session, account = resolved
    return Learner(account=account, session=session)


def current_learner(learner: Annotated[Learner | None, Depends(optional_learner)]) -> Learner:
    if learner is None:
        raise ProblemError(401, "unauthenticated", "Sign in to continue")
    return learner


CurrentLearner = Annotated[Learner, Depends(current_learner)]
OptionalLearner = Annotated[Learner | None, Depends(optional_learner)]
Db = Annotated[DbSession, Depends(get_db)]
