"""Command-line entry points for the OmniSource pipeline."""

from __future__ import annotations

import argparse
import sys

from omnisource import __version__
from omnisource.errors import SyncError
from omnisource.logutil import configure_logging, log
from omnisource.pipeline import run


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="OmniSource distribution pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--no-sync",
        action="store_true",
        help="rebuild from feeds/state.json without hitting upstream APIs",
    )
    parser.add_argument("--no-health", action="store_true", help="skip download link probing")
    parser.add_argument(
        "--verify-downloads",
        action="store_true",
        help="stream-download and hash app assets (full integrity; fails on rejection)",
    )
    parser.add_argument(
        "--verify-stale-days",
        type=int,
        default=None,
        metavar="N",
        help=(
            "with --verify-downloads: only re-verify assets whose recorded verification is older "
            "than N days (default: verify everything)"
        ),
    )
    parser.add_argument(
        "--verify-limit",
        type=int,
        default=0,
        metavar="N",
        help="with --verify-downloads: cap the number of apps verified per run (default: no cap)",
    )
    parser.add_argument("--only", metavar="SLUG", action="append", help="restrict the sync stage to these app slugs")
    parser.add_argument(
        "--incremental",
        action="store_true",
        help="skip pagination when the newest matching asset URL is unchanged",
    )
    parser.add_argument("--workers", type=int, default=8, help="concurrent link probes (default: 8)")
    parser.add_argument("-v", "--verbose", action="store_true", help="debug logging")
    parser.add_argument("--version", action="store_true", help="show the OmniSource version and exit")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.version:
        print(__version__)
        return 0
    configure_logging(args.verbose)
    try:
        code, _report = run(
            no_sync=args.no_sync,
            no_health=args.no_health,
            verify=args.verify_downloads,
            verify_stale_days=args.verify_stale_days,
            verify_limit=args.verify_limit,
            only=set(args.only) if args.only else None,
            incremental=args.incremental,
            workers=args.workers,
        )
        return code
    except SyncError as error:
        log.error("%s", error)
        return 1
    except KeyboardInterrupt:  # pragma: no cover
        return 130


if __name__ == "__main__":
    sys.exit(main())
