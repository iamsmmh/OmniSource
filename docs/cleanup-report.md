# OmniSource — Cleanup Report

Audit completed before any removal. Every file in the repository was checked
for references in `catalog.json`, `feeds/`, `apps/`, the GitHub Actions
workflows, the pipeline (`src/omnisource/pipeline.py`) and the test suite
before a deletion was made. **No file referenced by CI, feed generation,
app pages, the API or search was removed without a live replacement.**

## Files removed (24)

| Removed file | Why | Replacement |
| --- | --- | --- |
| `api/*.json` (18 files) | Byte-identical local mirrors of `feeds/*.json` regenerated on every build. Duplicated the entire API surface in the repo and doubled the committed JSON payload. | `_site/api/` is still built from `feeds/` by `src/omnisource/site.py` (with `.gz` twins) and deployed by `actions/upload-pages-artifact`. `api/` is now in `.gitignore`; the pipeline keeps regenerating it locally for SDK consumers who clone the repo. |
| `website/css/styles.css` | One of three disjoint hand-rolled stylesheets; duplicated design tokens with `app-page.css`. | `assets/design-system/tokens.css` + `components.css` + `utilities.css` (shared by the website and the generated app pages). |
| `website/css/app-page.css` | App-page-only stylesheet; tokens duplicated from `styles.css`; a third copy of the theme system. | Same design system — app pages now use the identical components (badges, buttons, cards, dialogs) as the website. |
| `website/css/compare.css` | Compare-page-only stylesheet. | Design-system compare components (`.cmp-*`, `.pair-*`, `.result-*`). |
| `website/js/app.js` | Landing-page logic; owned theme, search, dialogs, PWA and SW-update toast in one 1,233-line file that the other pages could not reuse. | `website/js/core.js` (OS namespace: theme, ⌘K palette, search engine, PWA, toasts) + `website/js/site.js` (page renderers). |
| `website/js/compare.js` | Compare-page logic duplicated the app lookup / render helpers from `app.js`. | The compare renderer in `website/js/site.js` (dispatched on `body[data-page]`). |
| `scripts/generate_pages.py` | Standalone app-page regeneration that duplicated the pipeline's app-page stage (its Makefile-only `pages` target was removed). | `python3 scripts/omnisource.py --no-sync --no-health` rebuilds pages from `state.json`; the pipeline's app-page stage is the single writer of `apps/`. |

## Files rewritten in place

