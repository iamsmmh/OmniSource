#!/usr/bin/env python3
"""Build the global source registry from generated source intelligence."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from omnisource.io import read_json, write_json_stable
from omnisource.source_registry import build_registry

ROOT = Path(__file__).resolve().parents[2]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", default=str(ROOT / "feeds" / "sources.json"))
    parser.add_argument("--discovered", default=str(ROOT / "data" / "published_sources.json"))
    parser.add_argument("--status", default=str(ROOT / "data" / "status.json"))
    parser.add_argument("--reputation", default=str(ROOT / "data" / "source_reputation.json"))
    parser.add_argument("--previous", default=str(ROOT / "data" / "source_registry.json"))
    parser.add_argument("--out", default=str(ROOT / "data" / "source_registry.json"))
    return parser.parse_args(argv)


def _sources(path: str, key: str) -> list[dict]:
    value = read_json(Path(path))
    if isinstance(value, dict) and isinstance(value.get(key), list):
        return [item for item in value[key] if isinstance(item, dict)]
    return []


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    source_doc = read_json(Path(args.sources))
    source_records = _sources(args.sources, "sources")
    if not source_records and isinstance(source_doc, list):
        source_records = [item for item in source_doc if isinstance(item, dict)]
    discovered = _sources(args.discovered, "sources")
    status = read_json(Path(args.status))
    reputation = read_json(Path(args.reputation))
    previous = read_json(Path(args.previous))
    document = build_registry(
        source_records,
        discovered=discovered,
        status=status if isinstance(status, dict) else None,
        reputation=reputation if isinstance(reputation, dict) else None,
        previous=previous if isinstance(previous, dict) else None,
    )
    changed = write_json_stable(Path(args.out), document)
    print(f"registry: {document['count']} sources{'' if changed else ' (unchanged)'} -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
