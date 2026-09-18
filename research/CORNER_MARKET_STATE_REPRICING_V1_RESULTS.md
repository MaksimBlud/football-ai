# CORNER_MARKET_STATE_REPRICING_V1_RESULTS

Status: **STRONG_REPRICING_SIGNAL / DISCOVERY SCREEN ONLY**

## Provenance

- frozen contract first commit: `8f116e93a7d3e5f8ace48c6ba6fab7ba6f8e2703`;
- implementation PR: #383;
- tested PR head: `413f3e947684bd23c6b2493ec19e0b366b6d8caf`;
- merge commit: `653b0c10433f522d0b8a2becdc3608a8f2bba57b`;
- dedicated workflow run: `35352713546`;
- immutable result artifact: `10550262038`;
- artifact digest: `sha256:92177e4ddb39331b33e9c97fc75541b0371f744f17a9dd6a2355188839960b92`;
- source rows: union of free immutable artifacts `10503575942` and `10506736726`;
- new paid/provider calls for replay: **0**;
- match outcomes used: **false**;
- football-state/CORNERS10 used: **false**.

## Frozen sample

- 55 eligible Bet365 full-time corner markets;
- 11 rows each: EPL, La Liga, Serie A, Bundesliga, Ligue 1;
- opening and closing line + both Over/Under prices;
- integer and half-integer lines only;
- opening/closing market states reconstructed to a comparable Poisson-implied centre;
- material repricing target = top 25% absolute centre movement;
- fixed leave-one-league-out transfer: train four leagues, test the fifth.

## Primary result

Frozen verdict: **`STRONG_REPRICING_SIGNAL`**.

Selected fixed feature variant: **`FAIR_CENTRE`** — the reconstructed opening corner-market centre.

Held-out league wins on **both Brier and LogLoss**:

- EPL: PASS;
- La Liga: PASS;
- Serie A: FAIL;
- Bundesliga: PASS;
- Ligue 1: PASS.

Total: **4/5 held-out leagues**.

Pooled out-of-fold result:

- n = 55;
- positives = 15;
- baseline Brier = `0.1988636364`;
- FAIR_CENTRE Brier = `0.1817366900`;
- delta Brier = **`-0.0171269464`**;
- baseline LogLoss = `0.5873036057`;
- FAIR_CENTRE LogLoss = `0.5396836907`;
- delta LogLoss = **`-0.0476199150`**;
- pooled ROC AUC = **`0.7458333333`**;
- pooled Average Precision = **`0.4882999665`** versus prevalence `0.2727272727`.

The fixed screen therefore satisfies the preregistered strong-signal rule: pooled Brier and LogLoss both improve and at least 4/5 held-out leagues beat the constant baseline on both metrics.

## Direction of the relationship

The single-feature logistic coefficient for `FAIR_CENTRE` was negative in **all five folds**:

- EPL held out: `-0.3883`;
- La Liga held out: `-0.3439`;
- Serie A held out: `-0.5457`;
- Bundesliga held out: `-0.3738`;
- Ligue 1 held out: `-0.4725`.

Interpretation:

> **Lower opening corner-market centres were associated with a higher probability of a large subsequent repricing by closing.**

This is a repricing-risk signal. It is **not** yet a claim about which direction the corner line will move.

## Secondary opening-market geometry

`PRICE_IMBALANCE` also won 4/5 held-out leagues, but its pooled gain was much smaller:

- pooled delta Brier: `-0.0004194050`;
- pooled delta LogLoss: `-0.0027430688`;
- pooled ROC AUC: `0.6050`.

`LINE_LEVEL` and `FULL_STATE` improved pooled metrics but won only 3/5 held-out leagues.

`ENTROPY` did not beat pooled baseline despite 3/5 fold wins.

`OVER_LEVEL` failed the pooled test.

No feature family may be re-ranked or retuned inside V1 after this result.

## Direction diagnostic

For the highest-risk quarter of rows inside each held-out league under the selected FAIR_CENTRE score:

- high-risk rows: 15;
- positive centre moves: 9;
- negative centre moves: 1;
- zero moves: 5;
- positive share among non-zero moves: `0.90`.

This is **diagnostic only**. The preregistered contract explicitly forbids promoting magnitude predictability into a direction claim. No direction classifier was tuned, and `stable_direction_claim = false`.

The 9/1 non-zero split is a hypothesis for a separately preregistered fresh-data test, not evidence that "lower opening corner totals will rise".

## Relationship to the 1X2 research

This is the intended analogue of the earlier 1X2 market-state repricing result.

The common pattern is:

1. observe only the current bookmaker market;
2. ignore the eventual match result;
3. ask whether the current market geometry predicts **how much the bookmaker market itself will later be repriced**;
4. test transfer to unseen temporal/league data;
5. treat direction separately.

The corner result therefore belongs to the market-discovery track, not the football-model-vs-market track.

## What the result does and does not mean

Supported by V1:

- there is a **real discovery-level signal** in opening corner-market state for subsequent repricing magnitude on this free 55-match sample;
- the strongest fixed signal is the opening fair market centre;
- the relationship transfers to 4/5 held-out leagues;
- lower opening centres consistently carry higher estimated repricing risk in all five trained folds.

Not supported by V1:

- profitable betting;
- a guaranteed market direction;
- a claim that a low corner line should automatically be bet Over;
- production readiness;
- robustness across seasons;
- robustness across bookmakers;
- exact ROI or CLV edge.

The sample is short and contemporary. It is sufficient to justify a fresh replication, not to promote the signal.

## Next binding research step

The next experiment must **not** retune this opened V1.

It should collect new free corner opening/closing markets and preregister a direct replication of:

- `FAIR_CENTRE` only as the primary repricing-risk feature;
- the same Poisson market-centre reconstruction;
- the same material-move concept;
- no match outcomes;
- no football-state inputs.

A separate direction experiment may test the now-observed positive-move diagnostic, but it must be frozen before new closing data are opened.

## Safety

- research-only;
- `NO_BET`;
- no production promotion;
- no production `.pkl` changes;
- no Supabase writes;
- no paid data;
- no automatic betting;
- no retuning V1 after opening this result.
