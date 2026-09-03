# Implementation roadmap

See [PLATFORM.md](PLATFORM.md) for the architecture. This page is the
ordered work list.

## Shipped (3.0)

- Modular source providers (GitHub Releases/Tags, GitLab, Codeberg, Forgejo, JSON/AltStore/Feather)
- Unified metadata (`StandardizedApp`) independent of AltStore
- Release tracking: version compare, changelog extract, update detection, asset validation
- OmniStore feeds: apps, categories, updates, featured, repositories, search-index
- Static API snapshots + generated OpenAPI 3.1
- Search inverted index with a `SearchBackend` seam for future FTS
- Asset management: icon magic-bytes, screenshot URL shape, missing/unused, directory cache
- Analytics interfaces (`AnalyticsSink` / `NullAnalytics`) — no tracking
- Injectable `Paths` + `Container` (dependency injection without a framework)
- Unit and offline integration tests in CI
- Incremental sync (`--incremental`) on the 6-hour schedule
- Job summaries with a from → to release report

## Next, in priority order

| # | Item | Why | Effort |
| --- | --- | --- | --- |
| 1 | Hash-verify IPA payloads when GitHub `digest` is absent | Highest remaining supply-chain control | M |
| 2 | Pin Actions to commit SHAs | Tag hijack resistance | S |
| 3 | PR comment with a rendered feed diff when `catalog.json` changes | Review quality | S |
| 4 | LiveContainer rewritten-bundle feed (`feeds/livecontainer/apps.json`) | Five YouTube mods cannot coexist otherwise | M |
| 5 | Historical version archive `feeds/archive/{slug}.json` | Rollback after a bad upstream | M |
| 6 | Screenshot pipeline for apps with empty `screenshotURLs` | OmniStore app pages look bare | M |
| 7 | SQLite FTS5 `SearchBackend` if `search-index.json` exceeds ~5 MB | 10k-app full-text | M |
| 8 | Live API implementing [API.md](API.md) | OmniStore needs query/search with low latency | L |
| 9 | Download / update-adoption counters behind `AnalyticsSink` | Only after OmniStore ships and with an explicit opt-in | L |

Nothing in this list is required for AltStore clients to keep working.
