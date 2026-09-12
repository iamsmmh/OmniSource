"""Per-client feed variants (AltStore / SideStore / Feather / ESign / LiveContainer).

All five clients consume the AltStore Source v2 envelope; the differences
are operational, not structural:

* **AltStore** — the reference feed, every app, no filtering.
* **SideStore** — identical envelope (SideStore is AltStore-compatible);
  carries explicit ``client`` metadata for diagnostics.
* **Feather** — identical envelope; Feather requires absolute ``iconURL``
  values, so relative icons are dropped rather than shipped broken.
* **ESign** — only apps with a direct ``https`` IPA download and a known
  positive size (ESign cannot install repository links or unknown sizes).
* **LiveContainer** — identical envelope; apps are additionally tagged
  with their bundle ID alias for LiveContainer's JIT-less mapping.

Every variant validates as an AltStore v2 feed (see
``scripts/validation/validate_feed.py``) and is published under
``feeds/clients/<client>.json``. Output is byte-stable for identical
input.
"""

from __future__ import annotations

from typing import Any

CLIENTS = ("altstore", "sidestore", "feather", "esign", "livecontainer")


def _is_https(url: Any) -> bool:
    return isinstance(url, str) and url.startswith("https://")


def _base_app(app: dict[str, Any]) -> dict[str, Any]:
    return {key: app.get(key) for key in sorted(app)}


def filter_for_client(app: dict[str, Any], client: str) -> dict[str, Any] | None:
    """Project one AltStore app entry onto ``client`` (None = excluded)."""
    entry = _base_app(app)
    if client == "esign":
        if not _is_https(entry.get("downloadURL")):
            return None
        size = entry.get("size")
        if not isinstance(size, int) or isinstance(size, bool) or size <= 0:
            return None
    if client == "feather" and not _is_https(entry.get("iconURL")):
        entry["iconURL"] = ""
    if client == "livecontainer":
        omni = dict(entry.get("omnisource") or {}) if isinstance(entry.get("omnisource"), dict) else {}
        omni.setdefault("bundleAlias", entry.get("bundleIdentifier", ""))
        entry["omnisource"] = omni
    return entry


def render_client_feed(envelope: dict[str, Any], client: str) -> dict[str, Any]:
    """Render the ``<client>.json`` distribution feed from ``apps.json``."""
    if client not in CLIENTS:
        raise ValueError(f"unknown client '{client}' (expected one of {', '.join(CLIENTS)})")
    apps = [item for item in envelope.get("apps", []) if isinstance(item, dict)]
    projected = [entry for app in apps if (entry := filter_for_client(app, client)) is not None]
    feed = {
        "name": envelope.get("name", "OmniSource"),
        "identifier": envelope.get("identifier", "com.omnisource.source"),
        "apiVersion": envelope.get("apiVersion", "v2"),
        "subtitle": envelope.get("subtitle", ""),
        "description": envelope.get("description", ""),
        "iconURL": envelope.get("iconURL", ""),
        "tintColor": envelope.get("tintColor", "FF0000"),
        "website": envelope.get("website", ""),
        "sourceURL": envelope.get("sourceURL", ""),
        "client": client,
        "apps": projected,
        "news": envelope.get("news", []),
    }
    return feed


def render_all(envelope: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Render all five client feeds; returns ``{client: feed}``."""
    return {client: render_client_feed(envelope, client) for client in CLIENTS}
