# Repository audit

*Date:* 2026-09-09 · *Scope:* full repository (`main` @ `dd1a82c` + working
branch) · *Method:* static analysis of scripts, workflows, schemas, tests,
generated feeds, website, README.

Gold rule observed while auditing: `catalog.json` is the only hand-maintained
data file; everything under `feeds/`, `apps/`, `api/` and the generated README
blocks is produced by the pipeline. **Nothing in this audit changes that**, and
all recommendations below are already implemented in the current branch.

---

## 1. Existing features

| Area | Status | Notes |
| --- | --- | --- |
| AltStore Source v2 feeds | ✅ | Per-app `feeds/<slug>.json` + master `feeds/apps.json`, `omnisource` extension block |
| Clients | ✅ | AltStore, SideStore, Feather, ESign, LiveContainer; deep links + copy fallback |
| Upstream providers | ✅ | GitHub Releases, GitHub Tags, JSON/AltStore/Feather feeds; host-scoped auth |
| Scheduled sync | ✅ | 6-hourly, incremental when scheduled, on-push full sync, manual `workflow_dispatch` |
| Download health | ✅ | Concurrent HEAD probes, mirrors, daily job, GitHub issue reporting |
| RSS/Atom | ✅ | Combined + per-app feeds, sanitized `updates.json` timeline |
| State persistence | ✅ | `state.json` (version history, update history, health), no DB |
| Validation | ✅ | `validation.py` + jq structural lint, reproducibility check, ruff, actionlint |
| PWA website | ✅ | Dark/light/system theme, searchable catalog, filters, sort, dialog, SW cache |
| Release builds | ✅ | Manual uYouEnhanced compile/inject/publish workflow |
| Notifications | ✅ | Discord/Telegram/ntfy/OmniSource webhooks on version changes |
| Assets | ✅ | Icons served from `assets/`; catalog → asset reference validation |

## 2. Missing features (pre-audit) → now implemented

| Feature | File |
| --- | --- |
| Searchable discovery catalog (auto-generated) | `src/omnisource/discovery.py` → `feeds/discovery.json` |
| Source index / API `sources.json` | `src/omnisource/discovery.py` → `feeds/sources.json` |
| Trust indicators (VERIFIED / COMMUNITY VERIFIED / UNVERIFIED) | `src/omnisource/verification.py` |
| Health monitoring board + per-source latency history | `src/omnisource/monitor.py` → `feeds/status.json` |
| Duplicate detection with recommendations | `src/omnisource/duplicates.py` |
| Metrics (weekly changes, dead links, verified counts, trends) | `src/omnisource/analytics.py` |
| Static app detail pages | `src/omnisource/app_pages.py` → `apps/<slug>/index.html` |
| Machine API surface (`api/`, gzip twins, manifest) | `scripts/build_site.py` |
| Homepage stats from feeds (total apps/sources, sync time, verified) | `website/js/site.js` + `feeds/analytics.json` |
| Most-downloaded sort + tag/verification search | `website/js/site.js` |
| README live badges + stats block | `src/omnisource/pipeline.py` (`stage_readme`) |
| Workflow matrix + caching | `.github/workflows/validate.yml`, `sync.yml` |

## 3. Duplicate logic

* Fixed: `scripts/health_check.py`, `scripts/merge_feeds.py` and
  `src/omnisource/constants.py` each maintained their own list of
  “non-feed JSON files”. The lists now share the same 12 names
  (`ALTSTORE_NON_FEED` is the single source; the standalone scripts keep
  explicit local copies so they stay runnable without importing the package).
* Remaining (intentional): `health_check.py` implements its own probe loop
  alongside `src/omnisource/http.py::probe`. The standalone script stays
  dependency-free so the daily health job can run without the full pipeline;
  both use the same `ALIVE_CODES`/`RETRYABLE_CODES` constants.

## 4. Dead code / not exercised

* `Catalog.platforms`, `StandardizedApp` and the discovery/provider
  `discover_apps()` paths are library surface for future apps — not dead, but
  untested end-to-end.
* The generated AltStore `assets[]` array and `downloads`/`digest` fields are
  additive and clients ignore them; they feed the discovery catalog.

## 5. Performance

* Sync: parallel workers (configurable), per-repo HTTP cache, incremental
  pagination skip, stdlib-only (no install step, no lock drift).
* Website: single static page, `loading="lazy"` images, SW stale-while-
  revalidate, search is an in-memory filter over < 100 entries (< 100 ms);
  API consumers can use `.json.gz` twins.
* GitHub Actions: validation split into parallel jobs (structural gate, unit
  test matrix 3.11/3.12, lint); pip cache; provider metadata cache persisted
  between sync runs.
* **Known limitation:** GitHub Pages serves pre-built `.gz` as
  `application/gzip`, so browsers cannot transparently decompress them; they
  are offered to API clients, while the website uses the plain JSON.

