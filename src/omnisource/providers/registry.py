"""Provider registry + default wiring."""

from __future__ import annotations

from omnisource.domain import RepositoryRef, SourceType
from omnisource.errors import ConfigurationError
from omnisource.http import HttpClient
from omnisource.providers.base import SourceProvider
from omnisource.providers.feed import AltStoreFeedProvider, GenericFeedProvider
from omnisource.providers.github import GitHubReleasesProvider, GitHubTagsProvider


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
    """Wire every provider used by the current catalog to a shared HTTP client."""
    registry = ProviderRegistry()
    registry.register(GitHubReleasesProvider(http))
    registry.register(GitHubTagsProvider(http))
    registry.register(GenericFeedProvider(http))
    registry.register(AltStoreFeedProvider(http))
    return registry
