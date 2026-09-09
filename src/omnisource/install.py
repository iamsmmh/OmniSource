"""Install card generator.

The website and per-app pages need a uniform "install with" card for every
supported client. The catalog only declares the supported clients; this
module combines that with each app's per-app feed URL to produce a fully
typed ``feeds/install.json`` document that the front-end can render without
recomputing deep links.

The result is intentionally not hard-coded — every URL is derived from
``baseURL`` and the per-app feed, so a future host rename is a single edit
to the catalog.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urlsplit

from omnisource.domain import Catalog, today

INSTALL_SCHEMA_VERSION = 1

# Each client is described with: id, name, icon, supported URL scheme(s),
# and whether the source URL is *deep-linkable*. ESign and LiveContainer
# don't expose a ``source?url=`` scheme, so users paste the URL manually.
CLIENT_PROFILES = {
    "altstore": {
        "id": "altstore",
        "name": "AltStore",
        "scheme": "altstore://source?url={url}",
        "deepLinkable": True,
        "instructions": "Tap to add the source to AltStore.",
        "manualSetup": False,
    },
    "sidestore": {
        "id": "sidestore",
        "name": "SideStore",
        "scheme": "sidestore://source?url={url}",
        "deepLinkable": True,
        "instructions": "Tap to add the source to SideStore.",
        "manualSetup": False,
    },
    "feather": {
        "id": "feather",
        "name": "Feather",
        "scheme": "feather://source/{host}{path}",
        "deepLinkable": True,
        "instructions": "Tap to add the source to Feather.",
        "manualSetup": False,
    },
    "esign": {
        "id": "esign",
        "name": "ESign",
        "scheme": "",
        "deepLinkable": False,
        "instructions": "Open ESign, choose Sources and paste the URL.",
        "manualSetup": True,
    },
    "livecontainer": {
        "id": "livecontainer",
        "name": "LiveContainer",
        "scheme": "",
        "deepLinkable": False,
        "instructions": "Open LiveContainer, choose Sources and paste the URL.",
        "manualSetup": True,
    },
}


def _build_url(profile: dict[str, Any], feed_url: str) -> str:
    template = profile.get("scheme") or ""
    if not template:
        return ""
    if profile.get("id") == "feather":
        parts = urlsplit(feed_url)
        host_path = parts.netloc + parts.path or feed_url.split("://", 1)[-1]
        return f"feather://source/{host_path}"
    return template.format(url=feed_url)


def install_url(client_id: str, feed_url: str) -> str:
    """Return the deep link that adds ``feed_url`` to ``client_id``.

    Clients without a source protocol (ESign, LiveContainer, unknown ids)
    return ``""`` — callers fall back to copy-paste.
    """
    profile = CLIENT_PROFILES.get(client_id)
    if profile is None:
        return ""
    return _build_url(profile, feed_url)


def build_install_doc(
    catalog: Catalog,
    *,
    base_url: str | None = None,
) -> dict[str, Any]:
    """Build ``feeds/install.json``."""
    base = (base_url or catalog.base_url).rstrip("/")
    # Use the clients declared in the catalog as the source of truth; the
    # CLIENT_PROFILES table is a fallback so a misconfigured catalog does
    # not silently drop a client.
    clients = []
    for client in catalog.clients:
        cid = str(client.get("id") or "")
        if not cid:
            continue
        profile = CLIENT_PROFILES.get(cid)
        if profile is None:
            clients.append(
                {
                    "id": cid,
                    "name": str(client.get("name") or cid.title()),
                    "icon": str(client.get("icon") or ""),
                    "deepLinkable": False,
                    "manualSetup": True,
                    "instructions": f"Open {client.get('name') or cid} and add the source manually.",
                    "scheme": "",
                }
            )
        else:
            clients.append({**profile, "icon": str(client.get("icon") or profile.get("icon", ""))})

    def _cards(feed_url: str) -> list[dict[str, Any]]:
        cards = []
        for client in clients:
            cid = client["id"]
            cards.append(
                {
                    "client": cid,
                    "name": client["name"],
                    "icon": client.get("icon", ""),
                    "compatible": True,
                    "recommended": cid in {"altstore", "sidestore"},
                    "manualSetup": bool(client.get("manualSetup", False)),
                    "url": _build_url(client, feed_url),
                    "feedURL": feed_url,
                    "instructions": client.get("instructions", ""),
                }
            )
        return cards

    apps = []
    for app in catalog.apps:
        feed_url = f"{base}/{app.slug}.json"
        apps.append(
            {
                "slug": app.slug,
                "name": app.name,
                "feedURL": feed_url,
                "cards": _cards(feed_url),
            }
        )
    # Catalog-level "add the whole OmniSource" card (built once, not per app).
    master_feed = f"{base}/apps.json"
    master = {
        "name": str(catalog.source.get("name", "OmniSource")),
        "feedURL": master_feed,
        "cards": _cards(master_feed),
    }
    return {
        "schemaVersion": INSTALL_SCHEMA_VERSION,
        "generatedAt": today(),
        "baseURL": base,
        "clients": clients,
        "master": master,
        "apps": apps,
    }
