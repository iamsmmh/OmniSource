# OmniSource Architecture

OmniSource is a **metadata intelligence platform** that curates sideloaded iOS apps from upstream sources and publishes them through a GitHub Pages-backed API and web app.

```
                         ┌──────────────────────────────┐
                         │       catalog.json (hand)     │
                         │  77 apps · sources · config   │
                         └──────────────┬───────────────┘
                                        │
                         ┌──────────────▼───────────────┐
                         │      Python Pipeline         │
                         │   src/omnisource/ (stdlib)   │
                         │                              │
                         │  ┌────────────────────────┐  │
                         │  │ sync (GitHub/feed/…)    │  │
                         │  │ health (probe URLs)     │  │
                         │  │ build (render feeds)    │  │
                         │  └────────┬───────────────┘  │
                         │           │                  │
                         │  ┌────────▼───────────────┐  │
                         │  │ intelligence engines:   │  │
                         │  │  analytics, trending,   │  │
                         │  │  related, reputation,   │  │
                         │  │  verification, trust,   │  │
                         │  │  health, duplicates,    │  │
                         │  │  dead-apps, discovery,  │  │
                         │  │  search-index, compare  │  │
                         │  └────────┬───────────────┘  │
                         └───────────┼──────────────────┘
                                     │
                    ┌────────────────┼─────────────────┐
                    │                │                 │
             ┌──────▼─────┐   ┌──────▼─────┐   ┌──────▼──────┐
             │ feeds/*.json│   │ apps/<slug>/│   │ api/v2/*.json
             │ feeds/*.xml │   │  index.html│   │             │
             └──────┬──────┘   └──────┬─────┘   └──────┬──────┘
                    │                │                │
                    └────────────────┼────────────────┘
                                     │
                         ┌───────────▼──────────────────┐
                         │     GitHub Pages (static)    │
                         │  ┌────────────────────────┐  │
                         │  │   Application shell    │  │
                         │  │  index.html, compare/, │  │
                         │  │  discover/, graph/,    │  │
                         │  │  status/, analytics/   │  │
                         │  └────────┬───────────────┘  │
                         │           │                  │
                         │  ┌────────▼───────────────┐  │
                         │  │  src/js/ Engines        │  │
                         │  │  ┌──────────────────┐   │  │
                         │  │  │ Data Layer       │   │  │
                         │  │  │  (single cache)  │   │  │
                         │  │  └────┬───┬───┬─────┘   │  │
                         │  │       │   │   │         │  │
                         │  │  ┌────▼─┐ │ ┌─▼──────┐  │  │
                         │  │  │Search│ │ │Compare │  │  │
                         │  │  └──────┘ │ └────────┘  │  │
                         │  │  ┌────▼─────┐ ┌────────┐│  │
                         │  │  │Recommend│ │Trust   ││  │
                         │  │  └──────────┘ └────────┘│  │
                         │  └────────────────────────┘  │
                         │                              │
                         │  Service Worker v11          │
                         │  ┌────────────────────────┐  │
                         │  │ Network-first: APIs    │  │
                         │  │ Cache-first: assets    │  │
                         │  │ SWR: metadata          │  │
                         │  └────────────────────────┘  │
                         └──────────────────────────────┘
                                     │
                   ┌─────────────────┼─────────────────┐
                   ▼                 ▼                 ▼
             ┌──────────┐     ┌────────────┐    ┌──────────────┐
             │ Website  │     │ OmniStore  │    │ Third-party  │
             │  (PWA)   │     │ iOS/Android│    │ integrations │
             └──────────┘     └────────────┘    └──────────────┘
```

## Pipeline Flow

1. **Sync** — Resolve newest releases from GitHub releases, AltStore feeds, Gitea/GitLab registries, and direct URLs. Uses failover chains so dead mirrors don't kill an app.
2. **Health** — Concurrently probe every download URL, record latency and reachability.
3. **Build** — Render AltStore v2 feeds, per-app JSON/XML, RSS, and all intelligence documents
   (reputation emits `Verified / Community Verified / Maintained / Warning / Inactive /
   Deprecated` from six weighted signals; `feeds/sources.json` joins health, verification and
   reputation so `sources/<slug>/index.html` pages and the /sources/ explorer render from one
   document).
4. **Validate** — Unit tests, JSON schema checks, reproducible-build check, jq lint.
5. **Publish** — Mirror canonical feeds to flat URLs and the v1/v2 API surface, write
   sitemap/robots/homepage stats, refresh the generated page trees (`apps/`, `collections/`,
   `sources/`), the static fallback table in `sources/index.html`, and the `docs/index.html`
   hub (rendered from the Markdown on disk).
6. **Deploy** — GitHub Actions assembles `_site/` and deploys to Pages.

## Data Contracts

### v1 API (stable, preserved)

| Path | Description |
|---|---|
| `/feeds/apps.json` | Installable AltStore source |
| `/feeds/discovery.json` | Searchable catalog |
| `/feeds/trending.json` | Trending/rising/recent |
| `/feeds/health.json` | Per-app download health |
| `/feeds/verification.json` | Verification + trust |
| `/feeds/related.json` | Relationship graph input |
| `/feeds/compare.json` | App summaries + bundle pairs (v2: slimmed) |
| `/feeds/analytics.json` | Metrics + history |
| `/feeds/status.json` | Source health board |
| `/feeds/sources.json` | Source index + Source Explorer roll-up (v2: `slug`, `page`, `status`, `score`, `healthScore`, `appCount`, `verifiedApps`, `updateFrequencyDays`, `lastUpdate`, per-source `statuses` map) |
| `/feeds/collections.json` | Curated collections |

### v2 API (new, for OmniStore)

