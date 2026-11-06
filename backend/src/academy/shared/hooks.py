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
