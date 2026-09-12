# Final deliverables, limitations, and technical debt

**Review date:** 2026-09-12

## Delivered

- Full repository audit in [`audit-report.md`](../audit-report.md), including
  source, feeds, APIs, website, workflows, assets, docs, collections and
  analytics.
- Discovery, validation, quarantine, verification boundary and generated
  source registry.
- Canonical app identity, duplicate detection, release history, metadata
  enrichment, mirrors, monitoring, self-healing, analytics and observability.
- SHA-256/SHA-512 metadata and optional bounded binary integrity checks with
  `data/security.json` and `security-report.json`.
- AltStore, SideStore, Feather, ESign, LiveContainer, single-app, and
  collection feed projections.
- JSON, SQLite, and generic DB-API repository adapters; typed event bus;
  feature flags; reviewed plugin ports.
- Static PWA compatibility site and modern Next.js/TypeScript/Tailwind web
  surface with eight lazy locale packs and English fallback.
- Discovery, validation, monitoring, security, analytics, website, publish,
  and backup workflows, plus daily/weekly/monthly recovery schedules.
- Architecture, security, performance, migration, operations, API, deployment,
  and contribution documentation.

## Known limitations

1. Public GitHub search is rate-limited and results depend on the token and
   search index at execution time.
2. An upstream source that omits a digest cannot be made cryptographically
   verified by OmniSource; the report records the omission.
3. Binary verification is opt-in due to runner bandwidth and storage costs.
4. Reputation is an explainable metadata signal, not a guarantee that an IPA
   is safe or correctly signed.
5. The static Pages deployment serves generated snapshots; dynamic API
   filtering requires the Node deployment.
6. The current repository is a Git-friendly JSON deployment. A production
   multi-writer service still needs operational database provisioning,
   migrations, backups, and secret rotation outside this checkout.
7. Some legacy scripts and workflows predate the new pipeline and remain for
   compatibility; `audit-report.md` calls out their ownership and risk.

## Technical debt register

| Priority | Debt | Mitigation / owner |
|---|---|---|
| P0 | Complete repository transaction atomicity for JSON and DB-API writes | Implement staged writes/commit boundary and failure-injection tests before multi-writer production |
| P0 | Add explicit verification/publication service around quarantine transitions | Keep default candidates `VALIDATING`; publish only from verified records |
| P1 | Replace legacy direct feed scripts with the shared pipeline | Mark old commands compatibility-only and remove after two stable releases |
| P1 | Expand external-provider contract tests with mocked rate limits and malformed responses | Add fixtures under `tests/fixtures/providers/` and run nightly |
| P1 | Run production-scale 1,000-source / 10,000-app benchmark | Capture wall time, memory, API calls and cache hit rate in deployment |
| P2 | Add durable outbox/event replay and database migrations | Use SQLite first, then PostgreSQL/DB-API adapter |
| P2 | Improve missing upstream digest coverage | Request publisher metadata; never synthesize a digest |
| P2 | Increase browser accessibility and visual regression coverage | Run Playwright against the static and Next.js surfaces |

## Production readiness score

**82 / 100 — ready for controlled GitHub Actions publication; not yet ready
as a multi-writer hosted service.**

| Area | Score | Reason |
|---|---:|---|
| Architecture and boundaries | 18/20 | Clear domain, adapters, quarantine and generated projections |
| Validation and security | 17/20 | Fail-closed gates and bounded verification; digest gaps remain |
| Automation and recovery | 17/20 | Required workflows, monitoring, backups and rollback path |
| Web/API and compatibility | 16/20 | Static compatibility plus modern web; scale testing remains |
| Operations and tests | 14/20 | Broad tests and reports; transaction and provider tests remain |

The score is intentionally conservative. The two P0 items above must be
closed, then the score should be reassessed with live provider and scale
measurements.
