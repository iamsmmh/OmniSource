#!/usr/bin/env python3
"""OmniSource feed builder (CLI wrapper).

Thin entry point over :mod:`omnisource.pipeline`. The package lives in
``src/omnisource``; this script puts ``src/`` on ``sys.path`` so a bare
``python3 scripts/omnisource.py`` keeps working without an install step.

Usage
-----
    python3 scripts/omnisource.py                 # full pipeline
    python3 scripts/omnisource.py --no-sync       # rebuild feeds from state.json
    python3 scripts/omnisource.py --no-health     # skip network link probing
    python3 scripts/omnisource.py --only ytlite   # restrict sync to one app
    python3 scripts/omnisource.py --incremental   # skip unchanged remotes
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from omnisource.cli import main

if __name__ == "__main__":
    sys.exit(main())
