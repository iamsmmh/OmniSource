# Repository audit — Phase 1

*Date:* 2026-09-10 · *Scope:* full repository (`main` @ `01a8f61`, branch
`arena/01a08a43-omnisource`) · *Method:* static analysis of the Python
package, scripts, workflows, schemas, tests, generated feeds, website, SDKs
and docs; automated scan for orphaned scripts, unused imports, unused
templates/assets, obsolete workflows and unreachable code paths.

Supersedes the 2026-09-09 audit. Nothing in this audit changed any code —
it is the report that precedes the production-upgrade phases (2–18).

> **Gold rule (unchanged):** `catalog.json` is the only hand-maintained data
> file. Everything under `feeds/`, `apps/`, `compare/*/`, `collections/*/`
> (generated curated pages), the API mirror, `snapshots/` and the generated
> README blocks is produced by the pipeline and never hand-edited.

---

## 1. Dependency map

The **runtime** (feed generation, validation, site assembly) is deliberately
**Python 3.11+ standard library only** — no `pip install` in CI, no lockfile
drift, no third-party code executing with a write-scoped token.

```text
                    ┌─────────────────────────────┐
                    │  Entry points (stdlib-only) │
                    ├─────────────────────────────┤
 scripts/omnisource.py ──► omnisource.cli ──► omnisource.pipeline
 scripts/build_site.py  ──► omnisource.site
 scripts/validate.py    ──► omnisource.validation
 scripts/smoke_test.py  ──► (self-contained, http.server)
 scripts/health_check.py ─► (self-contained, stdlib)
 scripts/merge_feeds.py  ──► (self-contained, stdlib)
 scripts/check_reproducible.py ─► (self-contained, stdlib)
 scripts/notify.py      ──► omnisource.notify
                              │
                              ▼
            ┌────────────────────────────────────────────┐
            │            omnisource (src/)               │
            │ pipeline ─► providers ─► http              │
            │          ─► tracking ─► utils.versioning   │
            │          ─► domain, di, config, constants  │
            │          ─► feeds/{altstore,rss,updates}   │
            │          ─► intelligence modules (below)   │
            ├────────────────────────────────────────────┤
            │ Intelligence modules (pure functions):     │
            │ discovery · verification · monitor ·       │
            │ duplicates · analytics · trending ·        │
            │ related · reputation · download_intel ·    │
            │ community · install · search_index ·       │
            │ compare · screenshots · app_pages ·        │
            │ notify (webhooks, urllib)                  │
            └────────────────────────────────────────────┘

 Website (browser, no build step)
   index.html, compare/, status/, analytics/, install/, search/,
   collections/, favorites/, apps/<slug>/
     └─► js/core.js (fetch + search engine)
         js/site.js (page renderers)
         js/features.js (favorites, collections, compare, QR, i18n)
         js/vendor/fuse.js (vendored Fuse.js 7.0.0, Apache-2.0)
         assets/design-system/*.css (minified in _site only)
     └─► feeds/*.json (+ /api/*.json twins)

 SDKs (optional, client-side): sdk/javascript (pure JS),
 sdk/python (stdlib + setup.py)
```

**Build-time-only** (never shipped with the runtime):

| Tool | Used by | Why |
| --- | --- | --- |
| `ruff` | `make lint`, validate.yml | formatting + lint (pinned in CI) |
| `actionlint` | validate.yml | workflow lint |
| `jq` | `scripts/validate_jq.sh` | feed contract checks |
| `node` | smoke_test (optional) | JS syntax check of site scripts |
| `coverage`/`pytest` | local dev only | test coverage; CI uses `unittest` |
| `brotli` | site builder (optional) | `.br` API twins; skipped with a warning when absent |

**External services (network at build time):** GitHub REST API (releases,
repo metadata — authenticated via `GH_TOKEN`), upstream AltStore/JSON feeds,
download-URL HEAD probes, Discord/Telegram/ntfy/webhook endpoints
(notification delivery is fire-and-forget and never blocks the build).

---

## 2. Workflow map

| Workflow | Triggers | Permissions | Writes | Role |
| --- | --- | --- | --- | --- |
| `sync.yml` | schedule (6 h, `--incremental`) · push (catalog/scripts/site paths) · dispatch | contents, pages | `feeds/`, `apps/`, `README.md`, published root URLs, **Pages deploy** | only scheduled writer; sync → tests → validate → reproducibility → publish root mirror → commit → build `_site/` → deploy-pages |
| `validate.yml` | PR · push main · dispatch | read-only | nothing | parallel offline gate: structural validation + reproducibility · unit-test matrix (py3.11/3.12) · ruff + actionlint (cached) |
| `merge.yml` | `feeds/*.json` changed · dispatch | contents | `feeds/apps.json` + its published copies | safety net re-deriving the master feed from modular feeds; republishes the root URLs; fails on drift |
| `health-check.yml` | schedule (daily 03:30) · dispatch | issues | GitHub Issue | HEAD-probes every download URL + mirror, appends one durable issue |
| `build-uyouenhanced.yml` | dispatch (feed-related) | contents, releases | release asset `uyouenhanced-v<ver>` | builds the uYouEnhanced IPA the catalog consumes → triggers `sync.yml` |
| `build-tweak.yml` | dispatch (generic tooling) | contents, releases | release asset | generic IPA+deb injector; **unrelated to feed generation** (see §9) |

