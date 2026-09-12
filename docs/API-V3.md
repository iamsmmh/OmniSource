# OmniSource API v3

Versioned, paginated, cache-friendly REST for OmniStore Pro clients and
third-party integrators. Served two ways:

1. **Static** — pre-rendered `api/v3/*.json` (181 documents, rebuilt by
   `publish.yml` via `scripts/build_api_v3.py`). Works from GitHub Pages.
2. **Dynamic** — `web/src/app/api/v3/[...route]/route.ts` (Next.js).
   Full query semantics. Works on any Node host.

Both share the envelope and the pure helpers in
`src/omnisource/api_v3.py` (unit-tested in `tests/test_api_v3.py`).

## Endpoints

| Endpoint | Description |
|---|---|
| `GET /api/v3` or `/api/v3/index.json` | Registry + `feedVersion` (compare to skip refresh) |
| `GET /api/v3/apps` | Paginated app catalog |
| `GET /api/v3/apps/{id}` | One normalized app record + versions |
| `GET /api/v3/sources` | Upstream sources |
| `GET /api/v3/sources/{id}` | One source record |
| `GET /api/v3/trending` | Trending / rising / recently updated |
| `GET /api/v3/search?q=…` | Ranked search results |
| `GET /api/v3/status` | Health board snapshot |
| `GET /api/v3/security` | Security posture snapshot |
| `GET /api/v3/analytics` | Live totals + rollup windows |
| `GET /api/v3/releases` | Sequenced release timeline |

## Query semantics (dynamic routes)

```
GET /api/v3/apps?page=2&per_page=20&sort=-versionDate&category=Games&q=youtube
GET /api/v3/apps?developer=acme&sort=name
GET /api/v3/sources?status=verified&sort=-score
GET /api/v3/search?q=trollstore
```

- **Pagination** — `page` (1-based), `per_page` (1–200, default 50).
  Response carries `pagination: {page, per_page, total, pages}`.
- **Sorting** — `sort=field` / `sort=-field`. Apps: `name` (default),
  `version`, `versionDate`, `category`, `developerName`, `size`.
  Sources: `source`, `score` (default `-score`).
- **Filtering** — exact (`category`, `status`) and substring
  (`developer`, `q`/`query`) matches; search uses the fuzzy ranker.
- **Envelope** — `{apiVersion: "3.0.0", schemaVersion: 3, feedVersion?,
  pagination?, data}`. Errors: `{error: "not_found"}` + HTTP 404.

## Caching & freshness

- `ETag: W/"…"` on every response; `If-None-Match` → `304`.
- `Cache-Control: public, s-maxage=300, stale-while-revalidate=3600`.
- Compression: Next.js negotiates gzip/brotli automatically.
- Static snapshots carry per-document SHA-256 in `index.json`
  (`checksums`) for conditional refresh without HTTP ETags.
- `feedVersion` (12 hex chars) changes if and only if content changed.

## Examples

```bash
# First page of Games, newest first
curl "https://HOST/api/v3/apps?category=Games&sort=-versionDate&per_page=5"

# Conditional refresh (empty 304 when unchanged)
ETAG=$(curl -sI "https://HOST/api/v3/apps" | grep -i etag | awk '{print $2}' | tr -d '\r')
curl -H "If-None-Match: $ETAG" -o /dev/null -w "%{http_code}\n" "https://HOST/api/v3/apps"

# Static snapshot from GitHub Pages
curl "https://iamsmmh.github.io/OmniSource/api/v3/index.json"
```

## Relationship to v2

v2 (`api/v2/`, delta-sync oriented) is unchanged and supported alongside
v3. New integrations should use v3. Both are generated from the same
`feeds/` source of truth; neither is hand-edited.
