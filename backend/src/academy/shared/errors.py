"""RFC 9457 problem details with stable error codes."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

PROBLEM_JSON = "application/problem+json"


class ProblemError(Exception):
    """Raise to return a problem details response with a stable ``code``."""

    def __init__(
        self,
        status: int,
        code: str,
        title: str,
        detail: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(title)
        self.status = status
        self.code = code
        self.title = title
        self.detail = detail
        self.extra = extra or {}


def problem_body(status: int, code: str, title: str, detail: str | None = None) -> dict[str, Any]:
    body: dict[str, Any] = {
        "type": f"https://agentic-academy.local/problems/{code}",
        "title": title,
        "status": status,
        "code": code,
    }
    if detail:
        body["detail"] = detail
    return body


def problem_response(
    status: int, code: str, title: str, detail: str | None = None, **extra: Any
) -> JSONResponse:
    body = problem_body(status, code, title, detail)
    body.update(extra)
    return JSONResponse(body, status_code=status, media_type=PROBLEM_JSON)


_STATUS_CODES = {
    400: "bad_request",
    401: "unauthenticated",
    403: "forbidden",
    404: "not_found",
    405: "method_not_allowed",
    409: "conflict",
    413: "payload_too_large",
    422: "validation_error",
    429: "rate_limited",
    503: "service_unavailable",
}


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ProblemError)
    async def _problem(_: Request, exc: ProblemError) -> JSONResponse:
        return problem_response(exc.status, exc.code, exc.title, exc.detail, **exc.extra)

    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = _STATUS_CODES.get(exc.status_code, "error")
        return problem_response(exc.status_code, code, str(exc.detail))

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        # Never echo input values back (they may contain passwords).
        fields = [".".join(str(p) for p in err.get("loc", [])) for err in exc.errors()]
        return problem_response(
            400, "invalid_request", "Invalid request", "Invalid fields: " + ", ".join(fields)
        )

    @app.exception_handler(Exception)
    async def _unexpected(_: Request, exc: Exception) -> JSONResponse:
        import logging

        logging.getLogger("academy.errors").exception("unhandled error: %s", type(exc).__name__)
        return problem_response(500, "internal_error", "Unexpected error")
