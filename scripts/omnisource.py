#!/usr/bin/env python3
"""OmniSource feed builder.

Single entry point for the whole distribution pipeline:

    catalog.json  ->  upstream sync  ->  link health  ->  feeds/  ->  root mirrors

Stages
------
1. ``sync``    Resolve the newest upstream GitHub releases for every catalog app.
2. ``health``  Probe every download URL concurrently and record the result.
3. ``build``   Render AltStore-compatible feeds plus ``feeds/health.json``.
4. ``mirror``  Copy generated feeds to the historical root-level paths.
5. ``readme``  Refresh the generated catalog block inside README.md.

Only the Python standard library is used, so the workflow needs no
dependency installation step.

Usage
-----
    python3 scripts/omnisource.py                 # full pipeline
    python3 scripts/omnisource.py --no-sync       # rebuild feeds from state.json
    python3 scripts/omnisource.py --no-health     # skip network link probing
    python3 scripts/omnisource.py --only ytlite   # restrict sync to one app
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import logging
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, ClassVar

REPO_ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = REPO_ROOT / "catalog.json"
STATE_PATH = REPO_ROOT / "feeds" / "state.json"
FEEDS_DIR = REPO_ROOT / "feeds"
ASSETS_DIR = REPO_ROOT / "assets"
README_PATH = REPO_ROOT / "README.md"

USER_AGENT = "OmniSource-Sync/2.0 (+https://github.com/iamsmmh/OmniSource)"
API_ROOT = "https://api.github.com"
VERSION_RE = re.compile(r"(\d+\.\d+(?:\.\d+)?)")
TAG_NUMBER_RE = re.compile(r"(\d+)\s*$")
README_MARKERS = ("<!-- omnisource:catalog:start -->", "<!-- omnisource:catalog:end -->")

# A download URL is considered reachable when the server answers with one of
# these. 206 covers ranged GET fallbacks, 3xx covers CDN redirects.
ALIVE_CODES = frozenset({200, 206, 301, 302, 303, 307, 308})
RETRYABLE_CODES = frozenset({408, 425, 429, 500, 502, 503, 504})

log = logging.getLogger("omnisource")


# ---------------------------------------------------------------------------
# GitHub Actions friendly logging
# ---------------------------------------------------------------------------
class ActionsFormatter(logging.Formatter):
    """Emit ``::warning::``/``::error::`` annotations when running on Actions."""

    PREFIX: ClassVar[dict[int, str]] = {
        logging.WARNING: "::warning::",
        logging.ERROR: "::error::",
        logging.CRITICAL: "::error::",
    }

    def __init__(self, *, annotate: bool) -> None:
        super().__init__("%(levelname)-7s %(message)s")
        self.annotate = annotate

    def format(self, record: logging.LogRecord) -> str:
        message = record.getMessage()
        if self.annotate:
            prefix = self.PREFIX.get(record.levelno, "")
            return f"{prefix}{message}" if prefix else message
        return f"{record.levelname:<7} {message}"


def configure_logging(verbose: bool) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(ActionsFormatter(annotate=bool(os.environ.get("GITHUB_ACTIONS"))))
    log.addHandler(handler)
    log.setLevel(logging.DEBUG if verbose else logging.INFO)
    log.propagate = False


class Group:
    """Collapsible log group; a no-op outside GitHub Actions."""

    def __init__(self, title: str) -> None:
        self.title = title
        self.enabled = bool(os.environ.get("GITHUB_ACTIONS"))

    def __enter__(self) -> Group:
        print(f"::group::{self.title}" if self.enabled else f"\n=== {self.title} ===", flush=True)
        return self

    def __exit__(self, *exc: object) -> None:
        if self.enabled:
            print("::endgroup::", flush=True)


class SyncError(RuntimeError):
    """Unrecoverable pipeline failure."""


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------
class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Stop at the first 3xx.

    Release hosts answer ``302`` and point at a signed CDN URL. Following that
    redirect proves nothing extra, costs an extra TLS handshake per app, and
    can start streaming a 120 MB IPA into the runner. A 3xx from the origin is
    sufficient evidence that the asset exists.
    """

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        return None


_PROBE_OPENER = urllib.request.build_opener(_NoRedirect)


