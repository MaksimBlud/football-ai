# Multi-Market V2 — Frozen OOS Evaluation Protocol

Status: **PREREGISTERED / OUTCOME-AGNOSTIC / RESEARCH-ONLY**

This protocol is frozen before any prospective Multi-Market V2 OOS outcome evaluation is activated. It defines sample construction and metrics in advance so later results cannot be tuned by changing evaluation rules after outcomes are observed.

## Scope

The evaluator is descriptive calibration evaluation for immutable pre-kickoff market probabilities stored by Multi-Market V1 and immutable Multi-Market V2 settlement revisions. It does **not** create betting recommendations, estimate profit, promote a production model, or claim an AI edge.

## Unit of evaluation

The unit is one canonical market observation per unique `(league, event_id)`.

When multiple pre-kickoff snapshots exist for an event, use exactly the latest snapshot whose `snapshot_time_utc < kickoff_utc`. This avoids pseudo-replication from repeated snapshots of the same match.

When multiple immutable settlement revisions exist for the same snapshot, prefer `GOALS_AND_CORNERS` over `GOALS_ONLY`. If two revisions have the same completeness for one snapshot, fail closed rather than choosing arbitrarily.

## Canonical evaluated sides

Two-sided market probabilities are complementary. Evaluating both sides would duplicate the same information, so only one preregistered side is scored:

- handicap: `HOME`
- total goals: `OVER`
- total corners: `OVER`
- home team corners: `OVER`
- away team corners: `OVER`

`NOT_OFFERED`, `UNSETTLED_MISSING_OUTCOME`, and `INVALID` are not converted into outcomes. They are excluded and counted explicitly by reason.

## Settlement-to-target mapping

Settlement classification is mapped to a soft binary target before scoring:

| Settlement | Target |
| --- | ---: |
| `WIN` | 1.00 |
| `HALF_WIN` | 0.75 |
| `PUSH` | 0.50 |
| `HALF_LOSS` | 0.25 |
| `LOSS` | 0.00 |

This preserves the quarter-line settlement contract without pretending that a half-win is a full binary win or discarding pushes after outcomes are known.

## Metrics

For market probability `p` and preregistered soft target `y`:

- Brier: `(p - y)^2`
- Soft LogLoss: `-[y log(p) + (1-y) log(1-p)]`

Probabilities must be finite and strictly inside `(0,1)`. Invalid probabilities fail closed for that observation and are counted explicitly.

Report:

1. per-league/per-market usable observations, unique events, mean Brier, and mean LogLoss;
2. pooled micro metrics across all usable canonical observations;
3. macro metrics as the unweighted mean of eligible per-market metric cells;
4. exclusion counts by reason.

No post-outcome market weighting is permitted.

## Descriptive readiness floor

A per-league/per-market cell is considered sample-ready only at **30 unique events / 30 usable observations**. This is a reporting floor, not a statistical significance claim and not an activation threshold for betting or production use.

Cells below the floor remain `INSUFFICIENT_SAMPLE`. Pooled metrics may be computed for diagnostics, but no cell below the floor may be presented as mature OOS evidence.

## Safety and immutability

- snapshot must be research-only `MULTI_MARKET_V1`;
- settlement must be research-only `MULTI_MARKET_SETTLEMENT_V2`;
- `snapshot_time_utc` must be strictly before `kickoff_utc`;
- snapshot identity must agree with settlement identity;
- no fuzzy fixture matching;
- no live provider calls inside the evaluator;
- no database writes inside the evaluator;
- no production artifact changes;
- no automatic activation from evaluator output.

Changing this protocol after prospective outcomes have been inspected requires a new protocol version and a new untouched prospective sample. Existing evaluated observations must not be silently re-scored under revised rules.
