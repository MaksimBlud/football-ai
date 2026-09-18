# CORNER_REPRICING_DIRECTION_REPLICATION_V1

Status: **PREREGISTERED / FRESH-UNSEEN FREE HOLDOUT / MARKET-ONLY**

## Purpose

This experiment is the fresh-data continuation of `CORNER_MARKET_STATE_REPRICING_V1`.

It does **not** test match outcomes, CORNERS10, team form, expected corners, profitability or betting returns.

It tests two already-observed market-state hypotheses without retuning V1:

1. **repricing magnitude replication** — does the V1 `FAIR_CENTRE` opening-market signal continue to identify corner markets that will be materially repriced by closing?
2. **direction replication** — among markets that the frozen V1 predictor ranks as highest repricing-risk, are non-zero closing moves disproportionately upward?

The second question exists because V1 showed a diagnostic 9 positive / 1 negative / 5 zero split in its high-risk rows. That diagnostic is now treated only as a hypothesis and must be tested on previously unused fixtures.

## Frozen discovery/training data

Training/discovery source is immutable and already opened:

- 5Dollar source pilot artifact `10503575942`;
- free corners screen artifact `10506736726`;
- the same 55 eligible Bet365 full-time corner markets used by `CORNER_MARKET_STATE_REPRICING_V1`;
- 11 rows each for EPL, La Liga, Serie A, Bundesliga and Ligue 1.

No V1 row may be removed or changed.

## Frozen fresh-holdout source and fixture selection

The holdout must contain **previously unused fixture IDs** from the provider's currently available Free window.

Selection is deterministic and fixed before new closing data are opened:

- leagues: EPL, LA_LIGA, SERIE_A, BUNDESLIGA, LIGUE_1;
- fetch completed fixtures from the free league endpoint;
- exclude every fixture ID present in either immutable V1 source artifact;
- sort remaining completed fixtures within league by kickoff descending, then fixture ID ascending;
- select the first **10** fixtures per league;
- target sample = 50 fresh rows;
- no fixture may be replaced because its odds movement is inconvenient;
- if a selected fixture lacks a structurally complete Bet365 full-time corner opening+closing market, it remains selected but is marked ineligible; do not backfill it with a later-ranked fixture.

No paid endpoint or subscription is allowed.

## Frozen market representation

Use exactly the V1 market reconstruction from `corner_market_state_repricing_v1.py`:

- proportional de-vig of Over/Under prices;
- integer and half-integer corner lines only;
- Poisson-implied comparable market centre `lambda`;
- solve interval `[1.0, 25.0]`;
- `centre_delta = closing_lambda - opening_lambda`;
- `movement_magnitude = abs(centre_delta)`.

Quarter-lines and malformed markets are excluded, not approximated.

## Frozen V1 predictor

Primary feature: **`FAIR_CENTRE` only** = reconstructed `opening_lambda`.

Using the immutable 55-row V1 sample only:

1. fit the material-move threshold as the 75th percentile of V1 `movement_magnitude`;
2. target = 1 when V1 `movement_magnitude >= threshold`;
3. fit:
   - `SimpleImputer(strategy="median")`;
   - `StandardScaler`;
   - `LogisticRegression(C=0.1, max_iter=2000)`;
4. fit once on all 55 V1 rows;
5. freeze the resulting threshold, preprocessing and classifier before scoring the fresh holdout.

No feature search, C search, quantile search, league-specific refit or threshold change is allowed.

## Primary magnitude replication

Fresh-holdout target uses the **frozen V1 movement threshold**, not a quantile refitted on the new sample.

Baseline probability is the material-move prevalence in the immutable V1 training sample.

Compare frozen candidate versus frozen constant baseline on the fresh eligible holdout using:

- Brier score;
- LogLoss.

Magnitude result:

- `REPRICING_MAGNITUDE_REPLICATED` if candidate is strictly better on **both** pooled Brier and pooled LogLoss;
- otherwise `REPRICING_MAGNITUDE_NOT_REPLICATED`.

Per-league metrics are diagnostic only because the fresh sample is small.

## Frozen high-risk direction test

Within each league, rank fresh eligible rows by the **frozen V1 predicted repricing-risk probability**, descending.

High-risk stratum:

- top 25% of eligible rows in that league, rounded up;
- if tied at the cutoff, stable deterministic fixture-ID ordering decides membership;
- the ranking uses opening state only.

Direction analysis uses only rows with non-zero `centre_delta`.

Primary direction hypothesis:

> high-risk non-zero moves are more often positive than negative.

Direction confirmation requires **all** of:

- at least 8 non-zero high-risk moves pooled;
- positive share among non-zero high-risk moves >= 0.70;
- one-sided exact binomial test versus p=0.50 has p-value < 0.10.

Also report the positive share among non-high-risk non-zero rows as a diagnostic comparison, but it is not a gate.

No direction classifier is fit or tuned.

## Sample gate

Evaluation is valid only if:

- at least 30 fresh eligible rows pooled;
- at least 4 eligible rows in each of at least 4 leagues.

Otherwise verdict = `SAMPLE_TOO_SMALL`.

## Final frozen verdicts

- `REPRICING_AND_DIRECTION_REPLICATED`:
  magnitude replication passes and direction confirmation passes.
- `REPRICING_REPLICATED_DIRECTION_NOT_CONFIRMED`:
  magnitude replication passes, direction confirmation fails.
- `NO_FRESH_REPLICATION`:
  magnitude replication fails.
- `SAMPLE_TOO_SMALL`:
  sample gate fails.

These are research-screen verdicts only.

## Safety

- research-only;
- `NO_BET`;
- no match outcomes;
- no CORNERS10 / football-state inputs;
- no ROI optimization;
- no production promotion;
- no production `.pkl` changes;
- no Supabase writes;
- no paid provider request;
- no retuning after opening the fresh holdout;
- production artifact hash guard required.
