"""Catalog, path and module read models (US1, US6; FR-001–FR-015)."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from academy.content.registry import Bundle, get_registry
from academy.progress import derivation
from academy.progress.evidence import Evidence, gather
from academy.progress.views import record_view
from academy.shared.errors import ProblemError

META_FIELDS = ("id", "version", "lang", "last_reviewed", "deprecation")


def _meta(item: dict[str, Any]) -> dict[str, Any]:
    return {k: item.get(k) for k in META_FIELDS}


def _competencies(bundle: Bundle, ids: list[str]) -> list[dict[str, Any]]:
    comps = bundle.competencies
    return [
        {"id": c, "title": comps[c]["title"], "level": comps[c]["level"]} for c in ids if c in comps
    ]


def path_summary(bundle: Bundle, path: dict[str, Any]) -> dict[str, Any]:
    return {
        **_meta(path),
        "title": path["title"],
        "summary": path["summary"],
        "level": path["level"],
        "status": path["status"],
        "order": path["order"],
        "estimated_hours": path["estimated_hours"],
        "prerequisite_paths": path["prerequisite_paths"],
        "competencies": _competencies(bundle, path["competencies"]),
    }


def list_catalog() -> list[dict[str, Any]]:
    bundle = get_registry().current()
    paths = sorted(bundle.data["paths"].values(), key=lambda p: (p["order"], p["id"]))
    return [path_summary(bundle, p) for p in paths]


def get_path(path_id: str, db: Session, account_id: Any | None) -> dict[str, Any]:
    bundle = get_registry().current()
    path = bundle.path(path_id)
    if path is None:
        raise ProblemError(404, "not_found", "Path not found")
    ev: Evidence | None = gather(db, account_id) if account_id else None
    modules = []
    for order, module_id in enumerate(path["modules"], start=1):
        m = bundle.module(module_id)
        if m is None:
            continue
        entry: dict[str, Any] = {"id": m["id"], "title": m["title"], "order": m.get("order", order)}
        entry["summary"] = m["summary"]
        if ev is not None:
            entry["status"] = derivation.module_status(m, ev)
        modules.append(entry)
    return {
        **path_summary(bundle, path),
        "objectives": path["objectives"],
        "entry_prerequisites": path["entry_prerequisites"],
        "modules": modules,
    }


def _deprecations(bundle: Bundle) -> dict[str, dict[str, Any]]:
    return {
        d["target"]: {
            "reason": d["reason"],
            "replacement": d.get("replacement"),
            "since": d["since"],
        }
        for d in bundle.deprecations
    }


def get_module(
    module_id: str, db: Session, account_id: Any, lesson_id: str | None = None
) -> dict[str, Any]:
    bundle = get_registry().current()
    m = bundle.module(module_id)
    if m is None:
        raise ProblemError(404, "not_found", "Module not found")
    path = bundle.path(m["path_id"]) or {"modules": []}
    order = path["modules"]
    idx = order.index(module_id) if module_id in order else -1
    previous_id = order[idx - 1] if idx > 0 else None
    next_id = order[idx + 1] if 0 <= idx < len(order) - 1 else None

    record_view(db, account_id, "module", module_id, m["version"], m["path_id"], module_id)
    if lesson_id and any(ls["id"] == lesson_id for ls in m["lessons"]):
        lesson = next(ls for ls in m["lessons"] if ls["id"] == lesson_id)
        record_view(db, account_id, "lesson", lesson_id, lesson["version"], m["path_id"], module_id)

    ev = gather(db, account_id)
    return {
        **_meta(m),
        "path_id": m["path_id"],
        "path_title": path.get("title"),
        "title": m["title"],
        "summary": m["summary"],
        "objectives": [{"id": o["id"], "statement": o["statement"]} for o in m["objectives"]],
        "competencies": _competencies(bundle, m["competencies"]),
        "status": derivation.module_status(m, ev),
        "objectives_demonstrated": derivation.objective_demonstrated(m, ev),
        "missing_prerequisites": derivation.missing_prerequisites(bundle.data, m, ev),
        "lessons": [
            {**_meta(ls), "title": ls["title"], "body_markdown": ls["body_markdown"]}
            for ls in m["lessons"]
        ],
        "references": m["references"],
        "knowledge_check_id": m["knowledge_check_id"],
        "challenge_ids": m["challenge_ids"],
        "challenges": [
            {"id": cid, "title": bundle.challenge(cid)["title"]}  # type: ignore[index]
            for cid in m["challenge_ids"]
            if bundle.challenge(cid)
        ],
        "lab_scenario_ids": m["lab_scenarios"],
        "lab_scenarios": [
            {"id": sid, "title": bundle.lab_scenario(sid)["title"]}  # type: ignore[index]
            for sid in m["lab_scenarios"]
            if bundle.lab_scenario(sid)
        ],
        "previous_module_id": previous_id,
        "next_module_id": next_id,
        "deprecations": _deprecations(bundle),
    }
