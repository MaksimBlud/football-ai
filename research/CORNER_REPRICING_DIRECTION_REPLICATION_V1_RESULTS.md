# CORNER_REPRICING_DIRECTION_REPLICATION_V1_RESULTS

Status: **REPRICING_AND_DIRECTION_REPLICATED / FRESH-UNSEEN FREE HOLDOUT / RESEARCH ONLY**

## Provenance

- preregistration first commit: `7a8db22e10382ccc80c6c6748ea2d8dc88077f47`;
- implementation PR: #385;
- tested PR head: `3827fc4c0964a4ec424ee071fa46adab2af4360a`;
- merge commit: `ed16e6551e2b567e147c76905c02642cbc7b0803`;
- dedicated live workflow run: `35355481894`;
- immutable result artifact: `10551727936`;
- artifact digest: `sha256:ca3c0f96338cf213e1dc76dbf47e88d01f7ad551f18e83ef2c185d4bc9eb6ba3`;
- paid subscription used: **false**;
- provider requests: **55 / 60**;
- match outcomes used: **false**;
- football-state/CORNERS10 used: **false**.

## Frozen sample

The immutable V1 55-row discovery sample remained training-only.

Fresh holdout:
- 50 previously unused fixture IDs;
- 10 each: EPL, La Liga, Serie A, Bundesliga, Ligue 1;
- all 50 produced eligible Bet365 full-time corner opening+closing markets;
- no fresh fixture overlapped the V1 55-row sample;
- fixture selection was deterministic before closing data were evaluated.

The frozen V1 predictor used:
- feature: `FAIR_CENTRE` = Poisson-reconstructed opening market centre;
- V1 material-move threshold: `0.3628350129`;
- V1 material-move prevalence: `0.2545454545`;
- full-V1 single-feature logistic coefficient: `-0.4734264224`.

The negative coefficient preserves the original V1 relationship: lower opening fair centres imply higher estimated risk of a material repricing by closing.

## Primary repricing-magnitude replication

Fresh-holdout pooled metrics:

Baseline:
- Brier: `0.1826115702`;
- LogLoss: `0.5516446554`.

Frozen FAIR_CENTRE predictor:
- Brier: `0.1631186776`;
- LogLoss: `0.5174742619`.

Improvement:
- delta Brier: **`-0.0194928926`**;
- delta LogLoss: **`-0.0341703935`**.

Both preregistered metrics improved on the 50 previously unused rows.

Magnitude result: **`REPRICING_MAGNITUDE_REPLICATED`**.

This is the key replicated signal:

> the opening corner-market fair centre contains information about whether the Bet365 corner market will later be materially repriced before closing.

This statement is about **market movement**, not the eventual match result.

## Frozen direction replication

The preregistered high-risk stratum used the frozen V1 repricing-risk score and selected the top 25% risk within each league.

Among high-risk rows with non-zero movement:
- n = **9**;
- positive/upward moves = **9**;
- negative/downward moves = **0**;
- positive share = **1.00**;
- one-sided exact binomial p-value versus 0.50 = **`0.001953125`**.

This passes the frozen direction gate:
- minimum non-zero high-risk n >= 8: PASS;
- positive share >= 0.70: PASS;
- one-sided p < 0.10: PASS.

Frozen direction result: **confirmed**.

## Critical direction caveat

The fresh holdout also showed a very strong **market-wide upward regime** outside the high-risk group:

- non-high-risk non-zero rows = **12**;
- non-high-risk positive share = **0.9166666667**;
- therefore 11 of 12 non-high-risk non-zero moves were also upward.

Across all non-zero fresh movements:
- positive = **20**;
- negative = **1**;
- positive share = **0.9523809524**.

Therefore the frozen statement "high-risk markets moved upward more often than 50/50" replicated, but this sample does **not** establish that the FAIR_CENTRE risk score uniquely predicts the **sign** of movement.

The stronger supported interpretation is:

1. **magnitude/risk is discriminative**: FAIR_CENTRE replicated out of sample for predicting whether repricing will be material;
2. **upward direction was real in this fresh window**, but it was broad across the market rather than clearly concentrated only in the FAIR_CENTRE high-risk stratum.

Do not restate the result as "low opening corner lines predict an upward move" without a separate fresh discrimination test against the contemporaneous market-wide direction baseline.

## Relationship to prior 1X2 / totals / handicap work

This result belongs to the same market-state research track:

- use pre-match bookmaker state;
- ignore match outcomes;
- predict the bookmaker market's own later repricing;
- treat movement magnitude separately from movement sign.

Unlike the earlier O/U2.5 football-state closing-movement V1, which failed its frozen validation gate, corner-market opening geometry has now passed:
- the original cross-league V1 discovery screen;
- a separate 50-row previously unseen replication for repricing magnitude.

That makes corner repricing-risk materially more promising than the tested O/U2.5 movement construction, while still remaining research-only.

## Binding next step

Do **not** retune V1 or this fresh holdout.

The next direction experiment, if run, must be preregistered on another untouched free batch and must explicitly test **direction discrimination versus the contemporaneous market-wide upward/downward regime**, not merely versus 50/50.

A suitable next primary question is:

> conditional on the current market-wide direction regime, does FAIR_CENTRE or another frozen opening-state variable identify which individual corner markets are especially likely to move upward versus downward?

Any such feature set, baseline and gate must be frozen before the next closing data are opened.

## Safety

- research-only;
- `NO_BET`;
- no production promotion;
- no production `.pkl` changes;
- no Supabase writes;
- no paid data;
- no outcome leakage;
- no post-result retuning of this holdout.
