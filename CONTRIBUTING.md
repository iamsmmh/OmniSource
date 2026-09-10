# Contributing to OmniSource

Thanks for helping keep OmniSource current, healthy and transparent. Every
app in the catalog resolves from an **official upstream**, so most
contributions fall into a few repeatable shapes below.

## Ground rules

- **Never hand-edit generated files.** Everything under `feeds/` (feeds,
  `apps.json`, `updates.json`, RSS, health data, badges, `state.json`) and the
  catalog table inside `README.md` is produced by
  `python3 scripts/omnisource.py`. Change `catalog.json` or the code, then run
  the pipeline and commit its output.
- Scripts stay **Python-stdlib only** — no virtualenv, no new dependencies.
- The website stays **dependency-free static** HTML/CSS/JS reading the
  generated JSON at runtime.
- Releases must come from the developer's own source (GitHub Releases, their
  own AltStore feed, or clearly-labelled community-built IPAs of official
  tweaks that publish no IPA). Never point at random re-uploads.

## Ways to contribute

### 1. Request an app

Open an [app request](https://github.com/iamsmmh/OmniSource/issues/new?template=01-app-request.yml)
with the official upstream link (GitHub repository or the developer's own
feed) and the exact IPA asset name if releases carry multiple assets.

### 2. Report a broken upstream or download

Open a [broken upstream](https://github.com/iamsmmh/OmniSource/issues/new?template=02-broken-upstream.yml)
issue. The daily [health check](.github/workflows/health-check.yml) already
files broken-link reports; including the URL and what the server returned
helps fix it faster. If the project moved or renamed, include the new
repository/feed URL.

### 3. Add or update an app yourself

1. Add an entry to `catalog.json` — `slug`, identity fields, `icon` (a file
   under `assets/`, ideally square PNG ≤ 512 KB), `verification`,
   `compatibility`, and an `upstream` block. See the schema in
   `schemas/catalog.schema.json` and the existing entries for examples.
2. Optional `upstream` knobs: `keepVersions` (default `1`, `0` = keep all),
   `includePrereleases`, `versionPattern`, `assetNamePattern`, `tagPrefix`,
   `minOSVersion` / `minOSVersionByTagNumber`.
3. Watch out for **bundle identifier collisions** — a client replaces an
   installed app whose `bundleIdentifier` matches another catalog entry.
4. Run locally:

   ```bash
   python3 scripts/omnisource.py --no-health   # sync upstreams + rebuild feeds
   make check                                   # lint, validate, tests
   ```

   or rebuild offline from existing state when you only changed metadata:

   ```bash
   python3 scripts/omnisource.py --no-sync --no-health
   ```

5. Commit `catalog.json`, any new `assets/` file, and the regenerated
   `feeds/` + `README.md` output together in one pull request. The pipeline
   also refreshes the published root mirror (`apps.json`, `<slug>.json|.xml`,
   `api/`, `sitemap.xml`, `robots.txt`) — commit it too: GitHub Pages serves
   the branch, so those files are the live URLs. Never hand-edit them;
   `scripts/publish_root.py` regenerates them from `feeds/`.

### 4. Improve the pipeline or website

Open a [feature idea](https://github.com/iamsmmh/OmniSource/issues/new?template=04-feature-idea.yml)
first so the direction is agreed before a large change lands. Code lives in
`src/omnisource/` (pipeline), `scripts/` (entry points), the repository root
(static site: `index.html`, section pages, `js/`, `sw.js`) and `tests/`.
Run `make check` before pushing; CI runs the same
lint (`ruff`), structural validation (`validate.py`, `validate_jq.sh`),
reproducibility and unit tests offline.

## Pull request checklist

- [ ] Changed `catalog.json`, never generated files by hand.
- [ ] Ran the pipeline and committed regenerated output (feeds/, app pages,
      README blocks and the published root URLs — `make check` verifies the
      mirror matches `feeds/`).
- [ ] `make check` passes locally (or the equivalent commands).
- [ ] Added/updated tests under `tests/` for new behaviour.
- [ ] Updated docs (`README.md`, `docs/website.md`, `docs/REPOSITORY.md`)
      when the layout, outputs or commands changed.

## Code of conduct

Be respectful and constructive. OmniSource is an independent community
project — apps, code and trademarks belong to their respective owners, and
users are responsible for complying with applicable laws and terms of
service.
