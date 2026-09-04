# LA_LIGA_MARKET_HOME_60_70_V1 — prospective validation protocol

Status: **FROZEN / RESEARCH ONLY**.

## Purpose

Prospectively validate the historical La Liga market anomaly without changing its rule after observing new results. This is not a production betting rule and is not evidence of Football-AI-specific incremental information.

## Frozen eligibility rule

A fixture qualifies only when all of the following are true before kickoff:

1. league is `LA_LIGA`;
2. canonical 1X2 market selection is HOME;
3. the margin-free HOME probability from the designated canonical pre-kickoff snapshot is `>= 0.60` and `< 0.70`;
4. the exact snapshot and offered HOME odds used for the decision are durably recorded before kickoff.

No team, month, season, bookmaker, or contextual exclusions may be introduced after outcomes are observed.

## Operational freeze addendum — 2026-09-04

This addendum was adopted before the operational prospective sample begins. It does not change the historical candidate thresholds.

- Operational prospective observations begin at `2026-09-04T17:00:00Z`. Earlier snapshots are excluded from the operational prospective sample even when the fixture kicks off later.
- The repository's existing canonical closing convention is used: the designated decision is the **latest durably recorded pre-kickoff `MARKET_ONLY` row** in `league_prediction_ledger` for the provider event.
- That immutable ledger row is the durable pre-kickoff tag source. Its `event_id + snapshot_time_utc` must match exactly one raw `odds_snapshots` row; the raw row supplies the offered HOME odds and must reproduce the stored margin-free market probabilities.
- Ambiguous provider event revisions or conflicting kickoff identities are excluded fail-closed. The implementation may not select one revision using later outcome information.
- Autonomous monitoring is outcome-free. It may use only settlement identity presence, not `result` values.
- Outcome evaluation is a separate explicit manual action and is time-gated until `2027-06-01T00:00:00Z`. No schedule or push trigger may bypass this gate.
- The post-gate evaluation remains descriptive and research-only. No production promotion rule, ROI threshold, p-value threshold, or match-count threshold is introduced by this addendum.

The machine-readable operational contract is `research/la_liga_market_home_60_70_v1_prospective_runtime.json`.

## Prospective accounting

Every qualifying fixture must be tagged before kickoff and later settled. Report count, wins, accuracy, expected wins from the recorded margin-free probabilities, actual-minus-expected wins, flat one-unit P&L/ROI at the recorded offered odds, average odds, max drawdown, calibration diagnostics, and temporal breakdown.

Historical evidence must never be pooled into the prospective score when deciding whether the prospective candidate reproduced.

## Market anomaly versus Football AI

The candidate is a market-only hypothesis. A separate incremental-information experiment is required for any claim that Football AI adds value:

- same qualifying fixtures;
- same decision timestamp;
- same canonical market probabilities;
- Football AI probabilities generated without future information;
- paired scoring on every fixture, preferably log loss and multiclass Brier/RPS;
- report `model - market` paired score differences with uncertainty;
- if testing a blend, its weight must be fixed using training data only and evaluated on later untouched data.

Accuracy or ROI of the market-only candidate cannot establish model alpha.

## Research decision states

Until a separately predeclared evidence gate is adopted, report only descriptive states:

- `ACCUMULATING` — prospective fixtures are being collected;
- `DIRECTIONALLY_CONSISTENT` — observed direction agrees with the historical hypothesis;
- `DIRECTIONALLY_INCONSISTENT` — observed direction does not agree;
- `INSUFFICIENT_FOR_DECISION` — no promotion decision is justified.

Do not invent a match-count, ROI, p-value, or calibration threshold after seeing prospective outcomes.

## Prohibited actions

This protocol does not authorize production `.pkl` modification, model promotion, Structural alpha/edge-threshold changes, automatic wagering, or changes to canonical settlement semantics.
