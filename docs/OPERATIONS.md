# Operations: Monitoring, Self-Healing, Mirrors, Analytics

Runbook for the autonomous operations layer (all `data/`, all scheduled).

## Health monitoring (`monitoring.yml`, every 30 min)

```
scripts/monitoring/report_status.py  → data/status.json (online/degraded/offline)
scripts/monitoring/check_sources.py  → per-source reachability table (stdout, exit 1 on failure)
scripts/monitoring/check_downloads.py → per-download reachability table
```

`data/status.json` keeps a 30-sample rolling `history` plus a `failing[]`
list. States: `online` (all reachable), `degraded` (partial), `offline`
(total). Probes are anonymous (no credentials), concurrent
(`--workers 16`), HEAD-first with GET fallback, and treat 2xx/3xx as
alive. `--offline` re-emits the previous document untouched.

The legacy daily `health-check.yml` (issue filing) still runs alongside.

## Self-healing (`scripts/selfheal.py`, runs inside `monitoring.yml`)

1. **Detect** — `broken_download` (from health probes),
   `missing_metadata` (critical display fields),
   `removed_release` (via `data/release_history.json`).
2. **Plan** — one action per issue: `retry` (transient errors),
   `repair` (recorded fallback URL), `replace` (mirror — needs review),
   `rebuild` (flag for full resync).
3. **Report** — `data/selfheal_report.json` with `suggestedPatches`.
   `--apply` writes `data/healed_apps.json` (fallback swaps only, for
   review) — pipeline outputs are never rewritten in place.
4. **Re-probe** — `--reprobe` re-checks downloads live before planning.

## Mirror management (`data/mirrors.json`)

Tiers: `github-release` (primary) → `github-pages` → `cdn` → `backup`.
`src/omnisource/mirrors.py` orders candidates (healthy first, then tier)
and `failover()` picks the next URL after a failure.
`scripts/mirror_check.py` writes `data/mirror_status.json`
(protected/unprotected per app).

To configure a mirror, add to `data/mirrors.json`:

```json
{"id": "r2-main", "type": "cdn", "urlTemplate": "https://cdn.example.com/{slug}.ipa", "apps": ["*"]}
```

`apps: ["*"]` covers everything; list slugs to scope. Disabled entries
carry `"enabled": false`. The registry ships as a skeleton — failover
logic is implemented and tested, real endpoints are operator-provided.

## Analytics (`analytics.yml`, daily)

`scripts/analytics_rollup.py` rolls `feeds/analytics.json` history (+ the
monitoring ledger) into `data/analytics_rollup.json`:

- `daily` — last 30 days · `weekly` — last 12 ISO weeks ·
  `monthly` — last 12 calendar months (per-period averages).

Content-stable: no commit when nothing changed. Served by the Statistics
page (both sites) and `GET /api/v3/analytics`.

## Release ledger & rollback

`data/release_history.json` (built by `publish.yml`) is append-only:
entries flip `current` → `superseded` (replaced) or `removed` (yanked
newest). Rollback plan for any previously seen version:

```bash
python3 scripts/build_release_history.py --rollback ytlite --to 2.1.0
```

## Reputation & quarantine

`scripts/reputation/score.py` maps the 0–100 score onto
`verified ≥85 / trusted ≥70 / good ≥50 / warning ≥25 / untrusted <25`
(`data/source_reputation.json`). Scores below 25 are **quarantined**:
kept for audit, never auto-published. Weights and signals are documented
in `src/omnisource/reputation.py`.

## Incident quick-reference

| Symptom | Check | Action |
|---|---|---|
| `data/status.json` → `degraded` | `failing[]`, `monitoring.yml` logs | `selfheal_report.json` plans; `retry` auto-clears transients |
| `security.yml` red | `data/security.json` findings | Fix `critical` (malformed digest) or `--fail-on high` breach, re-run |
| `publish.yml` red | `build_client_feeds --check`, `validate.py` | Never hand-edit `feeds/`; fix `catalog.json`, let `sync` rebuild |
| `discovery.yml` red | `validate_source.py` output | Quarantine offending record (reputation 0), re-run |
| Empty `monitoring` commit loop | `history` cap is 30 — by design | None; each run appends one sample |
