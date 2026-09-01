"""Provider registry — the composition seam between wiring and the engine."""

from __future__ import annotations

from collections.abc import Iterable, Iterator

from omnisource.core.exceptions import ConfigurationError
from omnisource.providers.base import BaseProvider


class ProviderRegistry:
    """An ordered, name-unique collection of providers."""

    def __init__(self, providers: Iterable[BaseProvider] = ()) -> None:
        self._providers: dict[str, BaseProvider] = {}
        for provider in providers:
            self.register(provider)

    def register(self, provider: BaseProvider) -> None:
        """Add ``provider``; raises if its name is already taken."""
        if provider.name in self._providers:
            raise ConfigurationError(f"duplicate provider name: {provider.name!r}")
        self._providers[provider.name] = provider

    def unregister(self, name: str) -> None:
        self._providers.pop(name, None)

    def get(self, name: str) -> BaseProvider:
        try:
            return self._providers[name]
        except KeyError as exc:
            raise ConfigurationError(f"unknown provider: {name!r}") from exc

    def select(self, names: Iterable[str] | None = None) -> list[BaseProvider]:
        """Return all providers, or just those named."""
        if names is None:
            return list(self._providers.values())
        return [self.get(name) for name in names]

    @property
    def names(self) -> list[str]:
        return list(self._providers)

    def __iter__(self) -> Iterator[BaseProvider]:
        return iter(self._providers.values())

    def __len__(self) -> int:
        return len(self._providers)

    def __contains__(self, name: object) -> bool:
        return name in self._providers