Concurrency: `sync-publish` (never two writers), `validate-<ref>`,
`merge-feeds`. `sync.yml` is the single publisher: it publishes `/apps.json`
+ the `api/` mirror into the repository root and uploads the `_site/` artifact
(which carries the full flat URL family) for the Actions deployment path.
Both are guarded by `tests/test_website_shell.py`.

**Gap (Phase 14):** deploy lives inside `sync.yml`; no independent
`deploy.yml` with rollback. `health-check.yml` is the health job.
`build-tweak.yml` should live in a dedicated builder repository.

---

## 3. Feed generation flow

```text
catalog.json ─┐
              ▼
┌──────────────────────────── pipeline.run ────────────────────────────┐
│ 1 SYNC (ThreadPool, N workers)                                       │
│    for each app:                                                    │
│      RepositoryRef.parse(catalog.upstream)                          │
│      provider = registry.resolve(ref)   (github | github-tags |      │
│                                          json-feed | altstore |      │
│                                          feather)                    │
│      provider.fetch_releases(ref)  →  select_versions()             │
│        (assetNamePattern, assetSuffixes, tagPrefix, keepVersions)   │
│      failure → keep last state (state.json) + retryCount            │
│ 2 HEALTH (ThreadPool)                                               │
│    HEAD-probe newest downloadURL (+ fallbackDownloadURLs mirrors)   │
│    remember_probe() → state[slug].health + healthHistory (cap 30)   │
│ 3 ASSETS                                                            │
│    inspect_catalog() → missing/oversized/unused icon report         │
│ 4 BUILD (all pure)                                                  │
│    per-app AltStore v2 feeds   feeds/<slug>.json  (+ <slug>.xml RSS)│
│    master feed                 feeds/apps.json                      │
│    health / updates / badges / RSS (feed.xml, rss.xml)              │
│    intelligence docs: discovery, sources, verification, status,     │
│    duplicates, analytics, trending, related, reputation,            │
│    download-intelligence, community, install, search-index,         │
│    compare, screenshots                                             │
│    app pages apps/<slug>/index.html (22)                            │
│ 5 PERSIST                                                           │
│    state.json (only after the whole build is valid)                 │
│    README generated blocks (catalog table + stats)                  │
│ 6 NOTIFY (only when versions changed)                               │
│    Discord / Telegram / ntfy / generic webhook                      │
└──────────────────────────────────────────────────────────────────────┘
        ▼
site.py publish_repo_artifacts() → repository root (/apps.json, /api/ + .gz,
                                  sitemap, robots, .nojekyll, homepage stats)
site.py build_site()            → _site/ (full flat URL family + minified CSS, .br)
        ▼
sync.yml → commit root surface → actions/upload-pages-artifact → deploy-pages
        → GitHub Pages
```

**Idempotence:** `atomic_write_text` skips byte-identical writes; a
`--no-sync --no-health` rebuild from committed state must be a no-op
(`check_reproducible.py` enforces this in CI).

---

## 4. Data flow diagram

```text
                    ┌──────────────┐   git    ┌─────────────────────┐
   upstream forges  │ catalog.json │          │  feeds/state.json   │
  (releases/feeds)  │ (hand-edited │          │  runtime memory:    │
        │           └──────┬───────┘          │  versions, update-  │
        │                  │                  │  history, health-   │
        │                  ▼                  │  history (cap 30)   │
        │        ┌──────────────────┐         └──────────▲──────────┘
        └───────►│  providers/      │ fetch_releases     │
   HTTP JSON     │  registry        │   (per-repo cache) │ remember_probe
                 └────────┬─────────┘                    │
                          ▼                              │
                 select_versions / tracking              │
                          │                              │
                          ▼                              │
                 ┌───────────────────────┐               │
                 │  stage_build (pure)   │───────────────┘
                 └────────┬──────────────┘
        ┌─────────────────┼──────────────────────────────────┐
        ▼                 ▼                                  ▼
  feeds/*.json      feeds/*.xml (RSS)              apps/<slug>/index.html
  (22 app feeds +   feed.xml · rss.xml +           README generated blocks
   apps.json + 14   per-app <slug>.xml             GITHUB_STEP_SUMMARY
   intelligence
   docs)
        │
        ▼  src/omnisource/site.py  (root mirror + _site/)
  GitHub Pages  →  { /<flat>, /feeds/, /api/ }  →  AltStore ·
  SideStore · Feather · ESign · LiveContainer · website · future OmniStore
```