def _request(
    url: str,
    *,
    headers: dict[str, str],
    method: str = "GET",
    timeout: float = 30.0,
    follow_redirects: bool = True,
):
    request = urllib.request.Request(url, headers=headers, method=method)
    opener = urllib.request.urlopen if follow_redirects else _PROBE_OPENER.open
    # Callers validate the URL scheme before reaching this point (see probe_url).
    return opener(request, timeout=timeout)


def fetch_json(url: str, *, retries: int = 3, token: str | None = None) -> Any:
    """GET a GitHub API endpoint with bounded exponential backoff.

    The repository token is attached here and *only* here. Third-party
    download URLs must never receive credentials.
    """
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": USER_AGENT,
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            with _request(url, headers=headers) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            last_error = error
            if error.code not in RETRYABLE_CODES:
                break
            # Honour secondary-rate-limit hints instead of hammering the API.
            delay = float(error.headers.get("Retry-After") or 2**attempt)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as error:
            last_error = error
            delay = float(2**attempt)
        if attempt < retries:
            log.warning("GitHub API attempt %d/%d failed (%s); retrying in %.0fs", attempt, retries, last_error, delay)
            time.sleep(delay)

    raise SyncError(f"GitHub API request failed after {retries} attempts: {url} ({last_error})")


def probe_url(url: str, *, timeout: float = 12.0, retries: int = 2) -> tuple[bool, str]:
    """Return ``(reachable, detail)`` for a download URL, without credentials.

    Uses HEAD first; falls back to a one-byte ranged GET for hosts that reject
    HEAD, so a probe never downloads a whole IPA into the runner.
    """
    if not isinstance(url, str) or not url:
        return False, "empty url"
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False, "not an http(s) url"

    headers = {"User-Agent": USER_AGENT}
    detail = "unknown"
    for attempt in range(1, retries + 1):
        for method, extra in (("HEAD", {}), ("GET", {"Range": "bytes=0-0"})):
            try:
                with _request(
                    url,
                    headers={**headers, **extra},
                    method=method,
                    timeout=timeout,
                    follow_redirects=False,
                ) as response:
                    if response.status in ALIVE_CODES:
                        return True, f"HTTP {response.status}"
                    detail = f"HTTP {response.status}"
            except urllib.error.HTTPError as error:
                detail = f"HTTP {error.code}"
                if error.code in ALIVE_CODES:
                    return True, detail
                if error.code in RETRYABLE_CODES:
                    break  # transient: retry the whole attempt
                if method == "GET":
                    return False, detail
                if error.code not in {403, 405, 501}:
                    return False, detail
            except (urllib.error.URLError, TimeoutError, OSError) as error:
                detail = str(getattr(error, "reason", error))
                break
        if attempt < retries:
            time.sleep(1.5 * attempt)
    return False, detail


# ---------------------------------------------------------------------------
# File helpers
# ---------------------------------------------------------------------------
def read_json(path: Path) -> Any | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def write_json(path: Path, data: Any) -> bool:
    """Atomically write ``data``; return True when the file actually changed."""
    payload = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") == payload:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    try:
        tmp.write_text(payload, encoding="utf-8")
        json.loads(tmp.read_text(encoding="utf-8"))  # never publish invalid JSON
        tmp.replace(path)
    finally:
        tmp.unlink(missing_ok=True)
    return True


def utc_now() -> datetime:
    return datetime.now(UTC)


def today() -> str:
    return utc_now().strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# Catalog model
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Upstream:
    repo: str
    tag_prefix: str = ""
    exclude_tag_prefixes: tuple[str, ...] = ()
    asset_suffixes: tuple[str, ...] = (".ipa",)
    max_pages: int = 3
    keep_versions: int = 1  # 0 == keep every matching release
    sort_by_tag_number: bool = False
    description_template: str = "{name} {version} | {label}"
    min_os_version: str = "16.0"
    min_os_by_tag_number: dict[str, str] = field(default_factory=dict)
    # Emit full ISO 8601 UTC release timestamps (e.g. 2026-01-03T17:51:54Z)
    # instead of date-only strings. Opt-in so existing feeds stay byte-stable.
    iso_dates: bool = False

    @classmethod
    def parse(cls, raw: dict[str, Any]) -> Upstream:
        return cls(
            repo=raw["repo"],
            tag_prefix=raw.get("tagPrefix", ""),
            exclude_tag_prefixes=tuple(raw.get("excludeTagPrefixes", ())),
            asset_suffixes=tuple(raw.get("assetSuffixes", (".ipa",))),
            max_pages=int(raw.get("maxPages", 3)),
            keep_versions=int(raw.get("keepVersions", 1)),
            sort_by_tag_number=bool(raw.get("sortByTagNumber", False)),
            description_template=raw.get("descriptionTemplate", "{name} {version} | {label}"),
            min_os_version=raw.get("minOSVersion", "16.0"),
            min_os_by_tag_number=dict(raw.get("minOSVersionByTagNumber", {})),
            iso_dates=bool(raw.get("isoDates", False)),
        )