| File | Change |
| --- | --- |
| `website/index.html` | Full rebuild: immersive hero, rails, statistics, source health, install guide, catalog, timeline, trust section — on the design system. |
| `website/compare.html` | Reduced to a redirect shim; the compare page moved to `website/compare/` (path-based, deep-linkable, shareable) preserving `?left=&right=`. |
| `website/sw.js` | v2 → v3: caches the whole page set (`/`, `compare/`, `status/`, `analytics/`, `install/`, `search/`), design-system CSS, stale-while-revalidate for every JSON feed, per-app pages cached on first visit. |
| `website/manifest.webmanifest` | Added PWA shortcuts (Catalog, Updates, Compare, Health, Install). |
| `src/omnisource/app_pages.py` | App Store-style template: tinted glass hero, capsule Get button, numbered sections, release-notes `<details>`, trust checklist, install cards, related apps, QR dialog, JSON-LD `SoftwareApplication`. Replaces ~300 lines of per-page inline `PAGE_SCRIPT` JS and inline CSS with shared `js/core.js` + design-system links. Also made CI-lint clean: long template lines wrapped as adjacent string concatenations (generated HTML byte-identical) and quote style normalized by `ruff format`. |
| `scripts/build_site.py` | Thin wrapper over the new `src/omnisource/site.py` builder, which now also emits `sitemap.xml`, `robots.txt`, minified design-system CSS and the gz API mirror. |
| `scripts/merge_feeds.py` | Fixed the same pre-existing stale skip-list bug as `scripts/validate_jq.sh`: `NON_FEED_FILES` had never been extended for the Phase 4–13 intelligence documents, so the merge exited with "community.json must contain exactly one app entry" and the "Rebuild apps.json from feeds/" CI job failed on every run. It now imports the canonical `ALTSTORE_NON_FEED` from `src/omnisource/constants.py`, so the list cannot drift again. |
| `src/omnisource/screenshots.py` + `src/omnisource/pipeline.py` | Fixed a real reproducibility bug in the "Verify generated artifacts are reproducible" CI job: `feeds/screenshots.json` embedded download results (`mirrored`/`size`/`sha256`) that depend on whether the *build machine* can reach third-party screenshot hosts, so the offline rebuild in the check drifts whenever the verifying environment differs from the one that generated the committed file. A mirror already on disk is now trusted as-is (deterministic offline rebuild, transient remote failures can no longer demote a good mirror); real sync runs pass `refresh=True` and re-download so upstream updates still land. |
| `scripts/check_reproducible.py` | Normalizes the network-dependent mirror state of `feeds/screenshots.json` before comparing (the URLs and thumbnail metadata stay fully checked), matching the existing date normalization for `generatedAt`/`lastSync`. |
| `Makefile` | `make check` now runs the entire CI gate, including `merge_feeds.py --check`, `check_reproducible.py --diff` and `ruff format --check` — the gap that let the two stale-skip-list bugs and the line-length lint ship in the first place. |
| `scripts/validate_jq.sh` | Fixed a pre-existing bug: the "not an AltStore feed" skip-list had never been extended for the Phase 4–13 intelligence documents, so `trending.json`, `related.json`, `reputation.json`, `download-intelligence.json`, `community.json`, `install.json`, `search-index.json`, `compare.json` and `screenshots.json` were wrongly validated against the AltStore v2 `.apps[]` contract and failed every run (reproduced on `main`). The list now mirrors `ALTSTORE_NON_FEED` from `src/omnisource/constants.py`. |
| `website/js/core.js` | (new file, bug note) count-up observer now arms a retry when the async value is set after first paint, and ratio values like `22/22` render directly — the hero stats previously could stay at `0` in real browsers. |

## Files added

| File | Purpose |
| --- | --- |
| `assets/design-system/{tokens,components,utilities,animations}.css` | The single design system (Apple-inspired glassmorphism, auto/light/dark tokens, motion, components). |
| `assets/*.webp` (21 files) | WebP icons, 85% smaller than the PNG originals (1.23 MB → 0.19 MB for the icon set). PNGs are kept as `<picture>`/legacy fallbacks; the validator treats a `.png` next to a referenced `.webp` as an intentional pair, not dead weight. |
| `website/js/core.js`, `website/js/site.js` | Shared front-end logic (see above). |
| `website/{compare,status,analytics,install,search}/index.html` | First-class pages: comparison matrix, Source Health Center, analytics dashboard, install center, search page. |
| `src/omnisource/site.py` | Modular site builder (copy + API mirror + sitemap + robots + minify + gzip). |

## Conserved functionality (verified)

- **22/22 app pages** regenerate with every build, including duplicate-group
  warnings, per-app install cards, release notes and the trust checklist.
- **22 AltStore feeds + `apps.json` + RSS** keep their exact URL contract
  (flat root + `/feeds/` organized + `/api/` mirror in the deployed site).
- **All 15 intelligence documents** (`discovery`, `sources`, `verification`,
  `status`, `duplicates`, `analytics`, `updates`, `health`, `trending`,
  `related`, `reputation`, `download-intelligence`, `community`, `install`,
  `search-index`, `compare`, `screenshots`) unchanged in shape.
- **Search** still runs over name / subtitle / description / category /
  tags / developer / bundle identifier with the Fuse.js-compatible index.
- **Deep links** keep working: `compare/?left=<slug>&right=<slug>`,
  `altstore://source?url=…`, `sidestore://source?url=…`,
  `feather://source/<host><path>` (generated by the same rules as
  `src/omnisource/install.py`).
