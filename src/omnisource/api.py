"""Static API snapshots and the versioned OmniStore API contract."""

from __future__ import annotations

from typing import Any

from omnisource.config import Category, Curation
from omnisource.constants import API_VERSION, OMNISTORE_SCHEMA_VERSION, PLATFORM_VERSION
from omnisource.domain import Catalog, StandardizedApp, UpdateEvent
from omnisource.feeds.omnistore import (
    render_apps,
    render_categories,
    render_featured,
    render_health,
    render_recent,
    render_repositories,
    render_trending,
    render_updates,
    standardize_app,
)
from omnisource.search import build_search_index


def _query_parameter(
    name: str, description: str, *, default: Any = None, required: bool = False, kind: str = "string"
) -> dict[str, Any]:
    parameter: dict[str, Any] = {
        "name": name,
        "in": "query",
        "required": required,
        "description": description,
        "schema": {"type": kind},
    }
    if default is not None:
        parameter["schema"]["default"] = default
    return parameter


def _json_response(description: str, schema: str, *, errors: list[str] | None = None) -> dict[str, Any]:
    responses: dict[str, Any] = {
        "200": {
            "description": description,
            "headers": {
                "ETag": {"schema": {"type": "string"}, "description": "Content hash for conditional requests."},
                "Cache-Control": {"schema": {"type": "string"}},
            },
            "content": {"application/json": {"schema": {"$ref": f"#/components/schemas/{schema}"}}},
        }
    }
    for status in errors or []:
        responses[status] = {
            "description": "Request failed",
            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Error"}}},
        }
    return responses


