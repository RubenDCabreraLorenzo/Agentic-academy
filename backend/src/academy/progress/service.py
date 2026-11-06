"""Dashboard and competency view (US3; FR-038–FR-042)."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from academy.catalog.service import path_summary
from academy.content.registry import Bundle, get_registry
from academy.progress import derivation
from academy.progress.evidence import Evidence, gather
from academy.progress.views import ContentView, last_position


def _viewed_lessons(db: Session, account_id: uuid.UUID) -> set[str]:
    return set(
        db.scalars(
            select(ContentView.content_id).where(
                ContentView.account_id == account_id, ContentView.content_type == "lesson"
            )
        )
    )


def _available_paths(bundle: Bundle) -> list[dict[str, Any]]:
    return sorted(
        (p for p in bundle.data["paths"].values() if p["status"] == "available"),
        key=lambda p: (p["order"], p["id"]),
    )


def _next_path(bundle: Bundle, path: dict[str, Any]) -> dict[str, Any] | None:
    later = sorted(
        (p for p in bundle.data["paths"].values() if p["order"] > path["order"]),
        key=lambda p: (path["id"] not in p["prerequisite_paths"], p["order"]),
    )
    return later[0] if later else None


def _next_step(
    bundle: Bundle, path: dict[str, Any], ev: Evidence, viewed: set[str]
) -> dict[str, Any] | None:
    for module_id in path["modules"]:
        m = bundle.module(module_id)
        if m is None or derivation.module_status(m, ev) == "completed":
            continue
        for lesson in m["lessons"]:
            if lesson["id"] not in viewed:
                return {
                    "kind": "lesson",
                    "target_id": f"{m['id']}#lesson-{lesson['id']}",
                    "label": lesson["title"],
                    "module_id": m["id"],
                }
        kc = m["knowledge_check_id"]
        if kc and ("knowledge_check", kc) not in ev.passed:
            return {
                "kind": "knowledge_check",
                "target_id": kc,
                "label": m["title"],
                "module_id": m["id"],
            }
        for cid in m["challenge_ids"]:
            if ("challenge", cid) not in ev.passed:
                ch = bundle.challenge(cid) or {"title": cid}
                return {
                    "kind": "challenge",
                    "target_id": cid,
                    "label": ch["title"],
                    "module_id": m["id"],
                }
    nxt = _next_path(bundle, path)
    if nxt:
        return {
            "kind": "next_path",
            "target_id": nxt["id"],
            "label": nxt["title"],
            "module_id": None,
        }
    return None


def _competency_rows(bundle: Bundle, ids: list[str], ev: Evidence) -> list[dict[str, Any]]:
    states = derivation.competency_states(bundle.data, ev)
    comps = bundle.competencies
    rows = []
    for cid in ids:
        if cid not in comps:
            continue
        st = states.get(cid)
        rows.append(
            {
                "id": cid,
                "title": comps[cid]["title"],
                "description": comps[cid]["description"],
                "level": comps[cid]["level"],
                "status": st.status if st else "not_started",
                "demonstrated_at": st.demonstrated_at.isoformat()
                if st and st.demonstrated_at
                else None,
                "evidence": [
                    {
                        "type": e.type,
                        "id": e.id,
                        "version": e.version,
                        "result_id": e.result_id,
                        "at": e.at.isoformat(),
                    }
                    for e in (st.evidence if st else [])
                ],
            }
        )
    return rows


def dashboard(db: Session, account_id: uuid.UUID) -> dict[str, Any]:
    bundle = get_registry().current()
    ev = gather(db, account_id)
    position = last_position(db, account_id)
    path = bundle.path(position.path_id) if position else None
    if path is None:
        available = _available_paths(bundle)
        path = available[0] if available else None
    if path is None:
        return {"active_path": None, "new_learner": True}
    viewed = _viewed_lessons(db, account_id)
    modules = [bundle.module(m) for m in path["modules"]]
    module_rows, pending = [], []
    for m in modules:
        if m is None:
            continue
        module_rows.append(
            {"id": m["id"], "title": m["title"], "status": derivation.module_status(m, ev)}
        )
        pending += [
            {
                "id": o["id"],
                "statement": o["statement"],
                "module_id": m["id"],
                "module_title": m["title"],
            }
            for o in derivation.pending_objectives(m, ev)
        ]
    competencies = _competency_rows(bundle, path["competencies"], ev)
    demonstrated = [c for c in competencies if c["status"] == "demonstrated"]
    completed = derivation.path_completed(bundle.data, path, ev)
    nxt = _next_path(bundle, path)
    return {
        "new_learner": position is None and not ev.attempted,
        "active_path": path_summary(bundle, path),
        "competencies_demonstrated": len(demonstrated),
        "competencies_total": len(competencies),
        "competencies": competencies,
        "modules": module_rows,
        "pending_objectives": pending,
        "next_step": _next_step(bundle, path, ev, viewed),
        "continue": (
            {"module_id": position.module_id, "lesson_id": position.lesson_id} if position else None
        ),
        "path_completed": completed,
        "completion_summary": (
            {
                "competencies": demonstrated,
                "recommended_next_path": (
                    {"id": nxt["id"], "title": nxt["title"], "status": nxt["status"]}
                    if nxt
                    else None
                ),
            }
            if completed
            else None
        ),
    }


def competency_view(
    db: Session, account_id: uuid.UUID, path_id: str | None
) -> list[dict[str, Any]]:
    bundle = get_registry().current()
    ev = gather(db, account_id)
    if path_id:
        path = bundle.path(path_id)
        ids = path["competencies"] if path else []
    else:
        ids = [c["id"] for c in bundle.data["competencies"]]
    return _competency_rows(bundle, ids, ev)
