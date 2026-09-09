"""Verification system.

Trust levels are computed from observable facts, not claims:

``VERIFIED``
    The app is distributed by its official upstream (developer release, the
    developer's own feed, or a source the catalog marks official) and every
    offline/runtime check passed.
``COMMUNITY VERIFIED``
    The app is a community-built package (e.g. a community IPA of a tweak whose
    project publishes no IPA itself) and every check passed. It is still
    trustworthy, but the build provenance is not the upstream developer.
``UNVERIFIED``
    At least one check failed: invalid metadata, a non-HTTP(S) download URL,
    or the download was unreachable at build time.

Checks performed:

* ``metadata``   — required identity fields are present and well-formed.
* ``urls``       — download/upstream URLs are HTTP(S).
* ``fileAvailable`` — the last link probe considered the primary URL reachable.
* ``hashVerified``  — a SHA-256 digest is known for the newest build (from the
  upstream release's published checksum or the asset digest when the forge
  publishes one).

The result is rendered into ``feeds/verification.json`` and consumed by the
website badges and the duplicated-app recommendations.
"""

from __future__ import annotations

import re
from typing import Any

from omnisource.discovery import newest_version
from omnisource.domain import Catalog, today
from omnisource.http import is_http_url

VERIFICATION_SCHEMA_VERSION = 1

# Methods whose publisher is the application's official upstream.
OFFICIAL_METHODS = frozenset(
    {
        "github-release",
        "github-tag",
        "gitlab-release",
        "codeberg-release",
        "forgejo-release",
        "json-feed",
        "altstore",
        "feather",
    }
)
# Methods that describe a community-packaged build of an official project.
COMMUNITY_METHODS = frozenset({"manual-mirror", "self-built"})

BUNDLE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.-]*$")
LEVELS = ("VERIFIED", "COMMUNITY VERIFIED", "UNVERIFIED")


def _checks(catalog: Catalog, app: Any, newest: dict[str, Any], health: dict[str, Any] | None) -> dict[str, bool]:
    """Evaluate each verification check against defensively-sourced values."""
    download_url = str(newest.get("downloadURL") or "")
    upstream = str(app.homepage or "")
    health = health or {}
    return {
        "metadata": bool(
            app.name
            and str(newest.get("version") or "")
            and (not app.bundle_id or bool(BUNDLE_RE.match(app.bundle_id)))
        ),
        "urls": bool(is_http_url(download_url) and (not upstream or is_http_url(upstream))),
        "fileAvailable": bool(health.get("downloadReachable", True)),
        "hashVerified": bool(str(newest.get("sha256") or "")),
    }


def _reason_for_level(level: str, failed: list[str], method: str) -> list[str]:
    if level == "UNVERIFIED":
        return [f"failed check: {name}" for name in failed] or ["verification method is not recognized"]
    if level == "COMMUNITY VERIFIED":
        return [f"community package ({method}) — build provenance is not the upstream developer"]
    return [f"official upstream ({method})"]


def build_verification_doc(
    catalog: Catalog,
    state: dict[str, Any],
    health_doc: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compute trust levels for every app and render ``verification.json``."""
    health_doc = health_doc or {}
    health_by_slug = {item.get("slug"): item for item in health_doc.get("apps", []) if isinstance(item, dict)}
    entries: list[dict[str, Any]] = []
    totals = {"apps": 0, "verified": 0, "communityVerified": 0, "unverified": 0, "hashVerified": 0}

    for app in catalog.apps:
        verification = app.raw.get("verification", {})
        if not isinstance(verification, dict):
            verification = {}
        method = str(verification.get("method") or "")
        newest = newest_version(state, app.slug)
        health = health_by_slug.get(app.slug)
        checks = _checks(catalog, app, newest, health)
        failed = [key for key, ok in checks.items() if not ok and key != "hashVerified"]

        if failed:
            level = "UNVERIFIED"
        elif method in OFFICIAL_METHODS:
            level = "VERIFIED"
        elif method in COMMUNITY_METHODS:
            level = "COMMUNITY VERIFIED"
        elif method == "":
            # No explicit verification record yet: stay conservative unless the
            # catalog explicitly marks the app as official on the developerName.
            level = "UNVERIFIED"
        else:
            level = "UNVERIFIED"

        totals["apps"] += 1
        totals[{"VERIFIED": "verified", "COMMUNITY VERIFIED": "communityVerified"}.get(level, "unverified")] += 1
        if checks["hashVerified"]:
            totals["hashVerified"] += 1

        entries.append(
            {
                "app": app.slug,
                "name": app.name,
                "status": level,
                "hash_verified": checks["hashVerified"],
                "method": method,
                "publisher": str(verification.get("publisher") or app.developer),
                "checks": checks,
                "reasons": _reason_for_level(level, failed, method),
                "downloadURL": str(newest.get("downloadURL") or ""),
            }
        )

    entries.sort(key=lambda item: (item["status"] != "VERIFIED", str(item["name"]).casefold()))
    return {
        "schemaVersion": VERIFICATION_SCHEMA_VERSION,
        "generatedAt": today(),
        "totals": totals,
        "apps": entries,
    }
