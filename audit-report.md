# OmniSource Complete Repository Audit — 2026-09-12

Scope: every Python module (`src/`, `scripts/`), website code (static PWA +
`web/`), GitHub Actions, feed generators, API routes, collections, data
files, assets, build systems and documentation. This report covers the
pre-modernization baseline (v3.1.0) and what the 3.2.0 modernization changed.

## Method

- `make audit` baselines (`reports/*.md`), full test suite (235 tests),
  `ruff check` + `format --check`, `scripts/validate.py`,
  `scripts/validate_jq.sh`, `check_reproducible.py`, `smoke_test.py`
  (both modes) — all green before and after.
- Manual review of all 6 (now 12) workflows, all feed renderers, the JS
  data/search/i18n layers, and every JSON schema.
- Live verification: production `next build` + runtime smoke of the new app.

## What was already excellent

| Area | Finding |
|---|---|
| Dead code | **0** unused files, **0** dead JS globals, **0** uncalled public Python functions (`reports/dead-code.md`) |
| Links/SEO | **0** broken internal links, **0** pages missing SEO metadata across 158 HTML files (`reports/links.md`) |
| i18n coverage | All 8 locales carry exactly the 151 English keys — **0** missing anywhere |
| TODO debt | Zero `TODO`/`FIXME`/`HACK` markers in `src/`, `scripts/`, `js/`, `src/js/` |
| Determinism | Offline rebuild is byte-stable (`check_reproducible.py` green, 697 files) |
| Supply chain | Runtime is stdlib-only; no `pip install` executes with a write token |

## Gaps found (and fixed in 3.2.0)

### P0 — Security: workflow script injection (FIXED)

- `build-tweak.yml` interpolated `${{ inputs.base_ipa_url }}`,
  `${{ inputs.tweak_deb_url }}`, `${{ inputs.bundle_id }}` and
  `${{ inputs.app_name }}` directly into `run:` scripts. Dispatch inputs
  are attacker-controlled → arbitrary command execution as the Actions
  runner. **Fixed:** `env:` indirection, https-only URL allowlists,
  bundle-ID character allowlist, sanitized artifact name.
- `sync.yml` interpolated `${{ inputs.skip_sync }}` / `skip_health` and
  used unquoted `$EXTRA`. **Fixed:** `env:` booleans + bash array.
- `build-uyouenhanced.yml` interpolated a step output into `run:`.
  **Fixed:** `env:` + path-traversal guard.
- `validate.yml` / `merge.yml` multi-line scripts lacked `set -euo
  pipefail`. **Fixed** everywhere; rules documented in
  `.github/workflows/README.md`.

### P1 — No autonomous discovery (FIXED)

New sources entered only via hand-edited `catalog.json`. **Fixed:**
`scripts/discovery/` (GitHub code search every 12h, feed probing, release
scans, web catalogs) → `data/discovered_sources.json`, gated by
`scripts/validation/` (invalid feeds never publish) — see `docs/DISCOVERY.md`.

### P1 — No deduplication database (FIXED)

11 of 94 records share bundle IDs (mostly YouTube tweaks — a known,
documented situation). There was no canonical record. **Fixed:**
`src/omnisource/canonical.py` → `data/canonical_apps.json` (83 canonical
apps), duplicate groups reportable via `scripts/build_canonical.py --report`.

### P1 — Release history was ephemeral (FIXED)

`feeds/state.json` keeps only the newest versions; yanked releases left no
trace. **Fixed:** append-only `data/release_history.json` with
`current`/`superseded`/`removed` lifecycle, version comparison and
rollback plans (`--rollback SLUG --to VERSION`).

### P1 — Monitoring was daily and issue-only (FIXED)

`health-check.yml` probed daily and only filed issues. **Fixed:**
`monitoring.yml` every 30 min → `data/status.json`
(`online`/`degraded`/`offline`) + self-healing plans + mirror readiness.

### P1 — No security gate (FIXED)

Hashes existed per-app but nothing aggregated them or blocked publication.
**Fixed:** `scripts/security/scan.py` → `data/security.json` (SHA-256/512
coverage, duplicate binaries, integrity, provenance); `security.yml`
fails on `critical`.

### P1 — No per-client feeds (FIXED)

One envelope served all five clients. **Fixed:**
`feeds/clients/{altstore,sidestore,feather,esign,livecontainer}.json`,
each validated as AltStore v2 before write.

### P1 — API gaps (FIXED)

v2 is snapshot-only (no pagination/filtering/ETag). **Fixed:** API v3 —
static `api/v3/*.json` (181 docs) + dynamic Next.js routes with
pagination, sorting, filtering, ETag/`304`, compression and cache
control. See `docs/API-V3.md`.

### P1 — No analytics windows (FIXED)

Only live totals + raw history. **Fixed:** `data/analytics_rollup.json`
(daily/weekly/monthly) via `analytics.yml`.

### P2 — Scale ceiling (MITIGATED)

Thread-pool probing is fine to ~hundreds of sources. **Added:**
`src/omnisource/async_http.py` (asyncio + optional aiohttp pooling,
stdlib fallback) as the documented 1,000+/10,000+ path. See
`docs/PERFORMANCE-REPORT.md`.

### P2 — Website framework ceiling (ADDRESSED, backward compatible)

The static PWA is excellent but hand-rolled (routing, search, i18n all
custom JS). Rewriting it in place would risk the installable source, so
the modernization **adds** `web/` (Next.js 15 + TS + Tailwind PWA, 11
routes + API, 8 lazy locales, verified production build) while the static
site keeps deploying untouched. See `web/README.md`.

## Residual risks / known limitations

1. **Bundle-ID collisions are inherent** (tweaks share IDs by design).
   Mitigated via single-app feeds + canonical DB; cannot be "fixed".
2. **30 apps lack SHA-256** (upstream publishes none). Tracked as `low`
   findings; `security.yml` gates only on `critical`.
3. **Mirror registry starts empty** (`data/mirrors.json` skeleton) —
   failover logic is implemented and tested, but real mirrors need
   operator configuration. See `docs/OPERATIONS.md`.
4. **Discovery code search needs a token with search scope**; the default
   `github.token` works but rate-limits aggressively — `discovery.yml`
   degrades gracefully (empty pass, exit 0).
5. **Next.js hosting is not GitHub Pages** — `website.yml` verifies and
   uploads the build; promotion to hosting is a documented manual step so
   a web regression can never take down the live source.
6. **Largest modules** (`validation.py` 1066, `site.py` 1062,
   `pipeline.py` 949 lines) are stable but dense — future splits should
   target them first.

## Verdict

Baseline: clean, deterministic, well-tested — but manual at the edges
(discovery, dedup, history, monitoring, gating). Post-modernization: all
ten core objectives have an implemented, tested, scheduled and documented
owner. Production readiness: **9.0/10** (see `docs/MODERNIZATION.md`).
