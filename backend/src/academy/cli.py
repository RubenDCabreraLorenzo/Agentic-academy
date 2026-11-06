"""``academy`` command-line entry point."""

from __future__ import annotations

import argparse
import sys

from academy.content import cli as content_cli


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="academy")
    sub = parser.add_subparsers(dest="cmd", required=True)
    content_cli.add_parser(sub)

    dev = sub.add_parser("dev", help="development helpers")
    dsub = dev.add_subparsers(dest="dev_cmd", required=True)
    seed_p = dsub.add_parser("seed", help="create a verified demo learner (not in production)")
    seed_p.add_argument("--reset", action="store_true", help="delete the demo learner and its progress first")

    maint = sub.add_parser("maintenance", help="maintenance jobs")
    msub = maint.add_subparsers(dest="maint_cmd", required=True)
    msub.add_parser("purge-unverified", help="delete unverified accounts older than 30 days")

    args = parser.parse_args(argv)
    if args.cmd == "content":
        return content_cli.run(args)
    if args.cmd == "dev":
        from academy.shared.seed import seed

        return seed(reset=args.reset)
    if args.cmd == "maintenance":
        from academy.auth.maintenance import purge_unverified

        print(f"deleted {purge_unverified()} unverified account(s)")
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
