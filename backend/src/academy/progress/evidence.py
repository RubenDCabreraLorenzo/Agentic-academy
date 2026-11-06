"""Evidence of learning gathered from the modules that record it.

Feature modules register providers so the progress module never reads their tables directly
(plan: modules interact through services). Only passed knowledge checks and passed challenges are
evidence; content views and laboratory visits are activity, never evidence (FR-036).
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy.orm import Session


@dataclass(frozen=True)
class EvidenceItem:
    type: str  # "knowledge_check" | "challenge"
    id: str
    version: str
    result_id: str
    at: datetime


@dataclass
class Evidence:
    passed: dict[tuple[str, str], EvidenceItem] = field(default_factory=dict)
    #: ids of items with any activity (attempts or submissions, passed or not)
    attempted: set[tuple[str, str]] = field(default_factory=set)
    #: module ids with any activity (views, attempts, submissions, lab visits)
    active_modules: set[str] = field(default_factory=set)

    def passed_ids(self, kind: str) -> set[str]:
        return {i for (k, i) in self.passed if k == kind}


Provider = Callable[[Session, uuid.UUID, Evidence], None]
_providers: list[Provider] = []


def register_provider(fn: Provider) -> Provider:
    _providers.append(fn)
    return fn


def gather(db: Session, account_id: uuid.UUID) -> Evidence:
    from academy.progress.views import viewed_modules

    ev = Evidence()
    ev.active_modules |= viewed_modules(db, account_id)
    for provider in _providers:
        provider(db, account_id, ev)
    return ev
