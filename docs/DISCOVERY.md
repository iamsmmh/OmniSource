# Autonomous Discovery Engine

OmniSource discovers third-party AltStore / SideStore / Feather / ESign /
LiveContainer sources without human intervention, on a 12-hour schedule
(`.github/workflows/discovery.yml`).

## Passes

| Script | What it does |
|---|---|
| `scripts/discovery/discover_github.py` | GitHub code search for `source.json`, `apps.json`, `altsource`, `altstore source`, `sidestore source`, `feather source` (+ `--term` extras) |
| `scripts/discovery/discover_feeds.py` | Probes candidate feed URLs (bare sites expand to likely filenames) and classifies live feeds by client |
| `scripts/discovery/discover_releases.py` | Flags `owner/repo`s whose releases ship `.ipa`/`.tipa` assets |
| `scripts/discovery/discover_web_catalogs.py` | Scrapes catalog pages for linked `*.json` feeds and probes each |
| `scripts/discovery/discover_sources.py` | Orchestrator: runs every pass, validates, merges into the store |

Core logic lives in `src/omnisource/autodiscovery.py` (stdlib-only;
network isolated in `fetch_*` helpers). `--dry-run` prints without writing.

## Store

`data/discovered_sources.json` (`schemas/discovery.schema.json`):

```json
{
  "source_id": "example-com-apps-json-a1b2c3d4e5",
  "name": "octo/source — apps.json",
  "url": "https://example.com/apps.json",
  "type": "altstore",
  "discovered_at": "2026-09-12T00:00:00Z",
  "last_checked": "2026-09-12T12:00:00Z",
  "health": "unknown",
  "reputation": 0
}
```

Merges are keyed by URL: re-discovery refreshes `last_checked` (and
`health` when probed) without duplicating.

## Validation gate (invalid feeds never publish)

`scripts/validation/` (`src/omnisource/remote_validation.py`):

- `validate_source.py` — store schema, https URLs, known types, 0–100
  reputation, slug IDs. Fails `discovery.yml` before commit.
- `validate_feed.py` — envelope schema, per-app rules, duplicate bundle
  IDs, optional `--check-downloads` reachability probe.
- `validate_app.py` — single app entry (+ `--check-download`).
- `validate_release.py` — tag, installable assets, digest format.

`assert_publishable()` returns `(ok, errors, warnings)`; anything with
errors is quarantined (kept in the store with `reputation: 0`, never
merged toward feeds).

## Promotion path

Discovery → validation → (`reputation ≥ 25`, healthy) → **explicit
promotion** into `catalog.json` (human PR or a pinned policy — never
automatic). The sync pipeline only reads `catalog.json`, so an
unreviewed discovery cannot reach users by construction.

## Rate limits & degradation

Code search uses `GITHUB_TOKEN`/`GH_TOKEN` and sleeps between pages; on
any API failure the pass yields zero candidates and exits 0 (a failed
search must never fail the pipeline). Feed/release passes are plain
HTTPS with per-request timeouts and payload caps (2 MB).
