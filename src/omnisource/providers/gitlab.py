"""GitLab Releases provider (gitlab.com and self-hosted)."""

from __future__ import annotations

import threading
import urllib.parse

from omnisource.constants import GITLAB_API_ROOT
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
from omnisource.http import HttpClient
from omnisource.logutil import log
from omnisource.providers.base import SourceProvider
from omnisource.tracking import pick_asset, release_is_eligible
from omnisource.utils.assets import detect_asset_metadata


def _api_root(source: RepositoryRef) -> str:
    if source.host:
        return source.host.rstrip("/") + "/api/v4"
    return GITLAB_API_ROOT


def _project_path(source: RepositoryRef) -> str:
    return urllib.parse.quote(source.repo, safe="")


class GitLabReleasesProvider(SourceProvider):
    name = "gitlab"
    source_type = SourceType.GITLAB_RELEASES

    def __init__(self, http: HttpClient) -> None:
        self.http = http
        self._cache: dict[tuple[str, str, int], list[RemoteRelease]] = {}
        self._incremental_hits: set[tuple[object, ...]] = set()
        self._cache_lock = threading.Lock()

    def _get(self, source: RepositoryRef, path: str) -> object:
        return self.http.get_json(f"{_api_root(source)}{path}")

    def validate_repository(self, source: RepositoryRef) -> ValidationResult:
        try:
            payload = self._get(source, f"/projects/{_project_path(source)}")
        except ProviderError as error:
            return ValidationResult(False, str(error), source.repo)
        if not isinstance(payload, dict):
            return ValidationResult(False, "unexpected project payload", source.repo)
        return ValidationResult(True, "ok", str(payload.get("web_url") or ""))

    def discover_apps(self, source: RepositoryRef) -> list[DiscoveredApp]:
        meta = self.fetch_metadata(source)
        return [
            DiscoveredApp(
                app_id=source.repo.split("/")[-1].lower(),
                name=meta.name,
                repository_url=meta.homepage or f"{source.host or 'https://gitlab.com'}/{source.repo}",
                source_type=self.source_type,
                developer=meta.developer,
                description=meta.description,
            )
        ]

    def fetch_metadata(self, source: RepositoryRef) -> AppMetadata:
        payload = self._get(source, f"/projects/{_project_path(source)}")
        if not isinstance(payload, dict):
            raise ProviderError(f"unexpected GitLab project payload for {source.repo}")
        namespace = payload.get("namespace") if isinstance(payload.get("namespace"), dict) else {}
        topics = payload.get("topics") if isinstance(payload.get("topics"), list) else []
        return AppMetadata(
            name=str(payload.get("name") or source.repo),
            developer=str(namespace.get("name") or source.repo.split("/")[0]),
            description=str(payload.get("description") or ""),
            icon=str(payload.get("avatar_url") or ""),
            homepage=str(payload.get("web_url") or ""),
            stars=int(payload.get("star_count") or 0),
            topics=tuple(str(topic) for topic in topics),
            default_branch=str(payload.get("default_branch") or ""),
            archived=bool(payload.get("archived")),
        )

    def fetch_releases(
        self,
        source: RepositoryRef,
        *,
        previous_latest_url: str | None = None,
        incremental: bool = False,
    ) -> list[RemoteRelease]:
        key = (source.host, source.repo, source.max_pages)
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
                batch = self._get(
                    source,
                    f"/projects/{_project_path(source)}/releases?per_page=100&page={page}",
                )
                if not isinstance(batch, list):
                    raise ProviderError(f"unexpected GitLab releases payload for {source.repo}")
                page_releases = [_release_from_gitlab(item) for item in batch if isinstance(item, dict)]
                collected.extend(page_releases)
                if (
                    incremental
                    and previous_latest_url
                    and page == 1
                    and _newest_url(page_releases, source) == previous_latest_url
                ):
                    log.debug("%s: GitLab incremental hit", source.repo)
                    self._incremental_hits.add(policy_key)
                    return []
                if len(batch) < 100:
                    break
            self._cache[key] = collected
            return collected


def _release_from_gitlab(raw: dict) -> RemoteRelease:
    assets_block = raw.get("assets") if isinstance(raw.get("assets"), dict) else {}
    links = assets_block.get("links") if isinstance(assets_block.get("links"), list) else []
    assets: list[RemoteAsset] = []
    for link in links:
        if not isinstance(link, dict):
            continue
        url = str(link.get("direct_asset_url") or link.get("url") or "")
        name = str(link.get("name") or "")
        if url and name:
            detected = detect_asset_metadata(name, url)
            assets.append(
                RemoteAsset(
                    name=name,
                    download_url=url,
                    size=int(link.get("size") or 0),
                    content_type=str(link.get("link_type") or ""),
                    platform=str(detected["platform"]),
                    architecture=detected["architecture"],
                    file_type=str(detected["fileType"]),
                    installable=bool(detected["installable"]),
                )
            )
    return RemoteRelease(
        tag=str(raw.get("tag_name") or ""),
        name=str(raw.get("name") or ""),
        body=str(raw.get("description") or ""),
        published_at=str(raw.get("released_at") or raw.get("created_at") or ""),
        assets=tuple(assets),
        prerelease=bool(raw.get("upcoming_release")),
        release_url=str(raw.get("_links", {}).get("self") or "") if isinstance(raw.get("_links"), dict) else None,
        source="gitlab",
    )


def _newest_url(releases: list[RemoteRelease], source: RepositoryRef) -> str | None:
    for release in releases:
        if not release_is_eligible(release, source):
            continue
        asset = pick_asset(release, source.asset_suffixes)
        if asset:
            return asset.download_url
    return None
