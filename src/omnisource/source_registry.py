"""Global source registry and source lifecycle history.

The registry is deliberately source-centric: it records where a feed comes
from, how it was verified, its observed health, and the applications/releases
it currently contributes.  It does not contain users, reviews, ratings, or
personalization signals.
"""

from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime
from typing import Any

REGISTRY_SCHEMA_VERSION = 1
CLASSIFICATIONS = ("Official", "Verified", "Community", "Experimental", "Archived")


def utcnow() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def stable_id(value: Any) -> str:
    raw = str(value or "").strip()
    if raw:
        slug = re.sub(r"[^a-z0-9]+", "-", raw.casefold()).strip("-")
        if slug:
            return slug[:64]
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _score(source: dict[str, Any], reputation: dict[str, Any] | None) -> float:
    value = source.get("score", source.get("reputation", source.get("reputation_score", 0)))
    if isinstance(reputation, dict):
        source_id = str(source.get("id") or source.get("source_id") or source.get("source") or "")
        for item in reputation.get("sources", []):
            if isinstance(item, dict) and str(item.get("id") or item.get("source") or "") in {
                source_id,
                str(source.get("source")),
            }:
                value = item.get("score", value)
                break
    try:
        return round(max(0.0, min(100.0, float(value or 0))), 2)
    except (TypeError, ValueError):
        return 0.0


def classify_source(
    source: dict[str, Any],
    *,
    score: float = 0.0,
    archived: bool = False,
) -> str:
    """Classify a source from explicit provenance and observed evidence."""
    if (
        archived
        or bool(source.get("archived"))
        or str(source.get("status", "")).casefold()
        in {
            "archived",
            "deprecated",
        }
    ):
        return "Archived"
    verification = str(source.get("verification_status") or source.get("verification") or "").casefold()
    source_type = str(source.get("type") or source.get("source_type") or "").casefold()
    publisher = str(source.get("publisher") or source.get("owner") or "").casefold()
    if source.get("official") is True or verification in {"official", "verified official"}:
        return "Official"
    if "community" in verification or "community" in publisher or source_type in {"community", "mirror"}:
        return "Community"
    if score >= 85 or verification in {"verified", "trusted"}:
        return "Verified"
    if score >= 25 or source.get("apps"):
        return "Experimental"
    return "Experimental"


def _health_for(source: dict[str, Any], status: dict[str, Any] | None) -> tuple[str, float | None]:
    health = str(source.get("health_status") or source.get("health") or source.get("status") or "unknown").casefold()
    uptime: float | None = None
    if isinstance(status, dict):
        source_id = str(source.get("id") or source.get("source_id") or source.get("source") or "")
        nodes = status.get("sources", [])
        for node in nodes if isinstance(nodes, list) else []:
            if not isinstance(node, dict):
                continue
            if str(node.get("id") or node.get("source_id") or "") == source_id:
                health = str(node.get("health") or node.get("status") or health).casefold()
                uptime_raw = node.get("uptime")
                try:
                    uptime = float(uptime_raw) if uptime_raw is not None else None
                except (TypeError, ValueError):
                    uptime = None
                break
    if health in {"healthy", "ok", "online", "verified"}:
        health = "online"
    elif health in {"warning", "degraded", "partial"}:
        health = "degraded"
    elif health in {"offline", "unavailable", "dead"}:
        health = "offline"
    else:
        health = "unknown"
    return health, uptime


def _source_url(source: dict[str, Any]) -> str:
    return str(
        source.get("sourceURL")
        or source.get("source_url")
        or source.get("url")
        or source.get("homepage")
        or source.get("feedURL")
        or ""
    )


