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
from omnisource.io import atomic_write_many, atomic_write_text, read_json, write_json
from omnisource.logutil import Group, log
from omnisource.repository_registry import build_repository_registry, record_repository_result, repository_key
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


def _sync_result(
    container: Container,
    app: App,
    *,
    incremental: bool,
    previous: dict[str, Any] | None,
) -> tuple[str, list[dict[str, Any]] | None, str | None]:
    """Worker boundary: one provider failure becomes one isolated result."""
    try:
        return app.slug, sync_app(container, app, incremental=incremental, previous=previous), None
    except Exception as error:  # provider failures must not stop sibling apps
        return app.slug, None, str(error)


def _history_events(state: dict[str, Any]) -> list[UpdateEvent]:
    raw = state.get("updateHistory", [])
    if not isinstance(raw, list):
        return []
    events: list[UpdateEvent] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        try:
            events.append(
                UpdateEvent(
                    app_id=str(item.get("appId") or ""),
                    name=str(item.get("name") or ""),
                    version=str(item.get("version") or ""),
                    previous_version=(str(item["previousVersion"]) if item.get("previousVersion") else None),
                    release_date=str(item.get("releaseDate") or ""),
                    download_url=str(item.get("downloadUrl") or ""),
                    changelog=str(item.get("changelog") or ""),
                    kind=str(item.get("kind") or "updated"),
                )
            )
        except (TypeError, ValueError):
            continue
    return events


def _remember_update(state: dict[str, Any], event: UpdateEvent, *, limit: int) -> None:
    history = state.setdefault("updateHistory", [])
    if not isinstance(history, list):
        history = []
        state["updateHistory"] = history
    key = (event.app_id, event.version, event.kind)
    material = [
        item
        for item in history
        if isinstance(item, dict) and (item.get("appId"), item.get("version"), item.get("kind")) != key
    ]
    material.append(event.to_json())
    material.sort(key=lambda item: (str(item.get("releaseDate") or ""), str(item.get("appId") or "")), reverse=True)
    state["updateHistory"] = material[: max(1, limit)]


def stage_sync(
    container: Container,
    catalog: Catalog,
    state: dict[str, Any],
    *,
    only: set[str] | None,
    incremental: bool,
    report: SyncReport,
    workers: int | None = None,
) -> dict[str, Any]:
    """Synchronize apps independently and apply results in catalog order."""
    if not (os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")):
        log.warning("No GH_TOKEN/GITHUB_TOKEN set - using unauthenticated API limits (60 req/h)")

    selected = [app for app in catalog.apps if not only or app.slug in only]
    report.repositories_checked = len({repository_key(app) for app in selected})
    max_workers = max(1, workers or container.settings.sync_workers)
    previous_by_slug = {app.slug: state.get(app.slug) for app in selected}
    results: dict[str, tuple[list[dict[str, Any]] | None, str | None]] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(max_workers, max(1, len(selected)))) as pool:
        futures = {
            pool.submit(
                _sync_result,
                container,
                app,
                incremental=incremental,
                previous=previous_by_slug[app.slug],
            ): app
            for app in selected
        }
        for future in concurrent.futures.as_completed(futures):
            app = futures[future]
            try:
                slug, versions, error = future.result()
            except Exception as error:  # executor boundary; preserve all known state
                slug, versions, error = app.slug, None, str(error)
            results[slug] = (versions, error)

    successful_repositories: set[str] = set()
    failed_repositories: set[str] = set()
    for app in selected:
        previous = previous_by_slug[app.slug]
        versions, error = results.get(app.slug, (None, "worker returned no result"))
        if error is not None:
            log.error("%s: upstream sync failed (%s) - keeping last known state", app.slug, error)
            report.apps_failed += 1
            report.errors.append(f"{app.slug}: {error}")
            failed_repositories.add(repository_key(app))
            entry = state.setdefault(app.slug, {})
            entry["lastError"] = error
            entry["retryCount"] = int(entry.get("retryCount") or 0) + 1
            record_repository_result(state, app, success=False, error=error, retry_count=entry["retryCount"])
            continue

        report.apps_synced += 1
        successful_repositories.add(repository_key(app))
        record_repository_result(state, app, success=True)
        entry = state.setdefault(app.slug, {})
        entry.pop("lastError", None)
        entry["retryCount"] = 0
        previous_versions = (previous or {}).get("versions") if isinstance(previous, dict) else None
        if versions is None:
            report.apps_incremental_hit += 1
            continue

        kind = detect_update(previous_versions if isinstance(previous_versions, list) else None, versions)
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
                _remember_update(state, event, limit=container.settings.max_update_history)
                if previous_version:
                    container.analytics.record_update(app.slug, previous_version, event.version)
        elif incremental:
            report.apps_incremental_hit += 1

    report.repositories_succeeded = len(successful_repositories - failed_repositories)
    report.repositories_failed = len(failed_repositories)
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

    def probe(url: str):
        return container.http.probe(url, timeout=container.settings.health_timeout)

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(probe, url): slug for slug, url in targets.items()}
        for future in concurrent.futures.as_completed(futures):
            slug = futures[future]
            try:
                result = future.result()
            except Exception as error:  # a probe must not cancel the other apps
                from omnisource.http import ProbeResult

                result = ProbeResult(False, f"probe failed: {error}", targets[slug])
            previous = state[slug].get("health", {})
            state[slug]["health"] = {
                "reachable": result.reachable,
                "detail": result.detail,
                "since": previous.get("since", today()) if previous.get("reachable") == result.reachable else today(),
            }
            container.analytics.record_health(slug, result.reachable)
            (log.info if result.reachable else log.warning)(
                "%-14s %s (%s)", slug, "reachable" if result.reachable else "UNREACHABLE", result.detail
            )
    log.info("Probed %d download URL(s) in %.1fs", len(targets), time.monotonic() - started)


