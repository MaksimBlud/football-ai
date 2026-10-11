# FREE_CORNERS_EPL_MARKET_SCREEN_V2

Status: **PREREGISTERED / FREE-ONLY / EARLY OOT MARKET SCREEN**

## Purpose

Answer the narrow question: does the already-validated, calibrated recent-corners signal add useful information beyond Bet365 opening corner-total prices on the currently available free EPL window?

This is an early screen, not a profitability or production gate.

## Why V2 exists

The five-league `FREE_CORNERS_SIGNAL_SCREEN_V1` could not reach evaluation because its external Football-Data download path failed inside GitHub Actions after market acquisition.

V2 does not retune V1 from observed metrics. No valid V1 aggregate target/model metrics were produced.

V2 uses a football model that predates the current 2026/27 sample: `CORNER_TOTAL_CALIBRATED_V2`, whose historical methodology was already preregistered and completed.

## Historical football model

Source: live Supabase `public.matches`, read-only.

League: EPL only.

Training seasons:
- 2016/2017 through 2025/2026
- 2026/2027 outcomes are forbidden from model fitting

Historical source coverage verified before this contract:
- 3800 EPL rows with corner outcomes
- 3564 eligible rows after both teams have 10 prior EPL matches
- last historical training date: 2026-05-24

Use exactly the existing V2 raw score:

- `expected_home = (home CF10 + away CA10) / 2`
- `expected_away = (away CF10 + home CA10) / 2`
- `raw_expected_total = expected_home + expected_away`

Frozen calibration fitted on all eligible historical rows through 2025/26:

- `slope = 0.2538332863573`
- `intercept = 7.68865415864642`
- `baseline_total = 10.3111672278339`
- `calibrated_total = intercept + slope * raw_expected_total`

No refit using 2026/27 is permitted.

## Pre-season state

For every current EPL team, seed the rolling 10-match corner-for / corner-against history from the final ten EPL appearances present in historical Supabase through 2025/26.

A team with fewer than 10 historical EPL appearances is not eligible until its sequential 2026/27 history reaches ten prior EPL matches.

The seed snapshot is frozen in a separate repository file before the live market run.

## Current OOT sample

Source fixture/outcome snapshot: the already persisted 5Dollar free-provider artifact from workflow run `35243301608`, artifact `10506736726`.

Use **all 40 finished EPL 2026/27 fixtures** contained in that frozen fixture list, in chronological order.

Do not select or drop fixtures based on realized corner outcome.

Fixture eligibility is determined only by:
- both teams have 10 prior EPL matches in the sequential state;
- a valid Bet365 full-time opening corner market exists;
- opening line is integer or half-integer;
- opening Over and Under decimal prices are finite and > 1.

Quarter lines are excluded before scoring.

## Market acquisition

Provider: 5DollarFootballAPI **Free plan only**.

Bookmaker: Bet365.

Market: full-time total corners.

Use opening line + opening Over/Under prices only.

Reuse any already persisted opening market from artifact `10506736726`; request only missing EPL fixture odds.

No subscription purchase or upgrade is authorized.

Hard budget for this V2 live completion run: **45 actual provider HTTP attempts**, including retries.

## Probabilities

De-vig market probability:

`p_market = (1/over) / ((1/over) + (1/under))`

Football probability uses a Poisson count distribution with mean `calibrated_total`.

For half line `k+0.5`:

`p_football = P(X >= k+1 | calibrated_total)`

For integer line `k`:

`p_football = P(X > k) / (P(X > k) + P(X < k))`

Exact integer-line pushes are excluded from binary proper-score metrics.

Fixed incremental blend, frozen before evaluation:

`p_blend25 = 0.75 * p_market + 0.25 * p_football`

No blend-weight search is allowed.

## Primary metrics

On identical eligible non-push rows:

- market Brier
- blend25 Brier
- market LogLoss
- blend25 LogLoss
- `residual_alignment = mean((y - p_market) * (p_football - p_market))`

Also report:
- football-only Brier / LogLoss
- eligible fixture count
- push count
- mean absolute disagreement `|p_football - p_market|`
- directional agreement when football and market differ

## Early-screen verdict

This screen is intended to answer whether there is a **clear early signal**, not whether a small edge is absent.

- If fewer than 25 non-push eligible rows: `SAMPLE_TOO_SMALL`.
- Otherwise `INDICATIVE_INCREMENTAL_SIGNAL` only if:
  - blend25 Brier < market Brier;
  - blend25 LogLoss < market LogLoss;
  - residual_alignment > 0.
- Otherwise: `NO_CLEAR_INCREMENTAL_SIGNAL`.

No ROI, betting threshold, staking rule, CLV claim or production-readiness claim is allowed.

A negative early screen means "no clear incremental signal in the free current window", not proof that a 1-2% edge cannot exist.

## Safety

- research-only
- `NO_BET`
- free provider tier only
- no paid subscription
- no The Odds API spend
- no Supabase writes
- no production `.pkl` changes
- no model promotion
- no post-result feature/window/blend/threshold tuning inside V2
