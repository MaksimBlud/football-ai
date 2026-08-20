# Football AI — Codex Project Instructions

## Source of truth

- Treat the current Git repository and current Supabase data as source of truth.
- Old audit reports, backups, saved files, and handoff documents are historical context only.
- Always inspect `git status --short` before changing anything.

## Dirty working tree

This repository intentionally contains existing modified and untracked research work.

NEVER:
- run `git clean`
- run `git reset --hard`
- delete unrelated untracked files
- mass-stage files
- mass-format the repository
- rewrite unrelated files
- assume untracked files are disposable

Only modify files that are necessary for the explicit task.

## Production safety

Production prediction logic and production artifacts must be treated conservatively.

Required production artifacts include:

- football_model_xgboost_elo.pkl
- football_model_no_odds.pkl
- 1x2_calibrator.pkl
- home_goals_model_no_odds.pkl
- away_goals_model_no_odds.pkl
- over_2_5_calibrator.pkl
- btts_calibrator.pkl

Rules:

- Training is NOT promotion.
- Research is NOT production.
- New training/calibration outputs should be candidate artifacts by default.
- Never overwrite or promote a production artifact unless the user explicitly asks for promotion.
- Never run a promotion command automatically.
- Never modify a production `.pkl` as a side effect of research.
- Preserve existing production inference compatibility unless the task explicitly requires a change.

## ML methodology

The project evaluates football predictions and betting-market edge.

Important principles:

- Use temporal / walk-forward evaluation.
- Prefer nested walk-forward when selecting hyperparameters or thresholds.
- Test seasons must never influence their own training or parameter selection.
- Features for a match must use only information available before that match.
- `result`, `home_goals`, `away_goals`, or derived future outcomes must never enter prediction features.
- Treat `NO BET` as a valid result.
- Do not optimize for one season only.
- Do not claim profitable edge without OOS evidence.
- Compare against bookmaker/fair-market baselines where appropriate.
- For betting/value research, report ROI, sample size, stability by season, and drawdown where available.
- Exploratory parameter searches are not promotion evidence unless validated on untouched data.

## Injury data caveat

Historical injury features may be event-time correct without proving that the information was publicly known before kickoff.

Do not describe historical injury backtests as strict information-time point-in-time unless this is actually proven by the data source.

## Closing market rules

- True closing snapshot means the last odds snapshot strictly before kickoff.
- Do not call a snapshot "true close" before kickoff has passed.
- Closing probabilities may be used as evaluation targets/reference values.
- Never use future closing probabilities as pre-match prediction features.

## Artifact lifecycle

- Candidate artifacts belong under `artifacts/candidates/`.
- Local audit snapshots belong under `artifacts/audit_snapshot/`.
- Candidate `.pkl` files must not be added to Git.
- Production promotion must be explicit and separately validated.
- Where practical, candidate metadata should include:
  - SHA256
  - producer script
  - UTC timestamp
  - training/input data hashes
  - model/calibrator type
  - feature names/count
  - parameters

## Task execution policy

For review/audit/diagnosis/planning tasks:

- Inspect relevant files and report findings.
- Do not implement unrelated changes.

For explicit build/fix/change tasks:

- Make only the smallest in-scope local changes.
- Run relevant non-destructive validation.
- Do not ask for confirmation for normal read-only inspection, syntax checks, or tests.
- Stop before destructive, external, production-promotion, or materially scope-expanding actions.

## Codex task efficiency

Codex task capacity is limited.

Do NOT spend substantial effort on:
- cosmetic refactors
- formatting-only work
- renaming for style
- simple git status checks
- trivial one-file inspection
- repeating existing experiments without a specific hypothesis
- broad "improve the codebase" work

Prefer high-value tasks such as:
- multi-file architectural fixes
- reproducibility hardening
- leakage/data-flow analysis
- nested validation frameworks
- artifact lifecycle
- meaningful research hypotheses with measurable OOS results

One task should answer one concrete engineering or research question.

## Testing and validation

Before finishing a change:

- run syntax checks where relevant
- run focused tests
- run `git diff --check`
- verify production artifacts were not unexpectedly changed
- inspect `git status --short`

If a training-related task runs candidate training:
- record production artifact SHA256 before and after
- prove production hash did not change

## Git behavior

Do not commit automatically unless the user explicitly requests it.

Do not push automatically unless the user explicitly requests it.

At task completion always report:

1. files changed
2. what was done
3. tests/validation run
4. `git diff --stat`
5. relevant risks or limitations
6. whether any production artifact changed
7. recommended next single task

## Current known project state

The current production safety behavior is intentional:

`train_model_xgboost_elo.py` saves a candidate artifact by default.
Production overwrite requires an explicit `--production` flag.

Do not weaken this invariant.
