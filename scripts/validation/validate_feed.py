#!/usr/bin/env python3
"""Validate a fetched feed envelope (file or URL) before it may publish.

Checks the envelope schema, every app entry, duplicate bundle IDs and —
optionally — download reachability. Invalid feeds must never be published.

Usage
-----
    python3 scripts/validation/validate_feed.py feeds/apps.json
    python3 scripts/validation/validate_feed.py https://example.com/apps.json --check-downloads
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from omnisource import autodiscovery
from omnisource.errors import ProviderError
from omnisource.remote_validation import assert_publishable


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("target", help="feed JSON file or https URL")
    parser.add_argument("--check-downloads", action="store_true", help="probe the first 25 download URLs")
    return parser.parse_args(argv)


def _load(target: str) -> tuple[bool, object, str]:
    if target.startswith(("http://", "https://")):
        try:
            return True, autodiscovery.fetch_json(target), ""
        except ProviderError as exc:
            return False, None, str(exc)
    try:
        return True, json.loads(Path(target).read_text(encoding="utf-8")), ""
    except (OSError, ValueError) as exc:
        return False, None, str(exc)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    ok, payload, error = _load(args.target)
    if not ok:
        print(f"validate_feed: cannot load {args.target}: {error}")
        return 1
    record = autodiscovery.new_record(url=args.target, name=args.target)
    publishable, errors, warnings = assert_publishable(
        record, feed_payload=payload, check_downloads=args.check_downloads
    )
    for message in errors:
        print(f"error: {message}")
    for message in warnings:
        print(f"warning: {message}")
    apps = len(payload.get("apps", [])) if isinstance(payload, dict) else 0
    print(f"validate_feed: {apps} app(s), publishable={publishable}")
    return 0 if publishable else 1


if __name__ == "__main__":
    sys.exit(main())
