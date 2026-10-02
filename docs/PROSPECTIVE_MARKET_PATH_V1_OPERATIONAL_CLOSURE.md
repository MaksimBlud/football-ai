# Prospective Market Path V1 — Operational Closure

Status: **OPERATIONAL IMPLEMENTATION CLOSED / RESEARCH-ONLY / PROSPECTIVE ACCUMULATION ACTIVE**

Date: **2026-09-04**

This closure means the engineering, governance, collection-safety, identity-safety, settlement monitoring, and readiness-monitoring work for `PROSPECTIVE_MARKET_PATH_V1` is complete. It does **not** claim a scientific result. The preregistered outcome comparison remains unresolved until genuine future observations satisfy the frozen readiness gate.

## Frozen research contract

The research protocol remains frozen at `2026-09-04T14:25:00Z`. Only fixtures kicking off at or after that timestamp are eligible. Feature information is cut at kickoff minus six hours. Each fixture requires at least three usable snapshots spanning at least twelve hours. The candidate adds exactly six preregistered probability-path features to the current no-vig market probabilities.

The frozen readiness gate remains unchanged: every EPL, La Liga, and Serie A sample must independently contain at least 100 settled eligible fixtures, at least four calendar months, and at least two valid monthly test blocks, with at least 60 prior training fixtures and at least 20 fixtures in every scored test block.

## Operational closure guarantees

The following infrastructure is complete and autonomous:

- existing EPL, La Liga, and Serie A odds collectors provide the prospective source snapshots;
- fixture-level coverage monitoring classifies active paths fail-closed and raises on active `IRRECOVERABLE` coverage loss;
- stale schedule revisions are classified as `SUPERSEDED`, while same-event kickoff conflicts remain excluded as `CONFLICT`;
- canonical settlement identity excludes ambiguous multi-event revisions instead of choosing one using later information;
- settlement-lag monitoring uses identity fields only and raises after the frozen 18-hour grace period if a canonical settlement identity is still missing;
- sample-growth/readiness monitoring uses settlement identity presence only and never queries result values;
- production `.pkl` hashes are checked around all research workflows that can run autonomously.

## Outcome evaluation gate

Autonomous and scheduled Market Path workflows are permanently outcome-free. They may report coverage, settlement health, settled-sample growth, and frozen readiness only.

The paired outcome evaluation is a separate explicit research action. It can run only through a manual `workflow_dispatch` with `evaluate=true`, which invokes `prospective_market_path_cycle.py --evaluate`. That explicit path re-checks the frozen all-three-league readiness gate and refuses evaluation if the gate is not satisfied.

No schedule or push trigger passes `--evaluate`. Reaching readiness therefore cannot automatically expose Brier score, log loss, paired deltas, or any other outcome comparison.

## Current live baseline

The first post-hardening settlement-lag audit reported 20 eligible EPL paths, 23 La Liga paths, and 22 Serie A paths, with zero `SETTLEMENT_LATE`; all were still inside the grace period. The first outcome-free sample-growth audit reported zero settled prospective fixtures in each league, zero calendar months, zero valid test blocks, and `ready=false` for all three leagues. No outcome scores were computed.

This is the expected state immediately after preregistration and does not represent a negative or positive research result.

## Production isolation

This block has no production activation path. It does not modify prediction ledgers, live selection rules, production inference, calibrators, thresholds, or production model artifacts. A future positive research result would still require a separate explicit promotion decision under repository governance.

## Closure decision

No additional Market Path V1 feature engineering, window tuning, eligibility tuning, model-family tuning, or retrospective probing is permitted while the prospective sample accumulates. Infrastructure changes are justified only to repair a concrete operational health failure without changing the frozen hypothesis.

The implementation phase is therefore **CLOSED**. The scientific experiment remains **ACTIVE_ACCUMULATING** until the preregistered readiness gate is satisfied and the explicit manual evaluation is run once under the frozen protocol.


## Post-closure operational repair — 2026-10-02

The operational closure permits infrastructure fixes only for concrete health failures that leave the frozen scientific hypothesis unchanged. PR #462 is such a repair.

A scheduled identity-only audit found six stale provider event revisions entering settlement/readiness even though the coverage subsystem already marked them `SUPERSEDED`, plus one `Atalanta BC` versus `Atalanta` identity mismatch. The repair unified settlement-lag, sample-growth and explicit evaluation with the already-existing provider-revision policy and added the missing team-name normalization. It did not alter any Market Path feature, cutoff, eligibility threshold, model, or outcome gate.

Merge:

`b2003667f6b779e2291980f64972d6010d4c9928`

Post-merge live settlement-lag run `37026271275` returned:

- EPL 20/20 settled, 0 late;
- La Liga 15/15 settled, 0 late;
- Serie A 19/19 settled, 0 late.

Artifact `11234609485`, digest
`sha256:6f350cb5fb783893d4780cce24169e85b87dcab06a57d5a574064ad582a49314`.

Post-merge outcome-free sample-growth run `37026271205` returned 20 / 15 / 19 settled fixtures respectively, one calendar month in each league, zero valid test blocks, `ready=false` in all three leagues, and settlement health `OK`.

Artifact `11235402989`, digest
`sha256:ed087c3059060aa5a67297f2c571ee194e061501d736262864da3ff7fa0e21af`.

No result values were queried by either monitor. The closure semantics are unchanged: the experiment continues accumulating prospectively and cannot be scored automatically.