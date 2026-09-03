"""Generic JSON feed provider: raw JSON, AltStore sources, Feather repositories.

AltStore and Feather both publish a document with an ``apps`` array. Feather
sources are AltStore-compatible; we treat them as the same shape and keep the
source type so OmniStore metadata can tell them apart.
"""

from __future__ import annotations

from omnisource.domain import (
    AppMetadata,
    DiscoveredApp,
    RemoteAsset,
    RemoteRelease,
    RepositoryRef,
    SourceType,
    ValidationResult,
)
from omnisource.errors import ProviderError
from omnisource.http import HttpClient, is_http_url
from omnisource.providers.base import SourceProvider


def _apps_from_payload(payload: object) -> list[dict]:
    if isinstance(payload, dict):
        apps = payload.get("apps")
        if isinstance(apps, list):
            return [item for item in apps if isinstance(item, dict)]
        # Obtainium / generic: a single app object.
        if "name" in payload and ("downloadURL" in payload or "versions" in payload):
            return [payload]
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    return []


def _releases_from_app(app: dict) -> list[RemoteRelease]:
    versions = app.get("versions")
    entries: list[dict]
    if isinstance(versions, list) and versions:
        entries = [item for item in versions if isinstance(item, dict)]
    else:
        entries = [
            {
                "version": app.get("version"),
                "date": app.get("versionDate") or app.get("date"),
                "localizedDescription": app.get("versionDescription") or app.get("localizedDescription") or "",
                "downloadURL": app.get("downloadURL"),
                "size": app.get("size") or 0,
                "sha256": app.get("sha256"),
            }
        ]
    releases: list[RemoteRelease] = []
    for entry in entries:
        version = str(entry.get("version") or "")
        url = str(entry.get("downloadURL") or "")
        if not version or not url:
            continue
        name = str(entry.get("name") or f"{version}.ipa")
        releases.append(
            RemoteRelease(
                tag=version,
                name=version,
                body=str(entry.get("localizedDescription") or ""),
                published_at=str(entry.get("date") or ""),
                assets=(
                    RemoteAsset(
                        name=name if name.endswith(".ipa") else f"{name}.ipa",
                        download_url=url,
                        size=int(entry.get("size") or 0),
                        sha256=str(entry["sha256"]) if entry.get("sha256") else None,
                    ),
                ),
            )
        )
    return releases


class GenericFeedProvider(SourceProvider):
    """Fetch a JSON document and expose it as apps + releases."""

    name = "json-feed"
    source_type = SourceType.JSON_FEED

    def __init__(self, http: HttpClient, source_type: SourceType | None = None) -> None:
        self.http = http
        if source_type is not None:
            self.source_type = source_type
            self.name = source_type.value
        self._payload_cache: dict[str, object] = {}

    def _load(self, source: RepositoryRef) -> object:
        url = source.feed_url
        if not url:
            raise ProviderError("feed provider requires upstream.feedURL")
        if url in self._payload_cache:
            return self._payload_cache[url]
        payload = self.http.get_json(url)
        self._payload_cache[url] = payload
        return payload

    def validate_repository(self, source: RepositoryRef) -> ValidationResult:
        if not is_http_url(source.feed_url):
            return ValidationResult(False, "feedURL is not an HTTP(S) URL", source.feed_url)
        try:
            payload = self._load(source)
        except ProviderError as error:
            return ValidationResult(False, str(error), source.feed_url)
        apps = _apps_from_payload(payload)
        if not apps:
            return ValidationResult(False, "feed contains no apps", source.feed_url)
        return ValidationResult(True, f"{len(apps)} app(s)", source.feed_url, {"apps": len(apps)})

    def discover_apps(self, source: RepositoryRef) -> list[DiscoveredApp]:
        payload = self._load(source)
        discovered: list[DiscoveredApp] = []
        for app in _apps_from_payload(payload):
            name = str(app.get("name") or "")
            bundle = str(app.get("bundleIdentifier") or app.get("bundleId") or "")
            slug = bundle.lower().replace(".", "-") or name.lower().replace(" ", "-")
            discovered.append(
                DiscoveredApp(
                    app_id=slug,
                    name=name or slug,
                    repository_url=source.feed_url,
                    source_type=self.source_type,
                    developer=str(app.get("developerName") or app.get("developer") or ""),
                    description=str(app.get("localizedDescription") or app.get("subtitle") or ""),
                )
            )
        return discovered

    def fetch_metadata(self, source: RepositoryRef) -> AppMetadata:
        payload = self._load(source)
        if isinstance(payload, dict):
            name = str(payload.get("name") or "feed")
            description = str(payload.get("description") or payload.get("subtitle") or "")
            icon = str(payload.get("iconURL") or "")
            return AppMetadata(name=name, developer="", description=description, icon=icon, homepage=source.feed_url)
        apps = self.discover_apps(source)
        first = apps[0] if apps else None
        return AppMetadata(
            name=first.name if first else "feed",
            developer=first.developer if first else "",
            description=first.description if first else "",
            homepage=source.feed_url,
        )

    def fetch_releases(
        self,
        source: RepositoryRef,
        *,
        previous_latest_url: str | None = None,
        incremental: bool = False,
    ) -> list[RemoteRelease]:
        payload = self._load(source)
        apps = _apps_from_payload(payload)
        # A catalog entry tracking a whole source uses the first app; a more
        # specific match can be added later via upstream.repo as bundle id.
        target = apps
        if source.repo:
            target = [
                app
                for app in apps
                if str(app.get("bundleIdentifier") or "") == source.repo or str(app.get("name") or "") == source.repo
            ] or apps
        releases: list[RemoteRelease] = []
        for app in target:
            releases.extend(_releases_from_app(app))
        if incremental and previous_latest_url and releases:
            newest = releases[0].assets[0].download_url if releases[0].assets else None
            if newest == previous_latest_url:
                return []
        return releases


class AltStoreFeedProvider(GenericFeedProvider):
    name = "altstore"
    source_type = SourceType.ALTSTORE


class FeatherFeedProvider(GenericFeedProvider):
    name = "feather"
    source_type = SourceType.FEATHER
