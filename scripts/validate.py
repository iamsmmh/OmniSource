#!/usr/bin/env python3
"""Offline validator for the OmniSource catalog and generated feeds.

Thin wrapper over :mod:`omnisource.validation`. See that module for the
rule set. Exit code 0 = clean, 1 = at least one error.

Usage
-----
    python3 scripts/validate.py
    python3 scripts/validate.py --strict
    python3 scripts/validate.py feeds/ytlite.json
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from omnisource.validation import main

if __name__ == "__main__":
    sys.exit(main())
