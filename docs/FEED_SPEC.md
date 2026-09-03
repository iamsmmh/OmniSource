# Feed specification

OmniSource publishes two families of machine-readable feeds. They share a
catalog but not a schema.

| Family | Clients | Root | Format |
| --- | --- | --- | --- |
| AltStore Source v2 | AltStore, SideStore, Feather, ESign, LiveContainer | `/apps.json`, `/{slug}.json`, `/feeds/*.json` | AltStore v2 (+ `omnisource` extension) |
| OmniStore | Future OmniStore app, any HTTP client | `/feeds/omnistore/*.json` | Unified metadata, this document |

JSON Schema: [`schemas/feed.schema.json`](../schemas/feed.schema.json) (AltStore),
[`schemas/omnistore.schema.json`](../schemas/omnistore.schema.json) (OmniStore).

`generatedAt` is derived from content (the newest `releaseDate` /
`statusSince`), never from wall-clock time, so a no-change rebuild is a
no-op.

---

## AltStore v2 (unchanged)

Documented by AltStore and by [`schemas/feed.schema.json`](../schemas/feed.schema.json).
OmniSource additions (`omnisource`, `fallbackDownloadURLs`) are ignored by
clients that do not understand them. Flat fields (`version`, `versionDate`,
`downloadURL`, `size`) always mirror `versions[0]`.

Published at:

- `https://iamsmmh.github.io/OmniSource/apps.json`
- `https://iamsmmh.github.io/OmniSource/feeds/apps.json` (byte-identical)
- `https://iamsmmh.github.io/OmniSource/{slug}.json`

---

## OmniStore feeds

All documents share:

```json
{
  "schemaVersion": 1,
  "generatedAt": "2026-09-01",
  "count": 11
}
```

### `feeds/omnistore/apps.json`

One record per catalog app, current version only. History lives in the
AltStore `versions[]` array and in `feeds/state.json`.

```json
{
  "schemaVersion": 1,
  "generatedAt": "2026-09-01",
  "count": 1,
  "apps": [
    {
      "appId": "spotiflac",
      "name": "SpotiFLAC Mobile",
      "developer": "zarzet",
      "description": "…",
      "icon": "https://iamsmmh.github.io/OmniSource/assets/SpotiFLAC.png",
      "screenshots": [],
      "category": "utilities",
      "version": "4.9.5",
      "buildNumber": null,
      "releaseDate": "2026-09-01",
      "bundleId": "com.zarzet.spotiflac",
      "minimumOSVersion": "16.0",
      "sourceType": "github",
      "repositoryUrl": "https://github.com/spotiflacapp/SpotiFLAC-Mobile",
      "changelog": "…",
      "downloadUrl": "https://github.com/…/SpotiFLAC-v4.9.5-ios-unsigned.ipa",
      "sha256": null,
      "size": 34122124,
      "status": "stable",
      "featured": true,
      "tags": ["utilities"],
      "fallbackDownloadUrls": []
    }
  ]
}
```

`sourceType` is one of `github`, `github-tags`, `gitlab`, `codeberg`,
`forgejo`, `json-feed`, `altstore`, `feather`, `manual`.

`sha256` is a 64-char hex digest when known (GitHub asset `digest`, or a
SHA-256 found in the release body). It is `null` otherwise — OmniSource does
not invent checksums.

### `feeds/omnistore/categories.json`

```json
{
  "categories": [
    {
      "id": "utilities",
      "name": "Utilities",
      "appCount": 2,
      "apps": ["spotiflac", "utm"]
    }
  ]
}
```

### `feeds/omnistore/featured.json`

Subset of `apps.json` where `featured: true`. Same app schema.

### `feeds/omnistore/updates.json`

Version changes detected by the most recent **sync** that actually observed a
difference. `--no-sync` rebuilds produce `updates: []` (idempotent). Kind is
`new` or `updated`; unchanged apps are omitted.

```json
{
  "updates": [
    {
      "appId": "spotiflac",
      "name": "SpotiFLAC Mobile",
      "version": "4.9.5",
      "previousVersion": "4.9.0",
      "releaseDate": "2026-09-01",
      "downloadUrl": "https://…",
      "changelog": "…",
      "kind": "updated"
    }
  ]
}
```

### `feeds/omnistore/repositories.json`

One row per unique `repositoryUrl`, with the slugs that track it. Five YouTube
mods sharing `mrdrvt99/YouProEXTRA` collapse to one repository with
`appCount: 5`.

### `feeds/omnistore/search-index.json`

Inverted index over name, developer, category, description, tags and bundle
id. Tokens are lowercase `[a-z0-9]+`, stopwords dropped.

```json
{
  "schemaVersion": 1,
  "documentCount": 11,
  "tokenCount": 180,
  "documents": [{ "appId": "utm", "name": "UTM", "developer": "UTM Team", "category": "utilities", "tags": ["utilities"], "bundleId": "com.utmapp.UTM" }],
  "index": { "utm": ["utm"], "virtual": ["utm"] }
}
```

A mobile client downloads this file once and queries locally. A live API
would accept `GET /search?q=` and run the same `InMemoryIndex` (or a future
FTS5 backend) on the server.

---

## Size budget

| File | 11 apps | ~10k apps (est.) |
| --- | --- | --- |
| AltStore `apps.json` | ~90 KB | keep per-app feeds; split the master or page it |
| OmniStore `apps.json` | small (one record / app, current version) | ~5–15 MB depending on changelog length |
| `search-index.json` | small | a few MB; switch to SQLite FTS5 past ~5 MB |

Changelogs in OmniStore `apps.json` are the current version's notes, not the
full history.
