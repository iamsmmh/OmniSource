# Workflows

The automation for OmniSource lives here. Every workflow starts with read-only
permissions and opts in to exactly what it needs, never more.

| Workflow | Trigger | Writes | Purpose |
| --- | --- | --- | --- |
| [`sync.yml`](sync.yml) | schedule (6 h, incremental) · push · manual | feeds, `apps/` pages, README, Pages | Resolve official upstream releases, probe links, rebuild every feed + intelligence documents + app pages, deploy |
| [`validate.yml`](validate.yml) | pull request · push · manual | nothing | Parallel offline gate: structural validation + reproducibility, unit test matrix (3.11/3.12), `ruff` + `actionlint` (cached) |
| [`merge.yml`](merge.yml) | `feeds/*.json` changed · manual | `feeds/apps.json` | Rebuild the unified master source from modular feeds |
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

1. **Settings → Pages** — source *GitHub Actions* (required). `sync.yml`
   assembles `_site/` and deploys it; the raw repository root is not a valid
   site on its own, because the flat feed URLs, `sitemap.xml`, `robots.txt`
   and homepage statistics are generated into `_site/` at build time.
2. **Settings → Actions → Workflow permissions** — leave at the default
   *read repository contents*; each workflow requests more explicitly.
3. No repository secrets are required — `github.token` covers every case.

## The single publisher: `sync.yml`

[`sync.yml`](sync.yml) is the only deployment. It assembles `_site/` in CI
(`scripts/build_site.py`) and deploys it: the site, all feeds, the flat
historical URLs, the `/api/` mirror with `.gz` twins, minified CSS,
`sitemap.xml` and `robots.txt`.

Do **not** point Pages back at *Deploy from a branch*: the branch build
would serve the raw repository root, which no longer carries the generated
flat feed URLs, so every subscriber URL (`/apps.json`, `/<feed>.json`, …)
would 404. The unit suite guards this invariant
(`tests/test_website_shell.py::test_pages_deploys_from_site_artifact`).

History: the repository previously committed ~70 flat feed copies at the
root so GitHub's managed Jekyll branch build served the same site as the
`_site/` artifact. That duplication was removed in favor of the single
Actions publisher; every public URL is unchanged.
