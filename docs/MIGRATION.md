# Migration Guide — 3.1.x → 3.2.0

3.2.0 is **backward compatible**: every 3.1 URL, feed, API endpoint, page
and script keeps working. This guide covers what moved, what is new, and
what (little) you may need to change.

## Nothing breaks

- `apps.json`, `feeds/*.json`, `feeds/*.xml`, `api/*`, `api/v2/*` —
  byte-identical contracts, same builder (`scripts/omnisource.py`).
- Static PWA (root `index.html`, `js/`, `src/js/`, locales) — untouched
  deployment via `sync.yml`.
- `catalog.json` remains the only hand-edited source of truth.
- `make build|serve|check` work exactly as before.

## New scheduled writers (all additive)

| Workflow | Writes | First-run effect |
|---|---|---|
| `discovery.yml` | `data/discovered_sources.json` | Empty store (candidates accumulate) |
| `monitoring.yml` | `data/status.json`, `data/selfheal_report.json`, `data/mirror_status.json` | First probes within 30 min |
| `security.yml` | `data/security.json` | Initial posture report |
| `analytics.yml` | `data/analytics_rollup.json` | First windows (history backfills over days) |
| `publish.yml` | `data/canonical_apps.json`, `data/release_history.json`, `data/enriched_apps.json`, `data/source_reputation.json`, `feeds/clients/*`, `api/v3/*` | One bulk commit |

`sync.yml`'s `git add` allowlist already covers `*.json`, so scheduled
writers commit cleanly; each also checks `git diff --cached --quiet`
before committing (no empty churn except the monitoring time-series).

## For feed consumers (AltStore/SideStore/Feather/ESign/LiveContainer)

- Keep using `apps.json`, or switch to the per-client variant that
  matches your app: `feeds/clients/{altstore,sidestore,feather,esign,
  livecontainer}.json`. Same AltStore v2 shape, client-appropriate
  filtering (ESign drops non-direct downloads, Feather drops relative
  icons).
- Single-app feeds (`feeds/<slug>.json`) are unchanged.

## For API consumers

- v1-style flat docs (`api/apps.json`, …) and **v2 are unchanged**.
- New: **API v3** — static `api/v3/*.json` on Pages today; dynamic
  query/pagination/ETag routes when `web/` is hosted. See `docs/API-V3.md`.
- New documents in `data/` are advisory (canonical DB, ledger,
  enrichment, reputation labels, security, rollups) — stable schemas,
  versioned with `schemaVersion`.

## For contributors

- New Make targets: `make discovery monitoring security analytics
  derived web` (all offline-safe; `web` needs `npm`).
- New tests: `tests/test_{autodiscovery,remote_validation,canonical,
  release_history,search,api_v3,client_feeds,ops,async_http}.py` —
  run with `python3 -m unittest discover -s tests`.
- Workflow hardening rules are now enforced by convention (see
  `.github/workflows/README.md`): `set -euo pipefail`, quoted vars,
  `env:`-only inputs. `actionlint` runs in CI.
- Version is now `3.2.0` (`pyproject.toml` + `src/omnisource/__init__.py`
  must stay in sync — `tests/test_version.py` guards this).

## For fork operators

1. Merge — no secrets or settings changes required.
2. Optionally set `DISCORD_/TELEGRAM_/NTFY_` secrets (unchanged behavior).
3. Optionally configure `data/mirrors.json` with real mirror endpoints.
4. Optionally host `web/` (Vercel/Cloudflare/self-hosted) — the static
   site keeps serving Pages either way.

## Rollback

Every 3.2.0 artifact is additive. To revert to 3.1 behavior, disable the
six new workflows — `sync.yml`, feeds, APIs and the site keep working
with zero code changes.
