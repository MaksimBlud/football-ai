# Prospective Market Path V1 — Status

Status: **OPERATIONAL IMPLEMENTATION CLOSED / RESEARCH-ONLY / ACTIVE PROSPECTIVE ACCUMULATION**

`PROSPECTIVE_MARKET_PATH_V1` tests one narrow question that was not answered by the prior historical market-timing or convergence work: whether the already-observed path of our own timestamped 1X2 market snapshots adds outcome-predictive information beyond the current market price available at a fixed pre-match cutoff.

The engineering and governance implementation is now closed. The scientific conclusion is intentionally still unknown and remains active only because genuine future observations must accumulate before the single frozen evaluation is allowed. See `docs/PROSPECTIVE_MARKET_PATH_V1_OPERATIONAL_CLOSURE.md` for the formal operational closure.

## Frozen information contract

The protocol was frozen at **2026-09-04T14:25:00Z**. Fixtures with kickoff before that timestamp are permanently ineligible, even if their historical snapshots and outcomes already exist in Supabase.

For every eligible fixture, the information cutoff is kickoff minus six hours. Only snapshots observed at or before that cutoff can enter features. A fixture needs at least three usable snapshots and at least twelve hours between the first and last eligible snapshot. Any later snapshot, closing price, match event, score, or result is forbidden from feature construction.

The current-price baseline is the no-vig home/draw/away probability vector from the latest eligible snapshot. `MARKET_PATH_V1` adds exactly six frozen trajectory features: the net home/draw/away probability moves from the first eligible snapshot to the cutoff snapshot and the total absolute home/draw/away probability path travelled across all eligible snapshots. No slope, acceleration, threshold, bookmaker-specific split, or alternative window may be selected after results are seen.

## Frozen evaluation

The comparison is `MARKET_MODEL` versus `MARKET_PATH_MODEL`, using the same median-imputation, standard-scaling, logistic-regression family. Evaluation is expanding monthly walk-forward on EPL, La Liga, and Serie A.

Outcome metrics are forbidden until **all three** leagues independently have:

- at least 100 settled eligible fixtures;
- at least four calendar months of eligible prospective coverage;
- at least two valid monthly test blocks;
- at least 60 prior training fixtures for each scored block;
- at least 20 fixtures in each scored test block.

Autonomous scheduled and push-triggered workflows may emit only coverage, settlement health, sample growth, and readiness. They do **not** query outcome values and cannot automatically transition to scoring when readiness becomes true.

The preregistered paired outcome evaluation is now an explicit manual research action only. It requires `workflow_dispatch` with `evaluate=true`, which invokes `prospective_market_path_cycle.py --evaluate`. That explicit path re-checks the frozen all-three-league readiness gate and refuses to score if the gate is not satisfied.

## Operational state

The block is read-only and needs no new database table, migration, or external provider. It consumes the already-existing immutable `odds_snapshots` and `league_finished_results` data. Autonomous research workflows are protected by production `.pkl` hash comparison before and after every run.

A separate two-hour fixture-level coverage monitor checks whether each observed provider event already satisfies, can still satisfy, or can no longer satisfy the frozen path requirements. Active fixtures that become `IRRECOVERABLE` make the monitor workflow fail **after** diagnostic CSV artifacts have been uploaded. Provider schedule revisions that are clearly stale are reported as `SUPERSEDED`; same-event kickoff ambiguity remains `CONFLICT` and is excluded fail-closed.

The live coverage audit on **2026-09-04** confirmed that the existing collection cadence is sufficient for the current active sample:

- EPL: 20 active fixtures, all 20 `READY`, 0 `IRRECOVERABLE`;
- La Liga: 23 active fixtures `READY`, plus 1 stale `SUPERSEDED` provider revision, 0 `IRRECOVERABLE`;
- Serie A: 21 active fixtures `READY`, plus 2 stale `SUPERSEDED` revisions and 1 same-event kickoff `CONFLICT`, 0 `IRRECOVERABLE`.

The known Serie A conflict is Cagliari–Lecce provider event `8f751e96142db860ba66bbea713baf50`; it is excluded rather than repaired or guessed. Settlement also excludes an entire canonical fixture identity if two distinct provider event IDs would otherwise map to the same league-local match date and normalized home/away pair. No later provider information is used to choose between revisions.

The first settlement-lag audit reported 20 eligible EPL paths, 23 La Liga paths, and 22 Serie A paths, all still inside the 18-hour settlement grace period and with `SETTLEMENT_LATE=0`.

The first outcome-free sample-growth audit on **2026-09-04** reported 0 settled eligible fixtures, 0 calendar months, and 0 valid test blocks for EPL, La Liga, and Serie A. It explicitly reported that readiness was not reached and no outcome evaluation was performed. This is the expected state immediately after preregistration.

No Supabase rows are written by the Market Path research monitors, no prediction ledger is changed, no production model or calibrator is promoted, and no live selection rule is affected.

## Closure semantics

No further Market Path V1 feature engineering, cutoff changes, span changes, eligibility tuning, model-family tuning, or retrospective probing is permitted while the prospective sample accumulates. Future code changes are justified only by a concrete operational health failure and must preserve the frozen hypothesis.

Therefore the **implementation phase is CLOSED**. The registry remains `ACTIVE_ACCUMULATING` only because the scientific experiment cannot be resolved until future data satisfy the preregistered gate. Reaching readiness will not trigger scoring automatically; evaluation remains a separate explicit manual action, and any future production promotion remains a separate explicit decision.
