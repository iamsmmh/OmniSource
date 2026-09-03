# Contributing

Thanks for helping maintain OmniSource. Almost every contribution is a change to one file:
`catalog.json`.

## Golden rule

**`catalog.json` is the only hand-edited data file.** `feeds/*.json` and the root-level `*.json`
mirrors are generated. A pull request that edits a generated file will fail CI.

## Setup

No virtualenv, no dependencies — the pipeline is standard library only.
`src/` is added to `sys.path` by the wrappers; for tests, set `PYTHONPATH=src`.

```bash
git clone https://github.com/iamsmmh/OmniSource.git
cd OmniSource
python3 scripts/omnisource.py                      # sync upstream + rebuild everything
python3 scripts/validate.py                        # offline structural checks
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Useful flags while iterating:

```bash
python3 scripts/omnisource.py --only ytlite      # sync one app
python3 scripts/omnisource.py --no-sync          # rebuild from feeds/state.json, no API calls
python3 scripts/omnisource.py --no-health        # skip link probing
python3 scripts/omnisource.py --incremental      # skip pagination when the newest asset URL is unchanged
python3 scripts/validate.py --strict             # treat warnings as errors
```

Set `GH_TOKEN` to a token with `public_repo` scope to lift the 60 requests/hour anonymous API
limit. A full sync uses about four requests.

## Adding an app

1. Add the icon to `assets/` (PNG, 512×512 or smaller, ideally under 100 KB).
2. Append an entry to `catalog.json`:

```json
{
  "slug": "example",
  "name": "Example",
  "subtitle": "One-line pitch",
  "bundleIdentifier": "com.example.app",
  "developerName": "upstream-author",
  "category": "utilities",
  "tintColor": "5B5BD6",
  "icon": "Example.png",
  "localizedDescription": "What the app does and what the tweak changes.",
  "screenshots": [],
  "featured": false,
  "status": "stable",
  "upstreamURL": "https://github.com/owner/project",
  "verification": {
    "method": "github-release",
    "publisher": "owner/project",
    "codeSigned": false,
    "checksumPublished": false
  },
  "compatibility": {
    "minOSVersion": "16.0",
    "maxOSVersion": null,
    "devices": ["iphone", "ipad"],
    "clients": ["altstore", "sidestore", "feather", "esign", "livecontainer"],
    "notes": ""
  },
  "upstream": {
    "repo": "owner/project",
    "tagPrefix": "",
    "assetSuffixes": [".ipa"],
    "maxPages": 3,
    "keepVersions": 1,
    "descriptionTemplate": "Example {version} | {label}",
    "minOSVersion": "16.0"
  }
}
```

3. Run `python3 scripts/omnisource.py && python3 scripts/validate.py`.
4. Commit `catalog.json`, the icon **and** the regenerated feeds together.

### `upstream` reference

| Key | Default | Purpose |
| --- | --- | --- |
| `provider` | `"github"` | `github`, `github-tags`, `gitlab`, `codeberg`, `forgejo`, `json-feed`, `altstore`, `feather` |
| `host` | provider default | Forge origin for self-hosted GitLab/Forgejo |
| `feedURL` | — | Required for `json-feed` / `altstore` / `feather` |
| `repo` | required for forges | `owner/name` of the repository holding releases |
| `tagPrefix` | `""` | Only consider tags starting with this prefix |
| `excludeTagPrefixes` | `[]` | Skip tags starting with any of these |
| `assetSuffixes` | `[".ipa"]` | Asset filename suffixes in priority order |
| `assetNamePattern` | `""` | Regex an asset filename must match before suffixes are tried; picks one flavour when a repository publishes several |
| `maxPages` | `3` | Release pages (100 per page) to scan |
| `keepVersions` | `1` | Versions to publish; `0` keeps every match |
| `sortByTagNumber` | `false` | Order by the trailing number in the tag instead of API order |
| `versionFromTag` | `false` | Read the version numbers from the release tag instead of the asset name |
| `descriptionTemplate` | — | Supports `{name} {version} {secondary} {label} {tag} {date}` |
| `minOSVersion` | `"16.0"` | Default floor for generated version entries |
| `minOSVersionByTagNumber` | `{}` | Per-tag-number override, e.g. `{"0": "14.0"}` |
| `isoDates` | `false` | Emit full ISO 8601 UTC release timestamps (`2026-01-03T17:51:54Z`) instead of date-only strings; opt-in so existing feeds stay byte-stable |

Apps with no GitHub upstream use `"upstream": null` plus a `manualRelease` block. An app may have
both: the upstream wins, and `manualRelease` is the fallback when nothing matches.

An app may also declare `appPermissions` (AltStore 2.0: `entitlements` + `privacy` usage strings)
and `permissions` (legacy array of `{type, usageDescription}` objects). Both pass straight through
to the generated feed; copy the `NS*UsageDescription` strings verbatim from the upstream `Info.plist`.

## Removing or retiring an app

Prefer `"status": "unmaintained"` over deletion — existing installs keep resolving. Only delete an
entry when the download is permanently gone, and remove its icon and root mirror in the same PR.

## Reporting compatibility

Open an issue with device, iOS version, client, app and version. Confirmed results are merged into
`compatibility.clients` and appear in the matrix on the next build.

## Pull request checklist

- [ ] Only `catalog.json`, `assets/`, docs or scripts hand-edited
- [ ] `python3 scripts/omnisource.py` run and generated files committed
- [ ] `python3 scripts/validate.py` passes with zero errors
- [ ] `PYTHONPATH=src python3 -m unittest discover -s tests -v` passes if `src/` or `tests/` changed
- [ ] `python3 -m ruff check src/ scripts/ tests/ && python3 -m ruff format --check src/ scripts/ tests/` passes if Python changed
- [ ] No credentials, tokens or private URLs in the diff

## What we will not merge

- Paid, cracked or piracy-focused applications
- Feeds pointing at URL shorteners or expiring file hosts
- Binaries committed to this repository
- Direct edits to generated feeds
