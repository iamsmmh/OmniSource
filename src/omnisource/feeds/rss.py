"""RSS 2.0 and Atom feed generator for release updates."""

from __future__ import annotations

import html
from datetime import UTC, datetime
from typing import Any

from omnisource.domain import Catalog


def _rfc822_date(date_str: str) -> str:
    """Format an ISO date string (YYYY-MM-DD or full timestamp) as RFC 822."""
    try:
        if "T" in date_str or " " in date_str:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        else:
            dt = datetime.strptime(date_str[:10], "%Y-%m-%d").replace(tzinfo=UTC)
        return dt.strftime("%a, %d %b %Y %H:%M:%S +0000")
    except Exception:
        return datetime.now(UTC).strftime("%a, %d %b %Y %H:%M:%S +0000")


def render_rss_feed(
    catalog: Catalog,
    state: dict[str, Any],
    limit: int = 25,
) -> str:
    """Generate a clean RSS 2.0 XML feed of recent updates."""
    base = catalog.base_url.rstrip("/")
    source_name = str(catalog.source.get("name", "OmniSource"))
    source_desc = str(catalog.source.get("description", "OmniSource curated iOS app updates"))

    now_rfc822 = datetime.now(UTC).strftime("%a, %d %b %Y %H:%M:%S +0000")

    app_by_slug = {app.slug: app for app in catalog.apps}

    items: list[dict[str, Any]] = []
    seen: set[str] = set()

    # 1. From recorded update history
    history = state.get("updateHistory", [])
    if isinstance(history, list):
        for event in history:
            if not isinstance(event, dict):
                continue
            app_id = str(event.get("appId") or "")
            app = app_by_slug.get(app_id)
            if not app:
                continue
            version = str(event.get("version") or "")
            guid = f"{app.slug}-{version}"
            if guid in seen:
                continue
            seen.add(guid)
            items.append(
                {
                    "title": f"{app.name} v{version}",
                    "link": f"{base}/{app.slug}.json",
                    "guid": guid,
                    "date": _rfc822_date(str(event.get("releaseDate") or "")),
                    "description": str(event.get("changelog") or app.short_description or ""),
                    "download_url": str(event.get("downloadUrl") or ""),
                }
            )
            if len(items) >= limit:
                break

    # 2. Seed with newest app versions if history is sparse
    if len(items) < limit:
        for app in catalog.apps:
            versions = state.get(app.slug, {}).get("versions")
            if not isinstance(versions, list) or not versions:
                continue
            newest = versions[0]
            version = str(newest.get("version") or "")
            guid = f"{app.slug}-{version}"
            if guid in seen:
                continue
            seen.add(guid)
            items.append(
                {
                    "title": f"{app.name} v{version}",
                    "link": f"{base}/{app.slug}.json",
                    "guid": guid,
                    "date": _rfc822_date(str(newest.get("date") or "")),
                    "description": str(newest.get("localizedDescription") or app.short_description or ""),
                    "download_url": str(newest.get("downloadURL") or ""),
                    "size": newest.get("size", 0),
                }
            )
            if len(items) >= limit:
                break

    item_xml_lines: list[str] = []
    for item in items:
        esc_title = html.escape(item["title"])
        esc_link = html.escape(item["link"])
        esc_guid = html.escape(item["guid"])
        esc_desc = f"<![CDATA[{item['description']}]]>"
        enclosure = ""
        if item.get("download_url"):
            esc_dl = html.escape(item["download_url"])
            size = item.get("size", 0)
            enclosure = f'\n      <enclosure url="{esc_dl}" length="{size}" type="application/octet-stream" />'

        item_xml_lines.append(f"""    <item>
      <title>{esc_title}</title>
      <link>{esc_link}</link>
      <guid isPermaLink="false">{esc_guid}</guid>
      <pubDate>{item["date"]}</pubDate>
      <description>{esc_desc}</description>{enclosure}
    </item>""")

    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>{html.escape(source_name)} Updates</title>
    <link>{html.escape(base)}/</link>
    <description>{html.escape(source_desc)}</description>
    <language>en-us</language>
    <lastBuildDate>{now_rfc822}</lastBuildDate>
    <atom:link href="{html.escape(base)}/feed.xml" rel="self" type="application/rss+xml"/>
{chr(10).join(item_xml_lines)}
  </channel>
</rss>
"""
    return xml_content