@dataclass
class App:
    slug: str
    raw: dict[str, Any]

    @property
    def name(self) -> str:
        return str(self.raw["name"])

    @property
    def icon(self) -> str:
        return str(self.raw.get("icon", "OmniSource.png"))

    @property
    def status(self) -> str:
        return str(self.raw.get("status", "stable"))

    @property
    def featured(self) -> bool:
        return bool(self.raw.get("featured", False))

    @property
    def upstream(self) -> Upstream | None:
        raw = self.raw.get("upstream")
        return Upstream.parse(raw) if isinstance(raw, dict) else None

    @property
    def manual_release(self) -> dict[str, Any] | None:
        raw = self.raw.get("manualRelease")
        return dict(raw) if isinstance(raw, dict) else None


@dataclass
class Catalog:
    source: dict[str, Any]
    clients: list[dict[str, Any]]
    apps: list[App]

    @classmethod
    def load(cls, path: Path = CATALOG_PATH) -> Catalog:
        raw = read_json(path)
        if not isinstance(raw, dict):
            raise SyncError(f"{path.name} is missing or not a JSON object")
        apps = [App(slug=entry["slug"], raw=entry) for entry in raw.get("apps", [])]
        if not apps:
            raise SyncError(f"{path.name} declares no apps")
        return cls(source=raw.get("source", {}), clients=raw.get("clients", []), apps=apps)

    @property
    def base_url(self) -> str:
        return str(self.source.get("baseURL", "")).rstrip("/")


# ---------------------------------------------------------------------------
# Stage 1 - upstream sync
# ---------------------------------------------------------------------------
def tag_number(tag: str) -> int:
    match = TAG_NUMBER_RE.search(tag)
    return int(match.group(1)) if match else -1


def pick_asset(release: dict[str, Any], suffixes: tuple[str, ...]) -> dict[str, Any] | None:
    assets = [a for a in release.get("assets", []) if isinstance(a, dict)]
    for suffix in suffixes:
        for asset in assets:
            if str(asset.get("name", "")).lower().endswith(suffix.lower()):
                return asset
    return None


class ReleaseFetcher:
    """Paginated release fetcher with a per-run, per-repo cache.

    Five catalog apps share ``mrdrvt99/YouProEXTRA``; without the cache the old
    pipeline paid for that repository's release history once per app.
    """

    def __init__(self, token: str | None) -> None:
        self.token = token
        self._cache: dict[tuple[str, int], list[dict[str, Any]]] = {}
        self.requests = 0

    def releases(self, repo: str, max_pages: int) -> list[dict[str, Any]]:
        cached = next((v for (r, p), v in self._cache.items() if r == repo and p >= max_pages), None)
        if cached is not None:
            return cached

        collected: list[dict[str, Any]] = []
        for page in range(1, max_pages + 1):
            url = f"{API_ROOT}/repos/{repo}/releases?per_page=100&page={page}"
            batch = fetch_json(url, token=self.token)
            self.requests += 1
            if not isinstance(batch, list):
                raise SyncError(f"Unexpected releases payload for {repo}")
            collected.extend(batch)
            if len(batch) < 100:
                break
        published = [r for r in collected if isinstance(r, dict) and not r.get("draft") and not r.get("prerelease")]
        self._cache[(repo, max_pages)] = published
        log.debug("%s: %d published releases (%d API call(s))", repo, len(published), self.requests)
        return published


