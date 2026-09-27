# Football AI — Gemini Research Agent Instructions

Read and obey `AGENTS.md` before making any change. These instructions add a narrower
contract for the free Gemini GitHub Actions research agent.

## Scope

You are implementing one GitHub Issue that has already passed the repository
Research Agent V2 gate with `READY_FOR_PREREGISTRATION`.

The workflow will tell you the issue number. You may create or edit files only under:

- `research/agent_runs/issue_<ISSUE_NUMBER>/`
- `tests/agent_runs/issue_<ISSUE_NUMBER>/`
- `docs/agent_runs/issue_<ISSUE_NUMBER>/`

Do not edit any other path. A deterministic gate will reject the run if you do.

## Research workflow

1. Inspect existing repository code and the signal research registry.
2. Create a frozen preregistration before outcome-reading evaluation.
3. Reuse existing read-only historical data and research helpers where possible.
4. Keep implementation self-contained inside the issue sandbox.
5. Add focused tests under the issue test directory.
6. Add a concise research report/status document under the issue docs directory.
7. If valid evaluation cannot be completed without paid APIs, Supabase writes,
   production changes, premature prospective outcome access, or unavailable data,
   document the blocker rather than bypassing it.

## Hard prohibitions

- No production promotion.
- No production `.pkl` modification.
- No Supabase writes or schema changes.
- No paid Odds API requests.
- No deployment or runtime calibration activation.
- No direct changes to `main`.
- No deletion, rename, or mass formatting.
- No retuning closed hypotheses on seen samples.
- No claims of betting edge without untouched OOS evidence.

Git operations and pull-request creation are handled by deterministic workflow code after
your edits pass safety gates. Do not attempt to manage GitHub state yourself.
