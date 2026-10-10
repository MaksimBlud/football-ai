# Football AI — migration to independent GitHub Actions

Status on 2026-10-10: **STAGED; NOT LIVE**. ChatGPT Backend/Frontend scheduled
tasks have repeatedly disabled themselves after ~64 seconds. GitHub Actions
is independent of that scheduler and supports deterministic commit/PR steps.

## Completed in this branch

- `engineering_autopilot_guard.py` enforces a narrow code allowlist:
  frontend: `static/match.html`, `tests/test_product_ui_contract.py`;
  backend: `product_snapshot_store.py`, `tests/test_product_snapshot_store.py`.
- Guard forbids other paths, added/deleted/renamed files, symlinks, missing
  changes, and oversized diffs. Runner-created Gemini logs are ignored but
  **never staged**.
- `tests/test_engineering_autopilot_guard.py`: eight independent safety tests.
- The scheduled workflow design was prepared and syntax-tested locally, but
  **GitHub workflow-file creation was blocked by OpenAI's connector safety
  checks**. Do not misreport migration as deployed or attempt to bypass that
  restriction. The workflow file must be installed through an authorized
  repository-owner workflow.

## Intended runner

- GitHub Actions schedule: minute 17 UTC, once per hour; separate backend and
  frontend jobs with concurrency guards.
- Manual dispatch provides `probe` (NO model call) and `execute` modes.
- Free Gemini coding is opt-in only, using an explicitly confirmed **non-billed**
  Google AI Studio key. Required: `GEMINI_API_KEY` repository secret plus
  `FOOTBALL_AI_ENGINEERING_FREE_TIER_ENABLED=true` repository variable.
- Model tools limited to repository file read/search/edit; Git/GitHub commands,
  test execution, hash checks and draft PR creation are deterministic runner
  steps after validating every modified path.
- Until PR #598 is resolved, the backend role refuses duplicate PRs.
- No automatic merge, paid The Odds API calls, live Supabase write, model .pkl
  modification, or production Vercel deployment.
- A draft PR created with `GITHUB_TOKEN` may not trigger usual `pull_request`
  CI checks. Do not merge until all required checks are independently confirmed.

## Verification and cutover gates

1. Repository owner installs the prepared workflow file into the existing
   `dev/engineering-actions-autopilot-20261010` branch.
2. CI for the workflow and guard passes.
3. Merge to `main` only after checks, then manually run `probe` in Actions.
4. Confirm the selected Gemini key is strictly free and not billed before
   enabling the variable. Without confirmation, leave the model gate closed.
5. Verify a scheduled job, scoped code change, green focused tests, pushed
   branch, and draft PR on GitHub. Verify required CI separately.
6. **Only then** disable the old ChatGPT Backend/Frontend schedules and
   related watchdog; retain Research Brain and Signal Scout until separately
   proven migrated.

A GitHub workflow is not a substitute for a configured AI model; a green
heartbeat without code or research results is not successful autonomous work.
