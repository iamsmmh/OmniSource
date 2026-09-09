"""Search index builder.

The website search runs entirely on the client; the only thing the build
pipeline needs to publish is a precomputed search index that Fuse.js (or
any other fuzzy-search library) can consume without any extra normalization.

The index carries the fields the user can search on:

* ``name``              — display name
* ``shortDescription``  — short blurb
* ``description``       — long description
* ``category``          — primary category
* ``tags``              — declared tags
* ``developer``         — author name
* ``bundleId``          — bundle identifier
* ``verificationLevel`` — community / verified / manual / unverified
* ``clientCompatibility`` — list of clients that can install the app
"""

from __future__ import annotations

from typing import Any

from omnisource.discovery import newest_version
from omnisource.domain import Catalog, today

SEARCH_INDEX_VERSION = 1


def _clients_for(app: Any, catalog: Catalog) -> list[str]:
    out: list[str] = []
    for client in catalog.clients:
        cid = str(client.get("id") or "")
        if cid:
            out.append(cid)
    return out


def build_search_index(
    catalog: Catalog,
    state: dict[str, Any],
    health_doc: dict[str, Any] | None = None,
    verification_doc: dict[str, Any] | None = None,
) -> dict[str, Any]:
    health_doc = health_doc or {}
    health_by_slug = {item.get("slug"): item for item in health_doc.get("apps", []) if isinstance(item, dict)}
    verification_by_slug = {
        item.get("app"): item for item in (verification_doc or {}).get("apps", []) if isinstance(item, dict)
    }
    docs: list[dict[str, Any]] = []
    for app in catalog.apps:
        newest = newest_version(state, app.slug)
        health = health_by_slug.get(app.slug) or {}
        verification = verification_by_slug.get(app.slug) or {}
        docs.append(
            {
                "id": app.slug,
                "slug": app.slug,
                "name": app.name,
                "subtitle": app.short_description,
                "shortDescription": app.short_description,
                "description": app.description,
                "category": app.category,
                "tags": list(app.tags),
                "developer": app.developer,
                "bundleId": app.bundle_id,
                "icon": f"assets/{app.icon}" if app.icon else "",
                "pageURL": f"apps/{app.slug}/",
                "version": str(newest.get("version") or ""),
                "verificationLevel": str(verification.get("status") or "UNVERIFIED"),
                "downloadReachable": bool(health.get("downloadReachable")),
                "clientCompatibility": _clients_for(app, catalog),
            }
        )
    return {
        "schemaVersion": SEARCH_INDEX_VERSION,
        "generatedAt": today(),
        "count": len(docs),
        "fuse": {
            "keys": [
                {"name": "name", "weight": 0.35},
                {"name": "shortDescription", "weight": 0.15},
                {"name": "description", "weight": 0.10},
                {"name": "category", "weight": 0.08},
                {"name": "tags", "weight": 0.10},
                {"name": "developer", "weight": 0.10},
                {"name": "bundleId", "weight": 0.12},
            ],
            "threshold": 0.38,
            "ignoreLocation": True,
            "minMatchCharLength": 2,
        },
        "documents": docs,
    }
