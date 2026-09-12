<div align="center">

<img src="assets/OmniSource.png" width="120" alt="OmniSource">

# OmniSource
**The App Store for sideloaded iOS — one feed, five clients, always current.**

One source URL for **AltStore · SideStore · Feather · ESign · LiveContainer**.

<!-- omnisource:stats:start -->

**94** apps · **78** upstream sources · **93** verified · **1** community verified · **94/94** downloads online · last sync **2026-09-12**.

<!-- omnisource:stats:end -->

[![Sync & Publish](https://github.com/iamsmmh/OmniSource/actions/workflows/sync.yml/badge.svg)](https://github.com/iamsmmh/OmniSource/actions/workflows/sync.yml)
[![Validate](https://github.com/iamsmmh/OmniSource/actions/workflows/validate.yml/badge.svg)](https://github.com/iamsmmh/OmniSource/actions/workflows/validate.yml)
[![Security](https://github.com/iamsmmh/OmniSource/actions/workflows/security.yml/badge.svg)](https://github.com/iamsmmh/OmniSource/actions/workflows/security.yml)
[![Website](https://img.shields.io/website?url=https%3A%2F%2Fiamsmmh.github.io%2FOmniSource%2F&label=website)](https://iamsmmh.github.io/OmniSource/)
[![License](https://img.shields.io/github/license/iamsmmh/OmniSource)](LICENSE)

[Add the Source](#-add-the-source) · [Website](https://iamsmmh.github.io/OmniSource/) · [API](#-api) · [Docs](#-documentation) · [Contributing](CONTRIBUTING.md)

</div>

---

## 🚀 Add the Source

**Source URL**

```
https://iamsmmh.github.io/OmniSource/apps.json
```

Tap to add in one go:

| Client | Link |
|---|---|
| **AltStore** | [➕ Add to AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/apps.json) |
| **SideStore** | [➕ Add to SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/apps.json) |
| **Feather** | [➕ Add to Feather](feather://source/iamsmmh.github.io/OmniSource/apps.json) |
| **ESign** | [➕ Add to ESign](esign://addsource?url=https://iamsmmh.github.io/OmniSource/apps.json) |
| **LiveContainer** | [➕ Add to LiveContainer](livecontainer://sources?url=https://iamsmmh.github.io/OmniSource/apps.json) |

Prefer a feed tuned to your client? Use `feeds/clients/<client>.json`
(`altstore`, `sidestore`, `feather`, `esign`, `livecontainer`) — same
AltStore v2 shape, client-appropriate filtering, each validated before publish.

> **Tip:** YouTube tweaks share a bundle ID and overwrite each other. Use a single-app feed at `feeds/<slug>.json` — each app page has a **Copy source link** button.

Full guides, QR codes and per-app links: **[Installation Center](https://iamsmmh.github.io/OmniSource/install/)**

---

## ✨ Why OmniSource?

- **Official upstreams only** — every release resolves from the developer's own GitHub Releases or AltStore feed. Community-built IPAs are clearly labeled *Community build*.
- **Verified & health-checked** — SHA-256, verification labels and automated probes keep every download installable.
- **Fully autonomous** — discovery (12h), sync (6h), monitoring (30m), security gates and publishing run with no human in the loop; self-healing retries, repairs and rebuilds automatically.
- **A real PWA, not just JSON** — search (⌘K), compare, health, analytics, favorites, collections and offline support — plus a modern Next.js app in [`web/`](web/).

---

## 🌐 Website

**Classic PWA** (GitHub Pages, zero frameworks): [Home](https://iamsmmh.github.io/OmniSource/) · [Apps](https://iamsmmh.github.io/OmniSource/#catalog) · [Collections](https://iamsmmh.github.io/OmniSource/collections/) · [Sources](https://iamsmmh.github.io/OmniSource/sources/) · [Status](https://iamsmmh.github.io/OmniSource/status/) · [Docs](https://iamsmmh.github.io/OmniSource/docs/) — plus [Compare](https://iamsmmh.github.io/OmniSource/compare/), [Analytics](https://iamsmmh.github.io/OmniSource/analytics/), [Install](https://iamsmmh.github.io/OmniSource/install/), [Search](https://iamsmmh.github.io/OmniSource/search/), [Favorites](https://iamsmmh.github.io/OmniSource/favorites/), [Discover](https://iamsmmh.github.io/OmniSource/discover/) and [Community](https://iamsmmh.github.io/OmniSource/api/community.json) under “More”.

**Modern app** ([`web/`](web/) — Next.js 15 + TypeScript + Tailwind PWA): Home, Apps, Sources, Collections, Categories, Trending, Search, Status, Security, Statistics, About — with 8 lazy locales (EN/BN/AR/ES/FR/DE/JA/ZH), offline support and a dynamic REST API. See [web/README.md](web/README.md).

---

## 📚 Catalog

<!-- omnisource:catalog:start -->

Browse the full **94-app catalog** on the [website](https://iamsmmh.github.io/OmniSource/#catalog) — all installable with one tap.

- Combined feeds: [`feeds/apps.json`](./feeds/apps.json), [`feeds/feed.xml`](./feeds/feed.xml), [`Catalog.json`](./Catalog.json)
- Substrate docs: [`feeds/sources.json`](./feeds/sources.json), [`feeds/discovery.json`](./feeds/discovery.json), [`feeds/health.json`](./feeds/health.json), [`feeds/updates.json`](./feeds/updates.json), [`feeds/verification.json`](./feeds/verification.json)
- Per-app feeds at `feeds/<slug>.json` and `feeds/<slug>.xml` — e.g. [`feeds/esign.json`](./feeds/esign.json)

_Last sync 2026-09-12 · 94/94 downloads reachable._

<!-- omnisource:catalog:end -->

---

## 🏗️ Architecture

```
Discovery (12h) ──▶ Validation ──▶ catalog.json (explicit promotion only)
                                          │
catalog.json → sync (6h) → feeds/*.json → publish → data/* + feeds/clients/* + api/v3/*
                                          │                      │
                                          ▼                      ▼
                                   static PWA → Pages     web/ Next.js → Node host
monitoring (30m) → data/status.json + self-heal │ security gate │ analytics (daily)
```

- **Discovery** — GitHub code search, feed probes, release scans, web catalogs → `data/discovered_sources.json`. [Docs](docs/DISCOVERY.md)
- **Validation** — schema, URLs, bundle IDs, digests, duplicates. Invalid feeds never publish.
- **Deduplication** — canonical app DB (`data/canonical_apps.json`, 83 apps from 94 records).
- **Release tracking** — append-only ledger with rollback (`data/release_history.json`).
- **Reputation** — 0–100 → verified/trusted/good/warning/untrusted + quarantine (`data/source_reputation.json`).
- **Health** — 30-minute probes → `data/status.json` (online/degraded/offline).
- **Self-healing** — retry/repair/replace/rebuild plans (`data/selfheal_report.json`).
- **Mirrors** — tiered failover registry (`data/mirrors.json`).
- **Security** — SHA-256/512, duplicate binaries, integrity, provenance → `data/security.json`, fails closed on critical.
- **Analytics** — daily/weekly/monthly windows (`data/analytics_rollup.json`).

Details: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) · [Operations runbook](docs/OPERATIONS.md) · [Audit report](audit-report.md)

---

## ⚙️ How It Works

```
catalog.json → scripts/omnisource.py (src/omnisource/, stdlib only)
            → feeds/*.json + apps/<slug>/ + api/*
            → scripts/build_site.py → _site/ → GitHub Pages
```

1. **Sync** — resolve newest release from declared upstream (GitHub / developer feed)
2. **Health** — probe every download URL
3. **Build** — render feeds, RSS, badges, intelligence docs and app pages
4. **Validate** — `ruff` + `scripts/validate.py` + `check_reproducible.py`
5. **Publish** — refresh `apps.json`, `/api/`, derived artifacts and deploy

```bash
make build        # sync + health + build
make derived      # canonical DB + ledger + enrichment + reputation + client feeds + API v3
make monitoring   # status + self-heal + mirrors (offline)
make security     # feed validation + security gate
make serve        # preview at http://localhost:8000
make check        # validate + tests
python3 scripts/omnisource.py --no-sync   # offline rebuild
```

Key paths: `catalog.json` source of truth · `src/omnisource/` pipeline · `scripts/` CLIs · `feeds/` output · `data/` operations · `js/` + `assets/design-system/` classic frontend · `web/` modern app

---

## 🔌 API

- **API v3** (new) — `api/v3/apps`, `/app/{id}`, `/sources`, `/source/{id}`, `/trending`, `/search`, `/status`, `/security`, `/analytics`, `/releases` with pagination, sorting, filtering, ETag/`304`, compression and cache control — static snapshots on Pages + dynamic routes in `web/`. [API v3 docs](docs/API-V3.md)
- **API v2 / flat docs** (unchanged) — `apps.json`, `catalog.json`, `health.json`, `analytics.json`, `install.json`, `search-index.json`, `sources.json` and more, each with `.gz` and listed in `api/index.json`. [API docs](docs/API.md)

Clients: [`sdk/javascript/`](sdk/javascript/) (`npm i github:iamsmmh/OmniSource/sdk/javascript`) · [`sdk/python/`](sdk/python/) (`python3 -m pip install ./sdk/python`)

Source-level data lives in [`feeds/sources.json`](feeds/sources.json) and is published as static pages under [`sources/`](sources/) — generated by the build, never hand-edited.

---

## 📖 Documentation

| Guide | Covers |
|---|---|
| [audit-report.md](audit-report.md) | Full repository audit: findings, fixes, residual risks |
| [docs/MODERNIZATION.md](docs/MODERNIZATION.md) | Delivery index: file-by-file changes, verification, readiness 9.0/10 |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design + data flow |
| [docs/API-V3.md](docs/API-V3.md) | API v3 contract + examples |
| [docs/DISCOVERY.md](docs/DISCOVERY.md) | Autonomous discovery + validation gate |
| [docs/OPERATIONS.md](docs/OPERATIONS.md) | Monitoring, self-healing, mirrors, analytics, incidents |
| [docs/SECURITY-REPORT.md](docs/SECURITY-REPORT.md) | Threat model, controls, current posture |
| [docs/PERFORMANCE-REPORT.md](docs/PERFORMANCE-REPORT.md) | Scale design, measurements, 1k+/10k+ guidance |
| [docs/MIGRATION.md](docs/MIGRATION.md) | 3.1 → 3.2 upgrade (backward compatible) |
| [docs/DEPLOYMENT-GUIDE.md](docs/DEPLOYMENT-GUIDE.md) | Deployment |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contribution guide |

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Edit **`catalog.json`** only — never generated files. Run `python3 scripts/omnisource.py` and commit regenerated output.

[Request an app](https://github.com/iamsmmh/OmniSource/issues/new?template=01-app-request.yml) · [Broken upstream](https://github.com/iamsmmh/OmniSource/issues/new?template=02-broken-upstream.yml) · [Bug report](https://github.com/iamsmmh/OmniSource/issues/new?template=03-bug-report.yml) · [Feature idea](https://github.com/iamsmmh/OmniSource/issues/new?template=04-feature-idea.yml)

---

## ❓ FAQ

**Can I install two YouTube apps side by side?**
No — they share a bundle ID. Add only the one you want via its single-app feed. The [compare page](https://iamsmmh.github.io/OmniSource/compare/) helps you choose.

**How do updates work?**
Refresh sources in your client — upstreams sync every 6h, health is monitored every 30m. Or subscribe to `feeds/<slug>.xml`.

**What do the badges mean?**
Per app: 🟢 stable · 🟡 beta · 🔵 manual · 🔴 unmaintained — plus *Official* / *Community* build and ✅/⚠️ reachability.
Per source: **Verified** (valid feed, reachable, updated <180 days ago) · **Community Verified** · **Maintained** · **Warning** (broken entries/links/probes) · **Inactive** (no release in a year) · **Deprecated** (archived).
Autonomous trust ladder: `verified ≥85 / trusted ≥70 / good ≥50 / warning ≥25 / untrusted <25` (quarantined).

**Is this safe?**
Metadata only, every entry discloses provenance and hash. The security gate blocks publication on critical findings. Sideloading trusts the app's developer — OmniSource just makes it transparent.

---

## ⚖️ License

Independent community project. Apps and trademarks belong to their owners. [GPL-3.0](LICENSE)

<div align="center">

⭐ **Star this repo if it makes sideloading easier** ⭐

[🌐 Website](https://iamsmmh.github.io/OmniSource/) · [📲 Install](https://iamsmmh.github.io/OmniSource/install/) · [🔌 API](docs/API.md)

</div>
