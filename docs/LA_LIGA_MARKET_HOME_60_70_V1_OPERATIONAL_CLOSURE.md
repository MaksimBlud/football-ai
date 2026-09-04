# LA_LIGA_MARKET_HOME_60_70_V1 — Operational Closure

Status: **OPERATIONAL IMPLEMENTATION CLOSED / RESEARCH-ONLY / PROSPECTIVE ACCUMULATION ACTIVE**

Date: **2026-09-04**

This closure means the engineering, source-contract validation, information-time safety, outcome-free accumulation, explicit evaluation gate, and governance work for `LA_LIGA_MARKET_HOME_60_70_V1` are complete. It does **not** claim that the historical anomaly reproduced prospectively.

## Frozen candidate

The historical candidate remains unchanged:

- league: `LA_LIGA`;
- canonical market pick: HOME;
- margin-free HOME probability: `>= 0.60` and `< 0.70`;
- research-only market hypothesis, not Football-AI alpha.

No prospective result was used to alter these thresholds.

## Operational prospective boundary

The operational prospective sample begins at `2026-09-04T17:00:00Z`. Earlier observations are excluded from the prospective score even when their fixtures kick off after the freeze.

The canonical decision is the latest durably recorded pre-kickoff `MARKET_ONLY` row in `league_prediction_ledger` for the provider event. That immutable ledger row is the pre-kickoff tag authority. The exact raw offered odds are recovered from the unique `odds_snapshots` row with the same `league + event_id + snapshot_time_utc`; raw no-vig probabilities must reproduce the ledger probabilities within the frozen numerical tolerance. Ambiguous provider revisions are excluded fail-closed.

## Live source-contract proof

After PR #82 was merged, the first live read-only source-contract run on `main` successfully checked the existing pre-freeze source history without reading outcomes and without using any prospective rows.

The audit checked **100 ledger rows across 23 unique provider events**. Every checked ledger row resolved to its exact raw odds snapshot, and the maximum absolute difference between the raw no-vig probabilities and the durable ledger probabilities was **`5.828670879282072e-16`**. The checked snapshot interval was `2026-09-03T21:09:21.553387Z` through `2026-09-04T16:29:24.526493Z`.

This proves the existing durable ledger/raw-odds source contract is sufficiently exact for prospective tagging without introducing a new Supabase table.

## Outcome isolation

Autonomous and scheduled runs are permanently outcome-free. They may report current canonical decisions, provisional/final tag counts, settlement identity coverage, source-contract health, and accumulation status only.

The scheduled path does not query `result` values. Outcome evaluation is available only through a manual `workflow_dispatch` with `evaluate=true`, and the code additionally refuses evaluation before `2027-06-01T00:00:00Z`.

The eventual post-gate evaluation is descriptive only. It reports the preregistered count, wins, accuracy, expected wins from recorded market probabilities, actual-minus-expected wins, flat one-unit P&L/ROI at recorded offered odds, average odds, max drawdown, calibration diagnostic, and temporal breakdown. Historical observations are never pooled into the prospective score.

No match-count threshold, ROI threshold, p-value threshold, or production promotion rule is introduced by this implementation.

## Production isolation

The block does not modify live selection rules, production inference, calibrators, thresholds, prediction artifacts, or production `.pkl` files. All autonomous research workflows hash-check production model artifacts before and after execution. A future favorable prospective description would still require a separate research decision and a separate explicit production-promotion process.

## Closure decision

No threshold tuning, contextual filtering, bookmaker reselection, team/month exclusions, or retrospective reuse of prospective outcomes is permitted while the sample accumulates. Infrastructure changes are justified only to repair a concrete operational failure without changing the frozen candidate.

The implementation phase is therefore **CLOSED**. The scientific block remains **ACTIVE_ACCUMULATING** until the post-season explicit evaluation is permitted and deliberately invoked after `2027-06-01T00:00:00Z`.
