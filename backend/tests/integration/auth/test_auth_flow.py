"""Account lifecycle, CSRF and rate limiting (FR-045a, FR-046, research R5)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from tests.helpers import PASSWORD, csrf, sign_up_and_in, token_from


def test_sign_up_is_identical_for_existing_email(client: TestClient, outbox: list) -> None:
    body = {"email": "same@example.com", "password": PASSWORD}
    first = client.post("/api/v1/auth/sign-up", json=body)
    second = client.post("/api/v1/auth/sign-up", json=body)
    assert first.status_code == second.status_code == 202
    assert first.content == second.content == b""


def test_weak_password_rejected(client: TestClient) -> None:
    r = client.post("/api/v1/auth/sign-up", json={"email": "w@example.com", "password": "short"})
    assert r.status_code == 400
    assert r.headers["content-type"].startswith("application/problem+json")
    assert "short" not in r.text  # input values are never echoed


def test_unverified_sign_in_is_forbidden(client: TestClient, outbox: list) -> None:
    client.post("/api/v1/auth/sign-up", json={"email": "u@example.com", "password": PASSWORD})
    r = client.post("/api/v1/auth/sign-in", json={"email": "u@example.com", "password": PASSWORD})
    assert r.status_code == 403 and r.json()["code"] == "email_not_verified"


def test_full_flow_sign_in_me_sign_out(client: TestClient, outbox: list) -> None:
    email = sign_up_and_in(client, outbox)
    cookie_header = client.cookies.get("aa_session")
    assert cookie_header
    me = client.get("/api/v1/me")
    assert me.status_code == 200 and me.json()["email"] == email and me.json()["email_verified"]
    assert client.post("/api/v1/auth/sign-out", headers=csrf(client)).status_code == 204
    client.cookies.set("aa_session", cookie_header)
    assert client.get("/api/v1/me").status_code == 401


def test_wrong_password(client: TestClient, outbox: list) -> None:
    email = sign_up_and_in(client, outbox)
    r = client.post("/api/v1/auth/sign-in", json={"email": email, "password": "wrong-password-123"})
    assert r.status_code == 401 and r.json()["code"] == "invalid_credentials"


def test_verification_token_single_use(client: TestClient, outbox: list) -> None:
    client.post("/api/v1/auth/sign-up", json={"email": "once@example.com", "password": PASSWORD})
    token = token_from(outbox)
    assert client.post("/api/v1/auth/verify-email", json={"token": token}).status_code == 204
    assert client.post("/api/v1/auth/verify-email", json={"token": token}).status_code == 400


def test_password_reset_revokes_all_sessions(client: TestClient, outbox: list) -> None:
    email = sign_up_and_in(client, outbox)
    old = client.cookies.get("aa_session")
    assert client.post("/api/v1/auth/password-reset/request", json={"email": email}).status_code == 202
    token = token_from(outbox, "reset-password")
    new_password = "another-strong-pass"
    r = client.post("/api/v1/auth/password-reset/confirm", json={"token": token, "new_password": new_password})
    assert r.status_code == 204
    client.cookies.set("aa_session", old)
    assert client.get("/api/v1/me").status_code == 401
    assert client.post("/api/v1/auth/sign-in", json={"email": email, "password": new_password}).status_code == 200


def test_reset_request_for_unknown_email_is_accepted(client: TestClient, outbox: list) -> None:
    before = len(outbox)
    assert client.post("/api/v1/auth/password-reset/request", json={"email": "nobody@example.com"}).status_code == 202
    assert len(outbox) == before


def test_csrf_required_for_state_changes(client: TestClient, outbox: list) -> None:
    sign_up_and_in(client, outbox)
    r = client.post("/api/v1/auth/sign-out")
    assert r.status_code == 403 and r.json()["code"] == "csrf_failed"
    r = client.post("/api/v1/auth/sign-out", headers={"X-CSRF-Token": "wrong"})
    assert r.status_code == 403


def test_rate_limit_on_sign_in(client: TestClient) -> None:
    codes = [
        client.post("/api/v1/auth/sign-in", json={"email": "rl@example.com", "password": "whatever-123"}).status_code
        for _ in range(7)
    ]
    assert 429 in codes


def test_delete_account_requires_confirmation_and_removes_data(client: TestClient, outbox: list) -> None:
    email = sign_up_and_in(client, outbox)
    r = client.request("DELETE", "/api/v1/me", json={"confirm": "nope"}, headers=csrf(client))
    assert r.status_code == 400
    r = client.request("DELETE", "/api/v1/me", json={"confirm": "DELETE"}, headers=csrf(client))
    assert r.status_code == 204
    assert client.get("/api/v1/me").status_code == 401
    r = client.post("/api/v1/auth/sign-in", json={"email": email, "password": PASSWORD})
    assert r.status_code == 401


def test_security_headers(client: TestClient) -> None:
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.headers["x-content-type-options"] == "nosniff"
    body = r.json()
    assert body["database"] == "ok" and body["evaluation"] == "unavailable"
