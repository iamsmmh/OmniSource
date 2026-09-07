# Workflows

The automation for OmniSource lives here. Every workflow starts with read-only
permissions and opts in to exactly what it needs, never more.

| Workflow | Trigger | Writes | Purpose |
| --- | --- | --- | --- |
| [`sync.yml`](sync.yml) | schedule (6 h, incremental) · push · manual | feeds, mirrors, README, Pages | Resolve official upstream releases, probe links, rebuild every feed, deploy the source to Pages |
| [`validate.yml`](validate.yml) | pull request · push · manual | nothing | Offline gate: Python + `jq` structural validation, reproducibility check, `ruff`, `actionlint` |
| [`merge.yml`](merge.yml) | `feeds/*.json` changed · manual | `*.json` mirrors | Rebuild the unified `apps.json` and the root mirrors from the modular `feeds/` (SSOT) |
| [`health-check.yml`](health-check.yml) | schedule (daily) · manual | GitHub Issue | HEAD-probe every download URL + mirror and report broken links via an issue |
| [`build-uyouenhanced.yml`](build-uyouenhanced.yml) | manual | Release asset | Build and publish the uYouEnhanced IPA, then trigger a feed sync |

## How they fit together

```
catalog.json ──▶ sync.yml (scripts/omnisource.py) ──▶ feeds/*.json ──▶ GitHub Pages
▲ │
│ ▼
build-uyouenhanced.yml   merge.yml (scripts/merge_feeds.py)
(publishes uyouenhanced-v release) ──▶ apps.json + root mirrors
```

- **`sync.yml`** is the only scheduled writer. `concurrency` prevents two runs from
  writing `feeds/` at once.
- **`merge.yml`** is the safety net for direct edits to `feeds/`: it re-derives
  `apps.json` and the root-level mirrors from the modular feeds — `feeds/` is the
  single source of truth.
- **`health-check.yml`** is independent of releases: a broken upstream link is
  reported even when nothing new has shipped.
- **`validate.yml`** guards pull requests. It is read-only and network-free, so it
  is safe on forks. The reproducibility step fails a PR that hand-edits a
  generated feed instead of `catalog.json`.

## After a fresh fork

1. **Settings → Pages → Source: GitHub Actions** (required for `sync.yml` to deploy).
2. **Settings → Actions → Workflow permissions** — leave at the default
   *read repository contents*; each workflow requests more explicitly.
3. No repository secrets are required — `github.token` covers every case.
