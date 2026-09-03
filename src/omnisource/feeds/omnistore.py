"""Render the canonical OmniStore feeds.

The AltStore renderer remains a separate compatibility path. These documents
are platform-neutral and carry application, release, asset, category,
repository, health, search, update, trending, and recent information.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from typing import Any
from urllib.parse import urlsplit

from omnisource.config import Category, Curation
from omnisource.constants import OMNISTORE_SCHEMA_VERSION
from omnisource.domain import App, Catalog, StandardizedApp, UpdateEvent
from omnisource.health import calculate_app_health
from omnisource.search import build_search_index
from omnisource.tracking import extract_changelog, extract_sha256
from omnisource.utils.assets import detect_asset_metadata


def _asset_from_version(
    raw: dict[str, Any], *, fallback_url: str = "", size: int = 0, sha256: str | None = None
) -> dict[str, Any] | None:
    url = str(raw.get("downloadUrl") or raw.get("downloadURL") or fallback_url or "")
    if not url:
        return None
    filename = str(raw.get("filename") or raw.get("name") or "")
    if not filename:
        filename = urlsplit(url).path.rsplit("/", 1)[-1] or "asset"
    detected = detect_asset_metadata(filename, url, mime_type=str(raw.get("mimeType") or ""))
    return {
        "filename": filename,
        "downloadUrl": url,
        "platform": str(raw.get("platform") or detected["platform"]),
        "architecture": raw.get("architecture") or detected["architecture"],
        "fileType": str(raw.get("fileType") or detected["fileType"]),
        "size": int(raw.get("size") if raw.get("size") is not None else size or 0),
        "sha256": raw.get("sha256") or sha256,
        "mimeType": raw.get("mimeType") or None,
        "installable": bool(raw.get("installable", detected["installable"])),
    }


def _release_from_version(app: App, version: dict[str, Any]) -> dict[str, Any]:
    version_name = str(version.get("version") or "")
    release_url = version.get("releaseUrl") or app.repository_url or None
    raw_assets = version.get("assets")
    assets: list[dict[str, Any]] = []
    if isinstance(raw_assets, list):
        assets = [
            asset
            for raw in raw_assets
            if isinstance(raw, dict)
            if (
                asset := _asset_from_version(
                    raw,
                    fallback_url=str(version.get("downloadURL") or ""),
                    size=int(version.get("size") or 0),
                    sha256=version.get("sha256"),
                )
            )
            is not None
        ]
    if not assets:
        asset = _asset_from_version(
            version,
            size=int(version.get("size") or 0),
            sha256=str(version["sha256"]) if version.get("sha256") else None,
        )
        if asset is not None:
            assets.append(asset)
    return {
        "version": version_name,
        "build": str(version["buildVersion"]) if version.get("buildVersion") is not None else None,
        "releaseDate": str(version.get("date") or ""),
        "releaseNotes": extract_changelog(str(version.get("localizedDescription") or "")),
        "releaseUrl": release_url,
        "assets": assets,
        "source": str(version.get("source") or app.source_type.value),
        "isPrerelease": bool(version.get("isPrerelease", False)),
        "isDraft": bool(version.get("isDraft", False)),
        "tag": str(version["tag"]) if version.get("tag") else None,
    }


def standardize_app(
    catalog: Catalog,
    app: App,
    versions: list[dict[str, Any]],
    *,
    state_entry: dict[str, Any] | None = None,
    health: dict[str, Any] | None = None,
    repository: dict[str, Any] | None = None,
    curation: Curation | None = None,
) -> StandardizedApp:
    """Build one canonical record while retaining the historical fields."""
    if not versions:
        raise ValueError(f"{app.slug}: cannot standardize an empty version list")
    state_entry = state_entry or {}
    newest = versions[0]
    releases = tuple(_release_from_version(app, version) for version in versions)
    newest_release = releases[0]
    assets = tuple(newest_release["assets"])
    changelog = str(newest_release["releaseNotes"])
    sha = newest.get("sha256") or (assets[0].get("sha256") if assets else None) or extract_sha256(changelog)
    if sha:
        sha = str(sha).lower()
    health_data = calculate_app_health(app, state_entry, repository=repository)
    if health:
        # ``health`` from the AltStore state uses reachable/detail/since;
        # canonical calculated signals are retained and the probe is overlaid.
        if "reachable" in health:
            health_data["downloadReachable"] = bool(health["reachable"])
            health_data["brokenDownloadLinks"] = 0 if health["reachable"] else 1
            health_data["status"] = "broken" if not health["reachable"] else app.lifecycle_status
        health_data["downloadDetail"] = str(health.get("detail") or health_data["downloadDetail"])
        health_data["statusSince"] = health.get("since")
    categories = app.categories
    curated_aliases = curation.aliases.get(app.slug, ()) if curation else ()
    aliases = tuple(dict.fromkeys((*app.aliases, *curated_aliases)))
    featured = app.featured or (curation is not None and app.slug in curation.featured)
    min_ios = app.minimum_ios_version or (str(newest.get("minOSVersion")) if newest.get("minOSVersion") else None)
    return StandardizedApp(
        app_id=app.slug,
        name=app.name,
        developer=app.developer,
        description=app.description,
        icon=f"{catalog.base_url}/assets/{app.icon}",
        screenshots=tuple(app.screenshots),
        category=app.category,
        version=str(newest.get("version") or ""),
        build_number=(str(newest["buildVersion"]) if newest.get("buildVersion") is not None else None),
        release_date=str(newest.get("date") or ""),
        bundle_id=app.bundle_id,
        minimum_os_version=min_ios or "",
        source_type=app.source_type.value,
        repository_url=app.repository_url,
        changelog=changelog,
        download_url=str(newest.get("downloadURL") or ""),
        sha256=sha,
        size=int(newest.get("size") or 0),
        status=app.status,
        featured=featured,
        tags=tuple(dict.fromkeys((*app.tags, *aliases))),
        fallback_download_urls=tuple(
            url
            for url in (
                newest.get("fallbackDownloadURLs")
                or (app.manual_release or {}).get("fallbackDownloadURLs")
                or app.raw.get("fallbackDownloadURLs")
                or []
            )
            if isinstance(url, str)
        ),
        short_description=app.short_description,
        app_categories=categories,
        platforms=app.platforms,
        homepage=app.homepage,
        documentation=app.documentation,
        license=app.license,
        package_name=app.package_name,
        minimum_android_version=app.minimum_android_version,
        lifecycle_status=str(health_data.get("status") or app.lifecycle_status),
        verified=app.verified,
        last_updated=str(state_entry.get("syncedAt") or newest.get("date") or ""),
        health=health_data,
        integrity={
            "sha256": sha,
            "sha256Available": bool(sha),
            "verified": health_data.get("integrityVerified"),
            "trustStatement": "A digest match proves integrity of bytes, not application safety.",
        },
        aliases=aliases,
        releases=releases,
        download_assets=assets,
    )


def _stamp(apps: Iterable[StandardizedApp]) -> str:
    dates = [app.release_date for app in apps if app.release_date]
    return max(dates) if dates else ""


def render_apps(apps: list[StandardizedApp]) -> dict[str, Any]:
    ordered = sorted(apps, key=lambda item: item.name.casefold())
    return {
        "schemaVersion": OMNISTORE_SCHEMA_VERSION,
        "generatedAt": _stamp(ordered),
        "count": len(ordered),
        "apps": [app.to_json() for app in ordered],
    }


def render_categories(apps: list[StandardizedApp], *, definitions: tuple[Category, ...] = ()) -> dict[str, Any]:
    buckets: dict[str, set[str]] = defaultdict(set)
    for app in apps:
        for category in app.app_categories or (app.category,):
            if category:
                buckets[category].add(app.app_id)
    names = {category.id: category.name for category in definitions}
    categories = [
        {
            "id": category_id,
            "name": names.get(category_id, category_id.replace("-", " ").replace("_", " ").title()),
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


def render_featured(apps: list[StandardizedApp], *, curation: Curation | None = None) -> dict[str, Any]:
    featured_ids = set(curation.featured) if curation else set()
    featured = [app for app in apps if app.featured or app.app_id in featured_ids]
    return {
        "schemaVersion": OMNISTORE_SCHEMA_VERSION,
        "generatedAt": _stamp(featured or apps),
        "count": len(featured),
        "apps": [app.to_json() for app in sorted(featured, key=lambda item: item.name.casefold())],
    }


def render_updates(
    events: list[UpdateEvent], *, generated_at: str, history: list[UpdateEvent] | None = None
) -> dict[str, Any]:
    """Render a bounded update index, omitting unchanged observations."""
    combined = list(history or []) + list(events)
    material: dict[tuple[str, str, str], UpdateEvent] = {}
    for event in combined:
        if event.kind != "unchanged":
            material[(event.app_id, event.version, event.kind)] = event
    ordered = sorted(material.values(), key=lambda event: (event.release_date, event.app_id), reverse=True)
    return {
        "schemaVersion": OMNISTORE_SCHEMA_VERSION,
        "generatedAt": generated_at,
        "count": len(ordered),
        "updates": [event.to_json() for event in ordered],
    }


def render_repositories(
    apps: list[StandardizedApp],
    *,
    registry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if registry and isinstance(registry.get("repositories"), list):
        return registry
    grouped: dict[str, dict[str, Any]] = {}
    for app in apps:
        url = app.repository_url or app.app_id
        bucket = grouped.setdefault(
            url,
            {
                "id": app.app_id,
                "name": app.developer or app.name,
                "url": url,
                "provider": app.source_type,
                "sourceType": app.source_type,
                "enabled": True,
                "lastSync": None,
                "lastSuccess": None,
                "lastError": None,
                "applicationIds": [],
                "appCount": 0,
            },
        )
        bucket["appCount"] += 1
        bucket["applicationIds"].append(app.app_id)
    repositories = sorted(grouped.values(), key=lambda item: (-item["appCount"], item["url"]))
    for repo in repositories:
        repo["applicationIds"] = sorted(repo["applicationIds"])
    return {
        "schemaVersion": OMNISTORE_SCHEMA_VERSION,
        "generatedAt": _stamp(apps),
        "count": len(repositories),
        "repositories": repositories,
    }


def _ranked_activity(apps: list[StandardizedApp]) -> list[StandardizedApp]:
    return sorted(apps, key=lambda app: (app.release_date or "", app.name.casefold()), reverse=True)


def render_trending(apps: list[StandardizedApp], *, limit: int = 50) -> dict[str, Any]:
    """Curator-free activity view: newest observed releases, not popularity."""
    ranked = _ranked_activity(apps)[:limit]
    return {
        "schemaVersion": OMNISTORE_SCHEMA_VERSION,
        "generatedAt": _stamp(apps),
        "methodology": "Ordered by latest observable release date; no downloads, users, or popularity are inferred.",
        "count": len(ranked),
        "apps": [
            {
                "appId": app.app_id,
                "name": app.name,
                "version": app.version,
                "releaseDate": app.release_date,
                "activity": "recent-release",
            }
            for app in ranked
        ],
    }


def render_recent(apps: list[StandardizedApp], *, limit: int = 100) -> dict[str, Any]:
    ranked = _ranked_activity(apps)[:limit]
    return {
        "schemaVersion": OMNISTORE_SCHEMA_VERSION,
        "generatedAt": _stamp(apps),
        "count": len(ranked),
        "apps": [
            {
                "appId": app.app_id,
                "name": app.name,
                "version": app.version,
                "releaseDate": app.release_date,
            }
            for app in ranked
        ],
    }


def render_health(apps: list[StandardizedApp]) -> dict[str, Any]:
    broken = [app for app in apps if not app.health.get("downloadReachable", True)]
    return {
        "schemaVersion": OMNISTORE_SCHEMA_VERSION,
        "generatedAt": _stamp(apps),
        "count": len(apps),
        "totals": {
            "apps": len(apps),
            "reachable": len(apps) - len(broken),
            "unreachable": len(broken),
        },
        "apps": [
            {
                "appId": app.app_id,
                "status": app.lifecycle_status,
                "downloadReachable": bool(app.health.get("downloadReachable", True)),
                "detail": app.health.get("downloadDetail", "not probed"),
                "metadataCompleteness": app.health.get("metadataCompleteness"),
                "lastReleaseDate": app.health.get("lastReleaseDate"),
            }
            for app in sorted(apps, key=lambda item: item.app_id)
        ],
    }


def render_omnistore_bundle(
    catalog: Catalog,
    *,
    versions_by_slug: dict[str, list[dict[str, Any]]],
    updates: list[UpdateEvent],
    state_by_slug: dict[str, dict[str, Any]] | None = None,
    repository_registry: dict[str, Any] | None = None,
    curation: Curation | None = None,
    categories: tuple[Category, ...] = (),
    update_history: list[UpdateEvent] | None = None,
) -> dict[str, dict[str, Any]]:
    """Return every machine feed generated under ``feeds/omnistore``."""
    state_by_slug = state_by_slug or {}
    standardized = [
        standardize_app(
            catalog,
            app,
            versions,
            state_entry=state_by_slug.get(app.slug),
            health=(state_by_slug.get(app.slug) or {}).get("health"),
            repository=_repository_for_app(repository_registry, app.slug),
            curation=curation,
        )
        for app in catalog.apps
        if (versions := versions_by_slug.get(app.slug))
    ]
    generated_at = _stamp(standardized)
    search_doc = build_search_index(standardized)
    search_doc["generatedAt"] = generated_at
    return {
        "apps.json": render_apps(standardized),
        "categories.json": render_categories(standardized, definitions=categories),
        "featured.json": render_featured(standardized, curation=curation),
        "updates.json": render_updates(update_history or [], generated_at=generated_at, history=None)
        if not updates
        else render_updates(updates, generated_at=generated_at, history=update_history),
        "repositories.json": render_repositories(standardized, registry=repository_registry),
        "search-index.json": search_doc,
        "trending.json": render_trending(standardized),
        "recent.json": render_recent(standardized),
        "health.json": render_health(standardized),
    }


def _repository_for_app(registry: dict[str, Any] | None, app_id: str) -> dict[str, Any] | None:
    if not registry:
        return None
    for item in registry.get("repositories", []):
        if isinstance(item, dict) and app_id in item.get("applicationIds", []):
            return item
    return None
