"""Canonical monitored repository and synchronization diagnostics."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Repository:
    """A monitored source entry, including last-known sync diagnostics."""

    id: str
    name: str
    url: str
    provider: str
    enabled: bool = True
    last_sync: str | None = None
    last_success: str | None = None
    last_error: str | None = None
    application_ids: list[str] = field(default_factory=list)
    retry_count: int = 0
    health: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "provider": self.provider,
            "enabled": self.enabled,
            "lastSync": self.last_sync,
            "lastSuccess": self.last_success,
            "lastError": self.last_error,
            "applicationIds": sorted(set(self.application_ids)),
            "retryCount": self.retry_count,
            "health": dict(self.health),
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> Repository:
        return cls(
            id=str(raw.get("id") or ""),
            name=str(raw.get("name") or ""),
            url=str(raw.get("url") or ""),
            provider=str(raw.get("provider") or "unknown"),
            enabled=bool(raw.get("enabled", True)),
            last_sync=(str(raw["lastSync"]) if raw.get("lastSync") else None),
            last_success=(str(raw["lastSuccess"]) if raw.get("lastSuccess") else None),
            last_error=(str(raw["lastError"]) if raw.get("lastError") else None),
            application_ids=[str(item) for item in raw.get("applicationIds", []) if item],
            retry_count=int(raw.get("retryCount") or 0),
            health=dict(raw.get("health") or {}) if isinstance(raw.get("health"), dict) else {},
        )
