# Workflows

The automation for OmniSource lives here. Every workflow starts with read-only
permissions and opts in to exactly what it needs, never more.

| Workflow | Trigger | Writes | Purpose |
| --- | --- | --- | --- |
| [`sync.yml`](sync.yml) | schedule (6 h, incremental) · push · manual | feeds, flat feed copies, `apps/` pages, README, home-page stats, sitemap/robots, Pages | Resolve official upstream releases, probe links, rebuild every feed + intelligence documents + app pages, deploy |
| [`validate.yml`](validate.yml) | pull request · push · manual | nothing | Parallel offline gate: structural validation + reproducibility, unit test matrix (3.11/3.12), `ruff` + `actionlint` (cached) |
| [`merge.yml`](merge.yml) | `feeds/*.json` changed · manual | `feeds/apps.json`, `apps.json` | Rebuild the unified master source from modular feeds (keeps the flat install URL in step) |
| [`health-check.yml`](health-check.yml) | schedule (daily) · manual | GitHub Issue | HEAD-probe every download URL + mirror and report broken links via an issue |
| [`build-uyouenhanced.yml`](build-uyouenhanced.yml) | manual | Release asset | Build and publish the uYouEnhanced IPA, then trigger a feed sync |

## How they fit together

```
catalog.json ──▶ sync.yml (scripts/omnisource.py) ──▶ feeds/*.json ──▶ GitHub Pages
▲ │
│ ▼
build-uyouenhanced.yml   merge.yml (scripts/merge_feeds.py)
(publishes uyouenhanced-v release) ──▶ feeds/apps.json
```

- **`sync.yml`** is the only scheduled writer. `concurrency` prevents two runs from
  writing `feeds/` at once.
- **`merge.yml`** is the safety net for direct edits to `feeds/`: it re-derives
  `feeds/apps.json` from the modular feeds, keeping `feeds/` as the single source
  of truth.
- **`health-check.yml`** is independent of releases: a broken upstream link is
  reported even when nothing new has shipped.
- **`validate.yml`** guards pull requests. It is read-only and network-free, so it
  is safe on forks. The reproducibility step fails a PR that hand-edits a
  generated feed instead of `catalog.json`.

## After a fresh fork

1. **Settings → Pages** — source *Deployment from branch* on `main` works out
   of the box (the repo root is a valid site, see below); alternatively keep
   the *GitHub Actions* source so only `sync.yml` deploys. Either way, no
   manual steps are required.
2. **Settings → Actions → Workflow permissions** — leave at the default
   *read repository contents*; each workflow requests more explicitly.
3. No repository secrets are required — `github.token` covers every case.

## The two publishers: `sync.yml` and the managed Jekyll build

Two deployments can publish this repository to Pages, and **both are correct**:

- **[`sync.yml`](sync.yml) (primary)** assembles `_site/` in CI
  (`scripts/build_site.py`) and deploys it. This is the full artifact: the
  site, all feeds, the flat historical URLs, the `/api/` mirror with `.gz`
  twins, minified CSS, `sitemap.xml` and `robots.txt`.
- **GitHub's server-managed *pages build and deployment*** (Jekyll) runs on
  **every push to the Pages source branch** and builds the **repository
  root**. The repository root *is* the site: hand-maintained pages live at
  the root, the pipeline commits the generated feeds, the flat historical
  copies, `sitemap.xml`/`robots.txt` and the home page's live statistics,
  and [`_config.yml`](../../_config.yml) excludes repo internals and
  `feeds/state.json`. So this build publishes the same working site — just
  without the `/api/` mirror and `.gz` twins (assembled only in CI). Feed
  subscribers and clients are unaffected by that difference: they use
  `/apps.json`, `/<feed>` and `/feeds/<feed>`, which are committed files.

Consequences:

- A push that only triggers the managed build (e.g. a `merge.yml` hotfix
  commit) deploys a **correct** site — the worst case is a window with no
  `/api/` mirror, not a broken site.
- The two publishers can race when a `Sync & Publish` run's feed commit
  starts a managed run while `sync.yml`'s own deploy is in flight; one of the
  deploy steps then fails on a concurrent-deployment conflict. That red X is
  **cosmetic** — when `Sync & Publish` is green, a successful deploy already
  won. Re-run neither; the latest successful run is what's live. (First
  observed on
  [34389219761](https://github.com/iamsmmh/OmniSource/actions/runs/34389219761),
  2026-09-09, when the repo root still was *not* a valid site.)
- **If you previously pointed Pages at a dedicated `pages` branch** to keep
  the managed build from clobbering the site (the pre-restructure
  mitigation), that branch is no longer load-bearing: the Jekyll build is a
  correct site either way. Keep the quiet branch or point the source back at
  `main` — either way both publishers stay consistent.
