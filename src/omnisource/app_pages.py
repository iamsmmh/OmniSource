"""Static app detail page generator.

Every catalog app gets a fully static, search-engine friendly page at
``apps/<slug>/index.html``. Pages are generated from the same data as the
feeds — catalog metadata, pipeline state (version history), health and
verification documents — and are never hand-edited. The Pages builder copies
the ``apps/`` directory into the deployed site, so each app has a permanent
URL: ``https://iamsmmh.github.io/OmniSource/apps/<slug>/``.

Pages are self-contained (inline theme/copy script, shared CSS) and link back
to the landing page, per-app feed, RSS and direct download, so they work with
or without JavaScript.
"""

from __future__ import annotations

import html
import shutil
from datetime import date
from pathlib import Path
from typing import Any

from omnisource.discovery import newest_version, source_label
from omnisource.domain import Catalog, today
from omnisource.duplicates import group_for_app
from omnisource.io import atomic_write_text


def _fmt_bytes(size: int) -> str:
    if not size or size < 0:
        return "Unknown"
    units = ["B", "KB", "MB", "GB"]
    value = float(size)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            break
        value /= 1024
    text = f"{value:.1f}" if value >= 10 or unit in ("MB", "GB") else f"{value:.0f}"
    return f"{text} {unit}"


def _fmt_date(value: str) -> str:
    try:
        parsed = date.fromisoformat(str(value)[:10])
        return parsed.strftime("%b %d, %Y")
    except ValueError:
        return str(value or "Unknown")


def _time_ago(value: str) -> str:
    try:
        parsed = date.fromisoformat(str(value)[:10])
    except ValueError:
        return "Unknown"
    days = max(0, (date.today() - parsed).days)
    if days == 0:
        return "today"
    if days == 1:
        return "yesterday"
    if days < 30:
        return f"{days}d ago"
    if days < 365:
        return f"{round(days / 30)}mo ago"
    return f"{round(days / 365)}y ago"


def _install_url(client_id: str, feed_url: str) -> str:
    if client_id in ("altstore", "sidestore"):
        return f"{client_id}://source?url={feed_url}"
    if client_id == "feather":
        return f"feather://source/{feed_url.removeprefix('https://').removeprefix('http://')}"
    return ""


def _badge(cls: str, label: str) -> str:
    return f'<span class="badge {html.escape(cls)}">{html.escape(label)}</span>'


def _badges(status: str, health_ok: bool, verification_level: str, stale: bool) -> str:
    parts = [
        _badge("stable" if status == "stable" else status, status.title()),
        _badge("ok" if health_ok else "bad", "● Online" if health_ok else "● Download unavailable"),
        _badge("neutral" if verification_level == "VERIFIED" else "warn", verification_level),
    ]
    if stale and status != "unmaintained":
        parts.append(_badge("warn", "Stale release"))
    return "".join(parts)


def _client_buttons(catalog: Catalog, feed_url: str) -> str:
    buttons: list[str] = []
    for client in catalog.clients:
        client_id = str(client.get("id") or "")
        name = str(client.get("name") or client_id.title())
        icon = str(client.get("icon") or "")
        if icon:
            image = f'<img src="../../assets/{html.escape(icon)}" alt="" width="20" height="20" loading="lazy">'
        else:
            image = f'<span class="cli-fallback">{html.escape(name[:1].upper())}</span>'
        url = _install_url(client_id, feed_url)
        if url:
            buttons.append(
                f'<a class="button client-button" href="{html.escape(url)}" '
                f'title="Add to {html.escape(name)}">{image}{html.escape(name)}</a>'
            )
        else:
            buttons.append(
                f'<button class="button client-button" type="button" '
                f'data-copy="{html.escape(feed_url)}" title="Open {html.escape(name)} '
                f'and paste the source URL">{image}{html.escape(name)}</button>'
            )
    return "".join(buttons)