def build_version_entry(app: App, up: Upstream, release: dict[str, Any], asset: dict[str, Any]) -> dict[str, Any]:
    asset_name = str(asset.get("name", "build.ipa"))
    tag = str(release.get("tag_name", ""))
    # GitHub publishes RFC 3339 timestamps (2026-01-03T17:51:54Z). Date-only is
    # the default so historical entries stay byte-stable across rebuilds; apps
    # may opt into full precision with upstream.isoDates.
    published = str(release.get("published_at") or "")
    if not published:
        date = utc_now().strftime("%Y-%m-%d")
    elif up.iso_dates:
        date = published
    else:
        date = published[:10]

    numbers = VERSION_RE.findall(asset_name)
    if not numbers:
        numbers = VERSION_RE.findall(tag) or VERSION_RE.findall(str(release.get("name") or ""))
    # Upstream IPA names put the host-app version first, the tweak version last.
    version = numbers[0] if numbers else date
    secondary = numbers[-1] if numbers else version

    label = asset_name.removesuffix(".ipa")
    description = up.description_template.format(
        name=app.name, version=version, secondary=secondary, label=label, tag=tag, date=date
    )
    body = (release.get("body") or "").strip()
    if body:
        description = f"{description}\n\n{body}"

    min_os = up.min_os_by_tag_number.get(str(tag_number(tag)), up.min_os_version)
    return {
        "version": version,
        "date": date,
        "localizedDescription": description,
        "downloadURL": asset.get("browser_download_url", ""),
        "size": int(asset.get("size", 0) or 0),
        "minOSVersion": min_os,
    }


def sync_app(app: App, fetcher: ReleaseFetcher) -> list[dict[str, Any]] | None:
    """Return the version list for ``app`` or ``None`` when nothing changed upstream."""
    up = app.upstream
    manual = app.manual_release

    def fallback(reason: str) -> list[dict[str, Any]] | None:
        if manual:
            log.info("%-14s %s - using manualRelease v%s from catalog.json", app.slug, reason, manual.get("version"))
            return [manual]
        log.warning("%-14s %s and no manualRelease fallback exists", app.slug, reason)
        return None

    if up is None:
        return fallback("no upstream configured")

    matches: list[dict[str, Any]] = []
    for release in fetcher.releases(up.repo, up.max_pages):
        tag = str(release.get("tag_name", ""))
        if up.tag_prefix and not tag.startswith(up.tag_prefix):
            continue
        if any(tag.startswith(p) for p in up.exclude_tag_prefixes):
            continue
        asset = pick_asset(release, up.asset_suffixes)
        if asset is None:
            log.debug("%s: %s has no matching asset", app.slug, tag or "<untagged>")
            continue
        matches.append({"release": release, "asset": asset, "tag": tag})

    if not matches:
        return fallback(f"no published release with a matching asset in {up.repo}")

    if up.sort_by_tag_number:
        matches.sort(key=lambda m: (tag_number(m["tag"]), m["release"].get("published_at") or ""), reverse=True)

    versions: list[dict[str, Any]] = []
    seen: set[str] = set()
    for match in matches:
        entry = build_version_entry(app, up, match["release"], match["asset"])
        if not entry["downloadURL"] or entry["downloadURL"] in seen:
            continue
        seen.add(entry["downloadURL"])
        versions.append(entry)
        if up.keep_versions and len(versions) >= up.keep_versions:
            break

    if not versions:
        return fallback("upstream produced no usable version entries")

    log.info("%-14s %-28s -> v%s (%d version(s))", app.slug, up.repo, versions[0]["version"], len(versions))
    return versions


def stage_sync(catalog: Catalog, state: dict[str, Any], only: set[str] | None) -> dict[str, Any]:
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or None
    if not token:
        log.warning("No GH_TOKEN/GITHUB_TOKEN set - using unauthenticated API limits (60 req/h)")
    fetcher = ReleaseFetcher(token)

    for app in catalog.apps:
        if only and app.slug not in only:
            continue
        try:
            versions = sync_app(app, fetcher)
        except SyncError as error:
            # One bad upstream must not sink the whole run; the previous state
            # for this app is kept and the feed still rebuilds.
            log.error("%s: upstream sync failed (%s) - keeping last known state", app.slug, error)
            continue
        if not versions:
            continue
        entry = state.setdefault(app.slug, {})
        # Timestamps only move when content moves. Otherwise every scheduled run
        # would produce a no-op commit and the rebuild would not be idempotent.
        if entry.get("versions") != versions:
            entry["versions"] = versions
            entry["syncedAt"] = today()

    log.info("Sync complete using %d GitHub API request(s)", fetcher.requests)
    return state


