#!/usr/bin/env python3
"""Validate one upstream release object (JSON file or stdin).

Accepts GitHub/GitLab/forge release shapes: requires a tag, an assets
array with at least one installable ``.ipa``/``.tipa``, and well-formed
digest fields.

Usage
-----
    python3 scripts/validation/validate_release.py release.json
    gh api repos/o/r/releases/latest | python3 scripts/validation/validate_release.py -
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from omnisource.remote_validation import validate_remote_release


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("path", help="JSON file with one release object ('-' for stdin)")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        raw = sys.stdin.read() if args.path == "-" else Path(args.path).read_text(encoding="utf-8")
        release = json.loads(raw)
    except (OSError, ValueError) as exc:
        print(f"validate_release: cannot read {args.path}: {exc}")
        return 1
    errors = validate_remote_release(release)
    for error in errors:
        print(f"error: {error}")
    print(f"validate_release: {'FAIL' if errors else 'OK'} ({len(errors)} error(s))")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