def _version_rows(versions: list[dict[str, Any]]) -> str:
    if not versions:
        return '<p class="ap-desc">No version history is published yet.</p>'
    rows: list[str] = []
    for index, version in enumerate(versions[:12]):
        notes = str(version.get("localizedDescription") or "")
        current = '<span class="tag">Current</span>' if index == 0 else ""
        sha = str(version.get("sha256") or "")
        sha_html = (
            f'<code title="SHA-256">{html.escape(sha[:16])}…</code>' if sha else ("<span>No checksum published</span>")
        )
        download = str(version.get("downloadURL") or "")
        if download:
            download_link = (
                f'<a class="button" href="{html.escape(download)}" target="_blank" rel="noopener">Download</a>'
            )
        else:
            download_link = ""
        number = html.escape(str(version.get("version") or "—"))
        published = html.escape(_fmt_date(str(version.get("date") or "")))
        size = html.escape(_fmt_bytes(int(version.get("size") or 0)))
        notes_html = html.escape(notes[:4000])
        rows.append(
            f"""<article class="ap-version">
  <div class="ap-version-head"><span class="v">v{number}</span>{current}
    <span class="d">{published}</span></div>
  <div class="meta"><span>{size}</span>{sha_html}{download_link}</div>
  <pre class="ap-notes">{notes_html}</pre>
</article>"""
        )
    return f'<div class="ap-version-list">{"".join(rows)}</div>'


def _checks_html(checks: dict[str, bool]) -> str:
    cells = []
    for key, ok in checks.items():
        state = "pass" if ok else "fail"
        cells.append(
            f'<div class="ap-cell"><span>Check</span><strong>{html.escape(key)}: {html.escape(state)}</strong></div>'
        )
    return "".join(cells)


def _install_cards_html(install_doc: dict[str, Any] | None, slug: str) -> str:
    """Render the per-client install card row for a given app slug."""
    if not install_doc:
        return ""
    app_entry = next(
        (item for item in install_doc.get("apps", []) if item.get("slug") == slug),
        None,
    )
    if not app_entry:
        return ""
    cards = app_entry.get("cards", [])
    if not cards:
        return ""
    items: list[str] = []
    for card in cards:
        name = html.escape(str(card.get("name") or ""))
        url = html.escape(str(card.get("url") or ""))
        icon = html.escape(str(card.get("icon") or ""))
        recommended = bool(card.get("recommended"))
        manual = bool(card.get("manualSetup"))
        badge = ""
        if recommended:
            badge = '<span class="ap-recommended">Recommended</span>'
        elif manual:
            badge = '<span class="ap-manual">Manual setup</span>'
        else:
            badge = '<span class="ap-compatible">Compatible</span>'
        icon_html = f'<img src="../../assets/{icon}" alt="" width="22" height="22" loading="lazy">' if icon else ""
        if url:
            items.append(
                f'<a class="ap-install-card" href="{url}" title="Open in {name}">'
                f"{icon_html}<div><b>{name}</b>{badge}</div>"
                f"<small>{html.escape(str(card.get('instructions') or ''))}</small>"
                f"</a>"
            )
        else:
            items.append(
                f'<button class="ap-install-card" type="button" '
                f'data-copy="{html.escape(str(card.get("feedURL") or ""))}" '
                f'title="Open {name} and paste the URL"><div>{icon_html}<b>{name}</b>{badge}</div>'
                f"<small>{html.escape(str(card.get('instructions') or ''))}</small></button>"
            )
    return '<div class="ap-install-grid">' + "".join(items) + "</div>"


def _related_html(related_doc: dict[str, Any] | None, slug: str) -> str:
    """Render the related-apps strip for a given app slug."""
    if not related_doc:
        return ""
    related = related_doc.get("related", {}).get(slug) or []
    if not related:
        return ""
    items: list[str] = []
    for entry in related[:5]:
        target_slug = html.escape(str(entry.get("slug") or ""))
        name = html.escape(str(entry.get("name") or ""))
        reason = html.escape(", ".join(entry.get("reasons") or []))
        score = entry.get("score") or 0
        items.append(
            f'<a class="ap-related-card" href="../{target_slug}/" title="{reason}">'
            f'<div class="ap-related-name">{name}</div>'
            f'<div class="ap-related-reason">{reason}</div>'
            f'<div class="ap-related-score">{round(float(score) * 100)}</div>'
            f"</a>"
        )
    return '<div class="ap-related-grid">' + "".join(items) + "</div>"


