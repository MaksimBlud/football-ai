# Football AI Research Agent V1

## Purpose

Research Agent V1 is a deliberately constrained first step toward autonomous
Football AI research in GitHub Actions.

V1 is **manual-dispatch, historical/read-only, research-only**. It does not
execute arbitrary model-generated commands and it cannot promote production
artifacts.

## V1 contract

The coordinator:

1. validates the existing signal research registry;
2. requires a non-empty research task and stable `hypothesis_family`;
3. rejects an exact hypothesis-family match already present in the registry;
4. emits a research specification for a novel family;
5. requires preregistration before outcome-reading evaluation.

The deterministic safety layer blocks:

- production `.pkl` changes;
- production promotion commands;
- direct pushes to `main`;
- selected runtime-calibration mutation paths;
- unsupported write/live modes.

## Explicitly unavailable in V1

V1 does not:

- write to Supabase;
- spend Odds API credits;
- deploy;
- merge pull requests;
- activate runtime calibration;
- score prospective outcomes automatically;
- promote any candidate model;
- execute arbitrary LLM-generated shell commands.

## Manual usage

Run the **Research Agent V1** workflow with:

- `task`: the research question;
- `hypothesis_family`: a stable snake_case family identifier.

The workflow uploads `research-agent-v1-spec`.

A novel family returns `READY_FOR_PREREGISTRATION`.
An existing exact family returns `REJECT_EXISTING_HYPOTHESIS_FAMILY`.

## Why V1 stops at a research specification

The repository already contains frozen preregistration, evaluation, signal
registry, production-hash and PR-validation mechanisms. The safest first
autonomous layer is therefore an orchestrator that must pass deterministic
gates before any future LLM executor is introduced.

## Next controlled step

After V1 passes CI and controlled manual trials, V2 may add an LLM planner that
can propose files and commands, but every proposed action must remain behind
the deterministic allowlist/safety gate. Issue-triggered execution should only
be enabled after that behavior is proven.
