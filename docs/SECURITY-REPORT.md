# Security Report — OmniSource 3.2.0

## Threat model

OmniSource aggregates **metadata** (never IPA payloads in-repo). Attack
surface: (1) malicious upstream feeds/releases, (2) compromised Actions
inputs or workflows, (3) credential leakage to third-party hosts,
(4) tampered binaries served upstream.

## Controls

### 1. Workflow hardening (all 12 workflows)

- `set -euo pipefail` on every multi-line `run:` block.
- All variables quoted; arrays for word-splitting (`"${ARGS[@]}"`).
- **No `${{ }}` interpolation into `run:` scripts** — inputs/step
  outputs pass through `env:` (fixes the `build-tweak.yml` script
  injection, the `sync.yml` flag injection and the uYou step-output
  interpolation found in the audit).
- Dispatch inputs validated: https-only URL allowlists, bundle-ID
  character allowlist, sanitized artifact names, path-traversal guards.
- Minimal `permissions` per job, `concurrency` groups, `timeout-minutes`,
  pinned action majors (`@v4`/`@v5`), `persist-credentials: false` on
  read-only checkouts.

### 2. Credential hygiene

- Tokens attach only to allowlisted API origins (`AuthRule` in
  `src/omnisource/http.py`); download probes are always anonymous.
- Discovery/monitoring/security jobs use the ephemeral `github.token`
  (no long-lived secrets required).
- `curl --proto '=https'` + `--max-time` on dispatch-driven downloads.

### 3. Supply-chain validation

- `scripts/validation/` — schema, URL, bundle-ID, version, icon,
  screenshot, duplicate-record and digest-format rules; **invalid feeds
  never publish** (`discovery.yml` + `security.yml` fail closed).
- `scripts/security/scan.py` → `data/security.json`: SHA-256/512
  coverage, duplicate-binary detection, download-integrity rollup,
  provenance audit. `security.yml` fails on `critical`.
- Client feeds are validated as AltStore v2 **before** write
  (`build_client_feeds.py` refuses to emit invalid output).
- Reproducibility gate: any hand-edit to generated files fails CI.

### 4. Quarantine & least promotion

- Reputation `< 25` → `untrusted`/quarantined: auditable, never
  auto-published. Promotion into `catalog.json` is always explicit.
- Self-healing only auto-applies recorded-fallback swaps (to a review
  file, never in place).

## Current posture (2026-09-12)

From `data/security.json`: verdict **pass** — 64/94 apps with SHA-256,
0 duplicate binaries, 0 failing downloads, 0 critical/high findings;
30 `low` hash-missing advisories (upstreams publish no digest).

## Residual risks

1. Upstream binaries are trusted to their developers; OmniSource
   verifies *recorded* hashes but does not re-host or re-sign IPAs.
2. `security.yml` gates on `critical` only — `--fail-on high` is opt-in.
3. Discovery code search depends on GitHub API availability/rate limits
   (fails open to empty candidates, never to unvalidated publishes).

## Reporting

See `SECURITY.md` for private disclosure. Workflow changes must keep the
hardening rules (`.github/workflows/README.md`) and pass `actionlint`.
