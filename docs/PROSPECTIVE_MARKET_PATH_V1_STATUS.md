# Prospective Market Path V1 — Status

Status: **PREREGISTERED / RESEARCH-ONLY / ACCUMULATING PROSPECTIVE SAMPLE**

`PROSPECTIVE_MARKET_PATH_V1` tests one narrow question that was not answered by the prior historical market-timing or convergence work: whether the already-observed path of our own timestamped 1X2 market snapshots adds outcome-predictive information beyond the current market price available at a fixed pre-match cutoff.

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

Until every league passes that gate, the autonomous cycle may emit only eligibility and readiness coverage. It must not calculate or print Brier or log-loss comparisons.

## Operational state

The block is read-only and needs no new database table, migration, or external provider. It consumes the already-existing immutable `odds_snapshots` and `league_finished_results` data. The weekly research workflow checks readiness and is protected by production `.pkl` hash comparison before and after every run.

No Supabase rows are written, no prediction ledger is changed, no production model or calibrator is loaded or promoted, and no live selection rule is affected.

The research conclusion is intentionally **not yet known**. The block remains open only for genuine prospective accumulation and the pre-registered evaluation once the frozen readiness gate is satisfied.
