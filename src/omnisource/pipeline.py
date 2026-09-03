"""Pipeline orchestrator.

Stages
------
1. ``sync``       Resolve upstream releases through the provider registry.
2. ``health``     Probe every download URL concurrently.
3. ``build``      Render AltStore feeds + OmniStore feeds + API snapshots.
4. ``mirror``     Copy AltStore feeds to the historical root-level paths.
5. ``readme``     Refresh the generated catalog block inside README.md.

A failing upstream degrades to "keep serving the last good build". The
pipeline is idempotent: unchanged payloads are not written.
"""

from __future__ import annotations

import concurrent.futures
import os
import re
import time
from pathlib import Path
from typing import Any

from omnisource.api import render_api_bundle
from omnisource.assets import DirectoryCache, inspect_catalog
from omnisource.constants import README_MARKERS
from omnisource.di import Container, build_container
from omnisource.domain import App, Catalog, SyncReport, UpdateEvent, today
from omnisource.errors import ConfigurationError, ProviderError, SyncError
from omnisource.feeds.altstore import feed_envelope, render_altstore_app, render_health_doc
from omnisource.feeds.omnistore import render_omnistore_bundle
from omnisource.io import read_json, write_json
from omnisource.logutil import Group, log
from omnisource.tracking import detect_update, select_versions


def _reuse_or(path: Path, fallback: dict[str, Any]) -> dict[str, Any]:
    existing = read_json(path)
    return existing if isinstance(existing, dict) else fallback


def load_catalog(container: Container) -> Catalog:
    raw = read_json(container.paths.catalog)
    if not isinstance(raw, dict):
        raise SyncError(f"{container.paths.catalog.name} is missing or not a JSON object")
    return Catalog.from_dict(raw)


def load_state(container: Container) -> dict[str, Any]:
    raw = read_json(container.paths.feeds / "state.json")
    return raw if isinstance(raw, dict) else {}


def _compile_pattern(app: App) -> re.Pattern[str] | None:
    up = app.upstream
    if up is None or not up.asset_name_pattern:
        return None
    try:
        return re.compile(up.asset_name_pattern)
    except re.error as error:
        raise SyncError(f"{app.slug}: upstream.assetNamePattern does not compile: {error}") from error


def _manual_versions(app: App, reason: str) -> list[dict[str, Any]] | None:
    manual = app.manual_release
    if manual:
        log.info("%-14s %s - using manualRelease v%s from catalog.json", app.slug, reason, manual.get("version"))
        return [manual]
    log.warning("%-14s %s and no manualRelease fallback exists", app.slug, reason)
    return None


def sync_app(
    container: Container,
    app: App,
    *,
    incremental: bool,
    previous: dict[str, Any] | None,
) -> list[dict[str, Any]] | None:
    """Return the version list for ``app`` or ``None`` to keep previous state."""
    up = app.upstream
    previous_versions = (previous or {}).get("versions") if isinstance(previous, dict) else None
    previous_url = None
    if isinstance(previous_versions, list) and previous_versions:
        previous_url = previous_versions[0].get("downloadURL")

    if up is None:
        return _manual_versions(app, "no upstream configured")

    provider = container.providers.resolve(up)
    try:
        releases = provider.fetch_releases(up, previous_latest_url=previous_url, incremental=incremental)
    except (ProviderError, ConfigurationError) as error:
        raise SyncError(str(error)) from error

    if incremental and previous_versions and not releases:
        log.info("%-14s incremental hit - keeping v%s", app.slug, previous_versions[0].get("version"))
        return None

    if not releases:
        return _manual_versions(app, f"no published release with a matching asset in {up.repo or up.feed_url}")

    versions = select_versions(app_name=app.name, ref=up, releases=releases, pattern=_compile_pattern(app))
    if not versions:
        return _manual_versions(app, "upstream produced no usable version entries")

    log.info(
        "%-14s %-28s -> v%s (%d version(s))",
        app.slug,
        up.repo or up.feed_url,
        versions[0]["version"],
        len(versions),
    )
    return versions


