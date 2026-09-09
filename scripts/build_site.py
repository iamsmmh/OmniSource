#!/usr/bin/env python3
"""Assemble the static GitHub Pages site into ``_site/``.

Thin wrapper over :mod:`omnisource.site` (the actual builder). The site
bundles the website, assets, generated feeds (organized + historical flat
URLs), the API mirror with gzip twins, static app pages, ``sitemap.xml``
and ``robots.txt`` — the exact artifact ``actions/upload-pages-artifact``
deploys.

Usage
-----
    python3 scripts/build_site.py                 # build into _site/
    python3 scripts/build_site.py --output dist   # custom output directory
"""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS = str(Path(__file__).resolve().parent)
if _SCRIPTS in sys.path:
    sys.path.remove(_SCRIPTS)
_SRC = str(Path(__file__).resolve().parents[1] / "src")
if _SRC in sys.path:
    sys.path.remove(_SRC)
sys.path.insert(0, _SRC)

from omnisource.site import main

if __name__ == "__main__":
    sys.exit(main())
