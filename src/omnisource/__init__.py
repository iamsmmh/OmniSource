"""OmniSource — an automatically maintained AltStore-compatible iOS app source.

This package *is* the feed pipeline: ``scripts/omnisource.py`` is a thin CLI
over ``omnisource.pipeline``. Downstream code (the CLI, the validator) imports
from here or from the named submodules.
"""

from __future__ import annotations

__version__ = "3.2.0"
__all__ = ["__version__"]
