# Repository guide

OmniSource separates hand-maintained inputs, generated distribution files, application code, and the website. This keeps routine changes small while preserving every existing source URL.

## Directory map

```text
OmniSource/
├── catalog.json              # Hand-maintained app catalog
├── config/                   # Pipeline settings
├── assets/                   # Source, client, and app icons
├── src/omnisource/           # Python package
│   ├── feeds/                # AltStore and RSS renderers
│   ├── providers/            # GitHub and external-feed adapters
│   └── utils/                # Shared helpers
├── scripts/                  # Small command-line entry points
├── schemas/                  # JSON schemas
├── tests/                    # Unit test suite
├── feeds/                    # Generated canonical feeds and health data
├── website/                  # Static website source
│   ├── index.html
│   ├── css/styles.css
│   └── js/app.js
└── docs/                     # Project documentation
```

## What should be edited?

| Change | Edit | Then run |
| --- | --- | --- |
| Add or update an app | `catalog.json` and, when needed, `assets/` | `make build` |
| Change sync behavior | `src/omnisource/` | `make check` |
| Change the landing page | `website/` | `make site` |
| Change pipeline defaults | `config/settings.json` | `make check` |
| Change validation rules | `schemas/` or `src/omnisource/validation.py` | `make check` |

Do not hand-edit `feeds/` or the generated catalog section in `README.md`. The sync pipeline owns them.

## How are historical source URLs preserved?

Generated files have one canonical home under `feeds/`, keeping the repository root clean. During deployment, `scripts/build_site.py` copies them to the website root as well. Existing subscriptions such as the following therefore continue to work:

```text
https://iamsmmh.github.io/OmniSource/apps.json
```

This avoids duplicate tracked files without changing any public URL.

## Common commands

```bash
make build       # Sync and regenerate feeds
make check       # Lint, validate, and test
make site        # Assemble the deployable site in _site/
make serve       # Build and preview the site locally
make clean       # Remove local site output
```

The Pages workflow calls `scripts/build_site.py`, so local and production site assembly use one implementation.
