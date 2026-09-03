"""Asset management: icon/screenshot validation, missing-asset detection,
dead-link recording, and a content-addressed cache protocol.

The cache never stores IPA payloads. It is reserved for small metadata
artefacts (icons, OpenAPI snapshots) so a future worker can avoid
re-downloading them. The default implementation is an on-disk directory
under ``.cache/omnisource/``, gitignored.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol
from urllib.parse import urlparse

from omnisource.constants import IMAGE_EXTENSIONS, JPEG_MAGIC, PNG_MAGIC
from omnisource.domain import App, Catalog
from omnisource.http import HttpClient, is_http_url

_SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")


@dataclass
class AssetIssue:
    slug: str
    kind: str  # icon | screenshot | missing | dead-link | oversized
    detail: str
    path: str = ""


@dataclass
class AssetReport:
    issues: list[AssetIssue] = field(default_factory=list)
    icons_ok: int = 0
    screenshots_ok: int = 0
    screenshots_missing: int = 0

    @property
    def errors(self) -> list[AssetIssue]:
        return [issue for issue in self.issues if issue.kind in {"missing", "dead-link"}]


class AssetCache(Protocol):
    def get(self, key: str) -> bytes | None: ...
    def put(self, key: str, payload: bytes) -> None: ...
    def has(self, key: str) -> bool: ...


class DirectoryCache:
    """Content-addressed file cache. Keys are hex SHA-256 of the payload or URL."""

    def __init__(self, root: Path) -> None:
        self.root = root

    def _path(self, key: str) -> Path:
        safe = key if _SHA256_HEX.match(key) else hashlib.sha256(key.encode("utf-8")).hexdigest()
        return self.root / safe[:2] / safe

    def get(self, key: str) -> bytes | None:
        path = self._path(key)
        try:
            return path.read_bytes()
        except OSError:
            return None

    def put(self, key: str, payload: bytes) -> None:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_bytes(payload)
        tmp.replace(path)

    def has(self, key: str) -> bool:
        return self._path(key).is_file()


class NullCache:
    def get(self, key: str) -> bytes | None:
        return None

    def put(self, key: str, payload: bytes) -> None:
        return None

    def has(self, key: str) -> bool:
        return False


def _looks_like_image_url(url: str) -> bool:
    path = urlparse(url).path.lower()
    return any(path.endswith(ext) for ext in IMAGE_EXTENSIONS)


def _icon_magic_ok(path: Path) -> str | None:
    try:
        header = path.read_bytes()[:16]
    except OSError as error:
        return f"unreadable ({error})"
    if header.startswith(PNG_MAGIC) or header.startswith(JPEG_MAGIC):
        return None
    if path.suffix.lower() in IMAGE_EXTENSIONS and path.stat().st_size > 0:
        return None
    return "does not look like a PNG/JPEG image"


def inspect_catalog(catalog: Catalog, *, assets_dir: Path) -> AssetReport:
    """Offline asset audit: existence, magic bytes, screenshot URL shape."""
    report = AssetReport()
    referenced: set[str] = set()
    for app in catalog.apps:
        _inspect_app(app, assets_dir, report, referenced)
    source_icon = catalog.source.get("icon")
    source_banner = catalog.source.get("banner")
    for name in (source_icon, source_banner):
        if name:
            referenced.add(str(name))
            path = assets_dir / str(name)
            if not path.is_file():
                report.issues.append(
                    AssetIssue("source", "missing", f"assets/{name} is referenced but missing", str(name))
                )
    for client in catalog.clients:
        icon = client.get("icon")
        if icon:
            referenced.add(str(icon))
            if not (assets_dir / str(icon)).is_file():
                report.issues.append(
                    AssetIssue("client", "missing", f"assets/{icon} is referenced by a client but missing", str(icon))
                )
    if assets_dir.is_dir():
        for asset in sorted(assets_dir.iterdir()):
            if asset.is_file() and asset.name not in referenced:
                report.issues.append(
                    AssetIssue("", "unused", f"assets/{asset.name} is not referenced by catalog.json", asset.name)
                )
            if asset.is_file() and asset.stat().st_size > 512_000:
                report.issues.append(
                    AssetIssue("", "oversized", f"assets/{asset.name}: {asset.stat().st_size // 1024} KB", asset.name)
                )
    return report


def _inspect_app(app: App, assets_dir: Path, report: AssetReport, referenced: set[str]) -> None:
    referenced.add(app.icon)
    path = assets_dir / app.icon
    if not path.is_file():
        report.issues.append(AssetIssue(app.slug, "missing", f"icon assets/{app.icon} does not exist", app.icon))
    else:
        magic = _icon_magic_ok(path)
        if magic:
            report.issues.append(AssetIssue(app.slug, "icon", magic, app.icon))
        else:
            report.icons_ok += 1
    screenshots = app.screenshots
    if not screenshots:
        report.screenshots_missing += 1
        report.issues.append(AssetIssue(app.slug, "screenshot", "no screenshots declared"))
        return
    for url in screenshots:
        if not is_http_url(url):
            report.issues.append(AssetIssue(app.slug, "screenshot", f"not an HTTP(S) URL: {url}", url))
            continue
        if not _looks_like_image_url(url):
            report.issues.append(AssetIssue(app.slug, "screenshot", f"URL does not look like an image: {url}", url))
            continue
        report.screenshots_ok += 1


def probe_screenshot_urls(
    catalog: Catalog,
    http: HttpClient,
    *,
    limit_per_app: int = 1,
) -> list[AssetIssue]:
    """Optional live probe of screenshot URLs. Off by default in CI."""
    issues: list[AssetIssue] = []
    for app in catalog.apps:
        for url in app.screenshots[:limit_per_app]:
            result = http.probe(url)
            if not result.reachable:
                issues.append(AssetIssue(app.slug, "dead-link", f"screenshot unreachable ({result.detail})", url))
    return issues
