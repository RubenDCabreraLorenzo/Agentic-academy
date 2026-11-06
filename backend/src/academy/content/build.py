"""Build immutable, versioned content bundles (contracts/content-schema.md "Bundle output").

A bundle is never overwritten. If the content is identical to the latest bundle, no new bundle is
written. Reference solutions are never included.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from academy.content.loader import ContentTree, LoadedChallenge, LoadedModule

BUNDLE_PREFIX = "bundle-"


def _challenge(ch: LoadedChallenge, module_id: str) -> dict[str, Any]:
    data = ch.meta.model_dump(mode="json")
    data["module_id"] = module_id
    data["starter_files"] = ch.starter
    data["tests"] = ch.tests
    data["test_ids"] = ch.test_ids
    return data


def _module(m: LoadedModule) -> dict[str, Any]:
    data = m.meta.model_dump(mode="json")
    data["path_id"] = m.path_id
    data["lessons"] = [
        {**ls.meta.model_dump(mode="json"), "body_markdown": ls.body, "anchors": sorted(ls.anchors)}
        for ls in m.lessons
    ]
    data["knowledge_check_id"] = m.knowledge_check.id if m.knowledge_check else None
    data["challenge_ids"] = [c.meta.id for c in m.challenges]
    return data


def bundle_items(tree: ContentTree) -> dict[str, Any]:
    """Language-specific bundle content, without versioning metadata."""
    paths, modules, checks, challenges = {}, {}, {}, {}
    for p in tree.paths:
        paths[p.meta.id] = p.meta.model_dump(mode="json")
        for m in p.modules:
            modules[m.meta.id] = _module(m)
            if m.knowledge_check:
                kc = m.knowledge_check.model_dump(mode="json")
                kc["module_id"] = m.meta.id
                checks[kc["id"]] = kc
            for ch in m.challenges:
                challenges[ch.meta.id] = _challenge(ch, m.meta.id)
    return {
        "competencies": [c.model_dump(mode="json") for c in tree.competencies.competencies]
        if tree.competencies
        else [],
        "paths": paths,
        "modules": modules,
        "knowledge_checks": checks,
        "challenges": challenges,
        "lab_scenarios": {sid: doc for sid, (doc, _p) in tree.lab_scenarios.items()},
        "deprecations": tree.deprecations.model_dump(mode="json")["deprecations"],
    }


def content_hash(items: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(items, sort_keys=True).encode()).hexdigest()


def item_hashes(items: dict[str, Any]) -> dict[str, str]:
    """Per-item hashes used by the version-bump rule (rule 9)."""
    out: dict[str, str] = {}
    for kind in ("paths", "modules", "knowledge_checks", "challenges", "lab_scenarios"):
        for item_id, item in items[kind].items():
            body = {k: v for k, v in item.items() if k not in {"version", "last_reviewed"}}
            out[f"{kind}/{item_id}"] = hashlib.sha256(
                json.dumps(body, sort_keys=True).encode()
            ).hexdigest()
    return out


def latest_bundle(lang_dir: Path) -> Path | None:
    bundles = sorted(lang_dir.glob(f"{BUNDLE_PREFIX}*.json"))
    return bundles[-1] if bundles else None


def build(tree: ContentTree, out: Path, now: datetime | None = None) -> tuple[Path, bool]:
    """Write a new bundle under ``out/<lang>/``. Returns ``(path, created)``."""
    items = bundle_items(tree)
    digest = content_hash(items)
    lang_dir = out / tree.lang
    lang_dir.mkdir(parents=True, exist_ok=True)
    previous = latest_bundle(lang_dir)
    if previous is not None:
        prev = json.loads(previous.read_text(encoding="utf-8"))
        if prev.get("content_hash") == digest:
            return previous, False
    stamp = (now or datetime.now(UTC)).strftime("%Y%m%dT%H%M%SZ")
    version = f"{stamp}-{digest[:8]}"
    target = lang_dir / f"{BUNDLE_PREFIX}{version}.json"
    if target.exists():
        raise FileExistsError(f"refusing to overwrite existing bundle {target}")
    bundle = {
        "bundle_version": version,
        "built_at": (now or datetime.now(UTC)).isoformat(),
        "lang": tree.lang,
        "content_hash": digest,
        "item_hashes": item_hashes(items),
        "item_versions": {
            f"{kind}/{item_id}": item.get("version")
            for kind in ("paths", "modules", "knowledge_checks", "challenges", "lab_scenarios")
            for item_id, item in items[kind].items()
        },
        **items,
    }
    with target.open("x", encoding="utf-8") as fh:
        json.dump(bundle, fh, ensure_ascii=False, sort_keys=True)
    return target, True
