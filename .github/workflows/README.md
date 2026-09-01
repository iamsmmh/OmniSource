# Pending workflows — activate in one command

These are the finished replacements for `.github/workflows/`. They live here for one reason: the
automation account that opened this pull request is a GitHub App without the `workflows`
permission, so GitHub rejects **any** push that adds, edits or deletes a file under
`.github/workflows/`. That is a platform restriction, not a design choice — everything else in the
refactor landed normally.

This directory is temporary. Delete it as soon as you have run the commands below.

## Activate

```bash
git checkout arena/01a05ed6-omnisource

# 1. Remove the six obsolete workflows (see docs/AUDIT.md §5.3)
git rm .github/workflows/ai-automated-committer.yml \
       .github/workflows/copilot-agent.yml \
       .github/workflows/copilot-setup-steps.yml \
       .github/workflows/lint-action.yml \
       .github/workflows/updatex.yml \
       .github/workflows/delete-old-workflows-run.yml \
       .github/workflows/omnisource-build-sync.yml

# 2. Install the replacements (build-uyouenhanced.yml is an in-place upgrade)
git mv .github/workflows-pending/sync.yml               .github/workflows/sync.yml
git mv .github/workflows-pending/validate.yml           .github/workflows/validate.yml
git mv .github/workflows-pending/build-uyouenhanced.yml .github/workflows/build-uyouenhanced.yml

# 3. Remove this directory
git rm -r .github/workflows-pending

git commit -m "ci: consolidate eight workflows into three"
git push
```

Alternatively, paste each file into **Actions → New workflow** in the web UI and delete the old
ones there.

## What you are installing

| File | Replaces | Purpose |
| --- | --- | --- |
| `sync.yml` | `omnisource-build-sync.yml` + `updatex.yml` | Every 6 h and on push: sync upstream releases, validate, commit, deploy Pages. The two workflows it replaces both wrote `apps.json` on overlapping 12 h / 13 h schedules and raced each other |
| `validate.yml` | `lint-action.yml`, `docs/ci.yml.txt` | Pull-request gate: offline feed validation, a reproducibility check, pinned `ruff`, pinned `actionlint`. Read-only, no token, safe on forks |
| `build-uyouenhanced.yml` | itself | Same 617-line build, hardened: `workflow_dispatch` inputs now travel through job-level `env:` instead of being interpolated into 24 `run:` lines (shell-injection fix), plus a final step that triggers `sync.yml` so a new build becomes a feed update automatically |

## Deleted workflows, briefly

| Workflow | Why |
| --- | --- |
| `updatex.yml` | Duplicate writer for `apps.json`; raced the sync workflow; pinned `actions/checkout@v7`, which does not exist |
| `ai-automated-committer.yml` | Any issue comment containing `@ai` sent untrusted text to an LLM and opened a PR with a PAT. The step also discarded the model's output, so it created empty PRs |
| `copilot-agent.yml` | Depends on `github/copilot-action@v1`, which is not a published action. Every run failed |
| `copilot-setup-steps.yml` | Installs from a `requirements.txt` that does not exist. No-op |
| `lint-action.yml` | Force-committed Prettier formatting back to contributor branches |
| `delete-old-workflows-run.yml` | Granted `actions: write` to a third-party action to erase run history |

Full reasoning: [`docs/AUDIT.md`](../../docs/AUDIT.md) §5.3 and §9.

## After activating

1. **Settings → Pages → Source: GitHub Actions** — required for the deploy job in `sync.yml`.
   Until then, branch-based Pages keeps serving the root-level feed mirrors, so nothing breaks.
2. **Settings → Actions → Workflow permissions** — leave at read-only; every workflow now requests
   what it needs explicitly.
3. Delete the `GH_TOKEN` repository secret if it exists; nothing uses it any more.
