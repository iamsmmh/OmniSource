# Architecture Guide

## One sentence

`catalog.json` describes what OmniSource distributes; `scripts/omnisource.py` turns that
description into AltStore-compatible feeds; GitHub Pages serves them.

## Data flow

```
                    ┌──────────────────────────────────────┐
   hand-edited ───▶ │  catalog.json                        │
                    │  apps · upstreams · metadata         │
                    └──────────────┬───────────────────────┘
                                   │
                    ┌──────────────▼───────────────────────┐
                    │  scripts/omnisource.py               │
                    │  1 sync    GitHub Releases API       │
                    │  2 health  concurrent HEAD probes    │
                    │  3 build   render feeds              │
                    │  4 mirror  copy to repo root         │
                    │  5 readme  refresh catalog block     │
                    └──────────────┬───────────────────────┘
                                   │
        ┌──────────────────────────┼──────────────────────────┐
        ▼                          ▼                          ▼
  feeds/apps.json           feeds/<slug>.json          feeds/health.json
  feeds/state.json                                     (dashboard input)
        │                          │                          │
        └──────────────────────────┴──────────────────────────┘
                                   │
                    ┌──────────────▼───────────────────────┐
                    │  GitHub Pages (website/ + feeds/)    │
                    └──────────────┬───────────────────────┘
                                   │
              AltStore · SideStore · Feather · ESign · LiveContainer
```

## Components

### `catalog.json`

The only hand-edited data file. Each app declares identity (`slug`, `name`, `bundleIdentifier`),
presentation (`subtitle`, `icon`, `tintColor`, `screenshots`), curation (`featured`, `status`), and
three metadata blocks the AltStore schema has no place for: `verification`, `compatibility` and
`upstream`.

Keeping resolution rules as *data* rather than code is the central design decision. Under the
previous design, each app had a bespoke `sync_*()` function; adding an app meant writing Python.
Now it means adding an object.

### `feeds/state.json`

The pipeline's memory: the last successfully resolved version list and link-health result per app.
It exists so that

- a failing upstream degrades to "keep serving the last good build" instead of dropping the app;
- `--no-sync` rebuilds deterministically with no network access;
- CI can prove that `feeds/` is reproducible from committed inputs.

### Generated feeds

`feeds/apps.json` (master) and `feeds/<slug>.json` (per app) are standard AltStore v2 feeds with one
addition: an `omnisource` object per app carrying status, verification, compatibility and health.
Unknown keys are ignored by every client, so this is schema-safe.

### Root mirrors

Subscribers installed `https://iamsmmh.github.io/OmniSource/apps.json` long before `feeds/` existed.
Those root files are byte-identical generated copies; `scripts/validate.py` fails the build if a
mirror drifts. They are marked `linguist-generated` so they collapse in diffs.

### Website

`website/` is a dependency-free static app (one HTML file, one stylesheet, one ES module) using
hash routing so GitHub Pages needs no rewrite rules. It fetches the same `apps.json` and
`health.json` the clients consume, so the site can never disagree with the feed.

## Idempotency contract

Running the pipeline twice with no upstream change must produce zero file changes. This is enforced
in CI ("Verify feeds are reproducible from catalog.json") and shapes two design rules:

1. **No wall-clock timestamps in output.** `health.json.generatedAt` is derived from content;
   `statusSince` only moves when a status actually changes.
2. **Write only on difference.** `write_json` compares the serialised payload before touching disk.

Without this, every scheduled run would produce an empty commit and the git history would be noise.

## Failure model

| Failure | Behaviour |
| --- | --- |
| GitHub API 5xx / rate limit | Retried with exponential backoff, honouring `Retry-After` |
| One upstream repository unavailable | Logged as an error; that app keeps its previous state; other apps still build |
| Upstream release has no matching asset | Falls back to `manualRelease` if present, otherwise keeps previous state |
| Download URL unreachable | App stays in the feed, flagged `downloadReachable: false` and ⚠️ in README |
| Every app fails | Non-zero exit; nothing is committed |

The old pipeline *removed* apps from the master feed on a failed link check, so a transient CDN
blip could silently delete apps from everyone's client. Flagging instead of deleting is deliberate.

## Performance

| Aspect | Approach |
| --- | --- |
| API calls | Per-repo release cache; five apps share one YouProEXTRA fetch (4 calls per full run) |
| Link probing | 8-way thread pool, HEAD first, ranged GET fallback |
| Redirects | Not followed during probes — a 302 from the origin proves the asset exists and avoids downloading 120 MB |
| Dependencies | Standard library only: no `pip install` step in CI |
| Writes | Content-compared, atomic via temp file + `Path.replace` |

## Workflows

| Workflow | Trigger | Permissions | Purpose |
| --- | --- | --- | --- |
| `sync.yml` | schedule (6h), push to main, manual | `contents: write`, `pages: write` | Sync, validate, commit, deploy Pages |
| `validate.yml` | pull request, push, manual | `contents: read` | Offline validation, reproducibility, lint |
| `build-uyouenhanced.yml` | manual only | `contents: write` | Compile and publish the uYouEnhanced IPA |

`build-uyouenhanced.yml` publishes to this repository's releases, which the catalog then treats as
the upstream for `uyouenhanced` — the build feeds itself back into the pipeline.

## Extending

| Goal | Change |
| --- | --- |
| Add an app | Append to `catalog.json` |
| Support a non-GitHub upstream | Add a resolver branch in `sync_app()` keyed on `upstream.provider` |
| Add a metadata field | Extend `render_app()` and add a rule in `validate.py` |
| Add a website page | Add a route to `ROUTES` in `website/app.js` |
