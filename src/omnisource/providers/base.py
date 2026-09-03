"""Provider contract.

Python methods are snake_case. The platform contract names (``discoverApps``,
``fetchMetadata``, ``fetchReleases``, ``validateRepository``) are bound as
aliases on the ABC so both styles resolve to the same implementation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from omnisource.domain import (
    AppMetadata,
    DiscoveredApp,
    RemoteAsset,
    RemoteRelease,
    RepositoryRef,
    SourceType,
    ValidationResult,
)

# Sentinel returned by fetch_releases when incremental sync proves nothing changed.
INCREMENTAL_UNCHANGED: list[RemoteRelease] = []


class SourceProvider(ABC):
    """One upstream kind (GitHub Releases, GitLab, a JSON feed, …)."""

    name: str
    source_type: SourceType

    @abstractmethod
    def validate_repository(self, source: RepositoryRef) -> ValidationResult:
        """Return whether ``source`` exists and looks distributable."""

    @abstractmethod
    def discover_apps(self, source: RepositoryRef) -> list[DiscoveredApp]:
        """List apps reachable from ``source`` (a repo, org, or feed URL)."""

    @abstractmethod
    def fetch_metadata(self, source: RepositoryRef) -> AppMetadata:
        """Fetch identity metadata (name, description, topics, …)."""

    @abstractmethod
    def fetch_releases(
        self,
        source: RepositoryRef,
        *,
        previous_latest_url: str | None = None,
        incremental: bool = False,
    ) -> list[RemoteRelease]:
        """Return published releases, newest first.

        When ``incremental`` is true and the newest matching asset URL equals
        ``previous_latest_url``, providers should return an empty list and
        *not* paginate further. The pipeline treats that as "keep last state".
        Distinguishing "nothing upstream" from "incremental hit" is the
        caller's job (it already has previous state).
        """

    # Platform-contract aliases ------------------------------------------------
    def validateRepository(self, source: RepositoryRef) -> ValidationResult:
        return self.validate_repository(source)

    def discoverApps(self, source: RepositoryRef) -> list[DiscoveredApp]:
        return self.discover_apps(source)

    def fetchMetadata(self, source: RepositoryRef) -> AppMetadata:
        return self.fetch_metadata(source)

    def fetch_assets(self, source: RepositoryRef, releases: list[RemoteRelease] | None = None) -> list[RemoteAsset]:
        """Return all discovered assets, reusing release metadata when supplied."""
        material = releases if releases is not None else self.fetch_releases(source)
        return [asset for release in material for asset in release.assets]

    def health_check(self, source: RepositoryRef) -> ValidationResult:
        """Run a cheap provider health check without downloading release files."""
        return self.validate_repository(source)

    def fetchReleases(
        self,
        source: RepositoryRef,
        *,
        previous_latest_url: str | None = None,
        incremental: bool = False,
    ) -> list[RemoteRelease]:
        return self.fetch_releases(source, previous_latest_url=previous_latest_url, incremental=incremental)

    def fetchAssets(self, source: RepositoryRef, releases: list[RemoteRelease] | None = None) -> list[RemoteAsset]:
        return self.fetch_assets(source, releases)

    def healthCheck(self, source: RepositoryRef) -> ValidationResult:
        return self.health_check(source)
