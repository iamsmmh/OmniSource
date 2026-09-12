# OmniSource — major issues

Static review of `iamsmmh/OmniSource` @ `8edb83e` (branch `arena/01a09439-omnisource`).
Everything below was reproduced in the working tree; line numbers are from that commit.

**What is genuinely healthy:** 235 unit tests pass, `ruff check` + `ruff format --check` are
clean, `validate.py` / `publish_root.py --check` / `merge_feeds.py --check` /
`check_reproducible.py --diff` all pass, no secrets matched a credential scan, and the
Python-side HTML escaping (`src/omnisource/app_pages.py`) is thorough. The problems below are
the ones those checks cannot see.

---

## P0 — High

### 1. Shell injection in `build-tweak.yml` (CWE-94)

`.github/workflows/build-tweak.yml:70,72,79,83` interpolate `workflow_dispatch` inputs directly
into `run:` shell text:

```yaml
curl -L "${{ inputs.base_ipa_url }}" -o workspace/base.ipa
curl -L "${{ inputs.tweak_deb_url }}" -o workspace/tweak.deb
FLAGS+=(-b "${{ inputs.bundle_id }}")
FLAGS+=(-n "${{ inputs.app_name }}")
```

Anyone who can dispatch this workflow gets arbitrary command execution on the runner. The job
declares `permissions: contents: write` and checks out with credentials persisted, so the
`GITHUB_TOKEN` in `.git/config` is in reach.

The sibling workflow already knows better — `build-uyouenhanced.yml:87-98` passes every input
through `env:` with the comment *"workflow_dispatch inputs are passed through the environment
rather than interpolated into `run:` scripts, which would allow shell injection."* Same file,
opposite decision.

**Fix:** mirror `build-uyouenhanced.yml` — move all four inputs into the job `env:` block and
reference them as `"$IN_BASE_IPA_URL"` etc.

---

### 2. Dead-app detection produces false "critical" takedowns

`src/omnisource/pipeline.py:295-305` records a `removedReleases` entry whenever the previously
newest version is absent from the freshly resolved set, and `src/omnisource/dead_apps.py:60-70`
turns any such entry into `classification: "critical"` with the reason *"removed upstream
release(s): …"*.

That test cannot distinguish a takedown from two routine events:

* **Ordinary version bumps.** 75 of 77 catalog rows use `upstream.keepVersions: 1`, so only the
  newest asset is ever offered. `iqface` moved `577.1 → 578.1` and was flagged critical even
  though `578.1` is live.
* **Failover between provider legs.** `swiftgram` still publishes `12.9.2`, but the URL changed
  `Swiftgram-12.9.2-MxGram.ipa → Swiftgram-12.9.2-iQTele.ipa` — same version, different build —
  and that was recorded as a removed release.

Live state for all nine: current download reachable, `HTTP 200`.

| slug | current version | flagged as removed | actual health |
|---|---|---|---|
| iqface | 578.1 | 577.1 | HTTP 200 |
| messenger-flow | 578.1.0 | 577.0.0 | HTTP 200 |
| msgplusx | 578.1.0 | 577.0.0 | HTTP 200 |
| ryukgram | 446.0.0 | 445.0.0 | HTTP 200 |
| sparkle | 446.0.0 | 445.0.0 | HTTP 200 |
| swiftgram | 12.9.2 | 12.9.2 (failover rename) | HTTP 200 |
| telegram-mxgram | 12.9.3 | 12.9.3 (failover rename) | HTTP 200 |
| threadsaver | 446.1 | 445.1 | HTTP 200 |
| turrit-mxgram | 1.5.3 | 1.5.3 (failover rename) | HTTP 200 |

Net effect: `api/dead_apps.json` publishes **33 of 77 apps (43%) as dead**, including 9 as
critical, while the README advertises *"77/77 downloads online"*. `tests/test_intelligence.py:183`
currently asserts the buggy behaviour, so the suite locks it in.

**Fix:** only record a removal when the previous version is *newer* than the current one (a real
rollback) or the old URL fails a probe. Otherwise treat it as supersession and clear the flag.

---

### 3. Full integrity verification never runs

`--verify-downloads` exists at `src/omnisource/cli.py:25-28` and `src/omnisource/integrity.py:185`,
but **no workflow invokes it**, and `src/omnisource/integrity.py:19-20` plus `pipeline.py:839`
document a *"weekly `verify.yml` job"* that is not in `.github/workflows/`.

Evidence: `feeds/state.json` has `lastFullVerification` on **0 of 77 apps**.

So the README's *"SHA-256, verification labels and automated probes keep every download
installable"* is metadata-only: 50/77 apps carry an upstream-published digest, 27 carry none, and
**not one digest is ever checked against the bytes it describes**. The pipeline never streams an
IPA.

**Fix:** add the missing scheduled workflow (the code is written and waiting), or soften the
README claim to "checksums published upstream are surfaced, not verified".

---

### 4. Reputation scores are degenerate — no source can reach "Verified"

Root cause: `catalog.json` sets `upstream.keepVersions: 1` for 75 of 77 apps, so
`feeds/state.json` holds exactly **one** version for 76 apps (one app keeps 3).

Consequences, visible in `api/reputation.json`:

* `updateFrequencyDays` is `None` for **60 of 61** sources, so `_compose_score` falls back to
  `cadence = 0.35` (`src/omnisource/reputation.py:208`) — the 20-point update-frequency signal is
  a constant, not a signal.
* **49 of 61 sources score exactly 73.9.** The score does not discriminate between Aidoku and a
  dormant side project.
