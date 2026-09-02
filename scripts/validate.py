#!/usr/bin/env python3
"""Offline validator for the OmniSource catalog and generated feeds.

Runs with zero network access so it is safe on pull requests from forks:

* ``catalog.json``  - structure, required fields, unique slugs/bundle IDs,
  known icons, well-formed upstream + compatibility + verification blocks.
* ``feeds/*.json``  - AltStore feed shape, version arrays, flat-field mirrors
  matching ``versions[0]``, HTTP(S) URLs, non-negative sizes.
* root mirrors      - byte-identical to their ``feeds/`` source of truth.
* ``assets/``       - every referenced icon exists on disk.

Exit code 0 = clean, 1 = at least one error. Warnings never fail the run
unless ``--strict`` is given.

Usage
-----
    python3 scripts/validate.py
    python3 scripts/validate.py --strict
    python3 scripts/validate.py feeds/ytlite.json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = REPO_ROOT / "catalog.json"
FEEDS_DIR = REPO_ROOT / "feeds"
ASSETS_DIR = REPO_ROOT / "assets"

REQUIRED_APP_FIELDS = ("name", "bundleIdentifier", "developerName", "version", "versionDate", "downloadURL")
REQUIRED_VERSION_FIELDS = ("version", "date", "downloadURL", "size", "localizedDescription")
REQUIRED_CATALOG_FIELDS = ("slug", "name", "bundleIdentifier", "developerName", "icon", "status", "compatibility")
VALID_STATUSES = {"stable", "beta", "manual", "unmaintained", "deprecated"}
VALID_VERIFICATION_METHODS = {"github-release", "manual-mirror", "self-built"}
KNOWN_CLIENTS = {"altstore", "sidestore", "feather", "esign", "livecontainer"}
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,31}$")
BUNDLE_RE = re.compile(r"^[A-Za-z0-9.-]+$")
# ISO-8601: YYYY-MM-DD, optionally followed by a time and/or UTC offset.
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}(?:[Tt ]\d{2}:\d{2}(?::\d{2})?(?:\.\d+)?(?:[Zz]|[+-]\d{2}:?\d{2})?)?$")
TINT_RE = re.compile(r"^[0-9A-Fa-f]{6}$")
# feeds/state.json is pipeline state, not a distributable feed.
NON_FEED_FILES = {"state.json", "health.json"}


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def extend(self, other: Report) -> None:
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)


def is_http_url(value: object) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        parsed = urlparse(value)
    except ValueError:
        return False
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def load_json(path: Path, report: Report) -> Any | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        report.error(f"{path.relative_to(REPO_ROOT)}: file not found")
    except (OSError, json.JSONDecodeError) as error:
        report.error(f"{path.relative_to(REPO_ROOT)}: invalid JSON ({error})")
    return None


# ---------------------------------------------------------------------------
# catalog.json
# ---------------------------------------------------------------------------
def validate_catalog(catalog: Any) -> Report:
    report = Report()
    if not isinstance(catalog, dict):
        report.error("catalog.json: root must be a JSON object")
        return report

    source = catalog.get("source")
    if not isinstance(source, dict):
        report.error("catalog.json: 'source' must be an object")
    else:
        for key in ("name", "identifier", "baseURL", "icon"):
            if not source.get(key):
                report.error(f"catalog.json: source.{key} is required")
        if source.get("baseURL") and not is_http_url(source["baseURL"]):
            report.error("catalog.json: source.baseURL must be an HTTP(S) URL")

    apps = catalog.get("apps")
    if not isinstance(apps, list) or not apps:
        report.error("catalog.json: 'apps' must be a non-empty array")
        return report

    seen_slugs: set[str] = set()
    seen_names: set[str] = set()
    for index, app in enumerate(apps):
        prefix = f"catalog.json: apps[{index}]"
        if not isinstance(app, dict):
            report.error(f"{prefix} must be an object")
            continue
        prefix = f"catalog.json: {app.get('slug', index)}"

        for key in REQUIRED_CATALOG_FIELDS:
            if not app.get(key):
                report.error(f"{prefix} is missing '{key}'")

        slug = app.get("slug", "")
        if slug and not SLUG_RE.match(slug):
            report.error(f"{prefix}: slug must be lowercase kebab-case (2-32 chars)")
        if slug in seen_slugs:
            report.error(f"{prefix}: duplicate slug")
        seen_slugs.add(slug)

        name = app.get("name", "")
        if name in seen_names:
            report.warn(f"{prefix}: duplicate app name '{name}' - clients may show them as one app")
        seen_names.add(name)

        if app.get("bundleIdentifier") and not BUNDLE_RE.match(app["bundleIdentifier"]):
            report.error(f"{prefix}: bundleIdentifier contains invalid characters")

        status = app.get("status")
        if status and status not in VALID_STATUSES:
            report.error(f"{prefix}: unknown status '{status}' (expected one of {sorted(VALID_STATUSES)})")

        icon = app.get("icon")
        if icon and not (ASSETS_DIR / icon).is_file():
            report.error(f"{prefix}: icon 'assets/{icon}' does not exist")

        tint = app.get("tintColor")
        if tint and not TINT_RE.match(str(tint).lstrip("#")):
            report.error(f"{prefix}: tintColor must be a 6-digit hex string")

        if not app.get("localizedDescription"):
            report.warn(f"{prefix}: no localizedDescription - clients will show an empty app page")

        report.extend(_validate_verification(prefix, app.get("verification")))
        report.extend(_validate_compatibility(prefix, app.get("compatibility")))
        report.extend(_validate_upstream(prefix, app))
        report.extend(_validate_fallback_urls(prefix, app.get("fallbackDownloadURLs")))
        manual = app.get("manualRelease")
        if isinstance(manual, dict):
            report.extend(
                _validate_fallback_urls(
                    f"{prefix}.manualRelease", manual.get("fallbackDownloadURLs"), manual.get("downloadURL")
                )
            )
        report.extend(_validate_permissions(prefix, app.get("appPermissions"), app.get("permissions")))

    return report


def _validate_verification(prefix: str, verification: Any) -> Report:
    report = Report()
    if verification is None:
        report.warn(f"{prefix}: no verification block - the app shows as unverified")
        return report
    if not isinstance(verification, dict):
        report.error(f"{prefix}: verification must be an object")
        return report
    method = verification.get("method")
    if method not in VALID_VERIFICATION_METHODS:
        report.error(f"{prefix}: verification.method must be one of {sorted(VALID_VERIFICATION_METHODS)}")
    if not verification.get("publisher"):
        report.error(f"{prefix}: verification.publisher is required")
    return report


def _validate_compatibility(prefix: str, compatibility: Any) -> Report:
    report = Report()
    if not isinstance(compatibility, dict):
        report.error(f"{prefix}: compatibility must be an object")
        return report
    min_os = compatibility.get("minOSVersion")
    if not isinstance(min_os, str) or not re.match(r"^\d+(\.\d+)*$", min_os):
        report.error(f"{prefix}: compatibility.minOSVersion must look like '16.0'")
    max_os = compatibility.get("maxOSVersion")
    if max_os is not None and not re.match(r"^\d+(\.\d+)*$", str(max_os)):
        report.error(f"{prefix}: compatibility.maxOSVersion must be null or look like '18.0'")
    clients = compatibility.get("clients")
    if not isinstance(clients, list) or not clients:
        report.error(f"{prefix}: compatibility.clients must be a non-empty array")
    else:
        unknown = sorted(set(clients) - KNOWN_CLIENTS)
        if unknown:
            report.error(f"{prefix}: unknown client id(s) {unknown}")
    return report


def _validate_upstream(prefix: str, app: dict[str, Any]) -> Report:
    report = Report()
    upstream = app.get("upstream")
    if upstream is None:
        if not isinstance(app.get("manualRelease"), dict):
            report.error(f"{prefix}: apps without an 'upstream' block need a 'manualRelease' block")
        else:
            manual = app["manualRelease"]
            for key in REQUIRED_VERSION_FIELDS:
                if key not in manual:
                    report.error(f"{prefix}: manualRelease is missing '{key}'")
            if not is_http_url(manual.get("downloadURL")):
                report.error(f"{prefix}: manualRelease.downloadURL must be an HTTP(S) URL")
        return report

    if not isinstance(upstream, dict):
        report.error(f"{prefix}: upstream must be an object or null")
        return report
    repo = upstream.get("repo", "")
    if not re.match(r"^[\w.-]+/[\w.-]+$", str(repo)):
        report.error(f"{prefix}: upstream.repo must be 'owner/name'")
    if int(upstream.get("keepVersions", 1) or 0) < 0:
        report.error(f"{prefix}: upstream.keepVersions must be >= 0 (0 means keep all)")
    if "{version}" not in str(upstream.get("descriptionTemplate", "{version}")):
        report.warn(f"{prefix}: upstream.descriptionTemplate has no {{version}} placeholder")
    pattern = upstream.get("assetNamePattern")
    if pattern is not None:
        if not isinstance(pattern, str) or not pattern:
            report.error(f"{prefix}: upstream.assetNamePattern must be a non-empty string")
        else:
            try:
                re.compile(pattern)
            except re.error as error:
                report.error(f"{prefix}: upstream.assetNamePattern is not a valid regex ({error})")
    if upstream.get("versionFromTag") is not None and not isinstance(upstream.get("versionFromTag"), bool):
        report.error(f"{prefix}: upstream.versionFromTag must be a boolean")
    return report


def _validate_fallback_urls(prefix: str, value: Any, primary: str | None = None) -> Report:
    """``fallbackDownloadURLs`` must be a de-duplicated list of HTTPS mirrors."""
    report = Report()
    if value is None:
        return report
    if not isinstance(value, list):
        report.error(f"{prefix}: fallbackDownloadURLs must be an array of URLs")
        return report
    seen: set[str] = set()
    for index, url in enumerate(value):
        label = f"{prefix}.fallbackDownloadURLs[{index}]"
        if not isinstance(url, str) or not is_http_url(url):
            report.error(f"{label} must be a valid HTTP(S) URL")
            continue
        if not url.startswith("https://"):
            report.warn(f"{label} is not HTTPS - mirrors should be served over TLS")
        if url in seen:
            report.error(f"{label} duplicates an earlier mirror")
        if primary and url == primary:
            report.error(f"{label} duplicates the primary downloadURL")
        seen.add(url)
    return report


def _validate_permissions(prefix: str, app_permissions: Any, legacy_permissions: Any) -> Report:
    """Permissions may be declared via ``appPermissions`` (AltStore 2.0) or ``permissions`` (legacy)."""
    report = Report()
    if legacy_permissions is not None:
        if not isinstance(legacy_permissions, list):
            report.error(f"{prefix}.permissions must be an array of {{type, usageDescription}}")
        else:
            for index, perm in enumerate(legacy_permissions):
                if not isinstance(perm, dict) or not perm.get("type") or not perm.get("usageDescription"):
                    report.error(f"{prefix}.permissions[{index}] must have 'type' and 'usageDescription'")
    if app_permissions is not None:
        if not isinstance(app_permissions, dict):
            report.error(f"{prefix}.appPermissions must be an object")
            return report
        entitlements = app_permissions.get("entitlements")
        if entitlements is not None and (
            not isinstance(entitlements, list) or not all(isinstance(e, str) for e in entitlements)
        ):
            report.error(f"{prefix}.appPermissions.entitlements must be an array of strings")
        privacy = app_permissions.get("privacy")
        if privacy is not None and (
            not isinstance(privacy, dict) or not all(isinstance(v, str) for v in privacy.values())
        ):
            report.error(f"{prefix}.appPermissions.privacy must be an object of string values")
    return report


# ---------------------------------------------------------------------------
# feeds
# ---------------------------------------------------------------------------
def validate_feed(path: Path, feed: Any) -> Report:
    report = Report()
    label = path.relative_to(REPO_ROOT)
    if not isinstance(feed, dict):
        report.error(f"{label}: root must be a JSON object")
        return report

    for key in ("name", "identifier", "apps"):
        if key not in feed:
            report.error(f"{label}: missing top-level '{key}'")
    for key in ("iconURL", "website"):
        if feed.get(key) and not is_http_url(feed[key]):
            report.error(f"{label}: {key} must be an HTTP(S) URL")

    apps = feed.get("apps")
    if not isinstance(apps, list) or not apps:
        report.error(f"{label}: 'apps' must be a non-empty array")
        return report

    for index, app in enumerate(apps):
        prefix = f"{label}: apps[{index}]"
        if not isinstance(app, dict):
            report.error(f"{prefix} must be an object")
            continue
        prefix = f"{label}: {app.get('name', index)}"

        for key in REQUIRED_APP_FIELDS:
            if not app.get(key):
                report.error(f"{prefix} is missing '{key}'")
        if app.get("bundleIdentifier") and not BUNDLE_RE.match(str(app["bundleIdentifier"])):
            report.error(f"{prefix}.bundleIdentifier contains invalid characters")
        if app.get("downloadURL") and not is_http_url(app["downloadURL"]):
            report.error(f"{prefix}.downloadURL must be an HTTP(S) URL")
        if app.get("versionDate") and not DATE_RE.match(str(app["versionDate"])):
            report.error(f"{prefix}.versionDate must be an ISO date (YYYY-MM-DD)")
        if app.get("iconURL") and not is_http_url(app["iconURL"]):
            report.error(f"{prefix}.iconURL must be an HTTP(S) URL")
        if app.get("tintColor") and not TINT_RE.match(str(app["tintColor"]).lstrip("#")):
            report.error(f"{prefix}.tintColor must be a 6-digit hex string")
        report.extend(_validate_fallback_urls(prefix, app.get("fallbackDownloadURLs"), app.get("downloadURL")))
        report.extend(_validate_permissions(prefix, app.get("appPermissions"), app.get("permissions")))

        versions = app.get("versions")
        if not isinstance(versions, list) or not versions:
            report.error(f"{prefix}.versions must be a non-empty array")
            continue

        seen: set[str] = set()
        for v_index, version in enumerate(versions):
            v_prefix = f"{prefix}.versions[{v_index}]"
            if not isinstance(version, dict):
                report.error(f"{v_prefix} must be an object")
                continue
            for key in REQUIRED_VERSION_FIELDS:
                if version.get(key) in (None, ""):
                    report.error(f"{v_prefix} is missing '{key}'")
            if version.get("downloadURL") and not is_http_url(version["downloadURL"]):
                report.error(f"{v_prefix}.downloadURL must be an HTTP(S) URL")
            size = version.get("size")
            if not isinstance(size, int) or isinstance(size, bool) or size < 0:
                report.error(f"{v_prefix}.size must be a non-negative integer")
            elif size == 0:
                report.warn(f"{v_prefix}.size is 0 - clients show a bogus download size")
            if version.get("date") and not DATE_RE.match(str(version["date"])):
                report.error(f"{v_prefix}.date must be an ISO date (YYYY-MM-DD)")
            report.extend(
                _validate_fallback_urls(v_prefix, version.get("fallbackDownloadURLs"), version.get("downloadURL"))
            )
            url = version.get("downloadURL")
            if url in seen:
                report.error(f"{v_prefix}.downloadURL is duplicated within this app")
            seen.add(url)

        newest = versions[0]
        if isinstance(newest, dict):
            for flat, nested in (
                ("version", "version"),
                ("versionDate", "date"),
                ("downloadURL", "downloadURL"),
                ("size", "size"),
            ):
                if app.get(flat) != newest.get(nested):
                    report.error(f"{prefix}.{flat} must mirror versions[0].{nested}")

        extension = app.get("omnisource")
        if extension is None:
            report.warn(f"{prefix}: no 'omnisource' metadata block")
        elif isinstance(extension, dict):
            if extension.get("status") not in VALID_STATUSES:
                report.error(f"{prefix}.omnisource.status is missing or unknown")
            health = extension.get("health", {})
            if isinstance(health, dict) and health.get("downloadReachable") is False:
                report.warn(f"{prefix}: download URL was unreachable at build time ({health.get('detail')})")

    return report


def validate_mirrors(catalog: Any) -> Report:
    """Root-level feeds must be byte-identical copies of feeds/."""
    report = Report()
    slugs = [app["slug"] for app in catalog.get("apps", []) if isinstance(app, dict) and app.get("slug")]
    for name in ["apps.json", *(f"{slug}.json" for slug in slugs)]:
        source, mirror = FEEDS_DIR / name, REPO_ROOT / name
        if not source.exists():
            report.error(f"feeds/{name}: missing - run scripts/omnisource.py")
            continue
        if not mirror.exists():
            report.error(f"{name}: root compatibility mirror missing - run scripts/omnisource.py")
            continue
        if mirror.read_text(encoding="utf-8") != source.read_text(encoding="utf-8"):
            report.error(f"{name}: root mirror is out of sync with feeds/{name}")
    return report


def validate_assets(catalog: Any) -> Report:
    report = Report()
    referenced = {app.get("icon") for app in catalog.get("apps", []) if isinstance(app, dict)}
    referenced |= {catalog.get("source", {}).get("icon"), catalog.get("source", {}).get("banner")}
    referenced |= {client.get("icon") for client in catalog.get("clients", []) if isinstance(client, dict)}
    referenced = {name for name in referenced if name}

    for name in sorted(referenced):
        if not (ASSETS_DIR / name).is_file():
            report.error(f"assets/{name}: referenced by catalog.json but missing")

    if ASSETS_DIR.is_dir():
        for asset in sorted(ASSETS_DIR.iterdir()):
            if asset.is_file() and asset.name not in referenced:
                report.warn(f"assets/{asset.name}: not referenced by catalog.json")
            if asset.is_file() and asset.stat().st_size > 512_000:
                report.warn(f"assets/{asset.name}: {asset.stat().st_size // 1024} KB - consider optimising")
    return report


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def emit(report: Report, *, strict: bool) -> int:
    annotate = bool(os.environ.get("GITHUB_ACTIONS"))
    for warning in report.warnings:
        print(f"::warning::{warning}" if annotate else f"WARN  {warning}")
    for error in report.errors:
        print(f"::error::{error}" if annotate else f"ERROR {error}")

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with Path(summary_path).open("a", encoding="utf-8") as handle:
            handle.write(
                f"## Validation\n\n- **Errors:** {len(report.errors)}\n- **Warnings:** {len(report.warnings)}\n\n"
            )
            for error in report.errors:
                handle.write(f"- ❌ `{error}`\n")
            for warning in report.warnings[:20]:
                handle.write(f"- ⚠️ `{warning}`\n")

    if report.errors:
        print(f"\nFAILED: {len(report.errors)} error(s), {len(report.warnings)} warning(s)")
        return 1
    if strict and report.warnings:
        print(f"\nFAILED (strict): {len(report.warnings)} warning(s)")
        return 1
    print(f"\nOK: 0 errors, {len(report.warnings)} warning(s)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("files", nargs="*", type=Path, help="specific feed files (default: catalog + every feed)")
    parser.add_argument("--strict", action="store_true", help="treat warnings as failures")
    parser.add_argument("--skip-mirrors", action="store_true", help="do not compare root mirrors with feeds/")
    args = parser.parse_args(argv)

    report = Report()

    if args.files:
        for raw in args.files:
            path = raw if raw.is_absolute() else REPO_ROOT / raw
            feed = load_json(path, report)
            if feed is not None:
                report.extend(validate_feed(path, feed))
        return emit(report, strict=args.strict)

    catalog = load_json(CATALOG_PATH, report)
    if catalog is None:
        return emit(report, strict=args.strict)

    report.extend(validate_catalog(catalog))
    report.extend(validate_assets(catalog))

    feed_paths = sorted(p for p in FEEDS_DIR.glob("*.json") if p.name not in NON_FEED_FILES)
    if not feed_paths:
        report.error("feeds/: no generated feeds found - run scripts/omnisource.py")
    for path in feed_paths:
        feed = load_json(path, report)
        if feed is not None:
            report.extend(validate_feed(path, feed))

    if not args.skip_mirrors:
        report.extend(validate_mirrors(catalog))

    print(f"Validated catalog.json, {len(feed_paths)} feed(s).")
    return emit(report, strict=args.strict)


if __name__ == "__main__":
    sys.exit(main())