def _detail_cells(
    app: Any,
    newest: dict[str, Any],
    health: dict[str, Any],
    verification_level: str,
    version_count: int,
) -> str:
    version = html.escape(str(newest.get("version") or "—"))
    updated_at = html.escape(_fmt_date(str(newest.get("date") or "")))
    updated_ago = html.escape(_time_ago(str(newest.get("date") or "")))
    size = html.escape(_fmt_bytes(int(newest.get("size") or 0)))
    required_os = html.escape(app.minimum_ios_version or "Not listed")
    category = html.escape(str(app.category or "other").title())
    developer = html.escape(app.developer or "—")
    bundle = html.escape(app.bundle_id or "—")
    checksum = html.escape(str(newest.get("sha256") or "Not published")[:20])
    health_text = html.escape("Online" if health.get("downloadReachable") else "Unavailable")
    verification = html.escape(verification_level)
    source = html.escape(source_label(app))
    cells = [
        ("Version", f"v{version}"),
        ("Updated", f"{updated_at} ({updated_ago})"),
        ("Size", size),
        ("Requires iOS", required_os),
        ("Category", category),
        ("Developer", developer),
        ("Bundle ID", f"<code>{bundle}</code>"),
        ("Verification", verification),
        ("Checksum", f"<code>{checksum}</code>"),
        ("Health", health_text),
        ("Version history", str(version_count)),
        ("Source", source),
    ]
    return "".join(
        f'<div class="ap-cell"><span>{html.escape(label)}</span><strong>{value}</strong></div>'
        for label, value in cells
    )


def _duplicate_banner(app: Any, duplicate: dict[str, Any] | None) -> str:
    if not duplicate:
        return ""
    recommended = duplicate.get("recommended") if isinstance(duplicate.get("recommended"), dict) else {}
    target = recommended.get("app") or ""
    reason = html.escape(str(duplicate.get("reason") or ""))
    recommendation = (
        f"Recommended: <b>{html.escape(str(recommended.get('name') or target))}</b> — "
        f"{html.escape(str(recommended.get('reason') or 'Newest version available'))}"
    )
    if target and target != app.slug:
        recommendation += f' <a href="../{html.escape(target)}/">Open {html.escape(target)} →</a>'
    return f"""<div class="ap-alert" role="note">
  <svg aria-hidden="true" viewBox="0 0 24 24" width="20" height="20" fill="none"
    stroke="currentColor" stroke-width="2"><path d="M12 3 2.8 20h18.4L12 3Zm0 6v5m0 3.2v.1"/></svg>
  <div>
    <b>Similar apps detected in the catalog.</b>
    <p>{reason} · {recommendation}</p>
  </div>
</div>"""


