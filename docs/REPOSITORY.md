# Repository guide

OmniSource separates hand-maintained inputs, generated distribution files, application code, and the website. This keeps routine changes small while preserving every existing source URL.

## Directory map

```text
OmniSource/
├── catalog.json              # Hand-maintained app catalog (source of truth)
├── config/                   # Pipeline settings
├── assets/                   # Source, client, and app icons
├── src/omnisource/           # Python package
│   ├── feeds/                # AltStore, RSS and updates-timeline renderers
│   ├── providers/            # GitHub and external-feed adapters
│   ├── utils/                # Shared helpers
│   ├── discovery.py          # Discovery catalog + source index
│   ├── verification.py       # Trust indicators
│   ├── monitor.py            # Source health board + probe history
│   ├── duplicates.py         # Duplicate detection
│   ├── analytics.py          # Repository-derived metrics
│   ├── trending.py           # Phase 1 trending score (recency + availability + featured + verification)
│   ├── related.py            # Phase 2 relationship graph (bundle / category / developer / tags)
│   ├── screenshots.py        # Phase 3 screenshot validation, mirror, thumbnails
│   ├── reputation.py         # Phase 6 source reputation engine
│   ├── download_intel.py     # Phase 7 download intelligence
│   ├── community.py          # Phase 13 community features
│   ├── search_index.py       # Phase 4 Fuse.js-style search index
│   ├── install.py            # Phase 9 install card generator
│   ├── compare.py            # Phase 5 side-by-side comparison engine
│   ├── api_mirror.py         # Phase 11 1:1 mirror of feeds/ → api/
│   └── app_pages.py          # Static app detail page generator
├── scripts/                  # Small command-line entry points
│   └── generate_pages.py     # Standalone app-page regeneration
├── schemas/                  # JSON schemas
├── tests/                    # Unit test suite
├── feeds/                    # Generated canonical feeds, RSS, intelligence docs, state
├── apps/<slug>/index.html    # Generated static app detail pages
├── website/                  # Static website source (dependency-free)
│   ├── index.html            # Landing page + rails (trending, featured, recent, verified, health, stats, community)
│   ├── compare.html          # Phase 5 side-by-side app comparison
│   ├── css/styles.css        # Landing page styles
│   ├── css/app-page.css      # Generated app-page styles
│   ├── css/compare.css       # Compare page styles
│   ├── js/app.js             # Landing page logic (rails, fuzzy search, SW update toast)
│   ├── js/compare.js         # Compare page logic
│   ├── manifest.webmanifest  # PWA install manifest
│   └── sw.js                 # PWA service worker (v2: per-app pages, update prompt)
├── sdk/                      # Phase 14: client SDKs
│   ├── javascript/           # ESM + CJS, no dependencies
│   └── python/               # Single-file, 3.8+, no dependencies
└── docs/                     # Project documentation
```

## What should be edited?

| Change | Edit | Then run |
| --- | --- | --- |
| Add or update an app | `catalog.json` and, when needed, `assets/` | `make build` |
| Change sync behavior | `src/omnisource/` | `make check` |
| Change the landing page | `website/` | `make site` |
| Change pipeline defaults | `config/settings.json` | `make check` |
| Change validation rules | `schemas/` or `src/omnisource/validation.py` | `make check` |

Do not hand-edit `feeds/` or the generated catalog section in `README.md`. The sync pipeline owns them.

## Generated outputs

Running the pipeline produces, under `feeds/`:

- a per-app AltStore feed (`<slug>.json`) and the master `apps.json`;
- a per-app RSS release feed (`<slug>.xml`) plus the combined `feed.xml`/`rss.xml`;
- `updates.json` — a sanitized "What's new" timeline for the website,
  derived from `state.json` update history and newest versions;
- `health.json` with per-app reachability plus `updatedDaysAgo`/`stale`
  annotations (staleness threshold: `config/settings.json` → `staleAfterDays`);
- the intelligence documents: `discovery.json` (searchable index),
  `sources.json` (upstreams + clients), `verification.json` (trust levels),
  `status.json` (health board + latency history), `duplicates.json`
  (duplicate groups + recommendations) and `analytics.json` (metrics +
  rolling snapshot history);
- Shields.io-compatible badges (`badge-*.json`) and pipeline state
  (`state.json`, never published).

