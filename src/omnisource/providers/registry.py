"""Provider registry + default wiring."""

from __future__ import annotations

from omnisource.domain import RepositoryRef, SourceType
from omnisource.errors import ConfigurationError
from omnisource.http import HttpClient
from omnisource.providers.base import SourceProvider
from omnisource.providers.feed import AltStoreFeedProvider, FeatherFeedProvider, GenericFeedProvider
from omnisource.providers.forgejo import CodebergReleasesProvider, ForgejoReleasesProvider
from omnisource.providers.github import GitHubReleasesProvider, GitHubTagsProvider
from omnisource.providers.gitlab import GitLabReleasesProvider


class ProviderRegistry:
    """Lookup table from :class:`SourceType` (or catalog provider id) to a provider."""

    def __init__(self) -> None:
        self._providers: dict[SourceType, SourceProvider] = {}

    def register(self, provider: SourceProvider) -> None:
        self._providers[provider.source_type] = provider

    def get(self, source_type: SourceType) -> SourceProvider:
        try:
            return self._providers[source_type]
        except KeyError as error:
            raise ConfigurationError(f"no provider registered for '{source_type.value}'") from error

    def resolve(self, ref: RepositoryRef) -> SourceProvider:
        return self.get(ref.provider)

    def __contains__(self, source_type: SourceType) -> bool:
        return source_type in self._providers

    def __iter__(self):
        return iter(self._providers.values())


def build_default_registry(http: HttpClient) -> ProviderRegistry:
    """Wire every first-party provider to a shared HTTP client (and thus cache)."""
    registry = ProviderRegistry()
    github = GitHubReleasesProvider(http)
    registry.register(github)
    registry.register(GitHubTagsProvider(http))
    registry.register(GitLabReleasesProvider(http))
    registry.register(CodebergReleasesProvider(http))
    registry.register(ForgejoReleasesProvider(http))
    registry.register(GenericFeedProvider(http))
    registry.register(AltStoreFeedProvider(http))
    registry.register(FeatherFeedProvider(http))
    return registry