def _validate_generated_document(path: Path, document: Any, *, root: Path) -> None:
    """Run schema validation before a generated document can be published."""
    from omnisource.schema import validate_file

    relative = path.relative_to(root).as_posix()
    schema_path: Path | None = None
    if relative.endswith("/apps.json") and ("omnistore" in relative or relative.startswith("feeds/api/")):
        schema_path = root / "schemas" / "omnistore.schema.json"
    elif "/apps/" in relative and relative.endswith(".json") and "/releases" not in relative:
        schema_path = root / "schemas" / "app.schema.json"
    elif relative.endswith("/releases.json"):
        # Validate the release list and each release with the release schema.
        schema_path = root / "schemas" / "release.schema.json"
        if not schema_path.exists():
            return
        releases = document.get("releases", []) if isinstance(document, dict) else []
        for index, release in enumerate(releases):
            if isinstance(release, dict):
                problems = validate_file(release, schema_path)
                if problems:
                    raise SyncError(f"{relative}.releases[{index}]: {'; '.join(problems)}")
        return
    elif relative in {
        "feeds/updates.json",
        "feeds/categories.json",
        "feeds/repositories.json",
        "feeds/featured.json",
        "feeds/trending.json",
        "feeds/recent.json",
    }:
        schema_path = root / "schemas" / "canonical-feed.schema.json"
    if schema_path is None or not schema_path.exists():
        return
    problems = validate_file(document, schema_path)
    if problems:
        raise SyncError(f"{relative}: {'; '.join(problems[:8])}")


