# Workflows

The automation for OmniSource lives here. Every workflow starts with read-only
permissions and opts in to exactly what it needs, never more.

| Workflow | Trigger | Writes | Purpose |
| --- | --- | --- | --- |
| [`sync.yml`](sync.yml) | schedule (6 h, incremental) · push · manual | feeds, `apps/` pages, README, published root URLs, Pages | Resolve official upstream releases, probe links, rebuild every feed + intelligence documents + app pages, republish the flat/API URLs, deploy |
| [`validate.yml`](validate.yml) | pull request · push · manual | nothing | Parallel offline gate: structural validation + reproducibility, unit test matrix (3.11/3.12), `ruff` + `actionlint` (cached) |
| [`merge.yml`](merge.yml) | `feeds/*.json` changed · manual | `feeds/apps.json` + its published copies | Rebuild the unified master source from modular feeds |
| [`health-check.yml`](health-check.yml) | schedule (daily) · manual | GitHub Issue | HEAD-probe every download URL + mirror and report broken links via an issue |
| [`build-uyouenhanced.yml`](build-uyouenhanced.yml) | manual | Release asset | Build and publish the uYouEnhanced IPA, then trigger a feed sync |

## How they fit together

```
catalog.json ──▶ sync.yml (scripts/omnisource.py) ──▶ feeds/*.json
                                     │
                                     ├─▶ repository root mirror  ─▶ GitHub Pages (branch deploy)
                                     └─▶ _site/                  ─▶ GitHub Pages (Actions deploy)
▲ │
│ ▼
build-uyouenhanced.yml   merge.yml (scripts/merge_feeds.py)
(publishes uyouenhanced-v release) ──▶ feeds/apps.json ──▶ scripts/publish_root.py
```

- **`sync.yml`** is the only scheduled writer. `concurrency` prevents two runs from
  writing `feeds/` at once.
- **`merge.yml`** is the safety net for direct edits to `feeds/`: it re-derives
  `feeds/apps.json` from the modular feeds and republishes the root mirror with
  `scripts/publish_root.py`, keeping `feeds/` as the single source of truth.
- **`health-check.yml`** is independent of releases: a broken upstream link is
  reported even when nothing new has shipped.
- **`validate.yml`** guards pull requests. It is read-only and network-free, so it
  is safe on forks. The reproducibility step fails a PR that hand-edits a
  generated feed instead of `catalog.json`.

## After a fresh fork

1. **Settings → Pages** — either source works:
   * *Deploy from a branch* (`main` / root) serves the committed tree. The
     generated URLs are published there by the pipeline, so `/apps.json`,
     `/<slug>.json`, `/api/*`, `sitemap.xml` and `robots.txt` resolve.
   * *GitHub Actions* serves the `_site/` artifact that `sync.yml` uploads.
     `sync.yml` deploys it either way; GitHub simply ignores the artifact
     while the branch mode is selected.
2. **Settings → Actions → Workflow permissions** — leave at the default
   *read repository contents*; each workflow requests more explicitly.
3. No repository secrets are required — `github.token` covers every case.

## Why the root carries published copies

GitHub Pages serves *one* of two things: the branch tree, or the uploaded
`_site/` artifact. The branch tree is what this repository is currently
served from, and a file that is not committed does not exist on the web —
including `/apps.json`, the URL installers register as a source. So
`src/omnisource/site.py` publishes the generated URLs **twice** from the
same canonical `feeds/`:

* `publish_repo_artifacts()` mirrors them into the repository root (flat
  feeds, `/api/` + `.gz` twins, `catalog.min.json`, `sitemap.xml`,
  `robots.txt`, `.nojekyll`, homepage statistics). The pipeline calls it at
  the end of every run; `scripts/publish_root.py` does the same for manual or
  `merge.yml` runs, and its `--check` mode reports drift.
* `build_site()` assembles the same URLs into `_site/` (plus minified CSS and
  optional `.br` twins) for the Actions deployment.

Copies are byte-identical to `feeds/` — git stores the shared blob once — and
`scripts/check_reproducible.py` (run by `validate.yml`, `merge.yml` and
`sync.yml`) fails a rebuild that would change one, so a hand-edited feed can
never be published. Never delete the root copies to "clean up": doing so
breaks the installable source URL until the next build, and the drift check
will fail.