- **CI**: `sync.yml`, `validate.yml`, `merge.yml`, `health-check.yml` and the
  two manual IPA builders were read before any change; none of the removed
  files are referenced by a workflow. `sync.yml`'s `git add` allowlist makes
  the gitignored `api/` safe (ignored files are never force-added).
- **Tests**: 89/89 unit tests pass.

## Metrics

| Measure | Before | After |
| --- | --- | --- |
| Tracked files | 253 | 258* |
| Duplicate JSON trees | `api/` (18 files, ~770 KB) | 0 (gitignored; built into `_site/api/`) |
| Stylesheets | 3 disjoint (61.6 KB) | 1 design system (106 KB raw, ~90 KB minified in `_site`), shared by 7 hand pages + 22 generated pages |
| Front-end JS | `app.js` + `compare.js` (1,407 lines) + ~300 lines inline JS duplicated into **all 22** app pages (≈6,600 duplicated lines) | `core.js` + `site.js` (2,410 lines total) + 22 shared `<script>` tags |
| Generator scripts | 9 in `scripts/` | 8 in `scripts/` (all thin wrappers over `src/omnisource/`) |
| Icon weight (21 icons) | 1.23 MB (PNG) | 0.19 MB (WebP) + PNG fallbacks |
| App page | 17.9 KB self-contained (21 KB of re-downloaded CSS+JS per page, 22×) | ~21 KB HTML referencing shared, cached assets |
| Offline coverage | Home + feed JSON only | Whole site: 7 pages + design system + all feeds + per-app pages on first visit |

\* The tracked-file count is flat-to-up because the old repo counted each
generated app page and feed once; the rebuild added 5 new site pages, the
design system and WebP assets while removing the 18-file `api/` duplicate
tree and 5 legacy front-end files. The consolidation target is the
*generator surface*: 3 stylesheets → 1 system, 2 logic files + 22 inline
copies → 2 files, 2 page generators → 1 pipeline stage, and the 18-file
duplicate JSON tree removed entirely.

## What was deliberately NOT removed

- `feeds/feed.xml` + `feeds/rss.xml` — identical content, but `feed.xml` is
  the AltStore-compatible source URL and `rss.xml` the reader-friendly name;
  both are subscriber-facing contracts.
- `.github/workflows/build-tweak.yml` / `build-uyouenhanced.yml` — manual
  IPA builders, not dead.
- `sdk/` — public SDK surface (JS + Python) consuming the API.
- PNG icons — kept as fallbacks (see WebP note above).
- `feeds/state.json` — runtime sync state, already excluded from the site.

## Follow-up: dedup + bug-fix pass (PR #20, merged on top of this report)

A second agent pass independently found the same two CI-red bugs (stale
`merge_feeds.py` skip-list, offline `screenshots.json` drift) plus more, and
was reconciled with this report's fixes at merge time:

- `merge_feeds.py` — kept this report's canonical `ALTSTORE_NON_FEED` import
  (as a defensive `set()` copy) and additionally deduplicated onto the
  shared `omnisource.io` JSON helpers (203 → 158 lines, byte-identical
  `apps.json`).
- `screenshots.py` + `pipeline.py` — kept this report's trust-on-disk /
  `refresh=True` mechanism and added a `previous`-document fallback layer:
  fresh checkouts (CI) have no on-disk mirrors since mirrors are not
  committed to git, so unchanged URLs reuse the last committed mirror
  metadata instead of degrading. The `check_reproducible.py` mirror-state
  normalization from this report stays as a backstop.
- `sdk/javascript/omnisource.{mjs,cjs}` — fixed a quadratic-ReDoS CodeQL
  alert (`/\/+$/` on caller-supplied `baseURL`) with an identical
  linear-time `stripTrailingSlashes()` helper in both twins.
- Also fixed: the ⌘K palette `open` flag/method collision (palette never
  opened), `sw.js` sub-path matching (v4), SDK CJS/MJS edge-case drift, and
  ~550 lines of duplication (`tracking.py` wrappers, a second HTTP probe,
  23 inline QR scripts → one `core.js` binding). Test suite: 102 tests.
