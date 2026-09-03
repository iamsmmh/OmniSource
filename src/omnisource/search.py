"""Search index for OmniStore clients.

Builds an inverted index over app name, developer, category, description and
tags. The on-disk form (``feeds/omnistore/search-index.json``) is designed so
a mobile client can download it once and query locally. The
:class:`SearchBackend` protocol is the seam for a future full-text engine
(SQLite FTS5, Typesense, …).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from omnisource.domain import StandardizedApp

TOKEN_RE = re.compile(r"[a-z0-9]+")
STOPWORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "for",
        "from",
        "in",
        "of",
        "on",
        "or",
        "the",
        "to",
        "with",
    }
)


def tokenize(text: str) -> list[str]:
    return [token for token in TOKEN_RE.findall(text.lower()) if token not in STOPWORDS and len(token) > 1]


@dataclass(frozen=True)
class SearchDocument:
    app_id: str
    name: str
    developer: str
    category: str
    description: str
    tags: tuple[str, ...]
    bundle_id: str = ""
    package_name: str = ""
    repository: str = ""
    aliases: tuple[str, ...] = ()

    @classmethod
    def from_app(cls, app: StandardizedApp) -> SearchDocument:
        return cls(
            app_id=app.app_id,
            name=app.name,
            developer=app.developer,
            category=app.category,
            description=app.description,
            tags=app.tags,
            bundle_id=app.bundle_id,
            package_name=app.package_name or "",
            repository=app.repository_url,
            aliases=app.aliases,
        )

    def field_tokens(self) -> dict[str, list[str]]:
        return {
            "name": tokenize(self.name),
            "developer": tokenize(self.developer),
            "category": tokenize(self.category),
            "description": tokenize(self.description[:1_500]),
            "tags": tokenize(" ".join(self.tags)),
            "bundle": tokenize(self.bundle_id.replace(".", " ")),
            "package": tokenize(self.package_name.replace(".", " ")),
            "repository": tokenize(self.repository.replace("/", " ").replace(".", " ")),
            "aliases": tokenize(" ".join(self.aliases)),
        }


@dataclass(frozen=True)
class SearchHit:
    app_id: str
    score: float
    fields: tuple[str, ...]


@runtime_checkable
class SearchBackend(Protocol):
    def index(self, documents: list[SearchDocument]) -> None: ...
    def search(self, query: str, *, limit: int = 25) -> list[SearchHit]: ...
    def dump(self) -> dict[str, Any]: ...


# Field weights bias name/developer matches over description noise.
_WEIGHTS = {
    "name": 8.0,
    "developer": 5.0,
    "category": 3.0,
    "tags": 4.0,
    "aliases": 6.0,
    "bundle": 2.0,
    "package": 2.0,
    "repository": 2.0,
    "description": 1.0,
}


@dataclass
class InMemoryIndex:
    """Inverted index with weighted term frequency. Suitable for 10k+ apps."""

    documents: dict[str, SearchDocument] = field(default_factory=dict)
    # token -> field -> {app_id: tf}
    postings: dict[str, dict[str, dict[str, int]]] = field(default_factory=dict)

    def index(self, documents: list[SearchDocument]) -> None:
        self.documents = {}
        self.postings = {}
        for document in documents:
            self.documents[document.app_id] = document
            for field_name, tokens in document.field_tokens().items():
                for token in tokens:
                    fields = self.postings.setdefault(token, {})
                    apps = fields.setdefault(field_name, {})
                    apps[document.app_id] = apps.get(document.app_id, 0) + 1

    def search(self, query: str, *, limit: int = 25) -> list[SearchHit]:
        tokens = tokenize(query)
        if not tokens:
            return []
        scores: dict[str, float] = {}
        matched_fields: dict[str, set[str]] = {}
        for token in tokens:
            # Prefix expansion keeps the index local and makes queries such as
            # ``spot`` find ``spotiflac`` without a server-side fuzzy engine.
            matching_tokens = [term for term in self.postings if term == token or term.startswith(token)]
            for matched_token in matching_tokens:
                fields = self.postings[matched_token]
                prefix_factor = 1.0 if matched_token == token else 0.75
                for field_name, apps in fields.items():
                    weight = _WEIGHTS.get(field_name, 1.0) * prefix_factor
                    for app_id, tf in apps.items():
                        scores[app_id] = scores.get(app_id, 0.0) + weight * tf
                        matched_fields.setdefault(app_id, set()).add(field_name)
        ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))[:limit]
        return [
            SearchHit(app_id=app_id, score=score, fields=tuple(sorted(matched_fields.get(app_id, ()))))
            for app_id, score in ranked
        ]

    def dump(self) -> dict[str, Any]:
        """Serialise a compact, client-friendly index.

        ``index`` maps each token to the app ids that contain it. ``documents``
        carry the display fields a client needs to render results without a
        second round-trip. Designed to stay well under a few MB at 10k apps.
        """
        inverted: dict[str, list[str]] = {}
        for token, fields in self.postings.items():
            ids: set[str] = set()
            for apps in fields.values():
                ids.update(apps)
            inverted[token] = sorted(ids)
        return {
            "schemaVersion": 1,
            "documentCount": len(self.documents),
            "tokenCount": len(inverted),
            "documents": [
                {
                    "appId": doc.app_id,
                    "name": doc.name,
                    "developer": doc.developer,
                    "category": doc.category,
                    "tags": list(doc.tags),
                    "aliases": list(doc.aliases),
                    "bundleId": doc.bundle_id,
                    "packageName": doc.package_name,
                    "repository": doc.repository,
                }
                for doc in sorted(self.documents.values(), key=lambda item: item.app_id)
            ],
            "index": dict(sorted(inverted.items())),
        }


def build_search_index(apps: list[StandardizedApp]) -> dict[str, Any]:
    backend = InMemoryIndex()
    backend.index([SearchDocument.from_app(app) for app in apps])
    return backend.dump()
