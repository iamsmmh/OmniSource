"""Runtime settings loader.

Catalog metadata lives in ``catalog.json`` (hand edited). Optional
``config/settings.json`` holds non-secret runtime policy; environment
variables override individual values so CI can tune a run without a commit.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from omnisource.errors import ConfigurationError


@dataclass(frozen=True)
class RuntimeSettings:
    """Non-secret runtime policy. Environment variables override values."""

    sync_workers: int = 8
    health_workers: int = 8
    request_timeout: float = 30.0
    request_retries: int = 3
    health_timeout: float = 12.0
    max_update_history: int = 100
    stale_after_days: int = 90

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> RuntimeSettings:
        return cls(
            sync_workers=max(1, _int(raw.get("syncWorkers"), cls.sync_workers)),
            health_workers=max(1, _int(raw.get("healthWorkers"), cls.health_workers)),
            request_timeout=max(1.0, _float(raw.get("requestTimeout"), cls.request_timeout)),
            request_retries=max(1, _int(raw.get("requestRetries"), cls.request_retries)),
            health_timeout=max(1.0, _float(raw.get("healthTimeout"), cls.health_timeout)),
            max_update_history=max(1, _int(raw.get("maxUpdateHistory"), cls.max_update_history)),
            stale_after_days=max(1, _int(raw.get("staleAfterDays"), cls.stale_after_days)),
        )

    def with_environment(self) -> RuntimeSettings:
        mapping = {
            "syncWorkers": "OMNISOURCE_SYNC_WORKERS",
            "healthWorkers": "OMNISOURCE_HEALTH_WORKERS",
            "requestTimeout": "OMNISOURCE_REQUEST_TIMEOUT",
            "requestRetries": "OMNISOURCE_REQUEST_RETRIES",
            "healthTimeout": "OMNISOURCE_HEALTH_TIMEOUT",
            "maxUpdateHistory": "OMNISOURCE_MAX_UPDATE_HISTORY",
            "staleAfterDays": "OMNISOURCE_STALE_AFTER_DAYS",
        }
        values = {key: os.environ.get(env) for key, env in mapping.items() if os.environ.get(env)}
        if not values:
            return self
        return RuntimeSettings.from_dict({**self.to_dict(), **values})

    def to_dict(self) -> dict[str, Any]:
        return {
            "syncWorkers": self.sync_workers,
            "healthWorkers": self.health_workers,
            "requestTimeout": self.request_timeout,
            "requestRetries": self.request_retries,
            "healthTimeout": self.health_timeout,
            "maxUpdateHistory": self.max_update_history,
            "staleAfterDays": self.stale_after_days,
        }


def load_runtime_settings(root: Path) -> RuntimeSettings:
    raw = _load_object(root / "config" / "settings.json")
    return RuntimeSettings.from_dict(raw).with_environment()


def _load_object(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ConfigurationError(f"invalid configuration file {path}: {error}") from error
    return raw if isinstance(raw, dict) else {}


def _int(value: Any, default: int) -> int:
    try:
        return int(value) if value is not None else default
    except (TypeError, ValueError):
        return default


def _float(value: Any, default: float) -> float:
    try:
        return float(value) if value is not None else default
    except (TypeError, ValueError):
        return default