def openapi_spec(*, base_url: str) -> dict[str, Any]:
    """Return an OpenAPI 3.1 document for the read-only public API."""
    api_root = f"{base_url.rstrip('/')}/feeds/api/{API_VERSION}"
    app_schema = {
        "type": "object",
        "required": [
            "id",
            "name",
            "developer",
            "description",
            "shortDescription",
            "icon",
            "screenshots",
            "category",
            "categories",
            "tags",
            "platforms",
            "latestVersion",
            "latestReleaseDate",
            "downloadAssets",
            "versions",
            "status",
            "verified",
            "lastUpdated",
        ],
        "additionalProperties": True,
        "properties": {
            "id": {"type": "string"},
            "appId": {"type": "string"},
            "name": {"type": "string"},
            "developer": {"type": "string"},
            "description": {"type": "string"},
            "shortDescription": {"type": "string"},
            "icon": {"type": ["string", "null"], "format": "uri"},
            "screenshots": {"type": "array", "items": {"type": "string", "format": "uri"}},
            "category": {"type": "string"},
            "categories": {"type": "array", "items": {"type": "string"}},
            "tags": {"type": "array", "items": {"type": "string"}},
            "repository": {"type": ["string", "null"], "format": "uri"},
            "sourceType": {"type": "string"},
            "homepage": {"type": ["string", "null"], "format": "uri"},
            "documentation": {"type": ["string", "null"], "format": "uri"},
            "license": {"type": ["string", "null"]},
            "platforms": {"type": "array", "items": {"type": "string"}},
            "bundleId": {"type": ["string", "null"]},
            "packageName": {"type": ["string", "null"]},
            "minimumIOSVersion": {"type": ["string", "null"]},
            "minimumAndroidVersion": {"type": ["string", "null"]},
            "latestVersion": {"type": "string"},
            "latestBuild": {"type": ["string", "null"]},
            "latestReleaseDate": {"type": "string"},
            "latestReleaseNotes": {"type": "string"},
            "downloadAssets": {"type": "array", "items": {"$ref": "#/components/schemas/Asset"}},
            "versions": {"type": "array", "items": {"$ref": "#/components/schemas/Release"}},
            "status": {
                "type": "string",
                "enum": ["active", "maintenance", "inactive", "archived", "broken", "unknown"],
            },
            "featured": {"type": "boolean"},
            "verified": {"type": "boolean"},
            "lastUpdated": {"type": "string"},
            "health": {"type": "object"},
            "integrity": {"type": "object"},
        },
    }
    pagination = [
        _query_parameter("page", "One-based page number.", default=1, kind="integer"),
        _query_parameter("pageSize", "Maximum records per page (1-100).", default=50, kind="integer"),
        _query_parameter("category", "Filter by category id."),
        _query_parameter("status", "Filter by lifecycle status."),
        _query_parameter("platform", "Filter by platform."),
        _query_parameter("sort", "Sort field: name, releaseDate, or updated.", default="name"),
        _query_parameter("order", "Sort order: asc or desc.", default="asc"),
    ]
    return {
        "openapi": "3.1.0",
        "info": {
            "title": "OmniSource / OmniStore API",
            "version": PLATFORM_VERSION,
            "summary": "Read-only application catalog, releases, updates, search, and source diagnostics.",
            "description": (
                "The public API is read-only. GitHub Pages serves a static snapshot at "
                f"`{api_root}`; a live deployment may use the same contract. "
                "ETag and Cache-Control headers are required for live responses."
            ),
            "license": {"name": "GPL-3.0", "identifier": "GPL-3.0-only"},
        },
        "servers": [{"url": api_root, "description": "Static GitHub Pages snapshot"}],
        "tags": [
            {"name": "apps"},
            {"name": "releases"},
            {"name": "updates"},
            {"name": "categories"},
            {"name": "repositories"},
            {"name": "search"},
            {"name": "health"},
        ],
        "paths": {
            "/apps": {
                "get": {
                    "tags": ["apps"],
                    "summary": "List applications",
                    "operationId": "listApps",
                    "parameters": pagination,
                    "responses": _json_response("Paginated application catalog", "AppList", errors=["400"]),
                }
            },
            "/apps/{id}": {
                "get": {
                    "tags": ["apps"],
                    "summary": "Get one application",
                    "operationId": "getApp",
                    "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}],
                    "responses": _json_response("Application record", "App", errors=["404"]),
                }
            },
            "/apps/{id}/releases": {
                "get": {
                    "tags": ["releases"],
                    "summary": "List releases for an application",
                    "operationId": "listAppReleases",
                    "parameters": [
                        {"name": "id", "in": "path", "required": True, "schema": {"type": "string"}},
                        _query_parameter("page", "One-based page number.", default=1, kind="integer"),
                        _query_parameter("pageSize", "Maximum records per page (1-100).", default=50, kind="integer"),
                    ],
                    "responses": _json_response("Paginated release history", "ReleaseList", errors=["404"]),
                }
            },
            "/updates": {
                "get": {
                    "tags": ["updates"],
                    "summary": "List detected application updates",
                    "operationId": "listUpdates",
                    "parameters": pagination[:2],
                    "responses": _json_response("Update index", "UpdateList"),
                }
            },
            "/categories": {
                "get": {
                    "tags": ["categories"],
                    "summary": "List categories",
                    "operationId": "listCategories",
                    "responses": _json_response("Category index", "CategoryList"),
                }
            },
            "/repositories": {
                "get": {
                    "tags": ["repositories"],
                    "summary": "List monitored repositories and diagnostics",
                    "operationId": "listRepositories",
                    "responses": _json_response("Repository registry", "RepositoryList"),
                }
            },
            "/search": {
                "get": {
                    "tags": ["search"],
                    "summary": "Search applications",
                    "operationId": "searchApps",
                    "parameters": [
                        _query_parameter("q", "Case-insensitive prefix query.", required=True),
                        _query_parameter("limit", "Maximum hits (1-100).", default=25, kind="integer"),
                    ],
                    "responses": _json_response("Search hits or static search index", "SearchResponse", errors=["400"]),
                }
            },
            "/health": {
                "get": {
                    "tags": ["health"],
                    "summary": "Catalog and synchronization health",
                    "operationId": "getHealth",
                    "responses": _json_response("Health report", "HealthResponse"),
                }
            },
            "/featured": {
                "get": {
                    "tags": ["apps"],
                    "summary": "Featured applications",
                    "operationId": "listFeatured",
                    "responses": _json_response("Featured apps", "AppList"),
                }
            },
            "/trending": {
                "get": {
                    "tags": ["apps"],
                    "summary": "Observable release activity",
                    "operationId": "listTrending",
                    "responses": _json_response("Activity feed", "ActivityList"),
                }
            },
            "/recent": {
                "get": {
                    "tags": ["apps"],
                    "summary": "Recently released applications",
                    "operationId": "listRecent",
                    "responses": _json_response("Recent feed", "ActivityList"),
                }
            },
        },
        "components": {
            "schemas": {
                "App": app_schema,
                "AppList": {
                    "type": "object",
                    "required": ["schemaVersion", "count", "apps"],
                    "properties": {
                        "schemaVersion": {"type": "integer", "const": OMNISTORE_SCHEMA_VERSION},
                        "generatedAt": {"type": "string"},
                        "count": {"type": "integer"},
                        "total": {"type": "integer"},
                        "page": {"type": "integer"},
                        "pageSize": {"type": "integer"},
                        "apps": {"type": "array", "items": {"$ref": "#/components/schemas/App"}},
                    },
                },
                "Asset": {
                    "type": "object",
                    "required": ["filename", "downloadUrl", "platform", "fileType", "size", "sha256"],
                    "properties": {
                        "filename": {"type": "string"},
                        "downloadUrl": {"type": "string", "format": "uri"},
                        "platform": {"type": "string"},
                        "architecture": {"type": ["string", "null"]},
                        "fileType": {"type": "string"},
                        "size": {"type": ["integer", "null"]},
                        "sha256": {"type": ["string", "null"]},
                        "mimeType": {"type": ["string", "null"]},
                        "installable": {"type": "boolean"},
                    },
                },
                "Release": {
                    "type": "object",
                    "required": [
                        "version",
                        "build",
                        "releaseDate",
                        "releaseNotes",
                        "releaseUrl",
                        "assets",
                        "source",
                        "isPrerelease",
                        "isDraft",
                    ],
                    "properties": {
                        "version": {"type": "string"},
                        "build": {"type": ["string", "null"]},
                        "releaseDate": {"type": "string"},
                        "releaseNotes": {"type": "string"},
                        "releaseUrl": {"type": ["string", "null"], "format": "uri"},
                        "assets": {"type": "array", "items": {"$ref": "#/components/schemas/Asset"}},
                        "source": {"type": "string"},
                        "isPrerelease": {"type": "boolean"},
                        "isDraft": {"type": "boolean"},
                    },
                },
                "ReleaseList": {"type": "object", "additionalProperties": True},
                "UpdateList": {"type": "object", "additionalProperties": True},
                "CategoryList": {"type": "object", "additionalProperties": True},
                "RepositoryList": {"type": "object", "additionalProperties": True},
                "SearchResponse": {"type": "object", "additionalProperties": True},
                "HealthResponse": {"type": "object", "additionalProperties": True},
                "ActivityList": {"type": "object", "additionalProperties": True},
                "Error": {
                    "type": "object",
                    "required": ["error"],
                    "properties": {"error": {"type": "string"}, "detail": {"type": "string"}},
                },
            }
        },
    }


