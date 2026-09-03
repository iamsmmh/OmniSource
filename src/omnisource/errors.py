"""Typed failures used across the pipeline."""

from __future__ import annotations


class OmniSourceError(RuntimeError):
    """Base class for recoverable-or-not pipeline failures."""


class SyncError(OmniSourceError):
    """Unrecoverable pipeline failure (bad catalog, empty build, …)."""


class ProviderError(OmniSourceError):
    """A source provider could not complete a request."""


class ValidationError(OmniSourceError):
    """Structural validation failed."""


class ConfigurationError(OmniSourceError):
    """A catalog entry or provider configuration is invalid."""
