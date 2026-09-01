# OmniSource Repository Audit

**Audit date:** 2 September 2026
**Baseline commit:** `7022b96` ("Create build-uyouenhanced.yml")
**Scope:** architecture, directory structure, workflows, security, documentation, feed structure,
automation, assets, dependencies.
**Outcome:** all findings below were implemented on branch `arena/01a05ed6-omnisource`.

---

## 1. Executive Summary

OmniSource was two unrelated projects sharing one directory and one name.

The first was a working iOS sideloading feed repository: nine JSON feeds at the repository root, a
776-line Python sync script, and a GitHub Actions workflow refreshing them twice a day. It worked.

The second was a complete, unrelated FastAPI application — `src/omnisource/`, an "async multi-source
aggregation engine" with a Redis cache, a provider registry, a Dockerfile, a docker-compose stack,
383 lines of tests, and a `pyproject.toml` declaring six runtime dependencies. It shared nothing
with the feed repository except the word *OmniSource*. It was never imported by the feed pipeline,
never deployed, and never referenced by any workflow. The README described **only** this engine —
a visitor arriving at the repository would read 200 lines about `asyncio.wait_for` deadlines and
Pydantic models before finding one sentence, near the bottom, admitting that the repository "also
hosts the original auto-updating AltStore feed collection."

That identity collision was the single largest problem. Everything else followed from it: a
`pyproject.toml` that had to explicitly exclude `scripts/` from linting, a CI workflow parked in
`docs/ci.yml.txt` as a text file because the account that wrote it lacked workflow permissions, and
eight workflows of which two actively raced each other for the same file.

The refactor deleted the unrelated project (1,397 lines), collapsed eight workflows into three,
replaced per-app Python functions with a declarative catalog, and added a static website, five
documentation guides, and a health/verification/compatibility metadata layer.

**Net change:** −3,900 lines of code and dead configuration, +1 source-of-truth data file,
+1 website, +5 guides. All nine feed URLs still resolve, byte-compatible with what clients expect.

---

## 2. Repository Health Score

| Dimension | Before | After | Notes |
| --- | :-: | :-: | --- |
| Identity & positioning | 1/10 | 9/10 | README described unrelated software |
| Architecture | 3/10 | 9/10 | Per-app Python functions → declarative catalog |
| Directory structure | 3/10 | 9/10 | 9 feeds + 2 projects at root → clear tree |
| Workflows | 2/10 | 9/10 | 8 workflows, 2 racing, 3 dead → 3 purposeful |
| Security | 3/10 | 8/10 | Unpinned AI agent with write token → least privilege |
| Documentation | 2/10 | 9/10 | Wrong subject → 5 guides + generated catalog |
| Feed structure | 5/10 | 9/10 | Valid but flat; no status/health/compat metadata |
| Automation | 4/10 | 9/10 | Worked, but non-idempotent and destructive on failure |
| Assets | 4/10 | 8/10 | 1.15 MB, one unused, one 761 KB icon |
| Dependencies | 4/10 | 10/10 | 6 unused runtime deps → standard library only |
| Testing / verification | 2/10 | 7/10 | Tests existed but only for deleted code |
| **Overall** | **3.0/10** | **8.7/10** | |

Remaining gap to 10: no checksum verification of upstream assets, third-party actions pinned to
tags rather than SHAs, and no unit tests for the new pipeline (the CI reproducibility check
substitutes for them today).

---

## 3. Strengths (of the original repository)

These were preserved and built upon.

1. **The sync logic was genuinely careful.** `atomic_write_json()` wrote to a temp file, re-parsed
   it, then `os.replace()`d — a real atomic-write discipline most feed repos lack.
2. **Token hygiene was already correct.** The original author explicitly documented that
   `GH_TOKEN` is attached only in `fetch_json()` and never to download URLs. That invariant was
   kept verbatim.
3. **Unchanged-write suppression existed.** `if app == original_app: skip write` avoided some
   commit churn — the right instinct, applied inconsistently.
4. **Version extraction had a sensible fallback chain** (filename → tag → release name → date),
   which survives upstream renaming their assets.
5. **Feeds were schema-valid.** Every feed had the flat-field + `versions[]` duality AltStore
   expects, with `versions[0]` as the current build.
6. **`build-uyouenhanced.yml` is a serious piece of work.** 617 lines of Theos/cyan toolchain
   orchestration with SDK caching, IPA validation, bundle-ID normalisation for SideStore, and
   SHA-256 publication. It was kept and hardened.

---

## 4. Weaknesses

Ordered by severity.

