"""``academy content validate|build``."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from academy.content.build import build
from academy.content.solutions import check_solutions
from academy.content.validate import validate


def _report(issues: list[object], as_json: bool) -> None:
    rows = [i.as_dict() for i in issues]  # type: ignore[attr-defined]
    if as_json:
        print(json.dumps({"ok": not rows, "issues": rows}, indent=2))
        return
    for r in rows:
        print(f"[{r['rule']}] {r['path']}: {r['message']}")
    print("content OK" if not rows else f"{len(rows)} issue(s) found", file=sys.stderr)


def add_parser(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    content = sub.add_parser("content", help="validate and build educational content")
    csub = content.add_subparsers(dest="content_cmd", required=True)
    for name in ("validate", "build"):
        p = csub.add_parser(name)
        p.add_argument("--root", type=Path, default=Path("content"))
        p.add_argument("--lang", default="en")
        p.add_argument("--json", action="store_true", help="machine-readable report")
        p.add_argument("--run-solutions", action="store_true", help="execute rule 7 checks")
        p.add_argument("--previous", type=Path, default=None, help="bundle dir for rule 9")
        if name == "build":
            p.add_argument("--out", type=Path, default=Path("dist/content"))


def run(args: argparse.Namespace) -> int:
    root = args.root
    if not root.exists() and Path("../content").exists():
        root = Path("../content")
    tree, issues = validate(root, args.lang)
    previous = args.previous or (args.out if args.content_cmd == "build" else None)
    if previous is not None:
        from academy.content.versioning import check_version_bumps

        check_version_bumps(tree, previous)
        issues = tree.issues
    if args.run_solutions and not issues:
        check_solutions(tree)
        issues = tree.issues
    _report(issues, args.json)
    if issues:
        return 1
    if args.content_cmd == "build":
        path, created = build(tree, args.out)
        print(f"{'built' if created else 'unchanged'}: {path}")
    return 0
