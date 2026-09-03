"""Minimal dependency-injection container.

No framework. The container is a dataclass constructed by :func:`build_container`
and passed into the pipeline. Tests swap ``http``, ``paths`` or ``analytics``
without patching globals.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from omnisource.analytics import AnalyticsSink, NullAnalytics
from omnisource.constants import USER_AGENT, Paths
from omnisource.http import AuthRule, HttpClient
from omnisource.providers.registry import ProviderRegistry, build_default_registry
from omnisource.search import InMemoryIndex, SearchBackend


def _auth_rules_from_env() -> tuple[AuthRule, ...]:
    """Host-scoped credentials. Tokens never attach to download URLs."""
    rules: list[AuthRule] = []
    github = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if github:
        rules.append(AuthRule("https://api.github.com", "Authorization", f"Bearer {github}"))
    gitlab = os.environ.get("GITLAB_TOKEN")
    if gitlab:
        rules.append(AuthRule("https://gitlab.com/api/", "PRIVATE-TOKEN", gitlab))
        # Self-hosted GitLab: operators can still set GITLAB_TOKEN; host matching
        # is prefix-based so only gitlab.com is covered by default. Extra hosts
        # can be added later via OMNISOURCE_GITLAB_HOST without changing call sites.
    codeberg = os.environ.get("CODEBERG_TOKEN")
    if codeberg:
        rules.append(AuthRule("https://codeberg.org/api/", "Authorization", f"token {codeberg}"))
    forgejo = os.environ.get("FORGEJO_TOKEN")
    forgejo_host = os.environ.get("FORGEJO_HOST", "").rstrip("/")
    if forgejo and forgejo_host:
        rules.append(AuthRule(f"{forgejo_host}/api/", "Authorization", f"token {forgejo}"))
    return tuple(rules)


@dataclass
class Container:
    paths: Paths
    http: HttpClient
    providers: ProviderRegistry
    analytics: AnalyticsSink
    search: SearchBackend


def build_container(
    *,
    paths: Paths | None = None,
    http: HttpClient | None = None,
    analytics: AnalyticsSink | None = None,
    search: SearchBackend | None = None,
) -> Container:
    paths = paths or Paths.default()
    http = http or HttpClient(user_agent=USER_AGENT, auth_rules=_auth_rules_from_env())
    return Container(
        paths=paths,
        http=http,
        providers=build_default_registry(http),
        analytics=analytics or NullAnalytics(),
        search=search or InMemoryIndex(),
    )