## 6. Reliability risks

| Risk | Mitigation |
| --- | --- |
| Upstream outage | last-known-good versions kept in `state.json`; `status.json` marks `unavailable`; broken links are reported via an issue |
| Concurrent writes to `feeds/` | sync `concurrency` group; atomic writes with rollback (`io.atomic_write_many`) |
| Stale apps | `health.json` staleness annotation + `degraded` status |
| Duplicate bundles replacing apps on-device | validator warning, `duplicates.json` + website banners |
| Reproducibility drift | validate job rebuilds from catalog and fails on diff |
| RSS `lastBuildDate` churn | pre-existing; XML is excluded from the reproducibility check (`scripts/check_reproducible.py`), which normalizes date-stamped fields so a PR opened days after a build still passes |
| Rate limits | unauthenticated fallback warning; incremental mode limits pagination |

## 7. Security concerns

* Tokens are host-scoped (`AuthRule`) and never attached to third-party IPA
  download URLs; health probes construct header dicts without `Authorization`.
* Validator and jq lint run offline and read-only; workflows use least
  privilege (`permissions: {}` then opt-in), no secrets needed for sync.
* Workflow inputs are passed via environment, never interpolated into
  shell — the `build-uyouenhanced.yml` workflow documents this explicitly.
* Noted for the future: `screenshots` are third-party URLs rendered in HTML
  (escaped); content is validated as HTTP(S) before use.

## 8. What was deliberately not changed

* The hand-maintained `catalog.json` stays the source of truth (the new
  auto-generated `discovery.json` is a *different* document and is published as
  `api/catalog.json`, so the request “never manually maintain catalog.json”
  applies to the discovery index).
* Flat historical URLs (`/<slug>.json`) keep working.
* AltStore v2 JSON byte structure is untouched apart from additive fields.
* stdlib-only runtime is preserved; `asyncio`/`aiohttp` were not introduced
  because the ThreadPoolExecutor + retry/backoff HTTP client already satisfies
  the parallel-fetch/retry/timeout/rate-limit requirements without adding a
  third-party dependency to the release pipeline.

## 3. Discovery v2 additions

The discovery engine is now a full ecosystem: trending, related apps,
reputation, download intelligence, install cards, screenshots, search
index, community lists and side-by-side comparison. The full set of
generated documents is listed in `docs/API.md`.

| Phase | New module | Generated artifact |
| --- | --- | --- |
| 1 | `src/omnisource/trending.py` | `feeds/trending.json` |
| 2 | `src/omnisource/related.py` | `feeds/related.json` |
| 3 | `src/omnisource/screenshots.py` | `feeds/screenshots.json` + `assets/screenshots/` |
| 4 | `src/omnisource/search_index.py` | `feeds/search-index.json` (Fuse.js compatible) |
| 5 | `src/omnisource/compare.py` | `feeds/compare.json` |
| 6 | `src/omnisource/reputation.py` | `feeds/reputation.json` |
| 7 | `src/omnisource/download_intel.py` | `feeds/download-intelligence.json` |
| 9 | `src/omnisource/install.py` | `feeds/install.json` |
| 11 | `src/omnisource/api_mirror.py` | `api/*.json` |
| 13 | `src/omnisource/community.py` | `feeds/community.json` |
| 14 | `sdk/javascript/`, `sdk/python/` | Zero-dependency client libraries |

## 4. Website v2

The static website gained seven new sections, an instant fuzzy search
popover and a side-by-side comparison page:

* **Trending / Featured / Recently Updated / Verified** — horizontal
  rails with skeleton placeholders.
* **Source Health** — reputation grid with TRUSTED / RELIABLE / AVERAGE
  / EXPERIMENTAL badges.
* **Statistics** — metric grid with availability, response time and
  mirror count.
* **Community** — popular apps, recently added, rising apps.
* **Search popover** — Fuse.js-style fuzzy search with verified /
  community filter chips, keyboard navigation, and result highlighting.
* **compare/** — full side-by-side comparison page driven entirely
  by `feeds/compare.json` (root `compare.html` remains as a redirect shim).
* **PWA v3** — `sw.js` pre-caches the whole site (all section pages +
  design system), serves JSON feeds stale-while-revalidate, caches per-app
  pages on first visit, and prompts the user to reload on a new service
  worker.

## 5. Validation enhancements

* `validate_generated_docs` now covers every new intelligence document.
  Critical errors (missing `id`, malformed score, out-of-range
  reputation, missing install cards) fail the CI run; minor issues
  (empty tag list, missing publisher) emit a warning.
* Icon / screenshot existence is enforced by the assets inspector; the
  validator no longer lets a broken `icon` slip through.
* Bundle-identifier collisions are still a warning, not an error,
  because the YouTube / YouTube Music overlap is deliberate and
  documented.