def render_api_bundle(
    catalog: Catalog,
    *,
    versions_by_slug: dict[str, list[dict[str, Any]]],
    updates: list[UpdateEvent],
    state_by_slug: dict[str, dict[str, Any]] | None = None,
    repository_registry: dict[str, Any] | None = None,
    curation: Curation | None = None,
    categories: tuple[Category, ...] = (),
    update_history: list[UpdateEvent] | None = None,
) -> dict[str, Any]:
    """Return filename → static API document for ``feeds/api/v1``."""
    state_by_slug = state_by_slug or {}
    standardized: list[StandardizedApp] = [
        standardize_app(
            catalog,
            app,
            versions,
            state_entry=state_by_slug.get(app.slug),
            health=(state_by_slug.get(app.slug) or {}).get("health"),
            repository=_repository_for_app(repository_registry, app.slug),
            curation=curation,
        )
        for app in catalog.apps
        if (versions := versions_by_slug.get(app.slug))
    ]
    generated_at = max((app.release_date for app in standardized if app.release_date), default="")
    bundle: dict[str, Any] = {
        "apps.json": render_apps(standardized),
        "updates.json": render_updates(updates, generated_at=generated_at, history=update_history),
        "categories.json": render_categories(standardized, definitions=categories),
        "repositories.json": render_repositories(standardized, registry=repository_registry),
        "featured.json": render_featured(standardized, curation=curation),
        "trending.json": render_trending(standardized),
        "recent.json": render_recent(standardized),
        "health.json": render_health(standardized),
        "search.json": build_search_index(standardized) | {"generatedAt": generated_at},
        "openapi.json": openapi_spec(base_url=catalog.base_url),
    }
    for app in standardized:
        bundle[f"apps/{app.app_id}.json"] = app.to_json()
        bundle[f"apps/{app.app_id}/releases.json"] = {
            "schemaVersion": 1,
            "appId": app.app_id,
            "count": len(app.releases),
            "releases": list(app.releases),
        }
    return bundle


def _repository_for_app(registry: dict[str, Any] | None, app_id: str) -> dict[str, Any] | None:
    if not registry:
        return None
    for item in registry.get("repositories", []):
        if isinstance(item, dict) and app_id in item.get("applicationIds", []):
            return item
    return None