def render_app_page(
    catalog: Catalog,
    app: Any,
    state: dict[str, Any],
    health_doc: dict[str, Any],
    verification_doc: dict[str, Any],
    duplicates_doc: dict[str, Any],
    related_doc: dict[str, Any] | None = None,
    install_doc: dict[str, Any] | None = None,
) -> str:
    """Render one app detail page as an HTML string."""
    base = catalog.base_url.rstrip("/")
    app_state = state.get(app.slug) if isinstance(state.get(app.slug), dict) else {}
    versions = app_state.get("versions") if isinstance(app_state.get("versions"), list) else []
    newest = newest_version(state, app.slug)
    health_item = next(
        (item for item in health_doc.get("apps", []) if item.get("slug") == app.slug),
        {},
    )
    verification_item = next(
        (item for item in verification_doc.get("apps", []) if item.get("app") == app.slug),
        {"status": "UNVERIFIED", "checks": {}, "reasons": []},
    )
    verification_level = str(verification_item.get("status") or "UNVERIFIED")
    duplicate = group_for_app(duplicates_doc, app.slug)

    icon_url = f"{base}/assets/{app.icon}"
    feed_url = f"{base}/{app.slug}.json"
    rss_url = f"{base}/{app.slug}.xml"
    page_url = f"{base}/apps/{app.slug}/"
    download_url = str(newest.get("downloadURL") or app.raw.get("downloadURL") or "")
    screenshots = [url for url in app.screenshots if str(url).startswith(("http://", "https://"))]
    publisher = str(app.raw.get("verification", {}).get("publisher") or app.developer)
    compatibility = app.raw.get("compatibility")
    source_notes = str(compatibility.get("notes") or "") if isinstance(compatibility, dict) else ""
    fallbacks = newest.get("fallbackDownloadURLs") or app.raw.get("fallbackDownloadURLs") or []
    fallbacks = [url for url in fallbacks if isinstance(url, str) and url.startswith(("http://", "https://"))]
    checks = verification_item.get("checks") if isinstance(verification_item.get("checks"), dict) else {}
    reasons = verification_item.get("reasons") if isinstance(verification_item.get("reasons"), list) else []

    title = html.escape(app.name)
    sub = html.escape(app.short_description or app.description or f"{app.name} on OmniSource")
    description = html.escape(app.description or "No description provided.")
    category_title = str(app.category or "other").title()
    extra_tags = [tag for tag in app.tags if tag != app.category]
    tagline = f"{category_title} · {' · '.join(extra_tags)}" if extra_tags else category_title
    version_text = html.escape(str(newest.get("version") or "—"))
    size_text = html.escape(_fmt_bytes(int(newest.get("size") or 0)))
    screenshots_html = "".join(
        f'<img src="{html.escape(url)}" alt="{title} screenshot {index}" loading="lazy">'
        for index, url in enumerate(screenshots, start=1)
    )
    fallback_html = "".join(
        f'<a class="button" href="{html.escape(url)}" target="_blank" rel="noopener">Mirror {index}</a>'
        for index, url in enumerate(fallbacks, start=1)
    )
    reasons_html = "".join(f"<li>{html.escape(reason)}</li>" for reason in reasons)
    method_text = html.escape(str(app.raw.get("verification", {}).get("method") or "upstream source").replace("-", " "))
    notes_html = html.escape(source_notes)
    upstream_url = html.escape(app.repository_url or "")

    head = [
        "<!doctype html>\n",
        '<html lang="en" data-theme="auto">\n<head>\n',
        '  <meta charset="utf-8">\n',
        '  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n',
        '  <meta name="theme-color" content="#f4f5fa" media="(prefers-color-scheme: light)">\n',
        '  <meta name="theme-color" content="#0b0c10" media="(prefers-color-scheme: dark)">\n',
        f"  <title>{title} — OmniSource</title>\n",
        f'  <meta name="description" content="{sub}">\n',
        f'  <link rel="canonical" href="{html.escape(page_url)}">\n',
        f'  <meta property="og:title" content="{title} — OmniSource">\n',
        f'  <meta property="og:description" content="{sub}">\n',
        f'  <meta property="og:image" content="{html.escape(icon_url)}">\n',
        '  <meta property="og:type" content="website">\n',
        f'  <meta property="og:url" content="{html.escape(page_url)}">\n',
        '  <link rel="icon" type="image/png" href="../../assets/OmniSource.png">\n',
        '  <link rel="apple-touch-icon" href="../../assets/OmniSource.png">\n',
        f'  <link rel="alternate" type="application/rss+xml" title="{title} releases"',
        f' href="{html.escape(rss_url)}">\n',
        '  <link rel="preload" href="../../css/styles.css" as="style">\n',
        '  <link rel="preload" href="../../css/app-page.css" as="style">\n',
        '  <link rel="stylesheet" href="../../css/styles.css">\n',
        '  <link rel="stylesheet" href="../../css/app-page.css">\n',
        '  <script type="application/ld+json">\n',
        "    {\n",
        '      "@context": "https://schema.org",\n',
        '      "@type": "SoftwareApplication",\n',
        f'      "name": "{html.escape(app.name, quote=True)}",\n',
        '      "applicationCategory": "UtilitiesApplication",\n',
        '      "operatingSystem": "iOS",\n',
        f'      "softwareVersion": "{html.escape(str(newest.get("version") or ""), quote=True)}",\n',
        f'      "url": "{html.escape(page_url, quote=True)}",\n',
        f'      "downloadUrl": "{html.escape(download_url, quote=True)}",\n',
        '      "author": { "@type": "Organization", "name":',
        f' "{html.escape(publisher, quote=True)}" }}\n',
        "    }\n",
        "  </script>\n</head>\n",
    ]

    hero = [
        '<body class="app-page">\n',
        '  <a class="skip-link" href="#main">Skip to app details</a>\n',
        '  <header class="ap-header">\n',
        '    <nav class="ap-header-inner" aria-label="App navigation">\n',
        '      <a class="brand" href="../../" aria-label="OmniSource home">\n',
        '        <img src="../../assets/OmniSource.png" alt="" width="34" height="34">\n',
        "        <span>OmniSource</span>\n",
        "      </a>\n",
        '      <div class="nav-links">\n',
        '        <a href="../../#catalog">Catalog</a>\n',
        f'        <a href="{html.escape(rss_url)}" target="_blank" rel="noopener">RSS</a>\n',
        f'        <a href="{html.escape(feed_url)}" target="_blank" rel="noopener">Feed</a>\n',
        '        <a href="https://github.com/iamsmmh/OmniSource"',
        ' target="_blank" rel="noopener">GitHub</a>\n',
        "      </div>\n",
        '      <button class="icon-button ap-theme" id="appTheme" type="button"',
        ' aria-label="Change color theme" title="Theme: system">\n',
        '        <svg class="icon-sun" aria-hidden="true" viewBox="0 0 24 24">',
        '<circle cx="12" cy="12" r="4.2"/><path d="M12 2.8v2M12 19.2v2M2.8 12h2M19.2 12h2',
        'M5.4 5.4l1.4 1.4M17.2 17.2l1.4 1.4M18.6 5.4l-1.4 1.4M6.8 17.2l-1.4 1.4"/></svg>\n',
        '        <svg class="icon-moon" aria-hidden="true" viewBox="0 0 24 24">',
        '<path d="M20.4 14.2A8.6 8.6 0 0 1 9.8 3.6a8.6 8.6 0 1 0 10.6 10.6Z"/></svg>\n',
        "      </button>\n",
        "    </nav>\n",
        "  </header>\n\n",
        '  <main class="ap-main" id="main">\n',
        '    <section class="ap-hero">\n',
        f'      <img class="ap-icon" src="{html.escape(icon_url)}" alt="{title} icon"',
        ' width="108" height="108">\n',
        "      <div>\n",
        f'        <span class="ap-kicker">{html.escape(tagline)}</span>\n',
        f'        <h1 class="ap-title">{title}</h1>\n',
        f'        <p class="ap-sub">{sub}</p>\n',
        f'        <p class="ap-dev">by {html.escape(app.developer or "Unknown developer")}</p>\n',
        '        <div class="ap-badges">',
        _badges(
            app.status,
            bool(health_item.get("downloadReachable", True)),
            verification_level,
            bool(health_item.get("stale")),
        ),
        "</div>\n      </div>\n",
        _duplicate_banner(app, duplicate),
        '      <div class="ap-install">\n',
        f'        <a class="button primary" href="{html.escape(download_url)}"',
        ' target="_blank" rel="noopener">⬇ Download IPA · ',
        f"{size_text}</a>\n",
        _client_buttons(catalog, feed_url),
        '        <button class="button ap-copy" type="button"',
        f' data-copy="{html.escape(feed_url)}">Copy source URL</button>\n',
        "      </div>\n",
        "    </section>\n",
    ]

    sections = [
        '    <section class="ap-section">\n',
        '      <h2><span class="num">01</span> About</h2>\n',
        f'      <p class="ap-desc">{description}</p>\n',
        f'      <div class="ap-screenshots">{screenshots_html}</div>\n',
        "    </section>\n\n",
        '    <section class="ap-section">\n',
        '      <h2><span class="num">02</span> Install with</h2>\n',
        '      <p class="ap-desc">Pick your client. URLs are generated from your catalog, never hard-coded.</p>\n',
        _install_cards_html(install_doc, app.slug),
        "    </section>\n\n",
        '    <section class="ap-section">\n',
        '      <h2><span class="num">03</span> Release notes</h2>\n',
        f"      {_version_rows(versions)}\n",
        "    </section>\n\n",
        '    <section class="ap-section">\n',
        '      <h2><span class="num">04</span> Details</h2>\n',
        '      <div class="ap-detail-grid">',
        _detail_cells(app, newest, health_item, verification_level, len(versions)),
        "</div>\n",
        "    </section>\n\n",
        '    <section class="ap-section">\n',
        '      <h2><span class="num">05</span> Trust &amp; provenance</h2>\n',
        '      <div class="ap-detail-grid">',
        _checks_html(checks),
        "</div>\n",
        '      <p class="ap-desc" style="margin-top:14px">',
        f"Published by {html.escape(publisher)} · {method_text}.</p>\n",
        f"      <ul>{reasons_html}</ul>\n",
        (
            '      <div class="ap-detail-note" style="margin-top:12px">'
            f"<b>Compatibility notes:</b> {notes_html}</div>\n"
            if source_notes
            else ""
        ),
        "    </section>\n\n",
        '    <section class="ap-section">\n',
        '      <h2><span class="num">06</span> Related apps</h2>\n',
        f'      <p class="ap-desc">Apps that share a bundle, category or developer with {html.escape(app.name)}.</p>\n',
        _related_html(related_doc, app.slug),
        "    </section>\n\n",
        '    <section class="ap-section">\n',
        '      <h2><span class="num">07</span> Downloads</h2>\n',
        '      <div class="ap-links">\n',
        f'        <a class="button primary" href="{html.escape(download_url)}"',
        ' target="_blank" rel="noopener">Primary IPA</a>\n',
        f"        {fallback_html}\n",
        f'        <a class="button" href="{html.escape(feed_url)}"',
        ' target="_blank" rel="noopener">App feed</a>\n',
        f'        <a class="button" href="{html.escape(rss_url)}"',
        ' target="_blank" rel="noopener">App RSS</a>\n',
        f'        <a class="button" href="{upstream_url}" target="_blank"',
        ' rel="noopener">Upstream</a>\n',
        f'        <a class="button" href="{html.escape(base)}/discovery.json"',
        ' target="_blank" rel="noopener">Discovery catalog</a>\n',
        f'        <a class="button" href="{html.escape(base)}/compare.html?left={html.escape(app.slug)}"',
        ' target="_blank" rel="noopener">Compare with another app</a>\n',
        "      </div>\n",
        "    </section>\n",
        "  </main>\n\n",
        '  <footer class="ap-footer">\n',
        '    <div class="shell">\n',
        f"      <span>Generated {html.escape(today())} · v{version_text} of {title}.</span>\n",
        '      <a href="../../#catalog">← Back to catalog</a>\n',
        "      <span>Independent community project. Apps and trademarks belong to",
        " their respective owners.</span>\n",
        "    </div>\n",
        "  </footer>\n\n",
        f"  <script>{PAGE_SCRIPT}</script>\n",
        "</body>\n</html>\n",
    ]
    return "".join(head + hero + sections)


