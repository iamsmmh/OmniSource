#!/usr/bin/env python3
"""Validate app metadata independently from feed-envelope validation.

The command accepts an AltStore-family feed, a single app object, or a JSON
array. It never downloads URLs and never writes input files. Invalid metadata
returns a non-zero status, so it can be used as a publication gate.

Examples::

    python3 scripts/validation/validate_metadata.py feeds/apps.json --strict
    python3 scripts/validation/validate_metadata.py app.json
    cat app.json | python3 scripts/validation/validate_metadata.py -
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from omnisource.metadata_validation import validate_feed_metadata, validate_metadata


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("path", help="JSON file, URL-free local object, or '-' for stdin")
    parser.add_argument("--strict", action="store_true", help="promote metadata warnings to failures")
    return parser.parse_args(argv)


def _load(path: str) -> object:
    raw = sys.stdin.read() if path == "-" else Path(path).read_text(encoding="utf-8")
    return json.loads(raw)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        payload = _load(args.path)
    except (OSError, json.JSONDecodeError) as error:
        print(f"validate_metadata: cannot read {args.path}: {error}")
        return 1
    if isinstance(payload, dict) and "apps" in payload:
        report = validate_feed_metadata(payload, strict=args.strict)
    elif isinstance(payload, list):
        report = validate_feed_metadata({"apps": payload}, strict=args.strict)
    else:
        report = validate_metadata(payload, strict=args.strict)
    for error in report.errors:
        print(f"error: {error}")
    for warning in report.warnings:
        print(f"warning: {warning}")
    print(
        f"validate_metadata: {'OK' if report.ok else 'FAIL'} "
        f"({len(report.errors)} error(s), {len(report.warnings)} warning(s))"
    )
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
