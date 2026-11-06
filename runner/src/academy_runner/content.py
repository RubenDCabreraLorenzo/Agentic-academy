"""Read challenges from immutable content bundles by pinned ``bundle_version`` (runner protocol §7)."""

from __future__ import annotations

import json
import re
import threading
from pathlib import Path
from typing import Any

_VERSION = re.compile(r"^[0-9A-Za-z_-]{1,64}$")


class ContentMissingError(RuntimeError):
    """The pinned bundle version is not available on this runner host (infrastructure error)."""


class BundleStore:
    def __init__(self, content_dir: Path) -> None:
        self.content_dir = content_dir
        self._cache: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()

    def challenge(self, bundle_version: str, challenge_id: str) -> dict[str, Any]:
        if not _VERSION.match(bundle_version):
            raise ContentMissingError("invalid bundle version")
        with self._lock:
            bundle = self._cache.get(bundle_version)
            if bundle is None:
                matches = list(self.content_dir.glob(f"*/bundle-{bundle_version}.json"))
                if not matches:
                    raise ContentMissingError(f"bundle {bundle_version} not found")
                bundle = json.loads(matches[0].read_text(encoding="utf-8"))
                self._cache[bundle_version] = bundle
        ch = bundle["challenges"].get(challenge_id)
        if ch is None:
            raise ContentMissingError(f"challenge {challenge_id} not in bundle {bundle_version}")
        return dict(ch)