def build_registry(
    sources: list[dict[str, Any]],
    *,
    discovered: list[dict[str, Any]] | None = None,
    status: dict[str, Any] | None = None,
    reputation: dict[str, Any] | None = None,
    previous: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a registry while preserving per-source history."""
    previous_sources = previous.get("sources", []) if isinstance(previous, dict) else []
    previous_by_id = {
        str(item.get("source_id") or item.get("id")): item
        for item in previous_sources
        if isinstance(item, dict) and (item.get("source_id") or item.get("id"))
    }
    current: dict[str, dict[str, Any]] = {}
    # Hand-maintained/catalog sources are already publication inputs. A
    # discovered record is an untrusted candidate until the explicit verifier
    # marks it verified or published; quarantined/validating candidates never
    # enter the public registry projection.
    discovered_public = [
        raw
        for raw in (discovered or [])
        if isinstance(raw, dict)
        and str(raw.get("status", "")).casefold() in {"verified", "published"}
        and str(raw.get("verification_status", "")).casefold() in {"verified", "trusted", "official"}
        and not raw.get("errors")
    ]
    for raw in [*sources, *discovered_public]:
        if not isinstance(raw, dict):
            continue
        url = _source_url(raw)
        key = str(raw.get("id") or raw.get("source_id") or raw.get("source") or url)
        source_id = stable_id(key)
        score = _score(raw, reputation)
        health, uptime = _health_for(raw, status)
        apps = raw.get("apps", [])
        app_count = len(apps) if isinstance(apps, list) else int(raw.get("appCount", 0) or 0)
        old = previous_by_id.get(source_id, {})
        first_seen = str(
            old.get("first_seen")
            or old.get("firstSeen")
            or raw.get("first_seen")
            or raw.get("discovered_at")
            or utcnow()
        )
        record = {
            "source_id": source_id,
            "source_name": str(raw.get("source_name") or raw.get("name") or raw.get("source") or url or source_id),
            "source_type": str(raw.get("source_type") or raw.get("type") or "unknown"),
            "source_url": url,
            "classification": classify_source(raw, score=score),
            "verification_status": str(raw.get("verification_status") or raw.get("verification") or "unverified"),
            "reputation_score": score,
            "health_status": health,
            "uptime": uptime,
            "first_seen": first_seen,
            "last_seen": str(raw.get("last_seen") or raw.get("last_checked") or utcnow()),
            "last_sync": str(raw.get("last_sync") or raw.get("lastUpdate") or raw.get("last_checked") or ""),
            "app_count": app_count,
            "release_count": int(raw.get("releaseCount", 0) or 0),
            "apps": [
                {
                    "id": str(item.get("slug") or item.get("id") or ""),
                    "name": str(item.get("name") or ""),
                    "version": str(item.get("version") or ""),
                }
                for item in apps
                if isinstance(item, dict)
            ],
            "history": list(old.get("history", [])) if isinstance(old.get("history"), list) else [],
        }
        snapshot = {
            "at": utcnow(),
            "health": health,
            "reputation": score,
            "appCount": app_count,
            "verification": record["verification_status"],
        }
        if not record["history"] or record["history"][-1] != snapshot:
            record["history"].append(snapshot)
        record["history"] = record["history"][-90:]
        current[source_id] = record
    # Keep historical records that disappeared from the feed as Archived rather
    # than deleting them; this supports timeline and rollback audits.
    for source_id, old in previous_by_id.items():
        if source_id in current or not isinstance(old, dict):
            continue
        archived = dict(old)
        archived["classification"] = "Archived"
        archived["health_status"] = "offline"
        archived["history"] = list(old.get("history", [])) if isinstance(old.get("history"), list) else []
        current[source_id] = archived
    records = sorted(current.values(), key=lambda item: str(item.get("source_name", "")).casefold())
    return {
        "schemaVersion": REGISTRY_SCHEMA_VERSION,
        "generatedAt": utcnow(),
        "count": len(records),
        "classifications": {
            name: sum(1 for item in records if item.get("classification") == name) for name in CLASSIFICATIONS
        },
        "sources": records,
    }


def source_by_id(registry: dict[str, Any], source_id: str) -> dict[str, Any] | None:
    return next(
        (item for item in registry.get("sources", []) if isinstance(item, dict) and item.get("source_id") == source_id),
        None,
    )


__all__ = ["CLASSIFICATIONS", "build_registry", "classify_source", "source_by_id", "stable_id"]