* The `Verified` band needs `score >= 85`, which is unreachable while the second-largest weight is
  pinned at 0.35. Result: **0 sources are Verified**; 80% land in "Community Verified" — even
  though the README FAQ presents *Verified* as a live status and `feeds/sources.json` v2 publishes
  `updateFrequencyDays` and `verifiedApps` as if they were meaningful.

Downstream, the same missing history weakens trending, the "update cadence" column on
`/sources/`, and the 90/180/365-day dead-app thresholds (which compare against a single data point).

**Fix:** raise `keepVersions` to ~5–10 (the knob already exists), or compute cadence and release
activity from `state["updateHistory"]` — which already holds 85 real update events — instead of
`state[slug]["versions"]`.

---

## P1 — Medium

### 5. `merge.yml` executes PR-authored code with a write-scoped token

`.github/workflows/merge.yml` triggers `on: pull_request`, grants `permissions: contents: write`
at the top level, checks out the PR merge ref with `persist-credentials` left at its default, and
then runs `scripts/merge_feeds.py` and `scripts/publish_root.py` **from that ref**. The
`paths: feeds/*.json` filter only decides *whether* it fires — it does not limit what is checked
out, so a PR can rewrite the scripts that run.

The commit step is correctly gated to `push`, so there is no direct push-to-main primitive, but
the token is still materialised in `.git/config` for whatever the PR's code does.

**Fix:** split into a read-only `pull_request` job (`persist-credentials: false`, `contents: read`)
and a privileged `push` job, or gate the whole job on `github.event_name == 'push'`.

### 6. RSS timestamp churn defeats the reproducibility gate and dirties the tree

`src/omnisource/feeds/rss.py:152` stamps `<lastBuildDate>` with wall-clock time
(`_now_rfc822()`), and `scripts/check_reproducible.py:90` then normalises that exact field away
before comparing.

Running `make check` therefore leaves **79 committed files modified** — timestamp-only diffs. I hit
this and reverted with `git checkout -- .`; `git status` is clean again.

In CI the same churn means `sync.yml`'s `git diff --cached --quiet` never reports "no changes", so
every 6-hour schedule produces a commit and a Pages redeploy even when nothing upstream moved. The
"generated artifacts are reproducible" gate passes only because it is configured to ignore the
thing that always changes.

**Fix:** derive `lastBuildDate` from the newest item's `pubDate` (deterministic), or have
`check_reproducible.py` restore the tree it mutated and drop the normaliser.

### 7. 15 of 77 apps collide on 4 bundle IDs in the single installable feed

`api/duplicates.json`:

| bundle identifier | apps |
|---|---|
| `com.google.ios.youtube` | 7 |
| `com.atebits.Tweetie2` | 3 |
| `com.burbn.instagram` | 3 |
| `com.google.ios.youtubemusic` | 2 |

AltStore-family clients key on bundle ID, so a user adding the one URL the project markets
(`/apps.json`) gets an arbitrary member of each collision group, and SideStore cannot add two at
all. The README carries a tip about this and the site renders a "Shared bundle ×N" badge — but
roughly **19% of the catalog is not reliably installable from the master feed**, which is the
product's headline feature.

**Fix:** exclude colliding apps from `apps.json` and ship them only as per-app feeds, or publish
one master feed per collision group.

### 8. One unescaped data path in the app detail dialog

`js/site.js:1115` puts `app.developerName` into the `infoPanel` cell array raw, and
`categoryLabel()` (`js/site.js:94`) falls through to the raw category string for any value not in
`CATEGORY_LABELS`. `js/site.js:1135` then prints `cell[1]` **without** `OS.esc` —
unlike every neighbouring value, which is escaped.

The page CSP is `script-src 'self' 'unsafe-inline'` (`src/omnisource/app_pages.py:37`), so an
injected inline handler would execute. Practical risk today is low: both fields come from the
maintainer-edited `catalog.json`. It becomes live the moment either is sourced from an upstream
feed (as `versionDescription` already is — that one *is* escaped, `js/site.js:1086`).

**Fix:** `OS.esc(app.developerName || '—')` and escape inside `categoryLabel`, or escape `cell[1]`
at the render site and drop the pre-built HTML from the cells that need it.

---

## P2 — Low / consistency

### 9. `api/health.json` `generatedAt` is not a build timestamp

`render_health_doc` (`src/omnisource/feeds/altstore.py:100-108`) sets `generatedAt` to
`max(statusSince, versionDate)` — the newest *app release* date, not when the build ran. It reads
`2026-09-11` while every sibling document from the same build reads `2026-09-12`, so the published
health feed looks a day stale whenever no app happened to ship.

### 10. Docs and CI drift

* `src/omnisource/integrity.py:19-20` and `pipeline.py:839` describe a `verify.yml` job that does
  not exist (see issue 3).
* `docs/` mixes reference material (`API.md`, `ARCHITECTURE.md`, `DEPLOYMENT-GUIDE.md`) with
  one-off phase write-ups (`FINAL-SUMMARY.txt`, `IMPLEMENTATION-SUMMARY.md`, `cleanup-report.md`,
  `REPOSITORY.md`, `FEATURES-P0-P3.md`) in a tree that GitHub Pages publishes.

---

## Suggested order of work

1. **Issue 1** — one-file change, closes a real injection hole.
2. **Issue 3** — the workflow is already written; wiring it up also fixes issue 10's doc drift.
3. **Issue 2** — small logic change; stops 9 healthy apps being published as dead.
4. **Issue 4** — flip `keepVersions` (or rewire cadence to `updateHistory`); unblocks the
   reputation, trending and cadence features at once.
5. **Issues 5, 6, 7** — CI hardening, build determinism, and feed layout.
6. **Issues 8, 9** — escaping consistency and a misleading timestamp.
