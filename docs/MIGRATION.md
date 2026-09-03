# Migration plan (OmniSource 2.x → 3.0)

This is a **compatible** upgrade. Sideloading clients do not need to do
anything. Maintainers need to run the pipeline once and commit the new
generated files.

## For feed subscribers (AltStore / SideStore / Feather / ESign / LiveContainer)

No action. These URLs are unchanged and remain AltStore Source v2:

- `https://iamsmmh.github.io/OmniSource/apps.json`
- `https://iamsmmh.github.io/OmniSource/{slug}.json`

## For repository maintainers

```bash
python3 scripts/omnisource.py --no-sync --no-health   # rebuild from state.json
python3 scripts/validate.py
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Commit the new files:

- `src/omnisource/**`
- `tests/**`
- `feeds/omnistore/*.json`
- `feeds/api/v1/**`
- wrapper `scripts/omnisource.py`, `scripts/validate.py`
- docs and workflow diffs

Do **not** hand-edit generated feeds. The golden rule is unchanged:
`catalog.json` is the only hand-edited data file.

## For catalog authors

Existing `upstream` blocks keep working. The default provider is `github`.
To track a non-GitHub source, add:

```json
"upstream": {
  "provider": "gitlab",
  "repo": "group/project",
  "host": "https://gitlab.com",
  "assetSuffixes": [".ipa"],
  "keepVersions": 1
}
```

Forgejo (self-hosted) requires `host`. Codeberg defaults `host` to
`https://codeberg.org`. JSON / AltStore / Feather sources use `feedURL`
instead of `repo`:

```json
"upstream": {
  "provider": "altstore",
  "feedURL": "https://example.com/source.json"
}
```

## For OmniStore client developers

Point the HTTP client at

```
https://iamsmmh.github.io/OmniSource/feeds/api/v1
```

and implement against [API.md](API.md). When a live API exists, change the
server URL; paths stay the same.

## Rollback

```bash
git revert <merge-sha>
```

Root AltStore mirrors never moved, so a revert restores working feeds
immediately.

## Compatibility matrix

| Artefact | 2.x | 3.0 |
| --- | --- | --- |
| `catalog.json` | required | required, additive fields |
| `feeds/{slug}.json` | AltStore v2 | AltStore v2 (same renderer) |
| `feeds/health.json` | yes | yes |
| `feeds/state.json` | yes | yes (same shape) |
| `feeds/omnistore/` | — | new |
| `feeds/api/v1/` | — | new |
| `python3 scripts/omnisource.py` | yes | yes (same flags + `--incremental`) |
| `python3 scripts/validate.py` | yes | yes (also checks OmniStore/API) |
| Runtime pip dependencies | none | none |