# ---------------------------------------------------------------------------
# Stage 2 - link health
# ---------------------------------------------------------------------------
def stage_health(catalog: Catalog, state: dict[str, Any], *, enabled: bool, workers: int) -> None:
    """Probe the newest download URL of every app concurrently.

    Results are stored back into ``state`` so a rebuild without ``--no-health``
    reproduces byte-identical feeds. ``since`` records when the current status
    was first observed, which keeps the output stable across no-change runs.
    """
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
        futures = {pool.submit(probe_url, url): slug for slug, url in targets.items()}
        for future in concurrent.futures.as_completed(futures):
            slug = futures[future]
            reachable, detail = future.result()
            previous = state[slug].get("health", {})
            state[slug]["health"] = {
                "reachable": reachable,
                "detail": detail,
                "since": previous.get("since", today()) if previous.get("reachable") is reachable else today(),
            }
            (log.info if reachable else log.warning)(
                "%-14s %s (%s)", slug, "reachable" if reachable else "UNREACHABLE", detail
            )
    log.info("Probed %d download URL(s) in %.1fs", len(targets), time.monotonic() - started)


# ---------------------------------------------------------------------------
# Stage 3 - feed rendering
# ---------------------------------------------------------------------------
def render_app(catalog: Catalog, app: App, versions: list[dict[str, Any]], health: dict[str, Any]) -> dict[str, Any]:
    base = catalog.base_url
    # Shallow-copy so fallback injection below never mutates the shared
    # pipeline state that stage_health already persisted.
    versions = [dict(version) for version in versions]
    newest = versions[0]
    raw = app.raw

    # fallbackDownloadURLs mirror the latest build. A manualRelease may declare
    # build-specific mirrors that override the app-level ones.
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
        # AltStore reads versions[0]; the flat mirrors below exist for older
        # clients and must never drift away from it.
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

    # OmniSource extensions. Unknown keys are ignored by AltStore-family
    # clients, and power the website, README and health dashboard.
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


def feed_envelope(catalog: Catalog, *, name: str, identifier: str, subtitle: str, description: str) -> dict[str, Any]:
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


