"""Content validation rules (contracts/content-schema.md "Validation rules", FR-050).

Rule numbers match the contract. Rule 7's execution of reference solutions lives in
:mod:`academy.content.solutions` and only runs with ``--run-solutions``.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from importlib import resources
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from academy.content.loader import ContentTree, Issue, LoadedModule, load_tree
from academy.content.schemas import Maturity

#: Secret-like patterns rejected anywhere in content (rule 10, FR-047).
SECRET_PATTERNS = [
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
    re.compile(r"\bxox[abpr]-[A-Za-z0-9-]{10,}\b"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
]


def _lab_validator() -> Draft202012Validator:
    raw = resources.files("academy.content").joinpath("lab_trace.schema.json").read_text()
    return Draft202012Validator(json.loads(raw))


def _cycle(graph: dict[str, list[str]]) -> list[str] | None:
    state: dict[str, int] = {}
    stack: list[str] = []

    def visit(node: str) -> list[str] | None:
        state[node] = 1
        stack.append(node)
        for nxt in graph.get(node, []):
            if state.get(nxt) == 1:
                return [*stack[stack.index(nxt) :], nxt]
            if state.get(nxt) is None and nxt in graph:
                found = visit(nxt)
                if found:
                    return found
        stack.pop()
        state[node] = 2
        return None

    for node in graph:
        if state.get(node) is None:
            found = visit(node)
            if found:
                return found
    return None


def _rule1_unique_and_lang(tree: ContentTree) -> None:
    def check(kind: str, items: Iterable[tuple[str, Path]]) -> None:
        seen: dict[str, Path] = {}
        for item_id, path in items:
            if item_id in seen:
                tree.issue("1-schema", path, f"duplicate {kind} id '{item_id}'")
            seen[item_id] = path

    if tree.competencies:
        check(
            "competency",
            ((c.id, tree.root / "competencies.yaml") for c in tree.competencies.competencies),
        )
    check("path", ((p.meta.id, p.path) for p in tree.paths))
    check("module", ((m.meta.id, m.path) for m in tree.modules))
    check("challenge", ((c.meta.id, c.path) for c in tree.challenges))
    check("lesson", ((ls.meta.id, ls.path) for m in tree.modules for ls in m.lessons))
    check(
        "knowledge check",
        ((m.knowledge_check.id, m.path) for m in tree.modules if m.knowledge_check),
    )
    headers: list[tuple[str, Path]] = [(p.meta.lang, p.path) for p in tree.paths]
    for m in tree.modules:
        headers.append((m.meta.lang, m.path))
        headers += [(ls.meta.lang, ls.path) for ls in m.lessons]
        if m.knowledge_check:
            headers.append((m.knowledge_check.lang, m.path / "knowledge-check.yaml"))
        headers += [(c.meta.lang, c.path) for c in m.challenges]
    for lang, path in headers:
        if lang != tree.lang:
            tree.issue("1-schema", path, f"lang '{lang}' does not match folder '{tree.lang}'")


def _rule2_references(tree: ContentTree, competency_ids: set[str]) -> None:
    path_ids = {p.meta.id for p in tree.paths}
    module_ids = {m.meta.id for m in tree.modules}
    for p in tree.paths:
        for pid in p.meta.prerequisite_paths:
            if pid not in path_ids:
                tree.issue("2-reference", p.path, f"unknown prerequisite path '{pid}'")
        for cid in p.meta.competencies:
            if cid not in competency_ids:
                tree.issue("2-reference", p.path, f"unknown competency '{cid}'")
        folder_ids = [m.meta.id for m in p.modules]
        if p.meta.modules != folder_ids:
            tree.issue(
                "2-reference",
                p.path,
                f"'modules' {p.meta.modules} must match module folders {folder_ids}",
            )
    for m in tree.modules:
        for cid in m.meta.competencies:
            if cid not in competency_ids:
                tree.issue("2-reference", m.path, f"unknown competency '{cid}'")
        for obj in m.meta.objectives:
            for cid in obj.competencies:
                if cid not in competency_ids:
                    tree.issue(
                        "2-reference", m.path, f"objective '{obj.id}': unknown competency '{cid}'"
                    )
        for pre in m.meta.prerequisites:
            if pre not in module_ids and pre not in competency_ids:
                tree.issue("2-reference", m.path, f"unknown prerequisite '{pre}'")
        for sid in m.meta.lab_scenarios:
            if sid not in tree.lab_scenarios:
                tree.issue("2-reference", m.path, f"unknown lab scenario '{sid}'")
        anchors = {f"{ls.meta.id}#{a}" for ls in m.lessons for a in ls.anchors}
        objective_ids = {o.id for o in m.meta.objectives}
        if m.knowledge_check:
            for q in m.knowledge_check.questions:
                if q.objective_id not in objective_ids:
                    tree.issue(
                        "2-reference",
                        m.path,
                        f"question '{q.id}': unknown objective '{q.objective_id}'",
                    )
                if q.lesson_anchor not in anchors:
                    tree.issue(
                        "2-reference",
                        m.path,
                        f"question '{q.id}': lesson anchor '{q.lesson_anchor}' not found",
                    )
        for ch in m.challenges:
            for cid in ch.meta.competencies:
                if cid not in competency_ids:
                    tree.issue("2-reference", ch.path, f"unknown competency '{cid}'")
    for sid, (doc, path) in tree.lab_scenarios.items():
        for mid in doc.get("module_ids", []):
            if mid not in module_ids:
                tree.issue("2-reference", path, f"unknown module '{mid}'")
        if doc.get("id") != sid:
            tree.issue("2-reference", path, "scenario id must match the file name")


def _rule3_prerequisites(tree: ContentTree) -> None:
    graph = {p.meta.id: list(p.meta.prerequisite_paths) for p in tree.paths}
    cycle = _cycle(graph)
    if cycle:
        tree.issue("3-prerequisites", tree.root, "path prerequisite cycle: " + " → ".join(cycle))
    for p in tree.paths:
        order = {m.meta.id: m.meta.order for m in p.modules}
        developed: dict[str, int] = {}
        for m in p.modules:
            for cid in m.meta.competencies:
                developed.setdefault(cid, m.meta.order)
        orders = [m.meta.order for m in p.modules]
        if orders != sorted(orders) or len(set(orders)) != len(orders):
            tree.issue(
                "3-prerequisites", p.path, "module 'order' must be unique and follow folder order"
            )
        mgraph = {m.meta.id: [x for x in m.meta.prerequisites if x in order] for m in p.modules}
        cycle = _cycle(mgraph)
        if cycle:
            tree.issue("3-prerequisites", p.path, "module prerequisite cycle: " + " → ".join(cycle))
        for m in p.modules:
            for pre in m.meta.prerequisites:
                if pre in order and order[pre] >= m.meta.order:
                    tree.issue(
                        "3-prerequisites",
                        m.path,
                        f"prerequisite module '{pre}' must come earlier in the path",
                    )
                if pre in developed and developed[pre] >= m.meta.order:
                    tree.issue(
                        "3-prerequisites",
                        m.path,
                        f"prerequisite competency '{pre}' is only developed later in the path",
                    )


def _rule4_multi_agent(tree: ContentTree) -> None:
    for p in tree.paths:
        seen_multi = False
        for m in p.modules:
            if m.meta.multi_agent:
                seen_multi = True
            elif seen_multi:
                tree.issue(
                    "4-multi-agent",
                    m.path,
                    "single-agent module after a multi-agent module (FR-005)",
                )


def _module_completeness(tree: ContentTree, m: LoadedModule) -> None:
    rule = "5-completeness"
    if not m.lessons:
        tree.issue(rule, m.path, "module needs at least one lesson")
    code = [b for ls in m.lessons for b in ls.code_blocks if b.language]
    if not code:
        tree.issue(rule, m.path, "module needs at least one code example with a language")
    diagrams = [d for ls in m.lessons for d in ls.diagrams]
    if not diagrams:
        tree.issue(rule, m.path, "module needs at least one diagram")
    for ls in m.lessons:
        for d in ls.diagrams:
            if not d["alt"].strip():
                tree.issue(rule, ls.path, "every diagram needs alt text (FR-014)")
        for name, attrs in ls.directives:
            if name == "maturity" and attrs.get("level") not in {x.value for x in Maturity}:
                tree.issue(
                    rule,
                    ls.path,
                    "maturity directive needs level=established|emerging|experimental",
                )
            if name == "vendor" and not attrs.get("name"):
                tree.issue(rule, ls.path, "vendor directive needs a name")
            if name not in {"maturity", "vendor", "deprecated"}:
                tree.issue(rule, ls.path, f"unknown directive ':::{name}'")
    if m.knowledge_check is None:
        tree.issue(rule, m.path, "module needs exactly one knowledge-check.yaml")
    if not m.challenges:
        tree.issue(rule, m.path, "module needs at least one challenge (FR-008)")


def _rule6_traceability(tree: ContentTree) -> None:
    for m in tree.modules:
        module_comps = set(m.meta.competencies)
        if m.challenges:
            uncovered = module_comps - {c for ch in m.challenges for c in ch.meta.competencies}
            if uncovered:
                # FR-036: a competency needs practical evidence, so a knowledge check alone can
                # never demonstrate it.
                tree.issue(
                    "6-traceability",
                    m.path,
                    f"competencies not covered by any challenge of the module: {sorted(uncovered)}",
                )
        for obj in m.meta.objectives:
            extra = set(obj.competencies) - module_comps
            if extra:
                tree.issue(
                    "6-traceability",
                    m.path,
                    f"objective '{obj.id}' maps to competencies outside the module: {sorted(extra)}",
                )
        for ch in m.challenges:
            extra = set(ch.meta.competencies) - module_comps
            if extra:
                tree.issue(
                    "6-traceability",
                    ch.path,
                    f"challenge competencies outside the module: {sorted(extra)}",
                )
    for p in tree.paths:
        if p.meta.status == "available":
            union = {c for m in p.modules for c in m.meta.competencies}
            if set(p.meta.competencies) != union:
                tree.issue(
                    "6-traceability",
                    p.path,
                    "path competencies must equal the union of its modules' competencies",
                )


def _rule7_challenges(tree: ContentTree) -> None:
    for p in tree.paths:
        last = 0
        for m in p.modules:
            for ch in m.challenges:
                if ch.meta.difficulty_rank <= last:
                    tree.issue(
                        "7-challenge",
                        ch.path,
                        "difficulty_rank must strictly increase along the path (FR-025)",
                    )
                last = ch.meta.difficulty_rank
    for ch in tree.challenges:
        if not ch.starter:
            tree.issue("7-challenge", ch.path, "challenge needs starter files")
        if not ch.tests:
            tree.issue("7-challenge", ch.path, "challenge needs tests")
        if not ch.solution:
            tree.issue("7-challenge", ch.path, "challenge needs a reference solution in solution/")
        mapped = {t for c in ch.meta.criteria for t in c.tests}
        found = set(ch.test_ids)
        for t in sorted(mapped - found):
            tree.issue("7-challenge", ch.path, f"criterion test '{t}' not found in tests/")
        for t in sorted(found - mapped):
            tree.issue("7-challenge", ch.path, f"test '{t}' is not mapped to any criterion")
        for name in ch.starter:
            top = name.split("/", 1)[0]
            if top == "tests" or name == "manifest.json":
                tree.issue("7-challenge", ch.path, f"starter file '{name}' uses a reserved path")


def _rule8_lab(tree: ContentTree) -> None:
    validator = _lab_validator()
    for _sid, (doc, path) in tree.lab_scenarios.items():
        for err in sorted(validator.iter_errors(doc), key=lambda e: list(e.path)):
            loc = "/".join(str(p) for p in err.path)
            tree.issue("8-lab", path, f"{loc}: {err.message}" if loc else err.message)
        _lab_semantics(tree, doc, path)


def _branch_prefix(variants: dict[str, Any], v: dict[str, Any]) -> list[dict[str, Any]]:
    """Elements a branch variant inherits from its parent, up to the branch point."""
    origin = v.get("branches_from")
    if not isinstance(origin, dict):
        return []
    parent = variants.get(str(origin.get("variant_id")))
    if parent is None or parent is v:
        return []
    out: list[dict[str, Any]] = [*_branch_prefix(variants, parent)]
    for e in parent.get("elements", []):
        out.append(e)
        if e.get("id") == origin.get("element_id"):
            break
    return out


def _lab_semantics(tree: ContentTree, doc: dict[str, Any], path: Path) -> None:
    tools = {t.get("name"): t.get("permission") for t in doc.get("tools", [])}
    variants = {v.get("id"): v for v in doc.get("variants", [])}
    branches = {
        (
            v["branches_from"]["variant_id"],
            v["branches_from"]["element_id"],
            v["branches_from"]["decision"],
        )
        for v in variants.values()
        if isinstance(v.get("branches_from"), dict)
        and {"variant_id", "element_id", "decision"} <= set(v["branches_from"])
    }
    for vid, v in variants.items():
        elements = v.get("elements", [])
        seqs = [e.get("seq") for e in elements]
        if seqs != sorted(seqs):
            tree.issue("8-lab", path, f"variant '{vid}': elements must be ordered by seq")
        ids = [e.get("id") for e in elements]
        if len(set(ids)) != len(ids):
            tree.issue("8-lab", path, f"variant '{vid}': duplicate element ids")
        for i, e in enumerate(elements):
            if e.get("kind") == "tool_call":
                prefix = _branch_prefix(variants, v)
                if e.get("tool") not in tools:
                    tree.issue("8-lab", path, f"variant '{vid}': unknown tool '{e.get('tool')}'")
                elif tools[e["tool"]] != e.get("permission"):
                    tree.issue(
                        "8-lab", path, f"variant '{vid}': tool '{e['tool']}' permission mismatch"
                    )
                if e.get("permission") == "destructive":
                    request = next(
                        (
                            x
                            for x in reversed(prefix + elements[:i])
                            if x.get("kind") == "execution_event"
                            and x.get("event") == "approval_request"
                        ),
                        None,
                    )
                    if request is None:
                        tree.issue(
                            "8-lab",
                            path,
                            f"variant '{vid}': destructive tool call without a preceding approval_request (FR-030)",
                        )
            if e.get("kind") == "execution_event" and e.get("event") == "approval_request":
                root = (
                    v.get("branches_from", {}).get("variant_id", vid)
                    if v.get("branches_from")
                    else vid
                )
                for decision in ("approved", "rejected"):
                    if (vid, e.get("id"), decision) not in branches and (
                        root,
                        e.get("id"),
                        decision,
                    ) not in branches:
                        tree.issue(
                            "8-lab",
                            path,
                            f"variant '{vid}': approval_request '{e.get('id')}' needs an '{decision}' branch variant",
                        )
            if e.get("kind") == "decision_summary":
                for ref in e.get("explains", []):
                    if ref not in ids:
                        tree.issue(
                            "8-lab",
                            path,
                            f"variant '{vid}': decision summary explains unknown element '{ref}'",
                        )
    for cmp in doc.get("comparisons", []):
        for side in ("left_variant", "right_variant"):
            if cmp.get(side) not in variants:
                tree.issue(
                    "8-lab", path, f"comparison references unknown variant '{cmp.get(side)}'"
                )
    for fc in doc.get("failure_cases", []):
        v = variants.get(fc.get("variant_id"))
        if v is None or fc.get("element_id") not in {e.get("id") for e in v.get("elements", [])}:
            tree.issue(
                "8-lab", path, f"failure case references unknown element '{fc.get('element_id')}'"
            )


def _rule10_secrets(tree: ContentTree) -> None:
    base = tree.root
    for f in sorted(base.rglob("*")):
        if not f.is_file() or f.suffix in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".pyc"}:
            continue
        try:
            text = f.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                tree.issue("10-secrets", f, "file contains a credential-like pattern")
                break


def validate_tree(tree: ContentTree) -> list[Issue]:
    """Run rules 1–8 and 10 on a loaded tree and return all issues (loader issues included)."""
    competency_ids = {c.id for c in tree.competencies.competencies} if tree.competencies else set()
    _rule1_unique_and_lang(tree)
    _rule2_references(tree, competency_ids)
    _rule3_prerequisites(tree)
    _rule4_multi_agent(tree)
    for p in tree.paths:
        if p.meta.status == "available":
            for m in p.modules:
                _module_completeness(tree, m)
    _rule6_traceability(tree)
    _rule7_challenges(tree)
    _rule8_lab(tree)
    _rule10_secrets(tree)
    return tree.issues


def validate(root: Path, lang: str = "en") -> tuple[ContentTree, list[Issue]]:
    tree = load_tree(root, lang)
    return tree, validate_tree(tree)