def stage_sync(
    container: Container,
    catalog: Catalog,
    state: dict[str, Any],
    *,
    only: set[str] | None,
    incremental: bool,
    report: SyncReport,
) -> dict[str, Any]:
    if not (os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")):
        log.warning("No GH_TOKEN/GITHUB_TOKEN set - using unauthenticated API limits (60 req/h)")

    for app in catalog.apps:
        if only and app.slug not in only:
            continue
        previous = state.get(app.slug)
        try:
            versions = sync_app(container, app, incremental=incremental, previous=previous)
        except SyncError as error:
            log.error("%s: upstream sync failed (%s) - keeping last known state", app.slug, error)
            report.apps_failed += 1
            report.errors.append(f"{app.slug}: {error}")
            continue

        report.apps_synced += 1
        if versions is None:
            report.apps_incremental_hit += 1
            continue

        previous_versions = (previous or {}).get("versions") if isinstance(previous, dict) else None
        kind = detect_update(previous_versions if isinstance(previous_versions, list) else None, versions)
        entry = state.setdefault(app.slug, {})
        if entry.get("versions") != versions:
            previous_version = None
            if isinstance(previous_versions, list) and previous_versions:
                previous_version = str(previous_versions[0].get("version") or "") or None
            entry["versions"] = versions
            entry["syncedAt"] = today()
            if kind != "unchanged":
                report.apps_updated += 1
                event = UpdateEvent(
                    app_id=app.slug,
                    name=app.name,
                    version=str(versions[0].get("version") or ""),
                    previous_version=previous_version,
                    release_date=str(versions[0].get("date") or ""),
                    download_url=str(versions[0].get("downloadURL") or ""),
                    changelog=str(versions[0].get("localizedDescription") or ""),
                    kind=kind,
                )
                report.updates.append(event)
                if previous_version:
                    container.analytics.record_update(app.slug, previous_version, event.version)
        elif incremental:
            report.apps_incremental_hit += 1

    report.api_requests = container.http.requests
    log.info("Sync complete using %d HTTP request(s)", container.http.requests)
    return state


def stage_health(
    container: Container,
    catalog: Catalog,
    state: dict[str, Any],
    *,
    enabled: bool,
    workers: int,
) -> None:
    targets = {
        app.slug: state[app.slug]["versions"][0]["downloadURL"]
        for app in catalog.apps
        if state.get(app.slug, {}).get("versions")
    }
    if not enabled:
        log.info("Link health probing disabled (--no-health); reusing stored results")
        return

    started = time.monotonic()
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(container.http.probe, url): slug for slug, url in targets.items()}
        for future in concurrent.futures.as_completed(futures):
            slug = futures[future]
            result = future.result()
            previous = state[slug].get("health", {})
            state[slug]["health"] = {
                "reachable": result.reachable,
                "detail": result.detail,
                "since": previous.get("since", today()) if previous.get("reachable") is result.reachable else today(),
            }
            container.analytics.record_health(slug, result.reachable)
            (log.info if result.reachable else log.warning)(
                "%-14s %s (%s)", slug, "reachable" if result.reachable else "UNREACHABLE", result.detail
            )
    log.info("Probed %d download URL(s) in %.1fs", len(targets), time.monotonic() - started)


