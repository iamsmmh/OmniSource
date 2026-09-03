"""Monitored repository registry and synchronization diagnostics."""

from __future__ import annotations

import hashlib
from collections import OrderedDict
from typing import Any

from omnisource.domain import App, Catalog, today
from omnisource.models.repository import Repository


def repository_key(app: App) -> str:
    ref = app.upstream
    if ref is None:
        return f"manual:{app.slug}"
    return ":".join((ref.provider.value, ref.host, ref.repo or ref.feed_url))


def repository_id(key: str) -> str:
    """Stable, URL-safe identifier independent of display names."""
    slug = "".join(character if character.isalnum() else "-" for character in key.lower()).strip("-")
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:8]
    return f"{slug[:40]}-{digest}"  # keep IDs bounded and collision-resistant


def build_repository_registry(
    catalog: Catalog,
    *,
    state: dict[str, Any] | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Group apps by upstream and merge persisted sync diagnostics."""
    state = state or {}
    grouped: OrderedDict[str, list[App]] = OrderedDict()
    for app in catalog.apps:
        grouped.setdefault(repository_key(app), []).append(app)

    persisted = state.get("repositories", {})
    if not isinstance(persisted, dict):
        persisted = {}
    repositories: list[dict[str, Any]] = []
    for key, apps in grouped.items():
        first = apps[0]
        ref = first.upstream
        url = first.repository_url
        provider = first.source_type.value
        diagnostics = persisted.get(key, {})
        if not isinstance(diagnostics, dict):
            diagnostics = {}
        repositories.append(
            Repository(
                id=repository_id(key),
                name=(ref.repo if ref and ref.repo else first.name),
                url=url,
                provider=provider,
                enabled=bool(diagnostics.get("enabled", True)),
                last_sync=diagnostics.get("lastSync"),
                last_success=diagnostics.get("lastSuccess"),
                last_error=diagnostics.get("lastError"),
                application_ids=[app.slug for app in apps],
                retry_count=int(diagnostics.get("retryCount") or 0),
                health=dict(diagnostics.get("health") or {}) if isinstance(diagnostics.get("health"), dict) else {},
            ).to_dict()
        )
    repositories.sort(key=lambda item: item["id"])
    return {
        "schemaVersion": 1,
        "generatedAt": generated_at or _latest_sync(repositories),
        "count": len(repositories),
        "repositories": repositories,
    }


def record_repository_result(
    state: dict[str, Any],
    app: App,
    *,
    success: bool,
    error: str | None = None,
    retry_count: int = 0,
) -> None:
    """Persist diagnostics without discarding the app's last known-good state."""
    key = repository_key(app)
    records = state.setdefault("repositories", {})
    if not isinstance(records, dict):
        records = {}
        state["repositories"] = records
    previous = records.get(key)
    if not isinstance(previous, dict):
        previous = {}
    previous.update(
        {
            "enabled": bool(previous.get("enabled", True)),
            "lastSync": today(),
            "lastSuccess": today() if success else previous.get("lastSuccess"),
            "lastError": None if success else error,
            "retryCount": max(0, retry_count),
        }
    )
    records[key] = previous


def _latest_sync(repositories: list[dict[str, Any]]) -> str:
    dates = [str(item["lastSync"]) for item in repositories if item.get("lastSync")]
    return max(dates) if dates else ""
