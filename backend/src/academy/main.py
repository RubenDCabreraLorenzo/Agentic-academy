"""Application factory: routers under ``/api/v1``, error handlers, CSRF and security headers."""

from __future__ import annotations

from fastapi import APIRouter, FastAPI, Request, Response
from starlette.middleware.base import RequestResponseEndpoint

from academy.auth.router import router as auth_router
from academy.auth.sessions import CsrfMiddleware
from academy.config import get_settings
from academy.shared.errors import install_error_handlers
from academy.shared.health import router as health_router
from academy.shared.logging import configure_logging

API_PREFIX = "/api/v1"

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
    "Cache-Control": "no-store",
}


def _routers() -> list[APIRouter]:
    routers = [health_router, auth_router]
    # Feature routers are optional imports so increments can be deployed independently.
    for module in (
        "academy.catalog.router",
        "academy.assessments.router",
        "academy.challenges.router",
        "academy.progress.router",
        "academy.lab.router",
    ):
        try:
            mod = __import__(module, fromlist=["router"])
        except ModuleNotFoundError as exc:
            if exc.name != module:
                raise
            continue
        routers.append(mod.router)
    return routers


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging()
    settings.enforce_guards()
    app = FastAPI(
        title="Agentic Academy API",
        version="0.1.0",
        docs_url=f"{API_PREFIX}/docs",
        openapi_url=f"{API_PREFIX}/openapi.json",
    )
    install_error_handlers(app)
    app.add_middleware(CsrfMiddleware)

    @app.middleware("http")
    async def security_headers(request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        if not request.url.path.startswith(f"{API_PREFIX}/docs"):
            for key, value in SECURITY_HEADERS.items():
                response.headers.setdefault(key, value)
        return response

    for router in _routers():
        app.include_router(router, prefix=API_PREFIX)
    return app
