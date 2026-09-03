"""Forgejo / Gitea / Codeberg Releases provider.

Codeberg is a public Forgejo instance. Self-hosted Forgejo uses the same
``/api/v1/repos/{owner}/{repo}/releases`` contract; pass ``upstream.host``.
"""

from __future__ import annotations

import threading

from omnisource.constants import CODEBERG_API_ROOT
from omnisource.domain import (
    AppMetadata,
    DiscoveredApp,
    RemoteAsset,
    RemoteRelease,
    RepositoryRef,
    SourceType,
    ValidationResult,
)
from omnisource.errors import ConfigurationError, ProviderError
from omnisource.http import HttpClient
from omnisource.logutil import log
from omnisource.providers.base import SourceProvider
from omnisource.tracking import extract_sha256, pick_asset, release_is_eligible


def _api_root(source: RepositoryRef, default_host: str) -> str:
    if source.host:
        return source.host.rstrip("/") + "/api/v1"
    if default_host:
        return default_host
    raise ConfigurationError("forgejo provider requires upstream.host (e.g. https://git.example.com)")


def _release_from_gitea(raw: dict, *, source_name: str = "forgejo") -> RemoteRelease:
    assets: list[RemoteAsset] = []
    for item in raw.get("assets") or []:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "")
        url = str(item.get("browser_download_url") or item.get("browserDownloadUrl") or "")
        if not name or not url:
            continue
        digest = item.get("digest") or item.get("uuid") or ""
        assets.append(
            RemoteAsset(
                name=name,
                download_url=url,
                size=int(item.get("size") or 0),
                sha256=extract_sha256(str(digest)) if digest else None,
            )
        )
    return RemoteRelease(
        tag=str(raw.get("tag_name") or ""),
        name=str(raw.get("name") or ""),
        body=str(raw.get("body") or ""),
        published_at=str(raw.get("published_at") or raw.get("created_at") or ""),
        assets=tuple(assets),
        prerelease=bool(raw.get("prerelease")),
        draft=bool(raw.get("draft")),
        release_url=str(raw.get("html_url") or raw.get("htmlURL") or "") or None,
        source=source_name,
    )


class ForgejoReleasesProvider(SourceProvider):
    """Forgejo/Gitea Releases. Subclassed by Codeberg with a default host."""

    name = "forgejo"
    source_type = SourceType.FORGEJO_RELEASES
    default_api_root = ""

    def __init__(self, http: HttpClient) -> None:
        self.http = http
        self._cache: dict[tuple[str, str, int], list[RemoteRelease]] = {}
        self._incremental_hits: set[tuple[object, ...]] = set()
        self._cache_lock = threading.Lock()

    def _root(self, source: RepositoryRef) -> str:
        return _api_root(source, self.default_api_root)

    def _get(self, source: RepositoryRef, path: str) -> object:
        return self.http.get_json(f"{self._root(source)}{path}")

    def validate_repository(self, source: RepositoryRef) -> ValidationResult:
        try:
            payload = self._get(source, f"/repos/{source.repo}")
        except (ProviderError, ConfigurationError) as error:
            return ValidationResult(False, str(error), source.repo)
        if not isinstance(payload, dict):
            return ValidationResult(False, "unexpected repository payload", source.repo)
        html = str(payload.get("html_url") or payload.get("htmlURL") or "")
        return ValidationResult(True, "ok", html)

    def discover_apps(self, source: RepositoryRef) -> list[DiscoveredApp]:
        meta = self.fetch_metadata(source)
        return [
            DiscoveredApp(
                app_id=source.repo.split("/")[-1].lower(),
                name=meta.name,
                repository_url=meta.homepage,
                source_type=self.source_type,
                developer=meta.developer,
                description=meta.description,
            )
        ]

    def fetch_metadata(self, source: RepositoryRef) -> AppMetadata:
        payload = self._get(source, f"/repos/{source.repo}")
        if not isinstance(payload, dict):
            raise ProviderError(f"unexpected Forgejo repository payload for {source.repo}")
        owner = payload.get("owner") if isinstance(payload.get("owner"), dict) else {}
        return AppMetadata(
            name=str(payload.get("name") or source.repo),
            developer=str(owner.get("login") or owner.get("username") or source.repo.split("/")[0]),
            description=str(payload.get("description") or ""),
            icon=str(owner.get("avatar_url") or owner.get("avatarURL") or ""),
            homepage=str(payload.get("html_url") or payload.get("htmlURL") or ""),
            stars=int(payload.get("stars_count") or payload.get("starsCount") or 0),
            default_branch=str(payload.get("default_branch") or payload.get("defaultBranch") or ""),
            archived=bool(payload.get("archived")),
        )

    def fetch_releases(
        self,
        source: RepositoryRef,
        *,
        previous_latest_url: str | None = None,
        incremental: bool = False,
    ) -> list[RemoteRelease]:
        key = (self._root(source), source.repo, source.max_pages)
        policy_key = (
            *key,
            source.tag_prefix,
            source.exclude_tag_prefixes,
            source.asset_suffixes,
            source.include_prereleases,
            source.include_drafts,
        )
        with self._cache_lock:
            if key in self._cache:
                return self._cache[key]
            if incremental and previous_latest_url and policy_key in self._incremental_hits:
                return []

            collected: list[RemoteRelease] = []
            for page in range(1, source.max_pages + 1):
                batch = self._get(source, f"/repos/{source.repo}/releases?limit=100&page={page}")
                if not isinstance(batch, list):
                    raise ProviderError(f"unexpected Forgejo releases payload for {source.repo}")
                page_releases = [
                    _release_from_gitea(item, source_name=self.source_type.value)
                    for item in batch
                    if isinstance(item, dict)
                ]
                published = [rel for rel in page_releases if rel.is_published]
                collected.extend(published)
                if (
                    incremental
                    and previous_latest_url
                    and page == 1
                    and _newest_url(published, source) == previous_latest_url
                ):
                    log.debug("%s: Forgejo incremental hit", source.repo)
                    self._incremental_hits.add(policy_key)
                    return []
                if len(batch) < 100:
                    break
            self._cache[key] = collected
            return collected


class CodebergReleasesProvider(ForgejoReleasesProvider):
    name = "codeberg"
    source_type = SourceType.CODEBERG_RELEASES
    default_api_root = CODEBERG_API_ROOT


def _newest_url(releases: list[RemoteRelease], source: RepositoryRef) -> str | None:
    for release in releases:
        if not release_is_eligible(release, source):
            continue
        asset = pick_asset(release, source.asset_suffixes)
        if asset:
            return asset.download_url
    return None
