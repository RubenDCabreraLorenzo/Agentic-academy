"""FR-051: results stay bound to the version they were obtained on; publishing new content never
removes a demonstrated competency."""

from __future__ import annotations

import shutil
import uuid
from datetime import UTC, datetime
from pathlib import Path

import yaml
from fastapi.testclient import TestClient

from academy.content.build import build
from academy.content.loader import load_tree
from academy.content.registry import Registry, set_registry
from tests.helpers import sign_up_and_in
from tests.integration.progress.test_dashboard_api import pass_challenge, pass_check

FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "content"


def test_competency_survives_new_major_version(client: TestClient, outbox: list, database_url: str, tmp_path: Path) -> None:
    bundles = tmp_path / "bundles"
    build(load_tree(FIXTURE), bundles, now=datetime(2026, 1, 1, tzinfo=UTC))
    set_registry(Registry.load(bundles))
    try:
        email = sign_up_and_in(client, outbox)
        pass_check(client)
        pass_challenge(database_url, email)
        before = {c["id"]: c for c in client.get("/api/v1/me/competencies").json()}
        assert all(c["status"] == "demonstrated" for c in before.values())

        content = tmp_path / "content"
        shutil.copytree(FIXTURE, content)
        kc_file = content / "en/paths/mini-path/modules/01-intro/knowledge-check.yaml"
        kc = yaml.safe_load(kc_file.read_text())
        kc["version"] = "2.0.0"
        kc["questions"][0]["correct"] = ["b"]
        kc_file.write_text(yaml.safe_dump(kc))
        ch_file = content / "en/paths/mini-path/modules/01-intro/challenges/hello-tool/challenge.yaml"
        ch = yaml.safe_load(ch_file.read_text())
        ch["version"] = "2.0.0"
        ch_file.write_text(yaml.safe_dump(ch))
        build(load_tree(content), bundles, now=datetime(2026, 2, 1, tzinfo=UTC))
        set_registry(Registry.load(bundles))

        after = {c["id"]: c for c in client.get("/api/v1/me/competencies").json()}
        assert all(c["status"] == "demonstrated" for c in after.values())
        versions = {e["version"] for c in after.values() for e in c["evidence"]}
        assert versions == {"1.0.0"}, "evidence stays attributed to the version completed"
        assert uuid.UUID(after["design-tools"]["evidence"][0]["result_id"])
    finally:
        set_registry(None)
