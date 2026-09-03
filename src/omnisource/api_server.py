"""Optional read-only HTTP API for OmniSource static catalog data.

The sync pipeline and GitHub Pages remain useful without this process. This
module is a dependency-free development/reference server implementing the
``/api/v1`` contract with pagination, filters, ETags, cache headers, and safe
input handling. It never exposes environment variables or filesystem paths.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

from omnisource.constants import API_VERSION
from omnisource.io import read_json
from omnisource.search import InMemoryIndex, SearchDocument

_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,63}$")
_ALLOWED_METHODS = {"GET", "HEAD"}


@dataclass(frozen=True)
class ApiResponse:
    status: int
    headers: dict[str, str]
    body: bytes


class CatalogApi:
    """Read-only catalog handler backed by generated JSON snapshots."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.omnistore = self.root / "feeds" / "omnistore"
        self.api_snapshot = self.root / "feeds" / "api" / API_VERSION
        self._load()

    def _load(self) -> None:
        self.apps_doc = _read_first(self.omnistore / "apps.json", self.api_snapshot / "apps.json") or {"apps": []}
        self.apps = [item for item in self.apps_doc.get("apps", []) if isinstance(item, dict)]
        self.by_id = {
            str(item.get("id") or item.get("appId")): item for item in self.apps if item.get("id") or item.get("appId")
        }
        self.documents = [
            SearchDocument(
                app_id=str(app.get("id") or app.get("appId")),
                name=str(app.get("name") or ""),
                developer=str(app.get("developer") or ""),
                category=str(app.get("category") or ""),
                description=str(app.get("description") or ""),
                tags=tuple(str(tag) for tag in app.get("tags", []) if tag),
                bundle_id=str(app.get("bundleId") or ""),
                package_name=str(app.get("packageName") or ""),
                repository=str(app.get("repository") or app.get("repositoryUrl") or ""),
                aliases=tuple(str(alias) for alias in app.get("aliases", []) if alias),
            )
            for app in self.apps
        ]
        self.search_index = InMemoryIndex()
        self.search_index.index(self.documents)

    def handle(self, method: str, request_path: str, request_headers: dict[str, str] | None = None) -> ApiResponse:
        if method.upper() not in _ALLOWED_METHODS:
            return self._error(405, "method_not_allowed", "Only GET and HEAD are supported.")
        headers = {key.lower(): value for key, value in (request_headers or {}).items()}
        parsed = urlsplit(request_path)
        route = _strip_prefix(parsed.path)
        query = parse_qs(parsed.query, keep_blank_values=True)
        try:
            document, max_age = self._dispatch(route, query)
        except BadRequest as error:
            return self._error(400, "bad_request", str(error))
        except NotFound as error:
            return self._error(404, "not_found", str(error))
        payload = json.dumps(document, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        etag = f'"{hashlib.sha256(payload).hexdigest()}"'
        response_headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Content-Length": str(len(payload)),
            "Cache-Control": f"public, max-age={max_age}",
            "ETag": etag,
            "Vary": "Accept-Encoding",
        }
        if headers.get("if-none-match") == etag:
            return ApiResponse(304, {"ETag": etag, "Cache-Control": response_headers["Cache-Control"]}, b"")
        return ApiResponse(200, response_headers, b"" if method.upper() == "HEAD" else payload)

    def _dispatch(self, route: str, query: dict[str, list[str]]) -> tuple[dict[str, Any], int]:
        route = route.rstrip("/") or "/"
        if route == "/apps":
            return self._list_apps(query), 300
        if route.startswith("/apps/"):
            parts = route.split("/")
            if len(parts) == 3:
                return self._get_app(parts[2]), 300
            if len(parts) == 4 and parts[3] == "releases":
                return self._get_releases(parts[2], query), 300
            raise NotFound("unknown application route")
        if route == "/updates":
            return self._snapshot("updates", {"updates": []}), 60
        if route == "/categories":
            return self._snapshot("categories", {"categories": []}), 900
        if route == "/repositories":
            return self._snapshot("repositories", {"repositories": []}), 300
        if route == "/search":
            return self._search(query), 300
        if route == "/health":
            return self._snapshot("health", self._derived_health()), 60
        if route in {"/featured", "/trending", "/recent"}:
            return self._snapshot(route[1:], {"apps": []}), 300
        if route in {"/", ""}:
            return {
                "apiVersion": API_VERSION,
                "endpoints": ["apps", "updates", "categories", "repositories", "search", "health"],
            }, 300
        raise NotFound("unknown endpoint")

    def _list_apps(self, query: dict[str, list[str]]) -> dict[str, Any]:
        apps = list(self.apps)
        category = _one(query, "category")
        status = _one(query, "status")
        platform = _one(query, "platform")
        if category:
            apps = [app for app in apps if category in app.get("categories", [app.get("category")])]
        if status:
            apps = [app for app in apps if app.get("status") == status]
        if platform:
            apps = [app for app in apps if platform in app.get("platforms", [])]
        sort = _one(query, "sort", "name")
        if sort not in {"name", "releaseDate", "updated", "version"}:
            raise BadRequest("sort must be name, releaseDate, updated, or version")
        field = {"releaseDate": "latestReleaseDate", "updated": "lastUpdated"}.get(sort, sort)
        reverse = _one(query, "order", "asc").lower() == "desc"
        if _one(query, "order", "asc").lower() not in {"asc", "desc"}:
            raise BadRequest("order must be asc or desc")
        apps.sort(key=lambda app: str(app.get(field) or "").casefold(), reverse=reverse)
        page, page_size = _pagination(query)
        start = (page - 1) * page_size
        selected = apps[start : start + page_size]
        return {
            "schemaVersion": self.apps_doc.get("schemaVersion", 1),
            "generatedAt": self.apps_doc.get("generatedAt", ""),
            "count": len(selected),
            "total": len(apps),
            "page": page,
            "pageSize": page_size,
            "apps": selected,
        }

    def _get_app(self, app_id: str) -> dict[str, Any]:
        _validate_id(app_id)
        try:
            return self.by_id[app_id]
        except KeyError as error:
            raise NotFound(f"application '{app_id}' was not found") from error

    def _get_releases(self, app_id: str, query: dict[str, list[str]]) -> dict[str, Any]:
        app = self._get_app(app_id)
        releases = app.get("versions", [])
        if not isinstance(releases, list):
            releases = []
        page, page_size = _pagination(query)
        start = (page - 1) * page_size
        selected = releases[start : start + page_size]
        return {
            "schemaVersion": 1,
            "appId": app_id,
            "count": len(selected),
            "total": len(releases),
            "page": page,
            "pageSize": page_size,
            "releases": selected,
        }

    def _search(self, query: dict[str, list[str]]) -> dict[str, Any]:
        text = _one(query, "q")
        if not text:
            raise BadRequest("q is required")
        limit = _limit(query, 25)
        hits = self.search_index.search(text, limit=limit)
        return {
            "schemaVersion": 1,
            "query": text,
            "count": len(hits),
            "hits": [{"appId": hit.app_id, "score": hit.score, "fields": list(hit.fields)} for hit in hits],
        }

    def _snapshot(self, name: str, fallback: dict[str, Any]) -> dict[str, Any]:
        document = _read_first(self.omnistore / f"{name}.json", self.api_snapshot / f"{name}.json")
        return document if isinstance(document, dict) else fallback

    def _derived_health(self) -> dict[str, Any]:
        broken = [
            app
            for app in self.apps
            if app.get("status") == "broken" or not app.get("health", {}).get("downloadReachable", True)
        ]
        return {
            "schemaVersion": 1,
            "generatedAt": self.apps_doc.get("generatedAt", ""),
            "totals": {"apps": len(self.apps), "reachable": len(self.apps) - len(broken), "unreachable": len(broken)},
        }

    def _error(self, status: int, code: str, detail: str) -> ApiResponse:
        payload = json.dumps({"error": code, "detail": detail}, separators=(",", ":")).encode("utf-8")
        return ApiResponse(
            status,
            {
                "Content-Type": "application/json; charset=utf-8",
                "Content-Length": str(len(payload)),
                "Cache-Control": "no-store",
            },
            payload,
        )