| Path | Description |
|---|---|
| `/api/v2/apps.json` | Full discovery catalog |
| `/api/v2/sources.json` | Sources with health/reputation |
| `/api/v2/trending.json` | Trending scores |
| `/api/v2/recommendations.json` | Per-app related + alternatives |
| `/api/v2/status.json` | Uptime/latency/pipeline |
| `/api/v2/trust.json` | Trust/security/maintenance scores |
| `/api/v2/graph.json` | Nodes + edges (app/dev/source/bundle) |
| `/api/v2/index.json` | Manifest |

## Frontend Engines

All engines live under `src/js/` and have no dependencies on each other beyond the data layer:

```
data-layer.js  ──►  search-engine.js
           ├──►  compare-engine.js
           ├──►  recommendation-engine.js
           └──►  trust-score.js

router.js  ──►  (dispatches to pages)
```

- **data-layer.js** — Fetches, caches, and normalizes every API doc; exposes `OmniData.ready()`, `getApp(slug)`, `getApps()`, `getCompareMatrix()`.
- **search-engine.js** — Fuzzy, typo-tolerant search with alias map (e.g. "yt" → YouTube family, "spotify" → SpotiFLAC/Spotube). Returns scored results.
- **compare-engine.js** — Builds a side-by-side matrix on demand: calculates per-dimension scores (verification 30%, health 25%, recency 20%, maintenance 15%, compatibility 10%) and generates a recommendation summary.
- **recommendation-engine.js** — Related apps (shared category/developer/source/tags/bundle), alternatives (same category, different dev), and "also from" lists. Augments server-side `related.json`.
- **trust-score.js** — Composite 0–100 score with letter-grade security (A+–F) and maintenance labels (Excellent/Good/Fair/Neglected/Unmaintained).
- **router.js** — Lightweight History-API router for deep links like `/compare?app1=x&app2=y`.

### Module layer (`js/modules/`)

ES modules added by the modernization pass; they are the canonical home for
all *new* client logic (the legacy scripts above keep their contracts so
existing pages and bookmarks never break). Rules: named exports only, no
`window` writes, no build step — pages reference them with
`<script type="module">`.

```
utils.js ── esc / fetchJSON / countUp / translate / localize
   ├── search.js    fuzzy core: bigram Dice + capped Levenshtein, field weights
   ├── status.js    reputation statuses → badge classes, score formatting
   ├── theme.js     light/dark/auto (defers to core.js when that has the button)
   ├── store.js     localStorage contract shared with features.js (favorites)
   ├── sources.js   /sources/ controller (Phase 4): search + filters + stats
   ├── favorites.js favorites read/toggle for module pages
   ├── analytics.js /analytics/ progressive enhancement (sparklines)
   ├── compare.js   ?left=&right= URL contract + winner marking
   ├── install.js   per-client install URLs + copy helper
   ├── collections.js collection-card hydration fallback
   └── pwa.js       service-worker status reporting
```

## Caching Strategy (Service Worker v11)

| Strategy | Used for |
|---|---|
| **Network-first** | API endpoints (`/api/v2/*`, `/api/*.json`) — freshest data wins |
| **Cache-first** | Images, icons, fonts, CSS, JS — instant loads, background refresh |
| **Stale-while-revalidate** | Metadata feeds (discovery, compare, health) — instant paint, silent refresh |
| **Network-first navigation** | HTML pages — fall back to cached shell offline |

## Future-ready

The architecture is designed so additional clients (OmniStore iOS/Android/Web, third-party integrations) only need to consume the v2 API surface. The Python pipeline stays stdlib-only and deterministic; the frontend stays zero-build-step. Engines are plain scripts with no module bundler, so they run directly in any browser.

## Autonomous extensions (3.2.0)

The 3.2.0 modernization adds an autonomous operations layer around the
unchanged core pipeline. Every extension is additive, scheduled, and
documented; `catalog.json` → `feeds/` → Pages remains the only path to users.

```
discovery.yml (12h) ──▶ data/discovered_sources.json ──▶ validation gate ──▶ catalog.json (human)
sync.yml (6h) ──▶ feeds/ ──▶ publish.yml ──▶ data/* + feeds/clients/* + api/v3/*
monitoring.yml (30m) ──▶ data/status.json + data/selfheal_report.json + data/mirror_status.json
security.yml ──▶ data/security.json (fails closed) │ analytics.yml ──▶ data/analytics_rollup.json
website.yml ──▶ web/ (Next.js 15 + TS + Tailwind PWA, dynamic /api/v3/*)
```

| Module family | Key modules |
|---|---|
| Discovery | `omnisource.autodiscovery` + `scripts/discovery/*` |
| Validation | `omnisource.remote_validation` + `scripts/validation/*` |
| Dedup / history | `omnisource.canonical`, `omnisource.release_history` |
| Reputation | `omnisource.reputation` (scores) + `reputation_labels` (public ladder) |
| Monitoring | `omnisource.probes` + `scripts/monitoring/*` |
| Enrichment | `omnisource.enrichment` |
| Security | `omnisource.security` + `scripts/security/scan.py` |
| Search | `omnisource.search` (+ `web/src/lib/search.ts` twin, `src/js/search-engine.js`) |
| Self-heal / mirrors | `omnisource.selfheal`, `omnisource.mirrors` |
| API v3 | `omnisource.api_v3` (+ static `api/v3/`, dynamic `web/` routes) |
| Client feeds | `omnisource.feeds.clients` → `feeds/clients/*.json` |
| Scale-out fetch | `omnisource.async_http` (asyncio + optional aiohttp) |

See `docs/MODERNIZATION.md` (delivery index), `audit-report.md`,
`docs/OPERATIONS.md`, `docs/API-V3.md` and `docs/DISCOVERY.md`.