---

## 5. Catalog generation diagram

`catalog.json` (`source`, `clients`, 22 `apps`) is transformed, never
mutated, into the distribution surface:

```text
                ┌──────────────── catalog.json ────────────────┐
                │ source ────────► feed_envelope()             │
                │ clients ───────► install.json, sources.json  │
                │ apps[]                                                │
                │  ├─ identity (slug/name/bundle/developer)  ─► all    │
                │  ├─ upstream{} ── RepositoryRef ─► providers ─► state │
                │  ├─ verification{} ─► verification.json (levels)      │
                │  ├─ compatibility{} ─► feeds (minOS), compare, pages  │
                │  ├─ manualRelease{} ─► fallback when upstream empty   │
                │  ├─ screenshots/featured/tags ─► discovery, pages     │
                │  └─ fallbackDownloadURLs ─► feeds + mirror probes     │
                └───────────────────────────────────────────────────────┘
                                │
   per app:  <slug>.json ─┬─► apps.json (master, envelope + news)
                          ├─► <slug>.xml / feed.xml / rss.xml
                          ├─► discovery.json · search-index.json
                          ├─► apps/<slug>/index.html
                          └─► compare.json (all pairs) · related.json
```

---

## 6. Dead code report

Automated scan (`grep -r` cross-reference of every public symbol against
callers in `src/`, `scripts/`, `tests/`):

| Symbol | Status | Finding |
| --- | --- | --- |
| `domain.StandardizedApp` | **unused** | defined + serialized (`to_json`) but no production code constructs it; library surface only. Keep (documented in SDK examples) or fold into discovery — flagged for Phase 17. |
| `domain.HealthSnapshot` | **unused** | no construction site anywhere. Candidate for removal (flagged; not removed — audit only). |
| `providers.*.discover_apps()` / `discoverApps()` | **not exercised by the pipeline** | implemented on all 4 providers, covered by tests, used only as SDK/library surface (future "auto-add app" feature). Not dead. |
| `providers.*.fetch_metadata()` / `fetchMetadata()` | **not exercised by the pipeline** | same as above. |
| `GitHubTagsProvider` | **registered, not in catalog** | no app currently uses `provider: github-tags`; needed for tagged-only upstreams. Keep. |
| `SourceType.GITLAB_RELEASES / CODEBERG_RELEASES / FORGEJO_RELEASES` | **declared, no provider** | `RepositoryRef.parse` accepts them, `build_default_registry` has no matching provider → `ConfigurationError` at resolve. **Broken configuration paths** (would fail at sync). Fixed in Phase 2. |
| `App.platforms` / `StandardizedApp` canonical fields | partially used | `platforms` used by `StandardizedApp` only; `lifecycle_status` used by feeds. Keep. |
| `scripts/notify.py` | used | imported lazily by `pipeline.run` on updates. |
| `feeds/badge-sync.json`, `badge-verified.json` | stale outputs | written by older pipeline versions; no generator emits them anymore but the files are committed and still referenced by the validator's non-feed list. Flagged (harmless; kept for URL stability). |
| `compare.html` | redirect shim | intentional (preserves `?left=&right=` URL). |

**Conclusion:** no unreachable code paths in the pipeline; two library-surface
symbols (`HealthSnapshot`, `StandardizedApp` construction) are unexercised and
one real defect (unregistered SourceTypes) is confirmed and scheduled for
Phase 2.

## 7. Duplicate code report

| Duplicate | Locations | Action |
| --- | --- | --- |
| `_parse_date(value)` (identical 6-line helper) | `analytics.py`, `community.py`, `compare.py`, `download_intel.py`, `reputation.py` | Extract to `omnisource/utils/dates.py::parse_date` (done in this upgrade). |
| `_update_frequency(state, slug)` (near-identical) | `compare.py`, `reputation.py` | Extract to `omnisource/utils/dates.py::average_update_gap_days`. |
| `_health_window`-style rolling probe stats | `reputation.py::_health_window`, `download_intel.py::_window_probe` | Extract to `omnisource/utils/health.py::probe_window`. |
| `health_check.py::probe_url` vs `http.py::HttpClient.probe` | intentional | standalone script stays dependency-free; both use the same `ALIVE_CODES`/`RETRYABLE_CODES` constants. Keep. |
| non-feed JSON name lists | `constants.ALTSTORE_NON_FEED`, `validate_jq.sh`, `merge_feeds.py`, `health_check.py` | `constants` is the single source; the three standalone scripts keep explicit local copies on purpose (no package import) with "keep in sync" comments. |
| `_newest_matching_url` (github vs feed providers) | `providers/github.py`, `providers/feed.py` | small, provider-specific ordering; keep. |

