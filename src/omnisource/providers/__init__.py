"""Source providers.

Every provider implements :class:`omnisource.providers.base.SourceProvider`:

* ``discover_apps()``     — list apps at a repository / organisation / feed
* ``fetch_metadata()``    — identity, description, topics
* ``fetch_releases()``    — normalised :class:`RemoteRelease` values
* ``validate_repository()`` / ``verify()`` — existence + basic sanity
* ``fetch_assets()``      — flattened assets across releases

CamelCase aliases matching the platform contract (``discoverApps``, …) are
exposed on the ABC so both naming conventions work.

Registered kinds: GitHub Releases, GitHub Tags, GitLab Releases, Gitea
(Codeberg + Forgejo), JSON/AltStore/Feather feeds, Direct-URL, Mirror and
archive.org. Per-app failover (primary → mirrors → cached state) is
orchestrated by :class:`omnisource.providers.failover.FailoverChain`.
"""

from __future__ import annotations

from omnisource.providers.base import INCREMENTAL_UNCHANGED, SourceProvider
from omnisource.providers.direct import ArchiveProvider, DirectURLProvider
from omnisource.providers.failover import FailoverChain, FailoverResult, leg_label
from omnisource.providers.feed import AltStoreFeedProvider, GenericFeedProvider
from omnisource.providers.gitea import GiteaReleasesProvider
from omnisource.providers.github import GitHubReleasesProvider, GitHubTagsProvider
from omnisource.providers.gitlab import GitLabReleasesProvider
from omnisource.providers.registry import ProviderRegistry, build_default_registry

__all__ = [
    "INCREMENTAL_UNCHANGED",
    "AltStoreFeedProvider",
    "ArchiveProvider",
    "DirectURLProvider",
    "FailoverChain",
    "FailoverResult",
    "GenericFeedProvider",
    "GitHubReleasesProvider",
    "GitHubTagsProvider",
    "GitLabReleasesProvider",
    "GiteaReleasesProvider",
    "ProviderRegistry",
    "SourceProvider",
    "build_default_registry",
    "leg_label",
]