PAGE_SCRIPT = """
(function () {
  'use strict';
  var applyTheme = function (theme) {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem('omnisource-theme', theme);
  };
  var theme = localStorage.getItem('omnisource-theme') || 'auto';
  if (['auto', 'light', 'dark'].indexOf(theme) === -1) theme = 'auto';
  applyTheme(theme);
  var button = document.querySelector('.ap-header .icon-button, #appTheme');
  if (button) button.addEventListener('click', function () {
    var order = ['auto', 'light', 'dark'];
    applyTheme(order[(order.indexOf(document.documentElement.dataset.theme) + 1) % order.length]);
  });
  document.addEventListener('click', function (event) {
    var trigger = event.target.closest ? event.target.closest('[data-copy]') : null;
    if (!trigger) return;
    var value = trigger.getAttribute('data-copy') || '';
    var done = function () {
      var label = trigger.textContent || 'Copy';
      trigger.textContent = 'Copied \\u2713';
      setTimeout(function () { trigger.textContent = label; }, 1800);
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(value).then(done, done);
    } else {
      var input = document.createElement('textarea');
      input.value = value;
      document.body.appendChild(input);
      input.select();
      document.execCommand('copy');
      input.remove();
      done();
    }
  });
})();
"""


def build_app_pages(
    catalog: Catalog,
    state: dict[str, Any],
    health_doc: dict[str, Any],
    verification_doc: dict[str, Any],
    duplicates_doc: dict[str, Any],
    *,
    pages_dir: Path,
    related_doc: dict[str, Any] | None = None,
    install_doc: dict[str, Any] | None = None,
) -> list[Path]:
    """Render every app page and remove pages for apps that left the catalog."""
    changed: list[Path] = []
    for app in catalog.apps:
        page = pages_dir / app.slug / "index.html"
        content = render_app_page(
            catalog,
            app,
            state,
            health_doc,
            verification_doc,
            duplicates_doc,
            related_doc=related_doc,
            install_doc=install_doc,
        )
        if atomic_write_text(page, content):
            changed.append(page)

    # Clean up stale pages so removed apps never stay published.
    valid = {app.slug for app in catalog.apps}
    if pages_dir.is_dir():
        for child in sorted(pages_dir.iterdir()):
            if child.is_dir() and child.name not in valid:
                shutil.rmtree(child, ignore_errors=True)
                changed.append(child)
    return changed
