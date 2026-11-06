"""Progress derivation rules (data-model §2.12; FR-036, FR-037, FR-040). Pure functions.

- Objective demonstrated ⇔ the module's knowledge check has been passed (any version).
- Competency demonstrated ⇔ every knowledge check and every challenge mapped to it has been passed
  (any version). Content views and lab visits never demonstrate anything.
- Module completed ⇔ knowledge check passed AND all its challenges passed. Never relaxed, even
  while challenge evaluation is not deployed (increment 1).
- Path completed ⇔ all its modules completed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from academy.progress.evidence import Evidence, EvidenceItem

Status = Literal["not_started", "in_progress", "completed"]
CompetencyStatus = Literal["not_started", "in_progress", "demonstrated"]


def check_competencies(bundle_data: dict[str, Any], check: dict[str, Any]) -> set[str]:
    """Competencies a knowledge check maps to, through its questions' objectives."""
    module = bundle_data["modules"].get(check["module_id"], {})
    by_objective = {o["id"]: set(o["competencies"]) for o in module.get("objectives", [])}
    out: set[str] = set()
    for q in check["questions"]:
        out |= by_objective.get(q["objective_id"], set())
    return out


@dataclass(frozen=True)
class CompetencyState:
    id: str
    status: CompetencyStatus
    evidence: list[EvidenceItem]
    demonstrated_at: Any


def competency_mapping(bundle_data: dict[str, Any]) -> dict[str, list[tuple[str, str]]]:
    """competency id → required evidence items ``(kind, id)``."""
    mapping: dict[str, list[tuple[str, str]]] = {c["id"]: [] for c in bundle_data["competencies"]}
    for check in bundle_data["knowledge_checks"].values():
        for cid in check_competencies(bundle_data, check):
            mapping.setdefault(cid, []).append(("knowledge_check", check["id"]))
    for ch in bundle_data["challenges"].values():
        for cid in ch["competencies"]:
            mapping.setdefault(cid, []).append(("challenge", ch["id"]))
    return mapping


def competency_states(bundle_data: dict[str, Any], ev: Evidence) -> dict[str, CompetencyState]:
    module_of: dict[tuple[str, str], str] = {}
    for check in bundle_data["knowledge_checks"].values():
        module_of[("knowledge_check", check["id"])] = check["module_id"]
    for ch in bundle_data["challenges"].values():
        module_of[("challenge", ch["id"])] = ch["module_id"]
    out: dict[str, CompetencyState] = {}
    for cid, required in competency_mapping(bundle_data).items():
        items = [ev.passed[r] for r in required if r in ev.passed]
        if required and len(items) == len(required):
            status: CompetencyStatus = "demonstrated"
            at = max(i.at for i in items)
        else:
            active = any(
                r in ev.attempted or module_of.get(r) in ev.active_modules for r in required
            )
            status = "in_progress" if active else "not_started"
            at = None
        out[cid] = CompetencyState(cid, status, items if status == "demonstrated" else [], at)
    return out


def objective_demonstrated(module: dict[str, Any], ev: Evidence) -> bool:
    kc = module.get("knowledge_check_id")
    return bool(kc) and ("knowledge_check", kc) in ev.passed


def module_status(module: dict[str, Any], ev: Evidence) -> Status:
    kc = module.get("knowledge_check_id")
    required = [("knowledge_check", kc)] if kc else []
    required += [("challenge", c) for c in module.get("challenge_ids", [])]
    if required and all(r in ev.passed for r in required):
        return "completed"
    if module["id"] in ev.active_modules or any(r in ev.attempted for r in required):
        return "in_progress"
    return "not_started"


def path_completed(bundle_data: dict[str, Any], path: dict[str, Any], ev: Evidence) -> bool:
    modules = [
        bundle_data["modules"][m] for m in path.get("modules", []) if m in bundle_data["modules"]
    ]
    return bool(modules) and all(module_status(m, ev) == "completed" for m in modules)


def pending_objectives(module: dict[str, Any], ev: Evidence) -> list[dict[str, Any]]:
    if objective_demonstrated(module, ev):
        return []
    return [{**o, "module_id": module["id"]} for o in module.get("objectives", [])]


def missing_prerequisites(
    bundle_data: dict[str, Any], module: dict[str, Any], ev: Evidence
) -> list[dict[str, str]]:
    """Prerequisites not yet demonstrated, with where they are taught (FR-006, non-blocking)."""
    states = competency_states(bundle_data, ev)
    competencies = bundle_data_competencies(bundle_data)
    path = bundle_data["paths"].get(module["path_id"], {})
    ordered = [
        bundle_data["modules"][m] for m in path.get("modules", []) if m in bundle_data["modules"]
    ]
    out: list[dict[str, str]] = []
    for pre in module.get("prerequisites", []):
        if pre in bundle_data["modules"]:
            other = bundle_data["modules"][pre]
            if module_status(other, ev) != "completed":
                out.append({"id": pre, "title": other["title"], "taught_in_module": pre})
        elif pre in competencies:
            if states.get(pre) and states[pre].status == "demonstrated":
                continue
            taught = next((m["id"] for m in ordered if pre in m.get("competencies", [])), "")
            out.append({"id": pre, "title": competencies[pre]["title"], "taught_in_module": taught})
    return out


def bundle_data_competencies(bundle_data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {c["id"]: c for c in bundle_data["competencies"]}