def stage_build(catalog: Catalog, state: dict[str, Any]) -> tuple[list[Path], dict[str, Any]]:
    written: list[Path] = []
    rendered: list[tuple[App, dict[str, Any]]] = []

    for app in catalog.apps:
        versions = state.get(app.slug, {}).get("versions")
        if not versions:
            log.error("%s has no known versions - excluded from this build", app.slug)
            continue
        rendered.append((app, render_app(catalog, app, versions, state[app.slug].get("health", {}))))

    if not rendered:
        raise SyncError("No app produced a valid feed entry")

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
        if write_json(FEEDS_DIR / f"{app.slug}.json", feed):
            written.append(FEEDS_DIR / f"{app.slug}.json")

    master = feed_envelope(
        catalog,
        name=str(catalog.source.get("name", "OmniSource")),
        identifier=str(catalog.source.get("identifier", "com.omnisource")),
        subtitle=str(catalog.source.get("subtitle", "")),
        description=str(catalog.source.get("description", "")),
    )
    master["apps"] = [entry for _, entry in sorted(rendered, key=lambda item: item[0].name.lower())]
    master["news"] = []
    if write_json(FEEDS_DIR / "apps.json", master):
        written.append(FEEDS_DIR / "apps.json")

    reachable = sum(1 for _, e in rendered if e["omnisource"]["health"]["downloadReachable"])
    health_doc = {
        # Derived from content, never from wall-clock time, so an unchanged
        # catalogue produces an unchanged file (and therefore no commit).
        "generatedAt": max(
            [entry["omnisource"]["health"]["statusSince"] for _, entry in rendered]
            + [entry["versionDate"] for _, entry in rendered]
        ),
        "totals": {
            "apps": len(rendered),
            "reachable": reachable,
            "unreachable": len(rendered) - reachable,
            "featured": sum(1 for _, e in rendered if e["omnisource"]["featured"]),
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
    if write_json(FEEDS_DIR / "health.json", health_doc):
        written.append(FEEDS_DIR / "health.json")

    log.info("Built %d app feed(s) + master feed (%d file(s) changed)", len(rendered), len(written))
    return written, health_doc


# ---------------------------------------------------------------------------
# Stage 4 - root mirrors (backwards compatibility)
# ---------------------------------------------------------------------------
def stage_mirror(catalog: Catalog) -> list[Path]:
    """Copy generated feeds to their historical root paths.

    Existing AltStore installs point at ``/OmniSource/<slug>.json``. Those URLs
    must keep resolving, so ``feeds/`` is the source of truth and the root files
    are byte-identical generated copies.
    """
    mirrored: list[Path] = []
    for name in ["apps.json", *(f"{app.slug}.json" for app in catalog.apps)]:
        source = FEEDS_DIR / name
        target = REPO_ROOT / name
        if not source.exists():
            continue
        payload = source.read_text(encoding="utf-8")
        if not target.exists() or target.read_text(encoding="utf-8") != payload:
            target.write_text(payload, encoding="utf-8")
            mirrored.append(target)
    if mirrored:
        log.info("Refreshed %d root mirror(s)", len(mirrored))
    return mirrored


# ---------------------------------------------------------------------------
# Stage 5 - README catalog block
# ---------------------------------------------------------------------------
def stage_readme(catalog: Catalog, health_doc: dict[str, Any]) -> bool:
    if not README_PATH.exists():
        return False
    start, end = README_MARKERS
    text = README_PATH.read_text(encoding="utf-8")
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
    README_PATH.write_text(updated, encoding="utf-8")
    log.info("README catalog block refreshed")
    return True


# ---------------------------------------------------------------------------
# Job summary
# ---------------------------------------------------------------------------
def write_summary(health_doc: dict[str, Any], changed: list[Path]) -> None:
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary:
        return
    totals = health_doc["totals"]
    lines = [
        "## OmniSource build summary",
        "",
        f"- **Apps:** {totals['apps']}",
        f"- **Downloads reachable:** {totals['reachable']}/{totals['apps']}",
        f"- **Files changed:** {len(changed)}",
        "",
        "| App | Version | Updated | Download |",
        "| --- | --- | --- | --- |",
    ]
    lines += [
        f"| {item['name']} | `{item['version']}` | {item['updatedAt']} | "
        f"{'✅' if item['downloadReachable'] else '⚠️ ' + item['detail']} |"
        for item in health_doc["apps"]
    ]
    with Path(summary).open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--no-sync", action="store_true", help="rebuild from feeds/state.json without hitting GitHub")
    parser.add_argument("--no-health", action="store_true", help="skip download link probing")
    parser.add_argument("--no-mirror", action="store_true", help="do not refresh the root-level compatibility copies")
    parser.add_argument("--only", metavar="SLUG", action="append", help="restrict the sync stage to these app slugs")
    parser.add_argument("--workers", type=int, default=8, help="concurrent link probes (default: 8)")
    parser.add_argument("-v", "--verbose", action="store_true", help="debug logging")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    configure_logging(args.verbose)

    try:
        catalog = Catalog.load()
        state = read_json(STATE_PATH) or {}
        known = {app.slug for app in catalog.apps}
        state = {slug: value for slug, value in state.items() if slug in known}

        if not args.no_sync:
            with Group("Sync upstream releases"):
                state = stage_sync(catalog, state, set(args.only) if args.only else None)

        with Group("Check download health"):
            stage_health(catalog, state, enabled=not args.no_health, workers=max(1, args.workers))
        write_json(STATE_PATH, dict(sorted(state.items())))

        with Group("Build feeds"):
            changed, health_doc = stage_build(catalog, state)

        if not args.no_mirror:
            with Group("Mirror feeds to repository root"):
                changed += stage_mirror(catalog)

        stage_readme(catalog, health_doc)
        write_summary(health_doc, changed)

        unreachable = health_doc["totals"]["unreachable"]
        if unreachable:
            log.warning("%d app(s) currently have an unreachable download URL", unreachable)
        log.info("Done. %d file(s) changed.", len(changed))
        return 0
    except SyncError as error:
        log.error("%s", error)
        return 1
    except KeyboardInterrupt:  # pragma: no cover
        return 130


if __name__ == "__main__":
    sys.exit(main())
