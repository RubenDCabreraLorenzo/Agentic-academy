"""Path progress reset (FR-043). Irreversible; requires ``confirm: "RESET"`` at the API."""

from __future__ import annotations

import uuid

from sqlalchemy import delete
from sqlalchemy.orm import Session

from academy.content.registry import get_registry
from academy.progress.views import ContentView
from academy.shared.errors import ProblemError
from academy.shared.hooks import PathScope, on_reset_path, run_reset_path


def scope_for(path_id: str) -> PathScope:
    bundle = get_registry().current()
    path = bundle.path(path_id)
    if path is None:
        raise ProblemError(404, "not_found", "Path not found")
    modules = [bundle.module(m) for m in path["modules"]]
    mods = [m for m in modules if m]
    return PathScope(
        path_id=path_id,
        module_ids={m["id"] for m in mods},
        challenge_ids={c for m in mods for c in m["challenge_ids"]},
        check_ids={m["knowledge_check_id"] for m in mods if m["knowledge_check_id"]},
        lab_ids={s for m in mods for s in m["lab_scenarios"]},
    )


@on_reset_path
def _reset_views(db: Session, account_id: uuid.UUID, scope: PathScope) -> None:
    db.execute(
        delete(ContentView).where(
            ContentView.account_id == account_id, ContentView.path_id == scope.path_id
        )
    )


def reset_path(db: Session, account_id: uuid.UUID, path_id: str) -> None:
    """Remove the learner's views, attempts, workspaces, submissions, hints and lab visits for the
    path in one transaction; competency status is derived, so it is recomputed automatically."""
    run_reset_path(db, account_id, scope_for(path_id))
