"""Mirror management: registry, health-aware selection, failover.

Upstream binaries disappear (force-pushed tags, deleted releases, expired
CDN signatures). The mirror registry (``data/mirrors.json``) records every
known-good alternate location per mirror tier:

* ``github-release`` — the upstream's own release assets (primary);
* ``github-pages`` — Pages-hosted copies of small utilities;
* ``cdn`` — project CDN / R2 / Pages mirrors;
* ``backup`` — community mirrors, last resort.

:func:`select_mirrors` orders the candidates for one app (healthy first,
then by tier priority); :func:`failover` picks the next URL after a
failure. Probing lives in :mod:`omnisource.probes` — this module only
decides, so it stays pure and offline.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

MIRRORS_SCHEMA_VERSION = 1

TIER_PRIORITY = {
    "github-release": 0,
    "github-pages": 1,
    "cdn": 2,
    "backup": 3,
}


def utcnow() -> str:
    """Current UTC timestamp in ISO-8601 format."""
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def default_registry() -> dict[str, Any]:
    """Empty-but-valid registry skeleton."""
    return {
        "schemaVersion": MIRRORS_SCHEMA_VERSION,
        "generatedAt": utcnow(),
        "fallbackOrder": ["github-release", "github-pages", "cdn", "backup"],
        "mirrors": [],
    }


def tier_rank(mirror: dict[str, Any]) -> int:
    """Sort rank for one mirror entry (lower = preferred)."""
    return TIER_PRIORITY.get(str(mirror.get("type", "")), 99)


def mirrors_for_app(registry: dict[str, Any], slug: str) -> list[dict[str, Any]]:
    """Mirrors covering ``slug`` (global ``apps: ["*"]`` entries apply)."""
    entries = registry.get("mirrors", [])
    if not isinstance(entries, list):
        return []
    covered = []
    for entry in entries:
        if not isinstance(entry, dict) or not entry.get("enabled", True):
            continue
        apps = entry.get("apps", ["*"])
        if apps == ["*"] or (isinstance(apps, list) and slug in apps):
            covered.append(entry)
    return covered


def select_mirrors(
    registry: dict[str, Any],
    slug: str,
    primary_url: str,
    *,
    health: dict[str, bool] | None = None,
) -> list[dict[str, Any]]:
    """Order every candidate URL for ``slug``: healthy first, tier order."""
    health = health or {}
    candidates = [{"url": primary_url, "type": "github-release", "primary": True}]
    for mirror in mirrors_for_app(registry, slug):
        template = str(mirror.get("urlTemplate") or mirror.get("url") or "")
        if not template:
            continue
        url = template.replace("{slug}", slug)
        candidates.append(
            {
                "url": url,
                "type": str(mirror.get("type", "backup")),
                "id": str(mirror.get("id", "")),
                "primary": False,
            }
        )
    for candidate in candidates:
        candidate["healthy"] = health.get(candidate["url"], True)
    candidates.sort(
        key=lambda item: (
            not item["healthy"],
            item["primary"] is False and item["healthy"] is False,
            TIER_PRIORITY.get(str(item["type"]), 99),
            item["primary"],
        )
    )
    # A healthy primary always wins; otherwise healthy mirrors by tier.
    healthy = [item for item in candidates if item["healthy"]]
    unhealthy = [item for item in candidates if not item["healthy"]]
    return healthy + unhealthy


def failover(
    registry: dict[str, Any],
    slug: str,
    primary_url: str,
    failed_url: str,
    *,
    health: dict[str, bool] | None = None,
) -> dict[str, Any]:
    """Pick the next candidate after ``failed_url`` broke."""
    ordered = select_mirrors(registry, slug, primary_url, health=health)
    remaining = [item for item in ordered if item["url"] != failed_url and item.get("healthy", True)]
    if remaining:
        return {"ok": True, "url": remaining[0]["url"], "type": remaining[0]["type"]}
    leftovers = [item for item in ordered if item["url"] != failed_url]
    if leftovers:
        return {"ok": True, "url": leftovers[0]["url"], "type": leftovers[0]["type"], "degraded": True}
    return {"ok": False, "url": "", "type": "", "reason": "no alternate mirror configured"}


def build_status(
    registry: dict[str, Any],
    slugs: list[str],
    *,
    health: dict[str, bool] | None = None,
) -> dict[str, Any]:
    """Per-app failover readiness snapshot (served inside status docs)."""
    health = health or {}
    apps = []
    for slug in sorted(slugs):
        mirrors = mirrors_for_app(registry, slug)
        apps.append(
            {
                "slug": slug,
                "mirrors": len(mirrors),
                "tiers": sorted({str(item.get("type", "")) for item in mirrors}),
                "protected": bool(mirrors),
            }
        )
    protected = sum(1 for item in apps if item["protected"])
    return {
        "schemaVersion": MIRRORS_SCHEMA_VERSION,
        "generatedAt": utcnow(),
        "appCount": len(apps),
        "protected": protected,
        "unprotected": len(apps) - protected,
        "apps": apps,
    }
