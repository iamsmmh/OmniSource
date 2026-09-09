#!/usr/bin/env python3
"""Generate static app detail pages from feed metadata.

Every catalog app gets ``apps/<slug>/index.html``. Pages are derived from the
same generated documents the pipeline produces (``feeds/state.json``,
``health.json``, ``verification.json``, ``duplicates.json``) — they are never
edited by hand, and the sync pipeline regenerates them on every build.

Usage
-----
    python3 scripts/generate_pages.py              # write apps/ next to catalog.json
    python3 scripts/generate_pages.py --output dist/apps
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SCRIPTS = str(Path(__file__).resolve().parent)
if _SCRIPTS in sys.path:
    sys.path.remove(_SCRIPTS)
_SRC = str(Path(__file__).resolve().parents[1] / "src")
if _SRC in sys.path:
    sys.path.remove(_SRC)
sys.path.insert(0, _SRC)


def _load(path: Path, default: object) -> object:
    try:
        import json

        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def main(argv: list[str] | None = None) -> int:
    from omnisource.app_pages import build_app_pages
    from omnisource.domain import Catalog

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1], help="repository root")
    parser.add_argument("--output", type=Path, default=None, help="pages output directory (default: <root>/apps)")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    catalog_raw = _load(root / "catalog.json", None)
    if not isinstance(catalog_raw, dict):
        print("generate_pages: catalog.json is missing or invalid")
        return 2

    state = _load(root / "feeds" / "state.json", {})
    health = _load(root / "feeds" / "health.json", {})
    verification = _load(root / "feeds" / "verification.json", {})
    duplicates = _load(root / "feeds" / "duplicates.json", {})
    required = (state, health, verification, duplicates)
    if not all(isinstance(item, dict) for item in required):
        print("generate_pages: run scripts/omnisource.py first (missing generated feeds)")
        return 2

    catalog = Catalog.from_dict(catalog_raw)
    pages_dir = (args.output or root / "apps").resolve()
    changed = build_app_pages(catalog, state, health, verification, duplicates, pages_dir=pages_dir)
    print(f"generate_pages: wrote {len(changed)} page(s) to {pages_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