It also renders one static page per app at `apps/<slug>/index.html`
(see `src/omnisource/app_pages.py`; `scripts/generate_pages.py` re-runs just
that stage). `scripts/build_site.py` copies every distributable JSON/XML,
`catalog.json`, the app pages and the machine API surface (`api/`, with
`.json.gz` twins and an `api/index.json` manifest) into the site. See
[`API.md`](API.md) for the endpoint contracts.

## How are generated artifacts published?

Generated files have canonical homes under `feeds/` (JSON/XML) and `apps/`
(pages), keeping the repository root clean. During deployment,
`scripts/build_site.py` copies them to the site root, the `feeds/` path and the
`api/` path as well. Existing subscriptions such as the following therefore
continue to work:

```text
https://iamsmmh.github.io/OmniSource/apps.json
```

This avoids duplicate tracked files without changing any public URL.

## Common commands

```bash
make build       # Sync and regenerate feeds
make check       # Lint, validate, and test
make site        # Assemble the deployable site in _site/
make serve       # Build and preview the site locally
make clean       # Remove local site output
```

The Pages workflow calls `scripts/build_site.py`, so local and production site assembly use one implementation.

## Data flow

```
                    ┌──────────────┐
                    │  catalog.json │  (hand-edited, source of truth)
                    └──────┬───────┘
                           │
              ┌────────────┼─────────────┐
              │            │             │
              ▼            ▼             ▼
        ┌─────────┐  ┌──────────┐  ┌────────────┐
        │  sync   │  │  health  │  │  validate  │
        │ (GH/    │  │  probes  │  │  (offline) │
        │  feeds) │  │          │  │            │
        └────┬────┘  └────┬─────┘  └────────────┘
             │            │
             ▼            ▼
        ┌─────────────────────┐
        │    state.json       │ (versions, health, update history)
        └────────┬────────────┘
                 │
                 ▼
        ┌─────────────────────┐
        │      build stage    │
        │  • apps.json        │  AltStore Source v2 (master)
        │  • <slug>.json      │  Per-app AltStore feeds
        │  • feed.xml, *.xml  │  RSS
        │  • discovery.json   │  Phase 0: search index
        │  • trending.json    │  Phase 1: trending score
        │  • related.json     │  Phase 2: relationship graph
        │  • screenshots.json │  Phase 3: screenshot catalog
        │  • search-index.json│  Phase 4: Fuse.js-compatible index
        │  • compare.json     │  Phase 5: side-by-side pairs
        │  • reputation.json  │  Phase 6: source reputation
        │  • download-intel…  │  Phase 7: availability / latency
        │  • install.json     │  Phase 9: install cards
        │  • community.json   │  Phase 13: community lists
        │  • apps/<slug>/     │  Static app detail pages
        └─────────┬───────────┘
                  │
        ┌─────────┴───────────┐
        ▼                     ▼
   feeds/                 api/            (1:1 mirror)
        │                     │
        └─────────┬───────────┘
                  ▼
          scripts/build_site.py
                  │
                  ▼
               _site/         (GitHub Pages deployment)

   website/ (index.html, compare.html, css/, js/, sw.js) is layered on top
   of the deployed feeds/ and api/ to render the live experience.
```

## Generation pipeline (Make targets)

| Target | What it does |
| --- | --- |
| `make build` | Runs the sync + health + build stages, writing everything under `feeds/`, `api/` and `apps/`. |
| `make site` | Calls `scripts/build_site.py` to assemble the deployable site in `_site/`. The site builder mirrors `feeds/` to the root, mirrors `feeds/` to `api/`, and copies the static `website/` files. |
| `make check` | Runs the offline validator (`scripts/validate.py`), the test suite (`pytest tests/`) and the reproducibility check. |
| `make serve` | Builds the site and serves `_site/` on a local port for development. |

The Pages workflow (`.github/workflows/sync.yml`) calls the same scripts so
local development and production are byte-identical.

## Performance budget

* Homepage render target: < 1 second on cold cache.
* Search target: < 50 ms per keystroke (in-memory fuzzy match).
* JSON size: each generated document is < 50 KB except `compare.json`
  (≈ 250 KB for the full pairwise matrix of 22 apps).
* Service worker version is bumped whenever a new feed is added, so
  existing clients pick up the new content on their next page load and
  the SW prompts the user to reload.
