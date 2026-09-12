#!/usr/bin/env python3
"""Validate one app entry (JSON file or stdin) against the app rules.

Usage
-----
    python3 scripts/validation/validate_app.py app.json
    cat app.json | python3 scripts/validation/validate_app.py -
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from omnisource.remote_validation import check_url_reachable, validate_remote_app


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("path", help="JSON file with one app object ('-' for stdin)")
    parser.add_argument("--check-download", action="store_true", help="also probe downloadURL reachability")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        raw = sys.stdin.read() if args.path == "-" else Path(args.path).read_text(encoding="utf-8")
        app = json.loads(raw)
    except (OSError, ValueError) as exc:
        print(f"validate_app: cannot read {args.path}: {exc}")
        return 1
    errors = validate_remote_app(app)
    if args.check_download and isinstance(app, dict):
        ok, detail = check_url_reachable(str(app.get("downloadURL", "")))
        if not ok:
            errors.append(f"downloadURL unreachable ({detail})")
    for error in errors:
        print(f"error: {error}")
    print(f"validate_app: {'FAIL' if errors else 'OK'} ({len(errors)} error(s))")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