## 8. Unused asset report

`assets.py::inspect_catalog` runs on every build (warnings in the pipeline
log). Current state:

* Every app icon referenced by `catalog.json` exists (PNG+WebP twin pairs).
* WebP twins are the deployable format; PNG twins are kept as
  `<picture>`/legacy fallbacks and are **not** reported unused
  (`_is_paired_asset`).
* `E-Sign.png/.webp`, `Instagram.png/.webp`, `X.png/.webp` — client/social
  icons referenced from website HTML (not the catalog): in use.
* No orphaned files in `assets/` at audit time (0 warnings of kind
  `unused`). Oversized-asset warnings: none (>512 KB).
* 10 apps declare `screenshots: []` → pipeline warning "no screenshots
  declared" (content gap, not dead code).

## 9. Unused workflow report

| Workflow | Verdict |
| --- | --- |
| `build-tweak.yml` | **Unrelated to feed generation.** Generic "inject any .deb into any decrypted .ipa" tool, manually dispatched. No pipeline module, test, feed or doc depends on it. *Recommendation (Phase 14):* deprecate in place with a migration header pointing at a dedicated builder repository (per maintainer decision 2026-09-10: no new repository; keep working, mark deprecated). |
| `build-uyouenhanced.yml` | **Feed-related.** Publishes the `uyouenhanced-v*` release the catalog syncs from and triggers `sync.yml` afterwards. Keep in this repository. |
| all others | exercised by `sync.yml`/`validate.yml`/`merge.yml`/`health-check.yml` on schedule or PR; no obsolete triggers found (`schedule` crons do not collide; `concurrency` groups unique). |

---

## 10. Phase-coverage matrix (what exists vs what the upgrade adds)

| Phase | Requirement | State at audit | Upgrade work |
| --- | --- | --- | --- |
| 2 | Provider redundancy + failover | GitHub/GitHub-tags/JSON/AltStore/Feather providers exist; **GitLab/Codeberg/Forgejo/Direct/Archive missing; no failover chain** | New providers + `upstream.mirrors` + failover (primary → mirror → archive → cached state), `verify()` alias, tests |
| 3 | Integrity validation | `sha256`/`size` stored when upstream publishes them; `hashVerified` check in verification | `integrity_report.json`, per-asset records {sha256,size,release_id,source}, reject rules, weekly full-hash workflow |
| 4 | Snapshots + rollback | none | `snapshots/{daily,weekly,monthly}`, `restore_snapshot()`, CLI, deploy rollback |
| 5 | Duplicate detection, fail CI | duplicates engine + `duplicates.json`; shared-bundle = **warning only** | hard CI errors for duplicate download URLs / undeclared shared bundles (`alternativeTo`), tests |
| 6 | Health score (30/25/20/15/10) | reachability health only | `health_score` engine → `health.json` + app pages + website |
| 7 | Trust score + badges | levels VERIFIED/COMMUNITY/UNVERIFIED + 0–100 source reputation | per-app 0–10 `trustScore` + Verified/Trusted/Community/Experimental badges |
| 8 | Dead app detection | staleness warnings only | `dead_apps.json` with 90/180/365 + removed-release rules |
| 9 | Comparison engine | `compare.json` + `compare/?left=&right=` | generated `/compare/<a>-vs-<b>/` pages |
| 10 | Collections | user-local collections UI only | curated `collections.json` + generated collection pages + API |
| 11 | Trending | score engine + trending/rising/recentlyUpdated | Today/Week/Month periods + UI |
| 12 | Indexed search (Fuse.js) | Fuse-compatible index + custom fuzzy engine | vendored Fuse.js 7.0.0 wired into search + home |
| 13 | Performance | lazy images, SW, `.gz` twins, CSS minify | `catalog.min.json`, brotli twins, incremental hardening |
| 14 | Workflow cleanup | sync/validate/merge/health-check + 2 builders | split `deploy.yml`, rename health job, deprecate `build-tweak.yml` |
| 15 | Monitoring | `status.json` + status page | pipeline + provider sections in `status.json` |
| 16 | API layer | `/api/<doc>.json` + manifest | `/api/apps|trending|collections|search|status` (no extension), per-app endpoints, collections/search endpoints |
| 17 | OmniStore readiness | discovery API documented | versioning policy + endpoint set + `docs/OMNISTORE.md` |
| 18 | Testing | 127 tests, all green | +tests for every new module; ≥90% coverage on `src/omnisource` |
