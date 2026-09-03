# OmniStore API specification

OmniSource does not run an HTTP server. GitHub Pages serves a **static
snapshot** of this contract at:

```
https://iamsmmh.github.io/OmniSource/feeds/api/v1/
```

The generated OpenAPI 3.1 document is
[`feeds/api/v1/openapi.json`](../feeds/api/v1/openapi.json) (after a pipeline
run) and is produced by `omnisource.api.openapi_spec`. A future live API
(`https://api.omnistore.app/v1`) must implement the same paths and schemas.
Clients can switch by changing the server URL.

## Endpoints

| Method | Path | Static file |
| --- | --- | --- |
| `GET` | `/apps` | `feeds/api/v1/apps.json` |
| `GET` | `/apps/{id}` | `feeds/api/v1/apps/{id}.json` |
| `GET` | `/updates` | `feeds/api/v1/updates.json` |
| `GET` | `/categories` | `feeds/api/v1/categories.json` |
| `GET` | `/repositories` | `feeds/api/v1/repositories.json` |
| `GET` | `/search?q=` | `feeds/api/v1/search.json` (the index; query locally) |

`{id}` is the catalog slug (`spotiflac`, `utm`, …).

## `GET /apps`

Returns `{ schemaVersion, generatedAt, count, apps: StandardizedApp[] }`.
See [FEED_SPEC.md](FEED_SPEC.md) for the app record.

## `GET /apps/{id}`

Returns a single `StandardizedApp`. Static snapshot: `404` is a missing file.
Live API: `404` JSON `{ "error": "not_found", "id": "…" }`.

## `GET /updates`

Recent version changes (`kind: new | updated`). Empty after a no-change
rebuild.

## `GET /categories`

`{ categories: [{ id, name, appCount, apps }] }`.

## `GET /repositories`

`{ repositories: [{ url, sourceType, developer, appCount, apps }] }`.

## `GET /search`

**Static:** the inverted index (`search-index.json` shape). The client tokenises
`q` and looks up `index[token]`.

**Live (future):**

```
GET /search?q=flac&limit=25
```

```json
{
  "query": "flac",
  "hits": [
    { "appId": "spotiflac", "score": 16.0, "fields": ["name", "description"] }
  ]
}
```

## Errors (live API only)

| Status | Body |
| --- | --- |
| 404 | `{ "error": "not_found" }` |
| 400 | `{ "error": "bad_request", "detail": "…" }` |
| 429 | `{ "error": "rate_limited" }` |

The static snapshot has no error documents.

## Versioning

The path prefix `/v1` is the API version. `schemaVersion` inside each
document is the feed schema version (currently `1`). They increment
independently. Additive fields are backwards compatible; removals require
`/v2`.

## Authentication

None. All documents are public. A live API must not require a key for read
endpoints. Write endpoints (if any) are out of scope.

## CORS

GitHub Pages already serves these files to browsers. A live API must send
`Access-Control-Allow-Origin` for the OmniStore origin.

## OpenAPI (abridged)

```yaml
openapi: 3.1.0
info:
  title: OmniSource / OmniStore API
  version: 3.0.0
servers:
  - url: https://iamsmmh.github.io/OmniSource/feeds/api/v1
    description: GitHub Pages static snapshot
  - url: https://api.omnistore.app/v1
    description: Future live API (not deployed)
paths:
  /apps:
    get:
      operationId: listApps
  /apps/{id}:
    get:
      operationId: getApp
      parameters:
        - name: id
          in: path
          required: true
          schema: { type: string }
  /updates:
    get:
      operationId: listUpdates
  /categories:
    get:
      operationId: listCategories
  /repositories:
    get:
      operationId: listRepositories
  /search:
    get:
      operationId: searchApps
      parameters:
        - name: q
          in: query
          required: true
          schema: { type: string }
```

The full document is generated at build time so it cannot drift from the
snapshots.
