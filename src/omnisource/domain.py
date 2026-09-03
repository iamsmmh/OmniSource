"""Type-safe domain model for the OmniSource platform.

These dataclasses are the single in-memory representation of catalog entries,
remote releases, and the unified OmniStore metadata record. Providers produce
:class:`RemoteRelease` values; the pipeline turns them into version entries
and :class:`StandardizedApp` records regardless of source.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from omnisource.errors import ConfigurationError, SyncError


class SourceType(StrEnum):
    """Supported upstream kinds. Values are the catalog ``upstream.provider`` ids."""

    GITHUB_RELEASES = "github"
    GITHUB_TAGS = "github-tags"
    GITLAB_RELEASES = "gitlab"
    CODEBERG_RELEASES = "codeberg"
    FORGEJO_RELEASES = "forgejo"
    JSON_FEED = "json-feed"
    ALTSTORE = "altstore"
    FEATHER = "feather"
    MANUAL = "manual"

    @classmethod
    def parse(cls, value: str | None) -> SourceType:
        if not value:
            return cls.GITHUB_RELEASES
        try:
            return cls(value)
        except ValueError as error:
            known = ", ".join(item.value for item in cls)
            raise ConfigurationError(f"unknown upstream.provider '{value}' (expected one of {known})") from error


def utc_now() -> datetime:
    return datetime.now(UTC)


def today() -> str:
    return utc_now().strftime("%Y-%m-%d")


@dataclass(frozen=True)
class RemoteAsset:
    """A downloadable file attached to a remote release, source-agnostic."""

    name: str
    download_url: str
    size: int = 0
    sha256: str | None = None
    content_type: str = ""


@dataclass(frozen=True)
class RemoteRelease:
    """A published release from any forge or feed, source-agnostic."""

    tag: str
    name: str
    body: str
    published_at: str
    assets: tuple[RemoteAsset, ...] = ()
    prerelease: bool = False
    draft: bool = False
    build_number: str | None = None

    @property
    def is_published(self) -> bool:
        return not self.draft and not self.prerelease


@dataclass(frozen=True)
class DiscoveredApp:
    """Lightweight identity returned by ``discover_apps()``."""

    app_id: str
    name: str
    repository_url: str
    source_type: SourceType
    developer: str = ""
    description: str = ""


@dataclass(frozen=True)
class AppMetadata:
    """Source-level metadata returned by ``fetch_metadata()``."""

    name: str
    developer: str
    description: str
    icon: str = ""
    homepage: str = ""
    license: str = ""
    stars: int | None = None
    topics: tuple[str, ...] = ()
    default_branch: str = ""
    archived: bool = False


@dataclass(frozen=True)
class ValidationResult:
    """Outcome of ``validate_repository()``."""

    ok: bool
    detail: str
    repository_url: str = ""
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RepositoryRef:
    """How to reach an upstream. Built from a catalog ``upstream`` block."""

    provider: SourceType
    repo: str = ""
    host: str = ""
    feed_url: str = ""
    tag_prefix: str = ""
    exclude_tag_prefixes: tuple[str, ...] = ()
    asset_suffixes: tuple[str, ...] = (".ipa",)
    asset_name_pattern: str = ""
    max_pages: int = 3
    keep_versions: int = 1
    sort_by_tag_number: bool = False
    version_from_tag: bool = False
    description_template: str = "{name} {version} | {label}"
    min_os_version: str = "16.0"
    min_os_by_tag_number: dict[str, str] = field(default_factory=dict)
    iso_dates: bool = False

    @property
    def cache_key(self) -> tuple[str, str, str, int]:
        return (self.provider.value, self.host, self.repo or self.feed_url, self.max_pages)

    @classmethod
    def parse(cls, raw: dict[str, Any]) -> RepositoryRef:
        provider = SourceType.parse(raw.get("provider"))
        repo = str(raw.get("repo") or "")
        feed_url = str(raw.get("feedURL") or raw.get("feedUrl") or "")
        if provider in {SourceType.JSON_FEED, SourceType.ALTSTORE, SourceType.FEATHER}:
            if not feed_url:
                raise ConfigurationError("feed providers require upstream.feedURL")
        elif not repo:
            raise ConfigurationError("forge providers require upstream.repo")
        return cls(
            provider=provider,
            repo=repo,
            host=str(raw.get("host") or "").rstrip("/"),
            feed_url=feed_url,
            tag_prefix=raw.get("tagPrefix", ""),
            exclude_tag_prefixes=tuple(raw.get("excludeTagPrefixes", ())),
            asset_suffixes=tuple(raw.get("assetSuffixes", (".ipa",))),
            asset_name_pattern=raw.get("assetNamePattern", ""),
            max_pages=int(raw.get("maxPages", 3)),
            keep_versions=int(raw.get("keepVersions", 1)),
            sort_by_tag_number=bool(raw.get("sortByTagNumber", False)),
            version_from_tag=bool(raw.get("versionFromTag", False)),
            description_template=raw.get("descriptionTemplate", "{name} {version} | {label}"),
            min_os_version=raw.get("minOSVersion", "16.0"),
            min_os_by_tag_number=dict(raw.get("minOSVersionByTagNumber", {})),
            iso_dates=bool(raw.get("isoDates", False)),
        )


@dataclass
class App:
    """One catalog entry. ``raw`` is the original JSON object."""

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
    def category(self) -> str:
        return str(self.raw.get("category", "utilities"))

    @property
    def developer(self) -> str:
        return str(self.raw.get("developerName", ""))

    @property
    def bundle_id(self) -> str:
        return str(self.raw.get("bundleIdentifier", ""))

    @property
    def description(self) -> str:
        return str(self.raw.get("localizedDescription", ""))

    @property
    def screenshots(self) -> list[str]:
        raw = self.raw.get("screenshots") or []
        return [url for url in raw if isinstance(url, str)]

    @property
    def tags(self) -> tuple[str, ...]:
        raw = self.raw.get("tags")
        if isinstance(raw, list):
            return tuple(str(tag) for tag in raw if tag)
        return (self.category,) if self.category else ()

    @property
    def upstream(self) -> RepositoryRef | None:
        raw = self.raw.get("upstream")
        return RepositoryRef.parse(raw) if isinstance(raw, dict) else None

    @property
    def manual_release(self) -> dict[str, Any] | None:
        raw = self.raw.get("manualRelease")
        return dict(raw) if isinstance(raw, dict) else None

    @property
    def source_type(self) -> SourceType:
        if self.upstream is None:
            return SourceType.MANUAL
        return self.upstream.provider

    @property
    def repository_url(self) -> str:
        explicit = self.raw.get("upstreamURL")
        if isinstance(explicit, str) and explicit:
            return explicit
        up = self.upstream
        if up is None:
            return ""
        if up.feed_url:
            return up.feed_url
        host = up.host or _default_host(up.provider)
        if up.repo and host:
            return f"{host}/{up.repo}"
        return ""


def _default_host(provider: SourceType) -> str:
    return {
        SourceType.GITHUB_RELEASES: "https://github.com",
        SourceType.GITHUB_TAGS: "https://github.com",
        SourceType.GITLAB_RELEASES: "https://gitlab.com",
        SourceType.CODEBERG_RELEASES: "https://codeberg.org",
        SourceType.FORGEJO_RELEASES: "",
    }.get(provider, "")


@dataclass
class Catalog:
    source: dict[str, Any]
    clients: list[dict[str, Any]]
    apps: list[App]

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> Catalog:
        apps = []
        for entry in raw.get("apps", []):
            app = App(slug=entry["slug"], raw=entry)
            _ = app.upstream  # parse/validate now so a bad catalog fails at load
            apps.append(app)
        if not apps:
            raise SyncError("catalog.json declares no apps")
        return cls(source=raw.get("source", {}), clients=raw.get("clients", []), apps=apps)

    @property
    def base_url(self) -> str:
        return str(self.source.get("baseURL", "")).rstrip("/")

    def app_by_slug(self, slug: str) -> App | None:
        return next((app for app in self.apps if app.slug == slug), None)


@dataclass(frozen=True)
class StandardizedApp:
    """Unified metadata record, independent of AltStore schema.

    Field names match the OmniStore / OmniSource platform contract. This is
    what ``feeds/omnistore/apps.json`` and the static API emit.
    """

    app_id: str
    name: str
    developer: str
    description: str
    icon: str
    screenshots: tuple[str, ...]
    category: str
    version: str
    build_number: str | None
    release_date: str
    bundle_id: str
    minimum_os_version: str
    source_type: str
    repository_url: str
    changelog: str
    download_url: str
    sha256: str | None
    size: int = 0
    status: str = "stable"
    featured: bool = False
    tags: tuple[str, ...] = ()
    fallback_download_urls: tuple[str, ...] = ()

    def to_json(self) -> dict[str, Any]:
        return {
            "appId": self.app_id,
            "name": self.name,
            "developer": self.developer,
            "description": self.description,
            "icon": self.icon,
            "screenshots": list(self.screenshots),
            "category": self.category,
            "version": self.version,
            "buildNumber": self.build_number,
            "releaseDate": self.release_date,
            "bundleId": self.bundle_id,
            "minimumOSVersion": self.minimum_os_version,
            "sourceType": self.source_type,
            "repositoryUrl": self.repository_url,
            "changelog": self.changelog,
            "downloadUrl": self.download_url,
            "sha256": self.sha256,
            "size": self.size,
            "status": self.status,
            "featured": self.featured,
            "tags": list(self.tags),
            "fallbackDownloadUrls": list(self.fallback_download_urls),
        }


@dataclass(frozen=True)
class HealthSnapshot:
    reachable: bool
    detail: str
    since: str


@dataclass
class UpdateEvent:
    app_id: str
    name: str
    version: str
    previous_version: str | None
    release_date: str
    download_url: str
    changelog: str
    kind: str  # "new" | "updated" | "unchanged"

    def to_json(self) -> dict[str, Any]:
        return {
            "appId": self.app_id,
            "name": self.name,
            "version": self.version,
            "previousVersion": self.previous_version,
            "releaseDate": self.release_date,
            "downloadUrl": self.download_url,
            "changelog": self.changelog,
            "kind": self.kind,
        }


@dataclass
class SyncReport:
    """Structured summary of one pipeline run, written to the job summary."""

    apps_total: int = 0
    apps_synced: int = 0
    apps_incremental_hit: int = 0
    apps_failed: int = 0
    apps_updated: int = 0
    api_requests: int = 0
    files_changed: int = 0
    updates: list[UpdateEvent] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
