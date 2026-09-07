"""Minimal dependency-injection container.

No framework. The container is a dataclass constructed by :func:`build_container`
and passed into the pipeline. Tests swap ``http`` or ``paths`` without patching
globals.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from omnisource.config import RuntimeSettings, load_runtime_settings
from omnisource.constants import USER_AGENT, Paths
from omnisource.http import AuthRule, HttpClient
from omnisource.providers.registry import ProviderRegistry, build_default_registry


def _auth_rules_from_env() -> tuple[AuthRule, ...]:
    """Host-scoped credentials. Tokens never attach to download URLs."""
    rules: list[AuthRule] = []
    github = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if github:
        rules.append(AuthRule("https://api.github.com", "Authorization", f"Bearer {github}"))
    return tuple(rules)


@dataclass
class Container:
    paths: Paths
    http: HttpClient
    providers: ProviderRegistry
    settings: RuntimeSettings = field(default_factory=RuntimeSettings)


def build_container(
    *,
    paths: Paths | None = None,
    http: HttpClient | None = None,
) -> Container:
    paths = paths or Paths.default()
    settings = load_runtime_settings(paths.root)
    http = http or HttpClient(
        user_agent=USER_AGENT,
        auth_rules=_auth_rules_from_env(),
        default_timeout=settings.request_timeout,
        retries=settings.request_retries,
        cache_dir=paths.cache / "http",
    )
    return Container(
        paths=paths,
        http=http,
        providers=build_default_registry(http),
        settings=settings,
    )
