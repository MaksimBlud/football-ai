# CORNER SIX SIGNAL SCREEN V1

Status: **PREREGISTERED RETROSPECTIVE MULTI-COHORT SCREEN / RESEARCH ONLY / NO_BET**

## User question

Without waiting for new prospective matches, close six remaining signal families in order:

1. opening corner-price pressure;
2. line-transition mechanics;
3. cross-market match shape;
4. referee effect;
5. corner-environment volatility;
6. coach/tactical/lineup/availability regime changes.

The purpose is not to manufacture a winner from already-opened samples. Each family gets one
frozen primary construction and one frozen decision rule before this suite reads its result.

## Evidence boundary

Corner movement cohorts are already-opened historical research samples:

- V1_55 = 55 rows;
- REP50 = 50 rows;
- V1_46 = 46 rows;
- V2B_43 = 43 rows.

Total:

**194 unique corner-market fixtures.**

Therefore signals 1-5 are **hypothesis screens**, not independent confirmation.

No new future matches are collected.

Historical football inputs for signals 3-6 use Football-Data rows already available for
completed seasons, plus the current 2026/27 file only to recover pre-match market/referee
identity and prior-match history. Current target-match outcomes are not used by signals 3-5.

## Immutable corner artifacts

- pilot artifact 10503575942,
  sha256 ed012ae16dc3835900e7696d572088056724990866485078fed250283b379fe0;
- V1 backfill artifact 10506736726,
  sha256 b5d426ee99bb04d7b5eeae59f494cf0ba6b16aa15fe93fd28ec13e3fcdc3a441;
- fresh-50 artifact 10551727936,
  sha256 ca3c0f96338cf213e1dc76dbf47e88d01f7ad551f18e83ef2c185d4bc9eb6ba3;
- V1_46 artifact 10557706131,
  sha256 5ff43199cdf1bb73e6b87649c3e68aa57bac628c68888a06a809c5df473b8d1f;
- V2B raw artifact 10899611444,
  sha256 c2f5313efad4afb8663d9980f5ea004f52fe02827a83b5c99a8b775c35498a57;
- V2B lock artifact 10899325930,
  sha256 ad6bba499cc12abf5ca10732d88e0403565e2582e6c6c8a642ca7bb81248726f;
- V2B normalized evaluator artifact 10899842049 remains provenance only.

No provider request is made.

## Signal 1 — opening price pressure

Frozen feature:

`opening_price_pressure = devigged_opening_Over_probability - 0.50`

Interpretation:

- positive -> Over is shorter than Under after de-vig -> UP call;
- negative -> Under is shorter -> DOWN call.

Target:

`centre_delta = closing_lambda - opening_lambda`.

Primary diagnostics:

- balanced direction accuracy;
- raw accuracy vs contemporaneous majority-direction rule;
- Pearson/Spearman score vs centre_delta;
- same diagnostics in all four cohorts.

Promising only when:

- pooled balanced accuracy >= 0.55;
- pooled Spearman > 0;
- at least 3/4 cohorts have positive Spearman.

## Signal 2 — line-transition mechanics

Use the exact same opening price-pressure feature.

Two frozen questions:

1. among matches where the quoted corner line actually changes, does pressure sign predict
   the sign of the line step?
2. does absolute pressure identify whether the quoted line will move at all?

Primary metrics:

- balanced direction accuracy on non-zero `closing_line - opening_line`;
- ROC AUC of `abs(opening_price_pressure)` for any line move.

Promising only if both pooled metrics are >=0.55 and at least 3/4 cohorts are above 0.50
on both components.

## Signal 3 — cross-market match shape

This family does not use corner history to create the signal.

For EPL, La Liga and Serie A:

1. use historical Bet365 opening 1X2, O/U 2.5 and Asian Handicap features from
   2019/20 through 2024/25;
2. fit one simple league-specific Ridge model for actual total corners;
3. validate without retuning on 2025/26 against the league-mean corner baseline;
4. refit on 2019/20 through 2025/26;
5. for 2026/27 corner-market fixtures compute:

`match_shape_gap = historical_market_shape_expected_corners - opening_corner_lambda`.

Frozen direction hypothesis:

- positive gap -> UP;
- negative gap -> DOWN.

The historical match-shape model must first beat the league-mean MAE in at least 2/3
leagues. Direction then uses the same 0.55 balanced-accuracy / positive-Spearman /
3-of-4-cohort gate as Signal 1.

## Signal 4 — referee corner bias

For each league, estimate a historical referee corner-total bias from completed seasons with
fixed shrinkage:

`shrunk_bias = n/(n+20) * (referee_mean_total_corners - league_mean)`.

First validate the referee predictor on 2025/26 using only 2019/20-2024/25 referee history.

Then estimate current bias from all 2019/20-2025/26 history and test whether:

- positive referee corner bias -> later corner-market UP;
- negative referee corner bias -> DOWN.

Unknown referees receive exactly zero bias, not an inferred identity.

Historical MAE must improve in at least 2/3 leagues before any current direction result can
be called promising.

## Signal 5 — volatility rather than mean corner state

This family deliberately does not retune CORNERS10 means.

For each target team:

- take the previous 10 top-flight matches available in the same league source across
  2025/26 and 2026/27, strictly before the target date;
- calculate standard deviation of total-match corners;
- fixture volatility = mean(home team SD10, away team SD10).

Primary question is repricing **magnitude**, not direction.

Frozen material-move threshold is inherited unchanged from CORNER_MARKET_STATE_REPRICING_V1:

`0.362835012901983`.

Four leave-one-cohort-out folds compare:

- baseline = logistic model using opening FAIR_CENTRE only;
- candidate = same model + joint volatility.

Promising only if candidate improves pooled Brier and LogLoss and wins both metrics in at
least 3/4 held-out cohorts.

Skew is recorded only as a diagnostic and may not replace the frozen volatility feature.

## Signal 6 — coach / tactics / lineup / availability regime changes

This block does **not** invent a proxy.

Audit the existing Football-Data schemas for explicit:

- manager;
- coach;
- lineup / starting XI;
- injury;
- suspension fields.

Project rules already forbid reconstructing historical availability from later start/end
dates without publication-time provenance.

If the existing sources do not contain explicit point-in-time regime-change information,
the binding verdict is a data gap.

Do not replace this family with another recent-form or corner-trend transform.

## Safety

- research-only;
- NO_BET;
- no new prospective fixture collection;
- no paid Odds API calls;
- no Supabase writes;
- no production model operations;
- no automatic promotion;
- production .pkl hashes must remain unchanged.
