<div align="center">

<img src="assets/OmniSource.png" width="120" alt="OmniSource">

# OmniSource

**An automated, source-first aggregation platform for iOS sideloading clients.**

AltStore · SideStore · Feather · ESign · LiveContainer

[![Validate](https://github.com/iamsmmh/OmniSource/actions/workflows/validate.yml/badge.svg)](https://github.com/iamsmmh/OmniSource/actions/workflows/validate.yml)
[![Security](https://github.com/iamsmmh/OmniSource/actions/workflows/security.yml/badge.svg)](https://github.com/iamsmmh/OmniSource/actions/workflows/security.yml)
[![Website](https://img.shields.io/website?url=https%3A%2F%2Fiamsmmh.github.io%2FOmniSource%2F)](https://iamsmmh.github.io/OmniSource/)
[![License](https://img.shields.io/github/license/iamsmmh/OmniSource)](LICENSE)

[Website](https://iamsmmh.github.io/OmniSource/) · [Install](https://iamsmmh.github.io/OmniSource/install/) · [API](docs/API.md) · [Contributing](CONTRIBUTING.md)

</div>

---

## What OmniSource does

OmniSource discovers and aggregates public iOS sources, validates their feed
and release metadata, tracks release history, enriches records, verifies
provenance and hashes, monitors availability, and publishes deterministic
feeds and machine-readable health reports.

It is deliberately **not** a social or marketplace product. There are no
accounts, comments, reviews, ratings, behavioral profiles, personalized
recommendation feeds, or marketplace transactions. Catalog collections are
committed, transparent source groupings; analytics describe repository and
release observations rather than user activity.

## Add the source

The compatibility feed is:

```text
https://iamsmmh.github.io/OmniSource/apps.json
```

Client-specific feeds are available at
`feeds/clients/{altstore,sidestore,feather,esign,livecontainer}.json`.
Single-app feeds live at `feeds/single/<slug>.json`; collection feeds live at
`feeds/collections/<slug>.json`. All of these are generated and validated
before publication.

| Client | Install link |
|---|---|
| AltStore | [Add to AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/apps.json) |
| SideStore | [Add to SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/apps.json) |
| Feather | [Add to Feather](feather://source/iamsmmh.github.io/OmniSource/apps.json) |
| ESign | [Add to ESign](esign://addsource?url=https://iamsmmh.github.io/OmniSource/apps.json) |
| LiveContainer | [Add to LiveContainer](livecontainer://sources?url=https://iamsmmh.github.io/OmniSource/apps.json) |

## Architecture

```mermaid
flowchart LR
    A[GitHub search and feed probes] --> B[data/discovered_sources.json]
    B --> C[Validation engine]
    C -->|invalid| Q[data/quarantine/]
    C --> D[Verification and registry]
    D --> E[Canonical app and release ledgers]
    E --> F[Metadata enrichment]
    F --> G[Reputation and security gates]
    G --> H[Incremental feed generation]
    H --> I[AltStore-family feeds]
    H --> J[Static API and Next.js web]
    K[30-minute monitoring] --> L[data/status.json]
    L --> M[Self-healing and mirror failover]
    M --> H
```

The source of truth is the hand-maintained `catalog.json` plus append-only
operational records. Generated feeds and pages are never hand-edited.

| Concern | Implementation | Durable output |
|---|---|---|
| Discovery | `scripts/discovery/` (12-hour GitHub/feed/repository passes) | `data/discovered_sources.json` |
| Quarantine | `src/omnisource/quarantine.py` | `data/quarantine/sources.json` |
| Validation | feed, source, release, metadata validators | rejected candidates never publish |
| Deduplication | bundle/app/repository/release/binary identity keys | `data/canonical_apps.json` |
| Registry | lifecycle, classification, history, health and reputation | `data/source_registry.json` |
| Release tracking | append-only version ledger and rollback planning | `data/release_history.json` |
| Enrichment | normalized developer, descriptions, icons, screenshots and notes | `data/enriched_apps.json` |
| Security | SHA-256/SHA-512 coverage, optional streamed binary verification, provenance | `data/security.json`, `security-report.json` |
| Monitoring | source/feed/download probes and state transitions | `data/status.json` |
| Intelligence | source growth/decline, app churn, cadence and timelines | `data/source_intelligence.json` |
| Search | fuzzy, developer/source/category/tag ranking | `feeds/search-index.json`, API v3 |
| Persistence | JSON adapter now; SQLite and generic DB-API adapters ready | `src/omnisource/repository.py` |
| Extensibility | typed event bus and reviewed plugin ports | `src/omnisource/events.py`, `plugins/` |

## Repository layout

```text
catalog.json                  hand-maintained application/source declarations
src/omnisource/                domain services, providers, pipeline and adapters
scripts/discovery/             scheduled discovery commands
scripts/validation/            publication gates
scripts/monitoring/            health and status commands
scripts/registry/              source registry build
scripts/intelligence/          source/package intelligence build
scripts/security/              security report and optional binary scan
scripts/backup/                verified disaster-recovery snapshots
feeds/                         canonical generated client and intelligence feeds
api/                           backward-compatible static API mirrors
web/                           Next.js 15 + TypeScript + Tailwind PWA
js/                            zero-dependency GitHub Pages frontend
schemas/                       machine-readable contracts
data/quarantine/              isolated untrusted discovery records
docs/                          architecture, API and operations guides
```

## Local development

Runtime code uses Python's standard library. Python 3.11 or newer is required.
Node 22 is used for the modern web application.

```bash
# Run from the repository root
export PYTHONPATH=src
python3 -m unittest discover -s tests
python3 scripts/validate.py
python3 scripts/validation/validate_feed.py feeds/apps.json --allow-duplicates
python3 scripts/validation/validate_metadata.py feeds/apps.json
python3 scripts/audit.py

# Offline deterministic pipeline
make build             # sync configured upstreams and rebuild feeds
make derived           # canonical, history, enrichment, registry and API
make monitoring        # status, self-healing and mirrors (offline-safe)
make security          # validation plus security report
make check             # lint/validation/tests/smoke checks when tools are installed
make serve             # build and serve the static site on 0.0.0.0:8000
```

Do not put IPA payloads, tokens, or HTTP caches in Git. Use `.env` locally
(`.env.example` documents supported overrides); credentials are scoped to
provider API hosts and are never attached to download probes.

## API and website

The backward-compatible feed/API surface remains available:

- `apps.json` — AltStore Source v2 feed;
- `api/*.json` — flat machine-readable snapshots and gzip twins;
- `api/v2/` — legacy delta-friendly endpoints;
- `api/v3/` — versioned pagination, filtering, sorting, fuzzy search, ETags,
  cache headers, sources, releases, status, security and analytics.

The modern app in `web/` provides Home, Apps, Sources, Collections, Categories,
Developers, Statistics, Status, Security, Search, About, source timelines,
source detail pages, and app release/security detail pages. It supports English,
Bangla, Arabic, Spanish, French, German, Japanese, and Chinese with lazy
loading and English fallback. The static PWA remains the GitHub Pages safety
path while `web/` can run on any Node host.

```bash
cd web
npm ci
npm run typecheck
npm run lint
npm run build
npm run dev
```

See [docs/API-V3.md](docs/API-V3.md) for the contract and
[web/README.md](web/README.md) for deployment.

## Automation

| Workflow | Schedule | Purpose |
|---|---:|---|
| `discovery.yml` | every 12 hours | discover candidates and isolate invalid sources |
| `sync.yml` | every 6 hours | resolve releases, build and publish feeds |
| `validation.yml` / `validate.yml` | PR/push | structural, metadata, translation and regression gates |
| `monitoring.yml` | every 30 minutes | probes, status, self-healing plans and mirrors |
| `security.yml` | daily + supply-chain changes | security report and fail-closed critical gate |
| `analytics.yml` | daily | daily/weekly/monthly rollups |
| `publish.yml` | after feed changes + daily | canonical registry, intelligence, client feeds and API |
| `backup.yml` | daily/weekly/monthly | verified metadata-only recovery artifacts |
| `website.yml` | web changes | Next.js typecheck, lint and production build |

Every shell block uses strict mode, quoted variables, HTTPS allowlists, least
privilege permissions, concurrency controls, and an explicit commit allowlist.
Untrusted workflow inputs are passed through environment variables and
validated before use.

## Documentation

- [Complete audit](audit-report.md)
- [Architecture and diagram](docs/ARCHITECTURE.md)
- [Discovery and quarantine](docs/DISCOVERY.md)
- [API documentation](docs/API.md) · [API v3](docs/API-V3.md)
- [Operations and self-healing](docs/OPERATIONS.md)
- [Security report](docs/SECURITY-REPORT.md)
- [Performance report](docs/PERFORMANCE-REPORT.md)
- [Migration guide](docs/MIGRATION.md)
- [Deployment guide](docs/DEPLOYMENT-GUIDE.md)
- [Final deliverables and known limitations](docs/FINAL-DELIVERABLES.md)
- [Contributing](CONTRIBUTING.md)

## Contribution policy

Edit `catalog.json`, schemas, source modules, or documentation—not generated
feeds, API copies, app pages, or operational snapshots. Add a test for every
new validator or provider. Run `make check` and the relevant workflow command
before opening a pull request. New source formats should use a plugin rather
than modifying core dispatch code.

## License

OmniSource is GPL-3.0. App names, icons, trademarks, and upstream releases
belong to their respective owners. OmniSource aggregates metadata and links to
public publishers; it does not claim ownership of upstream binaries.
