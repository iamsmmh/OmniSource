#!/usr/bin/env python3
"""Validate discovery-store records (``data/discovered_sources.json``).

Fails (exit 1) when any record violates the schema, so the discovery
workflow can quarantine the file instead of publishing it.

Usage
-----
    python3 scripts/validation/validate_source.py
    python3 scripts/validation/validate_source.py --store data/discovered_sources.json --strict
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from omnisource.remote_validation import assert_publishable

ROOT = Path(__file__).resolve().parents[2]
STORE = ROOT / "data" / "discovered_sources.json"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--store", default=str(STORE), help="discovery store path")
    parser.add_argument("--strict", action="store_true", help="treat warnings as failures")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        store = json.loads(Path(args.store).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"validate_source: cannot read {args.store}: {exc}")
        return 1
    sources = store.get("sources", []) if isinstance(store, dict) else []
    errors: list[str] = []
    warnings: list[str] = []
    quarantined = 0
    for record in sources:
        if not isinstance(record, dict):
            errors.append("?: record must be an object")
            continue
        # Quarantine is the intended fail-closed destination for malformed or
        # not-yet-verifiable candidates. Validate its shape for reporting, but
        # do not turn an isolated record into a publication failure.
        if str(record.get("status", "")).casefold() in {"quarantined", "rejected"}:
            quarantined += 1
            warnings.append(f"{record.get('url', record.get('source_url', '?'))}: retained in quarantine")
            continue
        _ok, record_errors, record_warnings = assert_publishable(record)
        errors.extend(f"{record.get('url', '?')}: {error}" for error in record_errors)
        warnings.extend(f"{record.get('url', '?')}: {warning}" for warning in record_warnings)
    for message in errors:
        print(f"error: {message}")
    for message in warnings:
        print(f"warning: {message}")
    failed = bool(errors) or (args.strict and bool(warnings))
    print(
        f"validate_source: {len(sources)} record(s), {len(errors)} error(s), "
        f"{len(warnings)} warning(s), {quarantined} quarantined"
    )
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
