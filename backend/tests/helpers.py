"""Test helpers for authenticated API calls."""

from __future__ import annotations

import re
import uuid

from fastapi.testclient import TestClient

PASSWORD = "correct-horse-battery"


def csrf(client: TestClient) -> dict[str, str]:
    return {"X-CSRF-Token": client.cookies.get("aa_csrf", "")}


def token_from(outbox: list, kind: str = "verify-email") -> str:  # type: ignore[type-arg]
    for email in reversed(outbox):
        m = re.search(rf"/{kind}\?token=([\w-]+)", email.body)
        if m:
            return m.group(1)
    raise AssertionError(f"no {kind} link in outbox")


def sign_up_and_in(client: TestClient, outbox: list, email: str | None = None) -> str:  # type: ignore[type-arg]
    address = email or f"learner-{uuid.uuid4().hex[:8]}@example.com"
    assert client.post("/api/v1/auth/sign-up", json={"email": address, "password": PASSWORD}).status_code == 202
    token = token_from(outbox)
    assert client.post("/api/v1/auth/verify-email", json={"token": token}).status_code == 204
    r = client.post("/api/v1/auth/sign-in", json={"email": address, "password": PASSWORD})
    assert r.status_code == 200, r.text
    return address
