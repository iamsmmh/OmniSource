# OmniSource platform architecture

**Date:** 2026-09-03
**Version:** 3.0
**Scope:** turn the existing AltStore feed repository into the backend
ecosystem for a future OmniStore client, without breaking any published URL.

This document is the architecture review, restructuring plan, directory
layout, domain model, migration plan and implementation roadmap in one place.
Feed and API contracts live in [FEED_SPEC.md](FEED_SPEC.md) and [API.md](API.md).

---

## 1. Architecture review

### What OmniSource is today

A curated iOS sideloading source. `catalog.json` is the only hand-edited data
file. `scripts/omnisource.py` (now a thin CLI over `src/omnisource`) resolves
GitHub Releases, probes download URLs, and publishes AltStore Source v2 feeds
to GitHub Pages. Eleven apps, four workflows, standard-library Python, no
runtime dependencies.

It already does several things a distribution platform needs:

- Declarative catalog (adding an app is data, not a new Python function)
- Idempotent builds (no wall-clock timestamps; no empty commits)
- Last-good-build degradation (a dead upstream does not delete the app)
- Token hygiene (`GH_TOKEN` never leaves `api.github.com`)
- Least-privilege GitHub Actions
- Health snapshots and a static website that consume the same artefacts
  the clients do

### What it was not

| Gap | Impact |
| --- | --- |
| GitHub-only resolver | GitLab, Codeberg, Forgejo, AltStore and Feather sources cannot be tracked without new code paths |
| No unified metadata | The only public record is the AltStore v2 schema. OmniStore would have to reverse-engineer `omnisource.*` extensions |
| No search index | The website scans `apps.json` in the browser. That does not scale to 10k apps |
| No categories / updates / featured / repositories feeds | A mobile client would parse the master AltStore feed and invent its own grouping |
| No provider interface | `sync_app()` spoke GitHub JSON directly |
| Global `Path` constants | The pipeline could not be tested against a temporary tree |
| No unit tests for the pipeline | CI proved reproducibility, not behaviour |
| Monolithic 900-line script | HTTP, catalog parsing, GitHub, health, rendering and README generation in one file |
| No API contract | Future OmniStore had nothing to code against |

A previous attempt at a FastAPI/Redis/Pydantic service was deleted because it
shared nothing with the feed pipeline except the name. This redesign inverts
that: the package **is** the pipeline. There is no parallel unused service,
no runtime server, and no new dependency in the write path.

### Technical debt addressed

| Item | Disposition |
| --- | --- |
| Monolithic `scripts/omnisource.py` | Split into `src/omnisource` (domain, providers, tracking, feeds, API, validation, pipeline). Scripts are wrappers. |
| GitHub-only upstream | Provider registry: GitHub Releases, GitHub Tags, GitLab, Codeberg, Forgejo, generic JSON / AltStore / Feather |
| Untestable globals | `Paths` and `Container` are injected |
| Duplicate HTTP probe | Shared `HttpClient.probe` (health_check.py still standalone for the daily issue reporter) |
| No SHA-256 on versions | Extracted from GitHub `digest` / changelog when present; omitted from AltStore entries when unknown so historical feeds stay stable |
| No incremental pagination | `--incremental` short-circuits when the newest matching asset URL is unchanged |
| No tests | `tests/` — unit + offline integration, run in `validate.yml` |
| No OmniStore artefacts | `feeds/omnistore/*` and `feeds/api/v1/*` |
| Analytics | Protocol + `NullAnalytics` only. No tracking is implemented. |

### Remaining (tracked, not in this change)

