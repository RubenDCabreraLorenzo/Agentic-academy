"""Auth and account routes (contracts/openapi.yaml "Auth & account")."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Request, Response
from pydantic import BaseModel, EmailStr, Field

from academy.auth import rate_limit, service
from academy.auth.dependencies import CurrentLearner, Db
from academy.auth.passwords import MAX_LENGTH, MIN_LENGTH, PasswordPolicyError
from academy.auth.sessions import clear_auth_cookies, set_auth_cookies
from academy.shared.errors import ProblemError

router = APIRouter()


class Credentials(BaseModel):
    email: EmailStr
    password: str = Field(min_length=MIN_LENGTH, max_length=MAX_LENGTH)


class SignInBody(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=MAX_LENGTH)


class TokenBody(BaseModel):
    token: str = Field(min_length=10, max_length=200)


class EmailBody(BaseModel):
    email: EmailStr


class ResetBody(BaseModel):
    token: str = Field(min_length=10, max_length=200)
    new_password: str = Field(min_length=MIN_LENGTH, max_length=MAX_LENGTH)


class DeleteBody(BaseModel):
    confirm: Literal["DELETE"]


class Me(BaseModel):
    id: str
    email: str
    locale: str
    email_verified: bool


def _me(account) -> Me:  # type: ignore[no-untyped-def]
    return Me(
        id=str(account.id),
        email=account.email,
        locale=account.locale,
        email_verified=account.email_verified_at is not None,
    )


@router.post("/auth/sign-up", status_code=202)
def sign_up(body: Credentials, request: Request, db: Db) -> Response:
    rate_limit.check(request, "sign-up", body.email)
    try:
        service.sign_up(db, body.email, body.password)
    except PasswordPolicyError as exc:
        raise ProblemError(400, "weak_password", str(exc)) from exc
    return Response(status_code=202)


@router.post("/auth/verify-email", status_code=204)
def verify_email(body: TokenBody, db: Db) -> Response:
    service.verify_email(db, body.token)
    return Response(status_code=204)


@router.post("/auth/sign-in")
def sign_in(body: SignInBody, request: Request, response: Response, db: Db) -> Me:
    rate_limit.check(request, "sign-in", body.email)
    account, token = service.sign_in(db, body.email, body.password)
    set_auth_cookies(response, token)
    return _me(account)


@router.post("/auth/sign-out", status_code=204)
def sign_out(learner: CurrentLearner, db: Db) -> Response:
    service.sign_out(db, learner.session.id)
    response = Response(status_code=204)
    clear_auth_cookies(response)
    return response


@router.post("/auth/password-reset/request", status_code=202)
def reset_request(body: EmailBody, request: Request, db: Db) -> Response:
    rate_limit.check(request, "reset", body.email)
    service.request_password_reset(db, body.email)
    return Response(status_code=202)


@router.post("/auth/password-reset/confirm", status_code=204)
def reset_confirm(body: ResetBody, request: Request, db: Db) -> Response:
    rate_limit.check(request, "reset-confirm")
    service.confirm_password_reset(db, body.token, body.new_password)
    return Response(status_code=204)


@router.get("/me")
def me(learner: CurrentLearner) -> Me:
    return _me(learner.account)


@router.delete("/me", status_code=204)
def delete_me(body: DeleteBody, learner: CurrentLearner, db: Db) -> Response:
    service.delete_account(db, learner.account.id)
    response = Response(status_code=204)
    clear_auth_cookies(response)
    return response
