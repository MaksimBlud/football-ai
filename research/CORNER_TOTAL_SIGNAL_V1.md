# CORNER_TOTAL_SIGNAL_V1

Status: PREREGISTERED HISTORICAL RESEARCH

## Goal

Test whether a simple, interpretable pre-match corner-state rule predicts the total number of match corners consistently across unseen EPL seasons.

This is a corners-specific target experiment. It is separate from CORNERS10-as-a-1X2-feature and separate from bookmaker corner-market acquisition.

## Evidence boundary

- Historical source: live Supabase `public.matches`, EPL only.
- Allowed seasons: 2016/2017 through 2025/2026.
- Forbidden: 2026/2027 outcomes and any current prospective frozen-cohort outcomes.
- Read-only research only. No Supabase writes, no Odds API calls, no production `.pkl` changes, no model promotion.

## Fixed pre-match signal

For each team, use only its previous 10 EPL matches available before the current kickoff.

For a fixture Home vs Away:

- expected_home_corners = (Home corners-for last 10 + Away corners-against last 10) / 2
- expected_away_corners = (Away corners-for last 10 + Home corners-against last 10) / 2
- expected_total_corners = expected_home_corners + expected_away_corners

A fixture is eligible only when both teams have at least 10 prior EPL matches in the historical stream. Histories are continuous across season boundaries; promoted teams become eligible only after accumulating 10 EPL matches.

No parameter or weight search is allowed in V1.

## Fixed baseline

The baseline prediction is the expanding mean total corners from all earlier eligible EPL matches available before the fixture.

The baseline must not use the current match or any future match.

## Evaluation seasons

Primary held-out seasons are fixed to:
- 2019/2020
- 2020/2021
- 2021/2022
- 2022/2023
- 2023/2024
- 2024/2025
- 2025/2026

Earlier seasons provide warm-up/history only.

## Primary metric

Mean Absolute Error (MAE) for predicted total corners.

For each held-out season calculate:
- signal MAE;
- baseline MAE;
- delta MAE = signal MAE - baseline MAE.

Lower is better.

Primary portability requirement:
- mean weighted delta MAE < 0; and
- signal beats baseline in at least 5 of 7 held-out seasons.

If both conditions pass: `PORTABLE_TOTAL_SIGNAL`.
Otherwise: `NOT_PORTABLE_TOTAL_SIGNAL`.

## Fixed Over/Under check

Primary betting-style line is fixed before evaluation at **9.5 total corners**.

Use `expected_total_corners` as a continuous score for actual `total_corners > 9.5`.

Report per held-out season:
- ROC AUC;
- simple hit rate from rule `expected_total_corners > 9.5`.

AUC is descriptive in V1 and is not allowed to override the primary MAE decision.

Robustness lines 8.5 and 10.5 may be reported only after the 9.5 result and may not replace the primary line.

## Interpretation rules

- A positive result means recent corner-state contains season-portable information about future corner totals.
- It does not prove betting profitability because historical bookmaker corner odds are not part of this dataset.
- It does not activate production or Multi-Market.
- If positive, the next step is a separately preregistered market comparison once bookmaker corner lines are available.
- If negative, do not tune weights or thresholds inside V1; any new formula must be a new experiment.