1. Verify SHA-256 of the IPA bytes themselves (needs a ranged hash or a
   trusted digest from upstream; GitHub's `digest` field is the first step).
2. Pin third-party Actions to commit SHAs.
3. Client-specific feed variants (LiveContainer bundle-id rewriting).
4. Screenshot pipeline for apps with empty `screenshotURLs`.
5. A live API process. The static snapshot **is** the contract; a server
   can be dropped in later without changing clients.

### Security

Unchanged invariants:

- Credentials attach only when the URL matches an `AuthRule` prefix
  (`api.github.com`, `gitlab.com/api/`, `codeberg.org/api/`, optional
  `FORGEJO_HOST/api/`). Download probes send no `Authorization`.
- `sync.yml` still runs first-party stdlib Python plus GitHub's own actions.
- `validate.yml` is read-only, credential-less, network-free except the
  pinned ruff/actionlint install.

New surface: GitLab / Codeberg / Forgejo tokens, all optional, all host-scoped.

### Scalability (10k apps, 100k releases)

| Concern | Design |
| --- | --- |
| API cost | Per-repo cache; incremental page-1 short-circuit; apps sharing a repo share one fetch |
| Feed size | AltStore `keepVersions` still caps history. OmniStore `apps.json` is one record per app (current version only). Full history stays in `state.json` |
| Search | Inverted index, ~O(tokens) query, dumpable to a single JSON file |
| Git | OmniStore + API files are generated; per-app API files are acceptable at 11 and still fine at a few thousand. At 10k a live API replaces `apps/{id}.json` with a datastore lookup — the OpenAPI contract does not change |
| Memory | Frozen dataclasses, no ORM, no in-memory copy of IPA bytes |

---

## 2. Repository restructuring plan

Executed in this change. Nothing is moved that a client URL depends on.

1. Introduce `src/omnisource/` as the pipeline package.
2. Reduce `scripts/omnisource.py` and `scripts/validate.py` to path-setup
   wrappers so `python3 scripts/omnisource.py` keeps working.
3. Keep `scripts/merge_feeds.py`, `scripts/health_check.py`,
   `scripts/validate_jq.sh` as AltStore-specific tools (they already ignore
   subdirectories).
4. Emit new artefacts under `feeds/omnistore/` and `feeds/api/v1/` — **not**
   at the repo root, so historical `/{slug}.json` URLs stay AltStore-only.
5. Add `tests/`.
6. Extend `validate.yml` with unittest + ruff over `src/` and `tests/`.
7. Scheduled `sync.yml` runs `--incremental`.

Rollback: revert the merge. Root AltStore mirrors never move.

---

## 3. Directory structure

```
OmniSource/
├── catalog.json                 hand-edited SSOT
├── apps.json, <slug>.json       generated AltStore root mirrors (historical URLs)
├── feeds/
│   ├── apps.json                AltStore master (SSOT for sideloading clients)
│   ├── <slug>.json              per-app AltStore
│   ├── health.json
│   ├── state.json               pipeline memory (not published)
│   ├── omnistore/               OmniStore machine feeds
│   │   ├── apps.json
│   │   ├── categories.json
│   │   ├── updates.json
│   │   ├── featured.json
│   │   ├── repositories.json
│   │   └── search-index.json
│   └── api/v1/                  static REST snapshots + OpenAPI
│       ├── apps.json
│       ├── apps/{id}.json
│       ├── updates.json
│       ├── categories.json
│       ├── repositories.json
│       ├── featured.json
│       ├── search.json
│       └── openapi.json
├── src/omnisource/              the pipeline (stdlib only)
│   ├── domain.py                type-safe models
│   ├── providers/               GitHub, GitLab, Codeberg, Forgejo, feeds
│   ├── tracking.py              versions, changelog, updates, assets
│   ├── feeds/                   AltStore + OmniStore renderers
│   ├── search.py                inverted index
│   ├── analytics.py             interfaces only
│   ├── assets.py                icon/screenshot/cache
│   ├── api.py                   OpenAPI + snapshots
│   ├── validation.py
│   ├── pipeline.py
│   ├── di.py                    container
│   └── http.py                  retrying client, host-scoped auth
├── scripts/                     CLI wrappers + AltStore-specific tools
├── tests/
├── schemas/                     catalog, AltStore feed, OmniStore
├── assets/  website/  docs/
└── .github/workflows/
```

---

## 4. Domain model

See `src/omnisource/domain.py`.

| Type | Role |
| --- | --- |
| `SourceType` | `github`, `github-tags`, `gitlab`, `codeberg`, `forgejo`, `json-feed`, `altstore`, `feather`, `manual` |
| `RepositoryRef` | How to reach an upstream (`repo` / `host` / `feedURL` + resolution rules) |
| `RemoteRelease` / `RemoteAsset` | Source-agnostic release. Providers produce these; nothing else speaks GitHub JSON |
| `App` / `Catalog` | Parsed `catalog.json` |
| `StandardizedApp` | Unified metadata record (the OmniStore document) |
| `UpdateEvent` | Version change detected this run |
| `SyncReport` | Job summary |

`StandardizedApp` fields (JSON names in parentheses):

`appId`, `name`, `developer`, `description`, `icon`, `screenshots`,
`category`, `version`, `buildNumber`, `releaseDate`, `bundleId`,
`minimumOSVersion`, `sourceType`, `repositoryUrl`, `changelog`,
`downloadUrl`, `sha256`.

---

## 5. Provider contract

Every provider implements:

```
validate_repository(source) -> ValidationResult
discover_apps(source)       -> list[DiscoveredApp]
fetch_metadata(source)      -> AppMetadata
fetch_releases(source)      -> list[RemoteRelease]
```

CamelCase aliases (`validateRepository`, `discoverApps`, `fetchMetadata`,
`fetchReleases`) are bound on the ABC so the platform contract names resolve.

`upstream.provider` in `catalog.json` selects the provider (default `github`).
Existing catalog entries need no change.

---

## 6. Migration plan

| Step | Effect on clients |
| --- | --- |
| 1. Land `src/omnisource` + wrappers | None. CLI flags identical. AltStore output byte-compatible on `--no-sync --no-health` |
| 2. Commit generated `feeds/omnistore/` and `feeds/api/v1/` | None. New URLs only |
| 3. Point a future OmniStore client at `feeds/api/v1/` | New client; AltStore unchanged |
| 4. (Later) live API behind the same OpenAPI paths | Swap the server URL in OmniStore. Static snapshot remains a fallback |
| 5. (Optional) retire root `{slug}.json` mirrors | **Not now.** Requires a deprecation window |

No catalog rewrite is required. Optional fields (`upstream.provider`,
`upstream.host`, `upstream.feedURL`, `tags`) are additive.

---

## 7. GitHub Actions

| Workflow | Change |
| --- | --- |
| `sync.yml` | Scheduled runs pass `--incremental`. Job summary includes a release report (from → to). Pages deploy already copies `feeds/` recursively so OmniStore + API are published |
| `validate.yml` | `unittest discover`, ruff over `src/` `scripts/` `tests/` |
| `merge.yml` | Unchanged. Globs `feeds/*.json`, ignores subdirectories |
| `health-check.yml` | Unchanged |
| `build-uyouenhanced.yml` | Unchanged |

Retry and failure recovery were already in the HTTP layer and per-app
degradation; they survive the extract.

---

## 8. Implementation roadmap

**Shipped in 3.0**

- [x] Provider architecture
- [x] Unified metadata
- [x] Release tracking (compare, changelog, update detection, asset validation)
- [x] OmniStore feeds + search index
- [x] Asset management (validate, missing, cache protocol)
- [x] Analytics interfaces
- [x] OpenAPI + static API snapshots
- [x] Tests + DI + injectable paths
- [x] Incremental sync + richer job summaries

**Next**

1. Hash-verify IPA payloads when GitHub `digest` is absent (high)
2. SHA-pin Actions (medium)
3. PR feed-diff comments (medium)
4. LiveContainer rewritten-bundle feed (medium)
5. SQLite FTS5 `SearchBackend` if the inverted JSON exceeds ~5 MB (low)
6. Live API (FastAPI or similar) implementing `docs/API.md` (when OmniStore ships)

---

## 9. What we deliberately did not do

- Did not add FastAPI, Redis, Pydantic, or any pip dependency to the write
  path. The last time that happened it became an unused second project.
- Did not put OmniStore documents at the repository root.
- Did not implement download tracking. The sink exists; it discards.
- Did not break AltStore v2, merge.yml, or historical feed URLs.
