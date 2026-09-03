"""GitHub Actions-friendly logging.

Emits ``::warning::`` / ``::error::`` annotations when ``GITHUB_ACTIONS`` is
set, and collapsible ``::group::`` sections. Locally it prints plain text.
"""

from __future__ import annotations

import logging
import os
import sys
from typing import ClassVar

log = logging.getLogger("omnisource")


class ActionsFormatter(logging.Formatter):
    """Emit ``::warning::``/``::error::`` annotations when running on Actions."""

    PREFIX: ClassVar[dict[int, str]] = {
        logging.WARNING: "::warning::",
        logging.ERROR: "::error::",
        logging.CRITICAL: "::error::",
    }

    def __init__(self, *, annotate: bool) -> None:
        super().__init__("%(levelname)-7s %(message)s")
        self.annotate = annotate

    def format(self, record: logging.LogRecord) -> str:
        message = record.getMessage()
        if self.annotate:
            prefix = self.PREFIX.get(record.levelno, "")
            return f"{prefix}{message}" if prefix else message
        return f"{record.levelname:<7} {message}"


def configure_logging(verbose: bool) -> None:
    if log.handlers:
        log.setLevel(logging.DEBUG if verbose else logging.INFO)
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(ActionsFormatter(annotate=bool(os.environ.get("GITHUB_ACTIONS"))))
    log.addHandler(handler)
    log.setLevel(logging.DEBUG if verbose else logging.INFO)
    log.propagate = False


class Group:
    """Collapsible log group; a no-op outside GitHub Actions."""

    def __init__(self, title: str) -> None:
        self.title = title
        self.enabled = bool(os.environ.get("GITHUB_ACTIONS"))

    def __enter__(self) -> Group:
        print(f"::group::{self.title}" if self.enabled else f"\n=== {self.title} ===", flush=True)
        return self

    def __exit__(self, *exc: object) -> None:
        if self.enabled:
            print("::endgroup::", flush=True)
