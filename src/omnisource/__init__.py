"""OmniSource — application distribution platform.

This package *is* the feed pipeline. It is not a parallel unused service:
``scripts/omnisource.py`` is a thin CLI over ``omnisource.pipeline``.

The public surface is intentionally small. Downstream code (the CLI, the
validator, tests) should import from here or from the named submodules.
"""

from __future__ import annotations

__version__ = "3.0.0"
__all__ = ["__version__"]
