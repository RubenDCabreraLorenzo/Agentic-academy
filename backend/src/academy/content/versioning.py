"""Rule 9: a content change requires a version bump relative to the latest published bundle."""

from __future__ import annotations

import json
from pathlib import Path

from academy.content.build import bundle_items, item_hashes, latest_bundle
from academy.content.loader import ContentTree


def check_version_bumps(tree: ContentTree, bundles_dir: Path) -> None:
    previous_file = latest_bundle(bundles_dir / tree.lang)
    if previous_file is None:
        return
    previous = json.loads(previous_file.read_text(encoding="utf-8"))
    old_hashes: dict[str, str] = previous.get("item_hashes", {})
    old_versions: dict[str, str] = previous.get("item_versions", {})
    items = bundle_items(tree)
    for key, digest in item_hashes(items).items():
        kind, item_id = key.split("/", 1)
        if key in old_hashes and old_hashes[key] != digest:
            version = items[kind][item_id].get("version")
            if version == old_versions.get(key):
                tree.issue(
                    "9-version",
                    tree.root,
                    f"{kind[:-1].replace('_', ' ')} '{item_id}' changed since bundle "
                    f"{previous['bundle_version']} but its version is still {version}",
                )
