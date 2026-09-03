#!/usr/bin/env python3
"""Run the optional local read-only OmniSource API.

The static GitHub Pages feeds do not depend on this process. For local use:
``python3 scripts/api_server.py --root . --port 8000``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from omnisource.api_server import serve


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="OmniSource repository root")
    parser.add_argument("--host", default="0.0.0.0")  # noqa: S104
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    serve(args.root, host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
