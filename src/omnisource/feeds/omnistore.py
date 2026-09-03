"""OmniStore feed renderer.

Produces machine-readable documents for the future OmniStore client:

* ``apps.json``          — unified metadata catalog (one record per app)
* ``categories.json``    — category index
* ``updates.json``       — version changes detected this run / recent history
* ``featured.json``      — featured subset
* ``repositories.json``  — unique upstream repositories
* ``search-index.json``  — inverted index (see ``omnisource.search``)

These live under ``feeds/omnistore/`` so they cannot be mistaken for AltStore
v2 documents by ``validate_jq.sh`` or ``merge_feeds.py``.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from omnisource.constants import OMNISTORE_SCHEMA_VERSION
from omnisource.domain import App, Catalog, StandardizedApp, UpdateEvent
from omnisource.search import build_search_index
from omnisource.tracking import extract_changelog, extract_sha256


def standardize_app(
    catalog: Catalog,
    app: App,
    versions: list[dict[str, Any]],
) -> StandardizedApp:
    newest = versions[0]
    changelog = extract_changelog(str(newest.get("localizedDescription") or ""))
    sha = newest.get("sha256")
    if not sha:
        sha = extract_sha256(changelog)
    fallbacks = newest.get("fallbackDownloadURLs") or app.raw.get("fallbackDownloadURLs") or []
    if app.manual_release and app.manual_release.get("fallbackDownloadURLs"):
        fallbacks = app.manual_release["fallbackDownloadURLs"]
    min_os = str(newest.get("minOSVersion") or (app.raw.get("compatibility") or {}).get("minOSVersion") or "16.0")
    icon = f"{catalog.base_url}/assets/{app.icon}"
    return StandardizedApp(
        app_id=app.slug,
        name=app.name,
        developer=app.developer,
        description=app.description,
        icon=icon,
        screenshots=tuple(app.screenshots),
        category=app.category,
        version=str(newest.get("version") or ""),
        build_number=str(newest["buildVersion"]) if newest.get("buildVersion") else None,
        release_date=str(newest.get("date") or ""),
        bundle_id=app.bundle_id,
        minimum_os_version=min_os,
        source_type=app.source_type.value,
        repository_url=app.repository_url,
        changelog=changelog,
        download_url=str(newest.get("downloadURL") or ""),
        sha256=str(sha) if sha else None,
        size=int(newest.get("size") or 0),
        status=app.status,
        featured=app.featured,
        tags=app.tags,
        fallback_download_urls=tuple(url for url in fallbacks if isinstance(url, str)),
    )


def _stamp(apps: list[StandardizedApp]) -> str:
    dates = [app.release_date for app in apps if app.release_date]
    return max(dates) if dates else ""


def render_apps(apps: list[StandardizedApp]) -> dict[str, Any]:
    ordered = sorted(apps, key=lambda item: item.name.lower())
    return {
        "schemaVersion": OMNISTORE_SCHEMA_VERSION,
        "generatedAt": _stamp(ordered),
        "count": len(ordered),
        "apps": [app.to_json() for app in ordered],
    }


def render_categories(apps: list[StandardizedApp]) -> dict[str, Any]:
    buckets: dict[str, list[str]] = defaultdict(list)
    for app in apps:
        buckets[app.category or "uncategorized"].append(app.app_id)
    categories = [
        {
            "id": category_id,
            "name": category_id.replace("-", " ").replace("_", " ").title(),
            "appCount": len(ids),
            "apps": sorted(ids),
        }
        for category_id, ids in sorted(buckets.items())
    ]
    return {
        "schemaVersion": OMNISTORE_SCHEMA_VERSION,
        "generatedAt": _stamp(apps),
        "count": len(categories),
        "categories": categories,
    }


def render_featured(apps: list[StandardizedApp]) -> dict[str, Any]:
    featured = [app for app in apps if app.featured]
    return {
        "schemaVersion": OMNISTORE_SCHEMA_VERSION,
        "generatedAt": _stamp(featured or apps),
        "count": len(featured),
        "apps": [app.to_json() for app in sorted(featured, key=lambda item: item.name.lower())],
    }


def render_updates(events: list[UpdateEvent], *, generated_at: str) -> dict[str, Any]:
    # Newest first; unchanged events are omitted so the file stays a signal.
    material = [event for event in events if event.kind != "unchanged"]
    material.sort(key=lambda event: event.release_date, reverse=True)
    return {
        "schemaVersion": OMNISTORE_SCHEMA_VERSION,
        "generatedAt": generated_at,
        "count": len(material),
        "updates": [event.to_json() for event in material],
    }


def render_repositories(apps: list[StandardizedApp]) -> dict[str, Any]:
    grouped: dict[str, dict[str, Any]] = {}
    for app in apps:
        url = app.repository_url or app.app_id
        bucket = grouped.setdefault(
            url,
            {
                "url": url,
                "sourceType": app.source_type,
                "developer": app.developer,
                "appCount": 0,
                "apps": [],
            },
        )
        bucket["appCount"] += 1
        bucket["apps"].append(app.app_id)
    repositories = sorted(grouped.values(), key=lambda item: (-item["appCount"], item["url"]))
    for repo in repositories:
        repo["apps"] = sorted(repo["apps"])
    return {
        "schemaVersion": OMNISTORE_SCHEMA_VERSION,
        "generatedAt": _stamp(apps),
        "count": len(repositories),
        "repositories": repositories,
    }


def render_omnistore_bundle(
    catalog: Catalog,
    *,
    versions_by_slug: dict[str, list[dict[str, Any]]],
    updates: list[UpdateEvent],
) -> dict[str, dict[str, Any]]:
    """Return a mapping of filename → document for every OmniStore feed."""
    standardized: list[StandardizedApp] = []
    for app in catalog.apps:
        versions = versions_by_slug.get(app.slug)
        if not versions:
            continue
        standardized.append(standardize_app(catalog, app, versions))
    generated_at = _stamp(standardized)
    search_doc = build_search_index(standardized)
    search_doc["generatedAt"] = generated_at
    return {
        "apps.json": render_apps(standardized),
        "categories.json": render_categories(standardized),
        "featured.json": render_featured(standardized),
        "updates.json": render_updates(updates, generated_at=generated_at),
        "repositories.json": render_repositories(standardized),
        "search-index.json": search_doc,
    }