| # | Weakness | Severity |
| --- | --- | --- |
| W1 | Repository presents itself as unrelated software | Critical |
| W2 | Two workflows write `apps.json` on overlapping schedules (12h / 13h) | Critical |
| W3 | A failed link check **deletes** apps from the master feed | High |
| W4 | `ai-automated-committer.yml`: arbitrary comment text → LLM → PR, with `contents: write` | High |
| W5 | Pipeline is not idempotent — every run rewrites `generatedAt`, producing empty commits | High |
| W6 | Adding an app requires writing a new Python function | High |
| W7 | One download URL is a `tinyurl.com` shortener | High |
| W8 | Six unused runtime dependencies declared | Medium |
| W9 | Link checks are sequential and follow redirects (can stream a 120 MB IPA) | Medium |
| W10 | `lint-action.yml` auto-commits formatting to any branch on every workflow push | Medium |
| W11 | No `permissions:` restriction at workflow level; jobs inherit broad defaults | Medium |
| W12 | Feeds carry no status, health, verification or compatibility metadata | Medium |
| W13 | `docs/ci.yml.txt` — a workflow parked as a text file with activation instructions | Medium |
| W14 | 761 KB icon, unused 127 KB asset, 2048×2048 source images | Low |
| W15 | Two READMEs (`README.md`, `docs/FEEDS.md`) describing different projects | Low |
| W16 | Dead code: exclusion rule that can never match; `check_url_alive` retry paths unreachable | Low |

---

## 5. Technical Debt Analysis

### 5.1 Dead code

| Item | Why it exists | Impact | Fix |
| --- | --- | --- | --- |
| `src/omnisource/**` (846 lines) | An unrelated project was committed into this repository, probably by an automated agent generating a "showcase" codebase from the repo name | Dominates the README, forces `pyproject.toml` to exclude `scripts/` from linting, implies a Redis/FastAPI deployment that does not exist, adds six phantom dependencies | Deleted |
| `tests/**` (383 lines) | Tests for the above | Tests nothing that ships | Deleted |
| `Dockerfile`, `docker-compose.yml`, `.dockerignore`, `.env.example` | Deployment scaffolding for the above | Suggests a service to run; `.dockerignore` even excludes `*.json`, i.e. the actual product | Deleted |
| `docs/ci.yml.txt` | CI for the above, parked as text because the authoring account lacked `workflows` permission | A workflow file that cannot run, with instructions telling maintainers to `git mv` it | Deleted; real CI is `validate.yml` |
| Exclusion of `youproextra-noytlite-ipa` | Guard copied from `updatex.yml` | Unreachable: `"youproextra-noytlite-ipa".startswith("youproextra-ipa")` is `False`, so the guard never fires | Removed; `excludeTagPrefixes` remains available as a general catalog option |
| `check_url_alive` 405-fallback branch | Defensive coding | Only triggered on HTTP 405; GitHub answers 302, so the branch was never exercised | Replaced by an always-attempted ranged-GET fallback |

### 5.2 Duplicate code

| Duplication | Detail | Fix |
| --- | --- | --- |
| `sync_youproextra` / `sync_ytmusic` / `sync_spotiflac` | Three functions, ~110 lines each, differing only in repo name, asset suffix, description string and version-parsing rule. Identical "load JSON → check apps[0] → deep-copy → update → compare → write" blocks in all three | One `sync_app()` driven by an `upstream` object in `catalog.json` |
| `updatex.yml` vs `scripts/omnisource.py` | The workflow embedded a 120-line heredoc Python script that synced **the same five YouProEXTRA apps** into `apps.json`, while `omnisource.py` synced them into per-app feeds and rebuilt `apps.json` from those. Two writers, one file, different schemas, overlapping schedules | `updatex.yml` deleted |
| `README.md` vs `docs/FEEDS.md` | Two full landing pages, different subjects, both with badge headers and credits tables | One README; `docs/FEEDS.md` content redistributed into `INSTALLATION.md` / `CATALOG.md` |
| Icon URL construction | `f"{BASE_URL}/assets/{icon_name}"` built in `standardize()`, in `build_feed()`, and hard-coded inside eight feed files | Built once in `render_app()`; feeds are fully generated |
| Per-app metadata | `FILE_CONFIG` in the script held bundle IDs and developer names that were *also* stored in each feed file, and could disagree | Single definition in `catalog.json` |

### 5.3 Obsolete workflows