def stage_build(
    container: Container,
    catalog: Catalog,
    state: dict[str, Any],
    report: SyncReport,
) -> tuple[list[Path], dict[str, Any]]:
    written: list[Path] = []
    rendered: list[tuple[App, dict[str, Any]]] = []
    versions_by_slug: dict[str, list[dict[str, Any]]] = {}

    for app in catalog.apps:
        versions = state.get(app.slug, {}).get("versions")
        if not versions:
            log.error("%s has no known versions - excluded from this build", app.slug)
            continue
        versions_by_slug[app.slug] = versions
        rendered.append((app, render_altstore_app(catalog, app, versions, state[app.slug].get("health", {}))))

    if not rendered:
        raise SyncError("No app produced a valid feed entry")

    feeds_dir = container.paths.feeds
    base = catalog.base_url
    for app, entry in rendered:
        feed = feed_envelope(
            catalog,
            name=f"OmniSource - {app.name}",
            identifier=f"{catalog.source.get('identifier', 'com.omnisource')}.{app.slug}",
            subtitle=app.raw.get("subtitle", app.name),
            description=f"Standalone distribution feed for {app.name}, curated within OmniSource.",
        )
        feed["sourceURL"] = f"{base}/{app.slug}.json"
        feed["apps"] = [entry]
        feed["news"] = []
        path = feeds_dir / f"{app.slug}.json"
        if write_json(path, feed):
            written.append(path)

    master = feed_envelope(
        catalog,
        name=str(catalog.source.get("name", "OmniSource")),
        identifier=str(catalog.source.get("identifier", "com.omnisource")),
        subtitle=str(catalog.source.get("subtitle", "")),
        description=str(catalog.source.get("description", "")),
    )
    master["apps"] = [entry for _, entry in sorted(rendered, key=lambda item: item[0].name.lower())]
    master["news"] = []
    if write_json(feeds_dir / "apps.json", master):
        written.append(feeds_dir / "apps.json")

    health_doc = render_health_doc(rendered)
    if write_json(feeds_dir / "health.json", health_doc):
        written.append(feeds_dir / "health.json")

    omnistore = render_omnistore_bundle(catalog, versions_by_slug=versions_by_slug, updates=report.updates)
    if not report.updates:
        # Keep the last release report across no-change / --no-sync rebuilds so
        # the file is idempotent and OmniStore still sees the most recent bump.
        omnistore["updates.json"] = _reuse_or(container.paths.omnistore / "updates.json", omnistore["updates.json"])
    for name, document in omnistore.items():
        path = container.paths.omnistore / name
        if write_json(path, document):
            written.append(path)

    api_bundle = render_api_bundle(catalog, versions_by_slug=versions_by_slug, updates=report.updates)
    if not report.updates:
        api_bundle["updates.json"] = _reuse_or(container.paths.api / "updates.json", api_bundle["updates.json"])
    for name, document in api_bundle.items():
        path = container.paths.api / name
        if write_json(path, document):
            written.append(path)

    # Record repository popularity (analytics interface only).
    repos: dict[str, int] = {}
    for app in catalog.apps:
        url = app.repository_url
        if url:
            repos[url] = repos.get(url, 0) + 1
    for url, count in repos.items():
        container.analytics.record_repository_seen(url, count)

    log.info(
        "Built %d app feed(s) + master + OmniStore/API (%d file(s) changed)",
        len(rendered),
        len(written),
    )
    return written, health_doc


def stage_mirror(container: Container, catalog: Catalog) -> list[Path]:
    """Copy generated AltStore feeds to their historical root paths."""
    mirrored: list[Path] = []
    for name in ["apps.json", *(f"{app.slug}.json" for app in catalog.apps)]:
        source = container.paths.feeds / name
        target = container.paths.root / name
        if not source.exists():
            continue
        payload = source.read_text(encoding="utf-8")
        if not target.exists() or target.read_text(encoding="utf-8") != payload:
            target.write_text(payload, encoding="utf-8")
            mirrored.append(target)
    if mirrored:
        log.info("Refreshed %d root mirror(s)", len(mirrored))
    return mirrored


def stage_readme(container: Container, catalog: Catalog, health_doc: dict[str, Any]) -> bool:
    readme = container.paths.readme
    if not readme.exists():
        return False
    start, end = README_MARKERS
    text = readme.read_text(encoding="utf-8")
    if start not in text or end not in text:
        log.debug("README has no generated catalog block - skipping")
        return False

    base = catalog.base_url
    by_slug = {item["slug"]: item for item in health_doc["apps"]}
    status_icon = {"stable": "🟢", "beta": "🟡", "manual": "🔵", "unmaintained": "🔴"}

    header = "| App | Bundle ID | Version | Updated | Status | Download | Install | Feed |"
    divider = "| --- | --- | --- | --- | --- | --- | --- | --- |"
    rows = [header, divider]
    for app in catalog.apps:
        item = by_slug.get(app.slug)
        if not item:
            continue
        feed_url = f"{base}/{app.slug}.json"
        bundle = str(app.raw.get("bundleIdentifier", "—"))
        reachable = "✅" if item["downloadReachable"] else "⚠️"
        install = f"[AltStore](altstore://source?url={feed_url}) · [SideStore](sidestore://source?url={feed_url})"
        rows.append(
            f"| **{app.name}** | `{bundle}` | `{item['version']}` | {item['updatedAt']} | "
            f"{status_icon.get(app.status, '⚪')} {app.status} | {reachable} | {install} | "
            f"[`{app.slug}.json`]({feed_url}) |"
        )

    totals = health_doc["totals"]
    block = "\n".join(
        [
            start,
            "",
            f"_Catalogue last changed {health_doc['generatedAt']} · {totals['apps']} apps · "
            f"{totals['reachable']}/{totals['apps']} downloads reachable._",
            "",
            *rows,
            "",
            end,
        ]
    )
    pattern = re.compile(re.escape(start) + ".*?" + re.escape(end), re.DOTALL)
    updated = pattern.sub(lambda _: block, text)
    if updated == text:
        return False
    readme.write_text(updated, encoding="utf-8")
    log.info("README catalog block refreshed")
    return True


