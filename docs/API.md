# OmniSource API

OmniSource publishes immutable, generated JSON snapshots for source discovery,
feed aggregation, release tracking, metadata/security verification, monitoring,
analytics, and client installation. GitHub Pages is the static API origin;
Node deployments may expose the same documents through the Next.js API routes.

OmniSource does not publish accounts, ratings, reviews, comments, social
activity, user profiles, or personalized recommendation feeds. Any ordering in
an endpoint is a deterministic field sort or a source-health/intelligence
measurement.

## URL families

| Family | Example | Compatibility |
|---|---|---|
| Root | `/apps.json` | AltStore Source v2 install feed |
| Feed | `/feeds/apps.json` | canonical generated feed |
| Client | `/feeds/clients/feather.json` | client-specific projection |
| API v2 | `/api/v2/apps.json` | legacy static snapshots |
| API v3 | `/api/v3/apps.json` | paginated, versioned snapshots |
| Intelligence | `/data/source_intelligence.json` | source/package observations |

All public documents are UTF-8 JSON and carry a schema version and generation
stamp where applicable. Gzip twins are generated for large API documents.
`api/index.json` and `api/v3/index.json` list available documents and checksums.

## Feeds

- `/apps.json` — merged AltStore-compatible Source v2 feed;
- `/feeds/clients/altstore.json`;
- `/feeds/clients/sidestore.json`;
- `/feeds/clients/feather.json`;
- `/feeds/clients/esign.json`;
- `/feeds/clients/livecontainer.json`;
- `/feeds/single/<slug>.json` — one app, if its record is verified;
- `/feeds/collections/<slug>.json` — committed source/category collection.

A feed entry includes name, bundle identifier, developer, version, version date,
description, icon, screenshots, size, download URL, source URL, release
history fields, and published SHA-256/SHA-512 values when the publisher
provides them. Missing data is explicit; it is never invented.

## API v3

| Endpoint | Purpose |
|---|---|
| `GET /api/v3` | API version and endpoint registry |
| `GET /api/v3/apps` | paginated canonical app records |
| `GET /api/v3/apps/{id}` | one app plus available versions |
| `GET /api/v3/sources` | source registry records |
| `GET /api/v3/sources/{id}` | source history, health, sync, and reputation |
| `GET /api/v3/search?q=...` | deterministic weighted metadata search |
| `GET /api/v3/releases` | append-only release timeline |
| `GET /api/v3/status` | source/feed/download availability |
| `GET /api/v3/security` | hashes, provenance, and integrity findings |
| `GET /api/v3/analytics` | daily/weekly/monthly operational rollups |

The legacy `/api/v3/trending` snapshot may remain for old clients during the
migration, but it is not linked by the website and is not a recommendation
surface. New consumers should use `/releases`, `/status`, `/analytics`, or
`/source_intelligence.json` according to their need.

### Query parameters

```text
/api/v3/apps?page=2&per_page=20&sort=-versionDate&category=music
/api/v3/apps?developer=acme
/api/v3/search?q=player&per_page=20
/api/v3/sources?status=verified&sort=-score
```

- `page` is one-based; `per_page` is clamped to 1–200;
- `sort` is a field with an optional leading `-` for descending order;
- app filters include `category`, `developer`, and `q`/`query`;
- source filters include `status`;
- search fields are name, bundle ID, developer, category, tags, description,
  and source metadata;
- search has no user or download-activity signal.

A normal response is:

```json
{
  "apiVersion": "3.0.0",
  "schemaVersion": 3,
  "feedVersion": "a1b2c3d4e5f6",
  "pagination": {"page": 1, "per_page": 50, "total": 1, "pages": 1},
  "data": [{"id": "example", "name": "Example", "version": "1.2.3"}]
}
```

## Caching and integrity

- Dynamic routes return a weak ETag; matching `If-None-Match` returns `304`.
- Responses use `public, s-maxage=300, stale-while-revalidate=3600`.
- Static manifests contain SHA-256 checksums of generated document bytes.
- `feedVersion` changes when generated document content changes.
- API consumers must treat unknown JSON keys as forward-compatible extensions.

## Operational documents

- `data/source_registry.json` — classification, lifecycle, sync, health,
  reputation, and history;
- `data/source_intelligence.json` — source quality and cadence observations;
- `data/package_intelligence.json` — package/release observations;
- `data/source_timeline.json` — append-only source/release events;
- `data/status.json` — current monitoring state;
- `data/security.json` / `security-report.json` — fail-closed security report;
- `data/analytics_rollup.json` — daily, weekly, monthly operational metrics.

These documents describe the catalog and its infrastructure. They do not
collect visitor identity or user behavior.

## Compatibility

`apps.json`, `api/v2/`, root app pages, and the static PWA remain available for
existing subscribers. Generated content must be changed through the pipeline,
not edited directly. See [API-V3.md](API-V3.md) and
[DEPLOYMENT-GUIDE.md](DEPLOYMENT-GUIDE.md).