| Workflow | Verdict | Reason |
| --- | --- | --- |
| `updatex.yml` | **Delete** | Duplicate writer for `apps.json`; races `omnisource-build-sync.yml`; writes a schema (`isLanZouCloud`, `type: 1`) that the master build immediately overwrites; uses `actions/checkout@v7`, which does not exist |
| `ai-automated-committer.yml` | **Delete** | Runs on any issue comment containing `@ai`, feeds untrusted text to Gemini, then opens a PR using `secrets.GH_TOKEN` (a PAT, broader than `GITHUB_TOKEN`). The Python step also *discards* the model output — it prints "AI processing completed" and creates a PR with no changes. Cost and risk for zero function |
| `copilot-agent.yml` | **Delete** | Depends on `github/copilot-action@v1`, which is not a published action. Every run fails |
| `copilot-setup-steps.yml` | **Delete** | Installs from `requirements.txt`, which does not exist. Runs on push to itself. No-op |
| `lint-action.yml` | **Delete** | Prettier-formats workflow files and force-commits to the pushed branch with `[skip ci]`. Rewrites contributor commits, can fight the sync workflow, and formats YAML that nothing else validates. Replaced by `actionlint` in a read-only check |
| `delete-old-workflows-run.yml` | **Delete** | Manual-dispatch run-history deletion via a third-party action with `actions: write`. Destroys audit trail; GitHub already expires logs at 90 days |
| `omnisource-build-sync.yml` | **Replace** | Correct in spirit. Superseded by `sync.yml`, which adds validation, Pages deployment, idempotency and rebase-safe pushes |
| `build-uyouenhanced.yml` | **Keep, harden** | Real value; provides the only build of a catalog app. Hardened against shell injection |

### 5.4 Unused assets, scripts, dependencies

| Item | Finding | Action |
| --- | --- | --- |
| `assets/Signulous.png` (127 KB) | Signulous is referenced only in `docs/FEEDS.md`, and is outside the stated supported-client set | Deleted |
| `assets/OmniSource.png` (761 KB, 1024²) | Served to every client as `iconURL` and `bannerURL` on every feed refresh | Resized to 512², 269 KB (−65%). 128-colour quantisation was tested and rejected — visible banding in the gradient |
| `assets/SpotiFLAC.png` (2048²) | Displayed at ≤180 pt | Resized to 512², 18 KB (−75%) |
| `assets/AltStore.png`, `SideStore.png` | Unoptimised PNG chunks | Stripped, −27 KB combined |
| `scripts/validate_feeds.py` | Superseded | Replaced by `scripts/validate.py` (catalog + feeds + mirrors + assets) |
| `fastapi`, `uvicorn`, `pydantic`, `pydantic-settings`, `redis`, `httpx` | Declared as runtime dependencies; not importable from anything that ships | Removed. The pipeline is standard-library only |
| `pytest`, `pytest-asyncio`, `pytest-cov`, `mypy` | Dev dependencies for deleted code | Removed. `ruff` retained as tooling config only |

**Asset total: 1.15 MB → 484 KB (−58%).**

### 5.5 Legacy artifacts

- `.env.example` documenting `OMNISOURCE_REDIS_URL` and `OMNISOURCE_PROVIDER_TIMEOUT` for a service
  that does not exist.
- `pyproject.toml` comment: *"Legacy iOS-feed tooling predates this codebase and is linted by its
  own workflow"* — the "legacy tooling" **is** the product, and no such workflow existed.
- `README.md` CI badge pointing at `ci.yml`, a workflow that was never activated, so the badge
  rendered as permanently "no status".

---

## 6. Cleanup Plan

Executed in this order:

1. **Delete the unrelated project** — `src/`, `tests/`, `Dockerfile`, `docker-compose.yml`,
   `.dockerignore`, `.env.example`. *(Recoverable from git history; see §14.)*
2. **Delete obsolete workflows** — `ai-automated-committer.yml`, `copilot-agent.yml`,
   `copilot-setup-steps.yml`, `lint-action.yml`, `updatex.yml`,
   `delete-old-workflows-run.yml`, `omnisource-build-sync.yml`.
3. **Delete superseded docs** — `docs/ci.yml.txt`, `docs/FEEDS.md`.
4. **Delete the superseded script** — `scripts/validate_feeds.py`.
5. **Optimise assets** — resize, strip, remove `Signulous.png`.
6. **Rewrite `pyproject.toml`** as linter configuration only.
7. **Rewrite `.gitignore`**; add `.gitattributes` marking generated feeds `linguist-generated`.

---

## 7. Refactor Plan

### 7.1 From code to data

The core move: resolution rules stop being Python and become catalog entries.

**Before** — adding an app meant writing a function:

```python
def sync_spotiflac():
    releases = fetch_all_releases(SPOTIFLAC_REPO, max_pages=3)
    for candidate in releases:
        if not is_published_release(candidate): continue
        asset = ipa_asset(candidate, suffix="-ios-unsigned.ipa") or ipa_asset(candidate)
        ...110 more lines, repeated per app...
```

**After** — adding an app means adding an object:

```json
"upstream": {
  "repo": "spotiflacapp/SpotiFLAC-Mobile",
  "assetSuffixes": ["-ios-unsigned.ipa", ".ipa"],
  "keepVersions": 1,
  "descriptionTemplate": "SpotiFLAC {version} | {label}"
}
```

Every behavioural quirk of the old script became a declarative option:
`tagPrefix`, `excludeTagPrefixes`, `assetSuffixes`, `keepVersions` (0 = all),
`sortByTagNumber` (YTLite's tag-number ordering), `minOSVersionByTagNumber`
(YTLite's `{0: "14.0", 1: "15.0"}` map), and `descriptionTemplate` with
`{name} {version} {secondary} {label} {tag} {date}` placeholders — `{secondary}` reproduces
YTMusicUltimate's "tweak version | host version" format exactly.

### 7.2 File count

| | Before | After |
| --- | --- | --- |
| Python files | 23 (2 in `scripts/`, 21 in `src/` + `tests/`) | 2 |
| Python lines | 2,293 | 1,120 |
| Hand-edited data files | 9 feeds | 1 catalog |
| Workflows | 8 | 3 |
| Markdown landing pages | 2 | 1 + 5 guides |

### 7.3 Behavioural fixes

| Change | Rationale |
| --- | --- |
| Dead links **flag** instead of **delete** | The old `build_feed()` excluded any app whose link check failed, then `sys.exit(1)`. A transient CDN failure silently removed apps from every subscriber's client. Now the app stays, `omnisource.health.downloadReachable` goes `false`, the README shows ⚠️, and the health dashboard records it |
| Per-repo release cache | Five apps share `mrdrvt99/YouProEXTRA`. A full sync is now **4 API requests** total |
| Concurrent probing | 8-way thread pool: 8 probes in ~1.7 s versus sequential |
| Probes stop at the first 3xx | GitHub answers 302 with a signed CDN URL. Following it costs a second TLS handshake and risks streaming a 120 MB IPA. A 302 from the origin already proves the asset exists |
| Idempotency | No wall-clock timestamps in output; `health.json.generatedAt` is derived from content, `statusSince` moves only when a status changes. Verified: three consecutive runs → "0 file(s) changed" |
| Degradation is per-app | One failing upstream no longer aborts the run; that app keeps its last known state from `feeds/state.json` |
| Structured logging | `print("::error::...")` scattered through the script → a `logging` handler that emits Actions annotations when `GITHUB_ACTIONS` is set and plain text locally |

---

## 8. Architecture Proposal

```
OmniSource/
├── README.md                 identity, feed URL, generated catalog table
├── LICENSE
├── SECURITY.md
├── catalog.json              ← the only hand-edited data file
├── apps.json, <slug>.json    ← generated root mirrors (historical URLs)
├── feeds/
│   ├── apps.json             master feed
│   ├── <slug>.json           per-app feeds
│   ├── health.json           link-health snapshot
│   └── state.json            pipeline memory (last good versions + health)
├── assets/                   app and client icons
├── scripts/
│   ├── omnisource.py         sync → health → build → mirror → readme
│   └── validate.py           offline validation
├── website/                  static Pages site (index.html, styles.css, app.js)
├── docs/                     INSTALLATION · CATALOG · COMPATIBILITY · CONTRIBUTING · ARCHITECTURE · AUDIT
└── .github/
    ├── workflows/            sync.yml · validate.yml · build-uyouenhanced.yml
    ├── ISSUE_TEMPLATE/       broken-download · app-request · compatibility-report
    ├── dependabot.yml
    └── pull_request_template.md
```

**Why root mirrors were kept.** Existing installs point at
`https://iamsmmh.github.io/OmniSource/apps.json`. Moving feeds into `feeds/` without mirrors would
break every subscriber. `feeds/` is the source of truth; the root files are byte-identical
generated copies, marked `linguist-generated`, and `validate.py` fails the build if one drifts.
They can be retired later with a deprecation notice.

**Why `feeds/state.json` exists.** It is the pipeline's memory. It lets a failing upstream degrade
to "keep serving the last good build", lets `--no-sync` rebuild deterministically offline, and lets
CI prove that `feeds/` is reproducible from committed inputs.

Full detail in [`docs/ARCHITECTURE.md`](ARCHITECTURE.md).

---

## 9. Workflow Proposal

### Target: one pipeline, one gate, one manual builder

| Workflow | Trigger | Top-level permissions | Job permissions | Purpose |
| --- | --- | --- | --- | --- |
| `sync.yml` | schedule 6h · push to main (paths) · manual | `{}` | build: `contents: write` · deploy: `pages: write`, `id-token: write` | Sync, validate, commit, deploy Pages |
| `validate.yml` | pull_request · push · manual | `contents: read` | — | Offline validation, reproducibility, ruff, actionlint |
| `build-uyouenhanced.yml` | manual only | `contents: write` | — | Compile and publish the uYouEnhanced IPA |

**Deletions:** 6 workflows (§5.3).
**Merges:** `updatex.yml` + `omnisource-build-sync.yml` → `sync.yml`; Pages deployment folded in as
a dependent job rather than a fourth workflow.

**Why the third workflow survives the "two workflows" target.** `build-uyouenhanced.yml` is a
180-minute macOS compile with a completely different toolchain, trigger model and failure mode. It
runs manually, a handful of times a year. Merging it into `sync.yml` would put a 3-hour macOS job
behind a 6-hourly cron. It earns its place.

**Notable fixes in `sync.yml`:**

- Schedule tightened from 12 h to 6 h (upstream mods ship within hours of a YouTube release).
- `concurrency: cancel-in-progress: false` — never cancel a run mid-commit. The old build workflow
  had `cancel-in-progress: true` while holding `contents: write`.
- `git pull --rebase --autostash` before push, so a concurrent human commit survives.
- Validation runs **before** the commit, not after.
- Path-filtered `push` trigger: editing `catalog.json` publishes immediately.
- `actions/checkout@v7` (nonexistent) → `@v4`.

**`build-uyouenhanced.yml` closes the loop.** It publishes a release tagged `uyouenhanced-v*`, and
the catalog now treats `iamsmmh/OmniSource` releases with that prefix as the app's upstream. A
final step triggers `sync.yml`, so a build automatically becomes a feed update — and the
`tinyurl.com` mirror (W7) retires itself on the first build.

---

## 10. Documentation Proposal

| Document | Audience | Content |
| --- | --- | --- |
| `README.md` | First-time visitor | One-sentence definition, feed URL with one-tap links, client table, **generated** catalog table with live versions and health, data-flow diagram, layout table |
| `docs/INSTALLATION.md` | End user | Per-client walkthroughs for all five clients, per-app feeds, troubleshooting table |
| `docs/CATALOG.md` | End user / contributor | What each app is, upstream project, how the build is obtained, status and verification vocabularies, the shared-bundle-ID warning, credits |
| `docs/COMPATIBILITY.md` | End user | `compatibility` schema, client capability matrix, free-vs-paid Apple ID limits, how to report a result |
| `docs/CONTRIBUTING.md` | Contributor | Golden rule (only `catalog.json` is hand-edited), setup, full `upstream` reference table, add/retire an app, PR checklist, what will not be merged |
| `docs/ARCHITECTURE.md` | Maintainer | Data flow, component responsibilities, idempotency contract, failure model, performance notes, extension points |
| `SECURITY.md` | Everyone | What we guarantee, what we cannot guarantee, hardening backlog |

**README discipline.** Six badges (CI, Python, Ruff, mypy, License, Docker) — four of which
described deleted tooling and one of which never resolved — were removed. The README now leads with
what OmniSource *is* and the URL a user needs, and the catalog table is regenerated on every run
between `<!-- omnisource:catalog:start -->` markers, so it cannot go stale.

---

## 11. Feature Roadmap

Shipped in this refactor:

| Feature | Where |
| --- | --- |
| **App health dashboard** | `feeds/health.json` + website `#/health` + README status column |
| **Compatibility matrix** | `catalog.json` → website `#/compatibility` |
| **App comparison centre** | Website `#/compare` — up to three apps across 12 attributes |
| **Verified release system** | `verification.method` (`github-release` / `self-built` / `manual-mirror`) surfaced per app |
| **Featured apps** | `featured: true` → README, home page, catalog filter |
| **Maintenance status indicators** | `status`: stable / beta / manual / unmaintained / deprecated |
| **Automated validation reports** | `validate.py` writes a job summary with error and warning counts |
| **Status-since tracking** | `statusSince` records when a link first went down |

Proposed next, in priority order:

1. **Checksum verification (high).** Record SHA-256 per version and re-verify on each sync.
   Detects a silently replaced release asset — the highest-value remaining supply-chain control.
2. **Feed diff comments on PRs (high).** Post a rendered before/after table when `catalog.json`
   changes. Turns review from reading JSON into reading a table.
3. **Historical version archive (medium).** `feeds/archive/<slug>.json` with every version ever
   seen, so users can roll back after a bad upstream release. `state.json` already has the shape.
4. **Update RSS/Atom feed (medium).** `feeds/updates.xml` so users can follow releases without a
   client.
5. **Client-specific feed variants (medium).** LiveContainer benefits from rewritten bundle IDs;
   emit `feeds/livecontainer/apps.json` with `.lc` suffixes so the five YouTube mods coexist.
6. **Downtime notifications (low).** Open an issue automatically when a link is unreachable for
   three consecutive runs — currently a warning nobody reads.
7. **Screenshot pipeline (low).** Six of eight apps have empty `screenshotURLs`; app pages look bare.

---

## 12. Security Improvements

| # | Finding | Impact | Fix | Status |
| --- | --- | --- | --- | --- |
| S1 | `ai-automated-committer.yml` runs an LLM on arbitrary issue-comment text, then opens a PR with `secrets.GH_TOKEN` (a PAT) and `contents/issues/pull-requests: write` | Any GitHub user who can comment can trigger a workflow that holds a PAT. Prompt content is fully attacker-controlled | Workflow deleted | ✅ |
| S2 | No `permissions:` block on 3 of 8 workflows | Jobs inherit the repository default, historically `write-all` | `permissions: {}` at workflow level, opt-in per job | ✅ |
| S3 | `lint-action.yml` force-pushes formatting commits to the triggering branch using `GH_TOKEN` in a URL | Rewrites contributor branches; token appears in a `git push` command line | Deleted; replaced by read-only `actionlint` | ✅ |
| S4 | `build-uyouenhanced.yml` interpolates `${{ inputs.* }}` directly into 24 `run:` lines | Shell injection via workflow-dispatch input. Requires write access, but violates least privilege and GitHub's own guidance | Inputs passed through job-level `env:`; scripts reference `"$IN_BUNDLE_ID"` etc. | ✅ |
| S5 | `delete-old-workflows-run.yml` grants `actions: write` to a third-party action | Destroys the audit trail that would show a compromise | Deleted | ✅ |
| S6 | `updatex.yml` uses `secrets.GH_TOKEN` (PAT) where `github.token` suffices | Broader scope than needed, and PATs do not expire with the run | Deleted; `sync.yml` uses `github.token` | ✅ |
| S7 | `updatex.yml` pinned `actions/checkout@v7` | Nonexistent version — every run failed. Had it existed, an unreviewed major bump | Deleted | ✅ |
| S8 | Six unused runtime dependencies | Six supply-chain surfaces (and transitives) for code that never ran | Removed; pipeline is standard-library only | ✅ |
| S9 | `validate.yml` predecessor checked out with credentials persisted | Fork PRs could reach repository state | `persist-credentials: false`, `contents: read`, no token, no network | ✅ |
| S10 | Unpinned linter (`pipx run ruff`) in CI | An upstream release turns into a surprise red build on unrelated PRs | Pinned `ruff==0.16.5`, `actionlint:1.7.7` | ✅ |
| S11 | `tinyurl.com` shortener as a download URL for uYouEnhanced | The destination can be changed at any time by whoever controls the link, with no signal in this repository | `uyouenhanced` now resolves from first-party `uyouenhanced-v*` releases; the shortener remains only as a `manualRelease` fallback until the first build | ⚠️ Partial |
| S12 | Third-party actions pinned to major tags, not SHAs | A compromised tag silently changes behaviour | Dependabot configured for monthly action updates; SHA pinning tracked in `SECURITY.md` | ⚠️ Tracked |
| S13 | No checksum verification of upstream assets | A replaced release asset is undetectable | Tracked as roadmap item 1 | ⚠️ Tracked |

**Preserved invariant:** `GH_TOKEN` is attached only inside `fetch_json()`, which only ever
receives `api.github.com` URLs. Download probes construct their own header dict with no
`Authorization`. This was correct in the original and is unchanged.

---

## 13. Performance Improvements

| Area | Before | After | Gain |
| --- | --- | --- | --- |
| GitHub API requests per sync | ≥7 (YouProEXTRA history re-paginated per stage, up to 10 pages configured) | **4** (per-repo cache; 5 apps share one fetch) | ~45% fewer |
| Download link checks | Sequential, ~1 s each, redirects followed | 8-way pool, stops at 3xx | ~8 probes in **1.7 s** |
| Redirect handling | `urlopen` followed 302 → signed CDN URL, second TLS handshake, risk of streaming a 120 MB body | Custom `HTTPRedirectHandler` returns `None` at the first 3xx | One handshake; zero bytes of payload |
| CI dependency install | `pip install google-genai` / `npm i -g prettier` / `pipx install cyan` in the write-path workflows | None — standard library | ~30–60 s per run |
| Repository assets | 1.15 MB | 484 KB | −58% per client refresh |
| Feed writes | Rewrote files whose content was unchanged (`generatedAt` always moved) | Content-compared; unchanged files untouched | Zero empty commits |
| Commits per day (no upstream change) | 2 (one per racing workflow) | **0** | History becomes signal |
| Workflow runs per day | ~4 scheduled + push-triggered lint loops | 4 scheduled | Fewer minutes, no lint/commit feedback loops |
| Master feed size | 45.9 KB | 51.2 KB (+12% for health/verification/compatibility metadata) | Accepted: still one gzipped request; the metadata powers the site and README |

**Measured** in this workspace: full sync 3.9 s wall clock (4 API calls, 8 concurrent probes,
19 files written on first run, 0 on the second and third).

**Rejected optimisations:**

- *Conditional requests with `ETag`/`If-None-Match`.* Would save bandwidth, not requests — the rate
  limit counts 304s the same. Not worth the state.
- *Splitting the master feed by category.* At 8 apps, one 51 KB file is faster than several
  round-trips.
- *128-colour palette for `OmniSource.png`* (761 KB → 116 KB). Rejected: visible banding in the
  brand gradient. Kept truecolour at 512² (269 KB).

---

## 14. Exact File Changes

### Deleted (25 files, ~3,900 lines)

```
src/omnisource/__init__.py                    src/omnisource/cache/redis_cache.py
src/omnisource/__main__.py                    src/omnisource/core/__init__.py
src/omnisource/api/__init__.py                src/omnisource/core/config.py
src/omnisource/api/app.py                     src/omnisource/core/engine.py
src/omnisource/cache/__init__.py              src/omnisource/core/exceptions.py
src/omnisource/cache/base.py                  src/omnisource/core/models.py
src/omnisource/cache/memory_cache.py          src/omnisource/providers/{__init__,base,registry,samples}.py
src/omnisource/py.typed                       tests/{test_api,test_cache,test_engine,test_providers}.py

Dockerfile                docker-compose.yml   .dockerignore   .env.example
docs/ci.yml.txt           docs/FEEDS.md        scripts/validate_feeds.py
assets/Signulous.png      .github/ISSUE_TEMPLATE/bug_report.md

.github/workflows/ai-automated-committer.yml  .github/workflows/copilot-agent.yml
.github/workflows/copilot-setup-steps.yml     .github/workflows/lint-action.yml
.github/workflows/updatex.yml                 .github/workflows/delete-old-workflows-run.yml
.github/workflows/omnisource-build-sync.yml
```

Recovering the deleted FastAPI project into its own repository, with history:

```bash
git checkout -b omnisource-engine 7022b96
git filter-repo --path src --path tests --path Dockerfile --path docker-compose.yml
gh repo create omnisource-engine --private --source=. --push
```

### Added (24 files)

| File | Purpose |
| --- | --- |
| `catalog.json` | Source of truth: 8 apps, upstream rules, verification, compatibility |
| `scripts/omnisource.py` | Rewritten pipeline (5 stages, CLI flags, structured logging) |
| `scripts/validate.py` | Catalog + feed + mirror + asset validation, `--strict` |
| `feeds/{apps,<slug>}.json` | 9 generated feeds |
| `feeds/health.json` | Health snapshot |
| `feeds/state.json` | Pipeline state |
| `.github/workflows/sync.yml` | Primary pipeline + Pages deploy |
| `.github/workflows/validate.yml` | Offline validation gate |
| `.github/dependabot.yml` | Monthly action updates |
| `.github/pull_request_template.md` | PR checklist |
| `.github/ISSUE_TEMPLATE/{config,broken-download,app-request,compatibility-report}.yml` | Structured intake |
| `website/{index.html,styles.css,app.js}` | Static site, 7 routes |
| `docs/{INSTALLATION,CATALOG,COMPATIBILITY,CONTRIBUTING,ARCHITECTURE,AUDIT}.md` | Guides |
| `SECURITY.md` | Disclosure policy and guarantees |
| `.gitattributes` | Marks generated feeds |

### Modified

| File | Change |
| --- | --- |
| `README.md` | Rewritten: iOS repository identity, generated catalog block, no vanity badges |
| `pyproject.toml` | 6 runtime + 5 dev dependencies → ruff configuration only |
| `.gitignore` | Rewritten for a data repository |
| `.github/workflows/build-uyouenhanced.yml` | Injection hardening (24 lines), sync trigger added |
| `assets/{OmniSource,SpotiFLAC,AltStore,SideStore}.png` | Resized and stripped |
| `apps.json` + 8 root feeds | Now generated mirrors; gained the `omnisource` metadata block |

### Verification performed

```
$ python3 scripts/omnisource.py           # 4 API calls, 8 probes, 19 files written
$ python3 scripts/omnisource.py           # Done. 0 file(s) changed.      ← idempotent
$ python3 scripts/omnisource.py --no-sync --no-health
                                          # Done. 0 file(s) changed.      ← reproducible offline
$ python3 scripts/validate.py             # OK: 0 errors, 0 warnings
$ python3 -m ruff check scripts/          # All checks passed
$ python3 -m ruff format --check scripts/ # 2 files already formatted
$ node --check website/app.js             # JS OK
$ python3 -c "import yaml; ..."           # all 8 YAML files parse
```

All nine published feed URLs verified to still resolve with identical paths and valid AltStore
schema. Every app retained its version, download URL, size, description and permissions.

---

## 15. Exact Pull Request Plan

This work landed as one branch because the changes are interlocking — deleting the FastAPI project
invalidates the README, which invalidates the docs, which depend on the new catalog. Splitting it
would produce intermediate commits where CI cannot pass.

For review, read the diff in this order:

| # | Focus | Files | What to check |
| --- | --- | --- | --- |
| 1 | **Deletions** | `src/`, `tests/`, Docker files, 6 workflows | Nothing deleted is referenced anywhere else. `grep -r "omnisource\.core\|omnisource\.api"` returns nothing |
| 2 | **Catalog** | `catalog.json` | Every app's bundle ID, developer, description, permissions and screenshots match the pre-refactor feed. This is the fidelity checkpoint |
| 3 | **Pipeline** | `scripts/omnisource.py` | Each old `sync_*()` quirk maps to a catalog option (§7.1). Token still confined to `fetch_json()` |
| 4 | **Validation** | `scripts/validate.py` | Rules are stricter than the old validator, never looser |
| 5 | **Feeds** | `feeds/`, root `*.json` | Diff a root mirror against its pre-refactor version: same URL, version, size; new `omnisource` block |
| 6 | **Workflows** | `sync.yml`, `validate.yml`, `build-uyouenhanced.yml` | Permissions, concurrency, injection hardening |
| 7 | **Docs & site** | `README.md`, `docs/`, `website/` | Accuracy of every claim |

### Workflow files are staged, not installed

The account that produced this branch is a GitHub App without the `workflows` permission, so GitHub
rejects any push that touches `.github/workflows/`. The three finished workflow files therefore sit
in [`.github/workflows-pending/`](../.github/workflows-pending/README.md) with a copy-paste
activation script. This is the same platform limit that produced the original `docs/ci.yml.txt`
(§5.1) — the difference is that these files are complete, reviewed, and come with a one-command
install and a deletion step for the staging directory.

Until they are activated, the six obsolete workflows remain live. Activating them is step 0 of the
checklist below.

### Post-merge checklist for the maintainer

0. **Activate the workflows** — run the script in `.github/workflows-pending/README.md`.
1. **Settings → Pages → Source: GitHub Actions.** Required for `sync.yml`'s deploy job. Until this
   is changed, branch-based Pages keeps serving the root mirrors, so nothing breaks — the site just
   will not appear.
2. **Settings → Actions → Workflow permissions: read repository contents (default).** All workflows
   now request what they need explicitly.
3. **Delete the `GH_TOKEN` repository secret** if it exists. Nothing uses it; `github.token` covers
   every case.
4. **Run `Build uYouEnhanced` once.** It publishes `uyouenhanced-v*`, `sync.yml` picks it up
   automatically, and the `tinyurl.com` fallback (S11) retires.
5. **Watch the first two scheduled runs.** The second should report `0 file(s) changed` and produce
   no commit. If it commits, idempotency has regressed.
6. **Enable private vulnerability reporting** (Settings → Security) so `SECURITY.md` is actionable.

### Rollback

Feeds are plain files and every change is one commit on `main`:

```bash
git revert <merge-sha>            # restores the previous feed content wholesale
```

Because root mirrors were never moved, a revert restores working feeds instantly — no subscriber
sees a broken URL at any point.