def stage_assets(container: Container, catalog: Catalog) -> None:
    report = inspect_catalog(catalog, assets_dir=container.paths.assets)
    for issue in report.issues:
        if issue.kind in {"missing"}:
            log.error("asset: %s %s", issue.slug or issue.path, issue.detail)
        elif issue.kind in {"oversized", "screenshot", "unused", "icon"}:
            log.warning("asset: %s %s", issue.slug or issue.path, issue.detail)
    # Touch the cache directory so operators know where it will live.
    DirectoryCache(container.paths.cache)


def write_summary(health_doc: dict[str, Any], changed: list[Path], report: SyncReport) -> None:
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary:
        return
    totals = health_doc["totals"]
    lines = [
        "## OmniSource build summary",
        "",
        f"- **Apps:** {totals['apps']}",
        f"- **Downloads reachable:** {totals['reachable']}/{totals['apps']}",
        (
            f"- **Synced:** {report.apps_synced} · incremental hits: "
            f"{report.apps_incremental_hit} · failed: {report.apps_failed}"
        ),
        f"- **Version changes:** {report.apps_updated}",
        f"- **HTTP requests:** {report.api_requests}",
        f"- **Files changed:** {len(changed)}",
        "",
        "### Catalog",
        "",
        "| App | Version | Updated | Download |",
        "| --- | --- | --- | --- |",
    ]
    lines += [
        f"| {item['name']} | `{item['version']}` | {item['updatedAt']} | "
        f"{'✅' if item['downloadReachable'] else '⚠️ ' + item['detail']} |"
        for item in health_doc["apps"]
    ]
    if report.updates:
        lines += ["", "### Release report", "", "| App | From | To | Kind |", "| --- | --- | --- | --- |"]
        lines += [
            f"| {event.name} | `{event.previous_version or '—'} ` | `{event.version}` | {event.kind} |"
            for event in report.updates
        ]
    if report.errors:
        lines += ["", "### Errors", ""]
        lines += [f"- `{error}`" for error in report.errors]
    with Path(summary).open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def run(
    *,
    container: Container | None = None,
    no_sync: bool = False,
    no_health: bool = False,
    no_mirror: bool = False,
    only: set[str] | None = None,
    incremental: bool = False,
    workers: int = 8,
) -> tuple[int, SyncReport]:
    """Execute the pipeline. Returns ``(exit_code, report)``."""
    container = container or build_container()
    report = SyncReport()

    catalog = load_catalog(container)
    report.apps_total = len(catalog.apps)
    state = load_state(container)
    known = {app.slug for app in catalog.apps}
    state = {slug: value for slug, value in state.items() if slug in known}

    if not no_sync:
        with Group("Sync upstream releases"):
            state = stage_sync(container, catalog, state, only=only, incremental=incremental, report=report)

    with Group("Check download health"):
        stage_health(container, catalog, state, enabled=not no_health, workers=max(1, workers))
    write_json(container.paths.feeds / "state.json", dict(sorted(state.items())))

    with Group("Validate local assets"):
        stage_assets(container, catalog)

    with Group("Build feeds"):
        changed, health_doc = stage_build(container, catalog, state, report)

    if not no_mirror:
        with Group("Mirror feeds to repository root"):
            changed += stage_mirror(container, catalog)

    stage_readme(container, catalog, health_doc)
    report.files_changed = len(changed)
    write_summary(health_doc, changed, report)

    unreachable = health_doc["totals"]["unreachable"]
    if unreachable:
        log.warning("%d app(s) currently have an unreachable download URL", unreachable)
    log.info("Done. %d file(s) changed.", len(changed))
    return 0, report
