"""Cross-module hooks that keep modules decoupled (plan: modules interact through services).

Modules register callbacks at import time; e.g. the challenges module cancels queued jobs before an
account is deleted (data-model §2.8).
"""

from __future__ import annotations

import uuid
from collections.abc import Callable

from sqlalchemy.orm import Session

_before_account_delete: list[Callable[[Session, uuid.UUID], None]] = []


def on_before_account_delete(
    fn: Callable[[Session, uuid.UUID], None],
) -> Callable[[Session, uuid.UUID], None]:
    _before_account_delete.append(fn)
    return fn


def run_before_account_delete(db: Session, account_id: uuid.UUID) -> None:
    for fn in _before_account_delete:
        fn(db, account_id)


_reset_path: list[Callable[[Session, uuid.UUID, PathScope], None]] = []


class PathScope:
    """Content ids belonging to one path, used to scope a progress reset (FR-043)."""

    def __init__(
        self,
        path_id: str,
        module_ids: set[str],
        challenge_ids: set[str],
        check_ids: set[str],
        lab_ids: set[str],
    ) -> None:
        self.path_id = path_id
        self.module_ids = module_ids
        self.challenge_ids = challenge_ids
        self.check_ids = check_ids
        self.lab_ids = lab_ids


def on_reset_path(
    fn: Callable[[Session, uuid.UUID, PathScope], None],
) -> Callable[[Session, uuid.UUID, PathScope], None]:
    _reset_path.append(fn)
    return fn


def run_reset_path(db: Session, account_id: uuid.UUID, scope: PathScope) -> None:
    for fn in _reset_path:
        fn(db, account_id, scope)