class BadRequest(ValueError):
    pass


class NotFound(LookupError):
    pass


def create_server(root: Path, *, host: str = "0.0.0.0", port: int = 8000) -> ThreadingHTTPServer:  # noqa: S104
    api = CatalogApi(root)

    class Handler(BaseHTTPRequestHandler):
        server_version = "OmniSourceAPI/1"

        def _respond(self) -> None:
            response = api.handle(self.command, self.path, dict(self.headers.items()))
            self.send_response(response.status)
            for key, value in response.headers.items():
                self.send_header(key, value)
            self.end_headers()
            if response.body:
                self.wfile.write(response.body)

        def do_GET(self) -> None:
            self._respond()

        def do_HEAD(self) -> None:
            self._respond()

        def log_message(self, format: str, *args: object) -> None:
            return None

    return ThreadingHTTPServer((host, port), Handler)


def serve(root: Path | None = None, *, host: str = "0.0.0.0", port: int = 8000) -> None:  # noqa: S104
    server = create_server(root or Path.cwd(), host=host, port=port)
    try:
        server.serve_forever()
    finally:
        server.server_close()


def _strip_prefix(path: str) -> str:
    for prefix in (f"/api/{API_VERSION}", f"/feeds/api/{API_VERSION}"):
        if path == prefix or path.startswith(prefix + "/"):
            return path[len(prefix) :] or "/"
    return path


def _read_first(*paths: Path) -> Any:
    for path in paths:
        value = read_json(path)
        if value is not None:
            return value
    return None


def _one(query: dict[str, list[str]], key: str, default: str = "") -> str:
    values = query.get(key, [])
    return values[0].strip() if values else default


def _limit(query: dict[str, list[str]], default: int) -> int:
    raw = _one(query, "limit", str(default))
    try:
        value = int(raw)
    except ValueError as error:
        raise BadRequest("limit must be an integer") from error
    if not 1 <= value <= 100:
        raise BadRequest("limit must be between 1 and 100")
    return value


def _pagination(query: dict[str, list[str]]) -> tuple[int, int]:
    raw_page = _one(query, "page", "1")
    raw_size = _one(query, "pageSize", _one(query, "limit", "50"))
    try:
        page, size = int(raw_page), int(raw_size)
    except ValueError as error:
        raise BadRequest("page and pageSize must be integers") from error
    if page < 1 or not 1 <= size <= 100:
        raise BadRequest("page must be >= 1 and pageSize must be between 1 and 100")
    return page, size


def _validate_id(app_id: str) -> None:
    if not _ID_RE.fullmatch(app_id):
        raise BadRequest("id must be a lowercase catalog id")
