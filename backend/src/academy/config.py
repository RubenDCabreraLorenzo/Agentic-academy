"""Application settings (quickstart.md "Environment variables").

Development-only security exceptions are refused when ``APP_ENV=production`` and logged as warnings
otherwise.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

log = logging.getLogger(__name__)


class ProductionGuardError(RuntimeError):
    """Raised when a development-only setting is used in production."""


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: Literal["development", "test", "production"] = "development"
    database_url: str = "postgresql+psycopg://academy:academy@localhost:5432/academy"
    session_secret: str = ""
    cookie_secure: bool = True
    public_base_url: str = "http://localhost:5173"
    email_backend: Literal["smtp", "console", "memory"] = "smtp"
    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "Agentic Academy <no-reply@academy.local>"
    content_dir: Path = Path("./dist/content")
    challenges_enabled: bool = False
    rate_limit_enabled: bool = True

    def dev_exceptions(self) -> list[str]:
        problems: list[str] = []
        if not self.cookie_secure:
            problems.append("COOKIE_SECURE=false")
        if not self.rate_limit_enabled:
            problems.append("RATE_LIMIT_ENABLED=false")
        if self.email_backend != "smtp":
            problems.append(f"EMAIL_BACKEND={self.email_backend}")
        if len(self.session_secret) < 32:
            problems.append("SESSION_SECRET shorter than 32 characters")
        return problems

    def enforce_guards(self) -> None:
        problems = self.dev_exceptions()
        if self.app_env == "production" and problems:
            raise ProductionGuardError(
                "Development-only settings are not allowed in production: " + ", ".join(problems)
            )
        for problem in problems:
            log.warning("development-only setting in use: %s", problem)


@lru_cache
def get_settings() -> Settings:
    return Settings()
