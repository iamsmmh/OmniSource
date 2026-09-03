"""Structured configuration loaders.

Catalog metadata remains backwards-compatible and hand editable. Optional
``config/*.json`` files hold provider/runtime policy and curation so automatic
synchronization never overwrites editorial decisions.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from omnisource.errors import ConfigurationError

DEFAULT_CATEGORIES = (
    "audio",
    "video",
    "social",
    "productivity",
    "utilities",
    "developer-tools",
    "education",
    "photography",
    "games",
    "networking",
    "customization",
    "security",
    "other",
)


@dataclass(frozen=True)
class RuntimeSettings:
    """Non-secret runtime policy. Environment variables override values."""

    api_version: str = "v1"
    sync_workers: int = 8
    health_workers: int = 8
    request_timeout: float = 30.0
    request_retries: int = 3
    health_timeout: float = 12.0
    hash_assets: bool = False
    hash_max_bytes: int = 512 * 1024 * 1024
    inspect_packages: bool = False
    max_update_history: int = 100
    max_search_description: int = 1_500
    allow_http_sources: bool = False

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> RuntimeSettings:
        return cls(
            api_version=str(raw.get("apiVersion", cls.api_version)),
            sync_workers=max(1, _int(raw.get("syncWorkers"), cls.sync_workers)),
            health_workers=max(1, _int(raw.get("healthWorkers"), cls.health_workers)),
            request_timeout=max(1.0, _float(raw.get("requestTimeout"), cls.request_timeout)),
            request_retries=max(1, _int(raw.get("requestRetries"), cls.request_retries)),
            health_timeout=max(1.0, _float(raw.get("healthTimeout"), cls.health_timeout)),
            hash_assets=_bool(raw.get("hashAssets"), cls.hash_assets),
            hash_max_bytes=max(1, _int(raw.get("hashMaxBytes"), cls.hash_max_bytes)),
            inspect_packages=_bool(raw.get("inspectPackages"), cls.inspect_packages),
            max_update_history=max(1, _int(raw.get("maxUpdateHistory"), cls.max_update_history)),
            max_search_description=max(100, _int(raw.get("maxSearchDescription"), cls.max_search_description)),
            allow_http_sources=_bool(raw.get("allowHttpSources"), cls.allow_http_sources),
        )

    def with_environment(self) -> RuntimeSettings:
        values = {
            "syncWorkers": os.environ.get("OMNISOURCE_SYNC_WORKERS"),
            "healthWorkers": os.environ.get("OMNISOURCE_HEALTH_WORKERS"),
            "requestTimeout": os.environ.get("OMNISOURCE_REQUEST_TIMEOUT"),
            "requestRetries": os.environ.get("OMNISOURCE_REQUEST_RETRIES"),
            "healthTimeout": os.environ.get("OMNISOURCE_HEALTH_TIMEOUT"),
            "hashAssets": os.environ.get("OMNISOURCE_HASH_ASSETS"),
            "hashMaxBytes": os.environ.get("OMNISOURCE_HASH_MAX_BYTES"),
            "inspectPackages": os.environ.get("OMNISOURCE_INSPECT_PACKAGES"),
        }
        values = {key: value for key, value in values.items() if value is not None}
        return RuntimeSettings.from_dict({**self.to_dict(), **values}) if values else self

    def to_dict(self) -> dict[str, Any]:
        return {
            "apiVersion": self.api_version,
            "syncWorkers": self.sync_workers,
            "healthWorkers": self.health_workers,
            "requestTimeout": self.request_timeout,
            "requestRetries": self.request_retries,
            "healthTimeout": self.health_timeout,
            "hashAssets": self.hash_assets,
            "hashMaxBytes": self.hash_max_bytes,
            "inspectPackages": self.inspect_packages,
            "maxUpdateHistory": self.max_update_history,
            "maxSearchDescription": self.max_search_description,
            "allowHttpSources": self.allow_http_sources,
        }


@dataclass(frozen=True)
class Category:
    id: str
    name: str
    description: str = ""
    aliases: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "aliases": list(self.aliases),
        }


@dataclass(frozen=True)
class Curation:
    featured: tuple[str, ...] = ()
    recommended: tuple[str, ...] = ()
    badges: dict[str, tuple[str, ...]] = field(default_factory=dict)
    aliases: dict[str, tuple[str, ...]] = field(default_factory=dict)


def load_runtime_settings(root: Path) -> RuntimeSettings:
    raw = _load_object(root / "config" / "settings.json")
    return RuntimeSettings.from_dict(raw).with_environment()


def load_categories(root: Path) -> tuple[Category, ...]:
    raw = _load_object(root / "config" / "categories.json")
    entries = raw.get("categories", raw) if isinstance(raw, dict) else raw
    result: list[Category] = []
    if isinstance(entries, list):
        for item in entries:
            if not isinstance(item, dict) or not item.get("id"):
                continue
            aliases = item.get("aliases")
            result.append(
                Category(
                    id=str(item["id"]),
                    name=str(item.get("name") or str(item["id"]).replace("-", " ").title()),
                    description=str(item.get("description") or ""),
                    aliases=tuple(str(alias) for alias in aliases if alias) if isinstance(aliases, list) else (),
                )
            )
    return tuple(result) or tuple(Category(item, item.replace("-", " ").title()) for item in DEFAULT_CATEGORIES)


def load_curation(root: Path) -> Curation:
    curated = _load_object(root / "config" / "curated.json")
    featured = _load_object(root / "config" / "featured.json")
    featured_ids = featured.get("apps", featured.get("featured", [])) if isinstance(featured, dict) else []
    recommended = curated.get("recommended", []) if isinstance(curated, dict) else []
    badges = curated.get("badges", {}) if isinstance(curated, dict) else {}
    aliases = curated.get("aliases", {}) if isinstance(curated, dict) else {}
    return Curation(
        featured=tuple(str(item) for item in featured_ids if item),
        recommended=tuple(str(item) for item in recommended if item),
        badges={
            str(app_id): tuple(str(badge) for badge in values if badge)
            for app_id, values in badges.items()
            if isinstance(values, list)
        },
        aliases={
            str(app_id): tuple(str(alias) for alias in values if alias)
            for app_id, values in aliases.items()
            if isinstance(values, list)
        },
    )


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


def _bool(value: Any, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}
