"""Static test-id discovery for the security suite (mirrors the content loader)."""

from __future__ import annotations

import ast


def ids_for(files: dict[str, str]) -> list[str]:
    ids = []
    for name, source in sorted(files.items()):
        base = name.rsplit("/", 1)[-1]
        if not (base.startswith("test_") and base.endswith(".py")):
            continue
        for node in ast.parse(source).body:
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                ids.append(f"{name}::{node.name}")
    return ids
