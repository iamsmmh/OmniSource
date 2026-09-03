"""Static API snapshots + OpenAPI 3.1 specification.

OmniSource does not run a server. GitHub Pages serves the documents under
``feeds/api/v1/`` which map 1:1 onto the REST contract the future OmniStore
client will call. When a real API is stood up, it must implement this spec.
"""

from __future__ import annotations

from typing import Any

from omnisource.constants import API_VERSION, OMNISTORE_SCHEMA_VERSION, PLATFORM_VERSION
from omnisource.domain import Catalog, StandardizedApp, UpdateEvent
from omnisource.feeds.omnistore import (
    render_apps,
    render_categories,
    render_featured,
    render_repositories,
    render_updates,
    standardize_app,
)
from omnisource.search import build_search_index


def openapi_spec(*, base_url: str) -> dict[str, Any]:
    """OpenAPI 3.1 document describing the OmniStore HTTP contract."""
    api_root = f"{base_url.rstrip('/')}/feeds/api/{API_VERSION}"
    app_schema = {
        "type": "object",
        "required": [
            "appId",
            "name",
            "developer",
            "description",
            "icon",
            "version",
            "bundleId",
            "sourceType",
            "downloadUrl",
        ],
        "additionalProperties": True,
        "properties": {
            "appId": {"type": "string"},
            "name": {"type": "string"},
            "developer": {"type": "string"},
            "description": {"type": "string"},
            "icon": {"type": "string", "format": "uri"},
            "screenshots": {"type": "array", "items": {"type": "string", "format": "uri"}},
            "category": {"type": "string"},
            "version": {"type": "string"},
            "buildNumber": {"type": ["string", "null"]},
            "releaseDate": {"type": "string"},
            "bundleId": {"type": "string"},
            "minimumOSVersion": {"type": "string"},
            "sourceType": {
                "type": "string",
                "enum": [
                    "github",
                    "github-tags",
                    "gitlab",
                    "codeberg",
                    "forgejo",
                    "json-feed",
                    "altstore",
                    "feather",
                    "manual",
                ],
            },
            "repositoryUrl": {"type": "string", "format": "uri"},
            "changelog": {"type": "string"},
            "downloadUrl": {"type": "string", "format": "uri"},
            "sha256": {"type": ["string", "null"], "pattern": "^[0-9a-fA-F]{64}$"},
            "size": {"type": "integer", "minimum": 0},
            "status": {"type": "string"},
            "featured": {"type": "boolean"},
            "tags": {"type": "array", "items": {"type": "string"}},
        },
    }
    return {
        "openapi": "3.1.0",
        "info": {
            "title": "OmniSource / OmniStore API",
            "version": PLATFORM_VERSION,
            "summary": "Application catalog, updates, search and repository metadata.",
            "description": (
                "Static snapshot of the OmniStore HTTP contract. Served from GitHub Pages "
                f"at `{api_root}`. A future live API must keep these paths and schemas."
            ),
            "license": {"name": "GPL-3.0", "identifier": "GPL-3.0-only"},
        },
        "servers": [
            {"url": api_root, "description": "GitHub Pages static snapshot"},
            {"url": f"https://api.omnistore.app/{API_VERSION}", "description": "Future live API (not deployed)"},
        ],
        "tags": [
            {"name": "apps"},
            {"name": "updates"},
            {"name": "categories"},
            {"name": "repositories"},
            {"name": "search"},
        ],
        "paths": {
            "/apps": {
                "get": {
                    "tags": ["apps"],
                    "summary": "List all applications",
                    "operationId": "listApps",
                    "responses": {
                        "200": {
                            "description": "Catalog listing",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/AppList"},
                                }
                            },
                        }
                    },
                }
            },
            "/apps/{id}": {
                "get": {
                    "tags": ["apps"],
                    "summary": "Get one application by id (slug)",
                    "operationId": "getApp",
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                            "description": "App slug (catalog.json `slug`).",
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Application record",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/App"}}},
                        },
                        "404": {"description": "Unknown app id"},
                    },
                }
            },
            "/updates": {
                "get": {
                    "tags": ["updates"],
                    "summary": "Recent version changes",
                    "operationId": "listUpdates",
                    "responses": {
                        "200": {
                            "description": "Update feed",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/UpdateList"}}},
                        }
                    },
                }
            },
            "/categories": {
                "get": {
                    "tags": ["categories"],
                    "summary": "List categories",
                    "operationId": "listCategories",
                    "responses": {
                        "200": {
                            "description": "Category index",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/CategoryList"}}},
                        }
                    },
                }
            },
            "/repositories": {
                "get": {
                    "tags": ["repositories"],
                    "summary": "List tracked upstream repositories",
                    "operationId": "listRepositories",
                    "responses": {
                        "200": {
                            "description": "Repository index",
                            "content": {
                                "application/json": {"schema": {"$ref": "#/components/schemas/RepositoryList"}}
                            },
                        }
                    },
                }
            },
            "/search": {
                "get": {
                    "tags": ["search"],
                    "summary": "Search the catalog",
                    "description": (
                        "The static snapshot is the inverted index itself "
                        "(`search-index.json`). Clients query locally. A live API "
                        "would accept `q` and return hits."
                    ),
                    "operationId": "searchApps",
                    "parameters": [
                        {
                            "name": "q",
                            "in": "query",
                            "required": True,
                            "schema": {"type": "string"},
                            "description": "Free-text query over name, developer, category, description, tags.",
                        },
                        {
                            "name": "limit",
                            "in": "query",
                            "schema": {"type": "integer", "minimum": 1, "maximum": 100, "default": 25},
                        },
                    ],
                    "responses": {
                        "200": {
                            "description": "Search index (static) or hit list (live)",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/SearchIndex"}}},
                        }
                    },
                }
            },
        },
        "components": {
            "schemas": {
                "App": app_schema,
                "AppList": {
                    "type": "object",
                    "required": ["schemaVersion", "apps"],
                    "properties": {
                        "schemaVersion": {"type": "integer", "const": OMNISTORE_SCHEMA_VERSION},
                        "generatedAt": {"type": "string"},
                        "count": {"type": "integer"},
                        "apps": {"type": "array", "items": {"$ref": "#/components/schemas/App"}},
                    },
                },
                "Update": {
                    "type": "object",
                    "required": ["appId", "version", "kind"],
                    "properties": {
                        "appId": {"type": "string"},
                        "name": {"type": "string"},
                        "version": {"type": "string"},
                        "previousVersion": {"type": ["string", "null"]},
                        "releaseDate": {"type": "string"},
                        "downloadUrl": {"type": "string", "format": "uri"},
                        "changelog": {"type": "string"},
                        "kind": {"type": "string", "enum": ["new", "updated"]},
                    },
                },
                "UpdateList": {
                    "type": "object",
                    "properties": {
                        "schemaVersion": {"type": "integer"},
                        "generatedAt": {"type": "string"},
                        "count": {"type": "integer"},
                        "updates": {"type": "array", "items": {"$ref": "#/components/schemas/Update"}},
                    },
                },
                "CategoryList": {"type": "object", "additionalProperties": True},
                "RepositoryList": {"type": "object", "additionalProperties": True},
                "SearchIndex": {"type": "object", "additionalProperties": True},
            }
        },
    }


def render_api_bundle(
    catalog: Catalog,
    *,
    versions_by_slug: dict[str, list[dict[str, Any]]],
    updates: list[UpdateEvent],
) -> dict[str, Any]:
    """Filename (relative to ``feeds/api/v1/``) → document.

    Per-app files live under ``apps/<id>.json``. At 10k apps this is still
    well within Git's comfort zone; a live API would replace them with a
    single datastore lookup.
    """
    standardized: list[StandardizedApp] = []
    for app in catalog.apps:
        versions = versions_by_slug.get(app.slug)
        if not versions:
            continue
        standardized.append(standardize_app(catalog, app, versions))

    generated_at = max((app.release_date for app in standardized if app.release_date), default="")
    listing = render_apps(standardized)
    bundle: dict[str, Any] = {
        "apps.json": listing,
        "updates.json": render_updates(updates, generated_at=generated_at),
        "categories.json": render_categories(standardized),
        "repositories.json": render_repositories(standardized),
        "featured.json": render_featured(standardized),
        "search.json": build_search_index(standardized) | {"generatedAt": generated_at},
        "openapi.json": openapi_spec(base_url=catalog.base_url),
    }
    for app in standardized:
        bundle[f"apps/{app.app_id}.json"] = app.to_json()
    return bundle
