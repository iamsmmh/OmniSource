"""Structured observability primitives for scheduled and local builds.

Logs are JSONL, metrics are a stable JSON snapshot, and sensitive values are
redacted before persistence.  The implementation is intentionally compatible
with stdout collectors, GitHub step summaries, and future OpenTelemetry
exporters without requiring a runtime dependency.
"""

from __future__ import annotations

import json
import logging
import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from omnisource.events import _scrub


def utcnow() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


@dataclass
class Metrics:
    counters: dict[str, int] = field(default_factory=dict)
    timings_ms: dict[str, list[float]] = field(default_factory=dict)
    gauges: dict[str, float] = field(default_factory=dict)
    errors: int = 0

    def increment(self, name: str, value: int = 1) -> None:
        self.counters[name] = self.counters.get(name, 0) + int(value)

    def gauge(self, name: str, value: float) -> None:
        self.gauges[name] = float(value)

    def observe(self, name: str, milliseconds: float) -> None:
        self.timings_ms.setdefault(name, []).append(round(float(milliseconds), 3))

    @contextmanager
    def timer(self, name: str) -> Iterator[None]:
        started = time.perf_counter()
        try:
            yield
        except Exception:
            self.errors += 1
            self.increment(f"{name}.errors")
            raise
        finally:
            self.observe(name, (time.perf_counter() - started) * 1000)

    def snapshot(self) -> dict[str, Any]:
        timings = {}
        for name, values in self.timings_ms.items():
            ordered = sorted(values)
            timings[name] = {
                "count": len(ordered),
                "minMs": ordered[0] if ordered else 0,
                "maxMs": ordered[-1] if ordered else 0,
                "p50Ms": ordered[len(ordered) // 2] if ordered else 0,
                "p95Ms": ordered[min(len(ordered) - 1, int(len(ordered) * 0.95))] if ordered else 0,
            }
        return {
            "schemaVersion": 1,
            "generatedAt": utcnow(),
            "counters": dict(sorted(self.counters.items())),
            "gauges": dict(sorted(self.gauges.items())),
            "timings": timings,
            "errors": self.errors,
        }


class JsonLogHandler(logging.Handler):
    """Write structured records to a JSONL file without leaking secrets."""

    def __init__(self, path: Path) -> None:
        super().__init__()
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def emit(self, record: logging.LogRecord) -> None:
        try:
            payload = {
                "at": utcnow(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
            }
            if record.exc_info:
                payload["exception"] = record.exc_info[0].__name__ if record.exc_info[0] else "Exception"
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(_scrub(payload), ensure_ascii=False, separators=(",", ":")) + "\n")
        except OSError:
            self.handleError(record)


def configure_logging(log_dir: Path, *, level: int = logging.INFO) -> logging.Logger:
    """Configure the ``omnisource`` logger for discovery/validation/sync logs."""
    logger = logging.getLogger("omnisource")
    logger.setLevel(level)
    logger.propagate = False
    if not any(isinstance(handler, JsonLogHandler) for handler in logger.handlers):
        logger.addHandler(JsonLogHandler(Path(log_dir) / "omnisource.jsonl"))
        logger.addHandler(logging.StreamHandler())
    return logger


__all__ = ["JsonLogHandler", "Metrics", "configure_logging"]
