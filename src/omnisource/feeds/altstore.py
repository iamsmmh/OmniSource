"""AltStore Source v2 renderer.

Output is byte-compatible with the historical ``scripts/omnisource.py``
renderer: same keys, same ordering, same `omnisource` extension block.
Unknown keys are ignored by every AltStore-family client.
"""

from __future__ import annotations

from typing import Any

from omnisource.domain import App, Catalog


def render_altstore_app(
    catalog: Catalog,
    app: App,
    versions: list[dict[str, Any]],
    health: dict[str, Any],
) -> dict[str, Any]:
    base = catalog.base_url
    # Shallow-copy so fallback injection never mutates pipeline state.
    versions = [dict(version) for version in versions]
    newest = versions[0]
    raw = app.raw

    manual = app.manual_release
    fallbacks = manual.get("fallbackDownloadURLs") if manual else None
    if fallbacks is None:
        fallbacks = raw.get("fallbackDownloadURLs") or []
    fallbacks = [url for url in fallbacks if isinstance(url, str) and url]

    entry: dict[str, Any] = {
        "name": app.name,
        "bundleIdentifier": raw["bundleIdentifier"],
        "developerName": raw["developerName"],
        "subtitle": raw.get("subtitle", ""),
        "localizedDescription": raw.get("localizedDescription", ""),
        "iconURL": f"{base}/assets/{app.icon}",
        "tintColor": str(raw.get("tintColor", "FF0000")).lstrip("#"),
        "category": raw.get("category", "utilities"),
        "version": newest["version"],
        "versionDate": newest["date"],
        "versionDescription": newest["localizedDescription"],
        "downloadURL": newest["downloadURL"],
        "size": newest["size"],
        "versions": versions,
        "screenshotURLs": raw.get("screenshots", []),
    }
    if raw.get("appPermissions"):
        entry["appPermissions"] = raw["appPermissions"]
    if raw.get("permissions"):
        entry["permissions"] = raw["permissions"]
    if fallbacks:
        entry["fallbackDownloadURLs"] = list(fallbacks)
        newest["fallbackDownloadURLs"] = list(fallbacks)

    entry["omnisource"] = {
        "slug": app.slug,
        "status": app.status,
        "featured": app.featured,
        "upstreamURL": raw.get("upstreamURL", ""),
        "verification": raw.get("verification", {}),
        "compatibility": raw.get("compatibility", {}),
        "health": {
            "downloadReachable": bool(health.get("reachable", True)),
            "detail": health.get("detail", "not probed"),
            "statusSince": health.get("since", newest["date"]),
            "lastUpdatedAt": newest["date"],
        },
    }
    return entry


def feed_envelope(
    catalog: Catalog,
    *,
    name: str,
    identifier: str,
    subtitle: str,
    description: str,
) -> dict[str, Any]:
    base = catalog.base_url
    source = catalog.source
    return {
        "name": name,
        "identifier": identifier,
        "apiVersion": "v2",
        "subtitle": subtitle,
        "description": description,
        "iconURL": f"{base}/assets/{source.get('icon', 'OmniSource.png')}",
        "bannerURL": f"{base}/assets/{source.get('banner', 'OmniSource.png')}",
        "tintColor": str(source.get("tintColor", "5B5BD6")).lstrip("#"),
        "website": f"{base}/",
        "sourceURL": f"{base}/apps.json",
    }


def render_health_doc(rendered: list[tuple[App, dict[str, Any]]]) -> dict[str, Any]:
    reachable = sum(1 for _, entry in rendered if entry["omnisource"]["health"]["downloadReachable"])
    return {
        "generatedAt": max(
            [entry["omnisource"]["health"]["statusSince"] for _, entry in rendered]
            + [entry["versionDate"] for _, entry in rendered]
        ),
        "totals": {
            "apps": len(rendered),
            "reachable": reachable,
            "unreachable": len(rendered) - reachable,
            "featured": sum(1 for _, entry in rendered if entry["omnisource"]["featured"]),
        },
        "apps": [
            {
                "slug": app.slug,
                "name": app.name,
                "status": app.status,
                "version": entry["version"],
                "updatedAt": entry["versionDate"],
                "sizeBytes": entry["size"],
                "downloadReachable": entry["omnisource"]["health"]["downloadReachable"],
                "detail": entry["omnisource"]["health"]["detail"],
                "statusSince": entry["omnisource"]["health"]["statusSince"],
            }
            for app, entry in rendered
        ],
    }
