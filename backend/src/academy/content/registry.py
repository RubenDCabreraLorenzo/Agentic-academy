"""Runtime access to published content bundles.

Every bundle in ``CONTENT_DIR/<lang>/`` is loaded (they are immutable). New activity uses the
current (latest) bundle; attempts and submissions resolve items by their pinned bundle version
(data-model §1.9, FR-051).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from academy.config import get_settings
from academy.content.build import BUNDLE_PREFIX


class ContentUnavailableError(RuntimeError):
    pass


@dataclass
class Bundle:
    data: dict[str, Any]

    @property
    def version(self) -> str:
        return str(self.data["bundle_version"])

    def path(self, path_id: str) -> dict[str, Any] | None:
        item: dict[str, Any] | None = self.data["paths"].get(path_id)
        return item

    def module(self, module_id: str) -> dict[str, Any] | None:
        item: dict[str, Any] | None = self.data["modules"].get(module_id)
        return item

    def knowledge_check(self, check_id: str) -> dict[str, Any] | None:
        item: dict[str, Any] | None = self.data["knowledge_checks"].get(check_id)
        return item

    def challenge(self, challenge_id: str) -> dict[str, Any] | None:
        item: dict[str, Any] | None = self.data["challenges"].get(challenge_id)
        return item

    def lab_scenario(self, scenario_id: str) -> dict[str, Any] | None:
        item: dict[str, Any] | None = self.data["lab_scenarios"].get(scenario_id)
        return item

    @property
    def competencies(self) -> dict[str, dict[str, Any]]:
        return {c["id"]: c for c in self.data["competencies"]}

    @property
    def deprecations(self) -> list[dict[str, Any]]:
        return list(self.data.get("deprecations", []))


@dataclass
class Registry:
    bundles: dict[str, dict[str, Bundle]] = field(default_factory=dict)

    @classmethod
    def load(cls, content_dir: Path) -> Registry:
        reg = cls()
        if not content_dir.is_dir():
            return reg
        for lang_dir in sorted(p for p in content_dir.iterdir() if p.is_dir()):
            for f in sorted(lang_dir.glob(f"{BUNDLE_PREFIX}*.json")):
                data = json.loads(f.read_text(encoding="utf-8"))
                reg.bundles.setdefault(lang_dir.name, {})[data["bundle_version"]] = Bundle(data)
        return reg

    def current(self, lang: str = "en") -> Bundle:
        versions = self.bundles.get(lang)
        if not versions:
            raise ContentUnavailableError(f"no content bundle for language '{lang}'")
        return versions[max(versions)]

    def get(self, version: str, lang: str = "en") -> Bundle:
        try:
            return self.bundles[lang][version]
        except KeyError as exc:
            raise ContentUnavailableError(f"bundle {version} not available") from exc

    def all(self, lang: str = "en") -> list[Bundle]:
        return [self.bundles[lang][v] for v in sorted(self.bundles.get(lang, {}))]


_override: Registry | None = None
_cache: tuple[tuple[str, ...], Registry] | None = None


def _bundle_files(content_dir: Path) -> tuple[str, ...]:
    if not content_dir.is_dir():
        return ()
    return tuple(sorted(str(p) for p in content_dir.glob(f"*/{BUNDLE_PREFIX}*.json")))


def get_registry() -> Registry:
    """Bundles are immutable, so the registry is reloaded only when new bundle files appear."""
    global _cache
    if _override is not None:
        return _override
    content_dir = get_settings().content_dir
    files = _bundle_files(content_dir)
    if _cache is None or _cache[0] != files:
        _cache = (files, Registry.load(content_dir))
    return _cache[1]


def set_registry(registry: Registry | None) -> None:
    """Testing hook: replace the process registry."""
    global _override
    _override = registry