def stage_build(
    container: Container,
    catalog: Catalog,
    state: dict[str, Any],
    report: SyncReport,
) -> tuple[list[Path], dict[str, Any]]:
    rendered: list[tuple[App, dict[str, Any]]] = []
    versions_by_slug: dict[str, list[dict[str, Any]]] = {}

    for app in catalog.apps:
        versions = state.get(app.slug, {}).get("versions")
        if not isinstance(versions, list) or not versions:
            log.error("%s has no known versions - excluded from this build", app.slug)
            continue
        versions_by_slug[app.slug] = versions
        rendered.append((app, render_altstore_app(catalog, app, versions, state[app.slug].get("health", {}))))

    if not rendered:
        raise SyncError("No app produced a valid feed entry")

    feeds_dir = container.paths.feeds
    base = catalog.base_url
    documents: dict[Path, Any] = {}
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
        documents[feeds_dir / f"{app.slug}.json"] = feed

    master = feed_envelope(
        catalog,
        name=str(catalog.source.get("name", "OmniSource")),
        identifier=str(catalog.source.get("identifier", "com.omnisource")),
        subtitle=str(catalog.source.get("subtitle", "")),
        description=str(catalog.source.get("description", "")),
    )
    master["apps"] = [entry for _, entry in sorted(rendered, key=lambda item: item[0].name.casefold())]
    master["news"] = []
    documents[feeds_dir / "apps.json"] = master

    health_doc = render_health_doc(rendered)
    documents[feeds_dir / "health.json"] = health_doc

    repository_registry = build_repository_registry(catalog, state=state)
    history = _history_events(state)
    omnistore = render_omnistore_bundle(
        catalog,
        versions_by_slug=versions_by_slug,
        updates=report.updates,
        state_by_slug=state,
        repository_registry=repository_registry,
        curation=container.curation,
        categories=container.categories,
        update_history=history,
    )
    # Keep the required short feed URLs in addition to the namespaced feeds.
    for name, document in omnistore.items():
        documents[container.paths.omnistore / name] = document
    for name in (
        "updates.json",
        "categories.json",
        "repositories.json",
        "featured.json",
        "trending.json",
        "recent.json",
    ):
        documents[feeds_dir / name] = omnistore[name]

    api_bundle = render_api_bundle(
        catalog,
        versions_by_slug=versions_by_slug,
        updates=report.updates,
        state_by_slug=state,
        repository_registry=repository_registry,
        curation=container.curation,
        categories=container.categories,
        update_history=history,
    )
    for name, document in api_bundle.items():
        documents[container.paths.api / name] = document

    # Validation happens against the complete temporary document set before
    # any production path is touched. A provider error therefore cannot leave
    # half a catalog behind.
    for path, document in documents.items():
        _validate_generated_document(path, document, root=container.paths.root)
    changed = atomic_write_many(documents)

    for url, count in _repository_counts(catalog).items():
        container.analytics.record_repository_seen(url, count)

    log.info(
        "Built %d app feed(s) + canonical feeds + API snapshots (%d file(s) changed)",
        len(rendered),
        len(changed),
    )
    return changed, health_doc


def _repository_counts(catalog: Catalog) -> dict[str, int]:
    counts: dict[str, int] = {}
    for app in catalog.apps:
        url = app.repository_url
        if url:
            counts[url] = counts.get(url, 0) + 1
    return counts


def stage_mirror(container: Container, catalog: Catalog) -> list[Path]:
    """Publish historical root mirrors only after the feed set is valid."""
    documents: dict[Path, Any] = {}
    for name in ["apps.json", *(f"{app.slug}.json" for app in catalog.apps)]:
        source = container.paths.feeds / name
        if source.exists():
            document = read_json(source)
            if isinstance(document, dict):
                documents[container.paths.root / name] = document
            else:
                log.warning("Skipping invalid mirror source %s", source)
    mirrored = atomic_write_many(documents)
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
    changed = atomic_write_text(readme, updated)
    if changed:
        log.info("README catalog block refreshed")
    return changed


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
    report = SyncReport(started_at=today())

    catalog = load_catalog(container)
    report.apps_total = len(catalog.apps)
    loaded_state = load_state(container)
    known = {app.slug for app in catalog.apps}
    state = {slug: value for slug, value in loaded_state.items() if slug in known and isinstance(value, dict)}
    # State metadata is deliberately kept outside the app slug namespace.
    for key in ("repositories", "updateHistory", "schemaVersion"):
        if key in loaded_state:
            state[key] = loaded_state[key]

    if not no_sync:
        with Group("Sync upstream releases"):
            state = stage_sync(
                container,
                catalog,
                state,
                only=only,
                incremental=incremental,
                report=report,
                workers=workers,
            )

    with Group("Check download health"):
        stage_health(container, catalog, state, enabled=not no_health, workers=max(1, workers))

    with Group("Validate local assets"):
        stage_assets(container, catalog)

    with Group("Build feeds"):
        changed, health_doc = stage_build(container, catalog, state, report)

    # Persist state only after the complete generated dataset passed validation;
    # a failed build therefore leaves both data and memory at last-known-good.
    if write_json(container.paths.feeds / "state.json", dict(sorted(state.items()))):
        changed.append(container.paths.feeds / "state.json")

    if not no_mirror:
        with Group("Mirror feeds to repository root"):
            changed += stage_mirror(container, catalog)

    if stage_readme(container, catalog, health_doc):
        changed.append(container.paths.readme)
    report.finished_at = today()
    report.files_changed = len(changed)
    write_summary(health_doc, changed, report)

    unreachable = health_doc["totals"]["unreachable"]
    if unreachable:
        log.warning("%d app(s) currently have an unreachable download URL", unreachable)
    log.info("Done. %d file(s) changed.", len(changed))
    return 0, report
