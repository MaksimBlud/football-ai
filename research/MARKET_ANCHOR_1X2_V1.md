# MARKET_ANCHOR_1X2_V1

Status: **research-only candidate**. No production promotion is authorized by this protocol.

## Motivation

The current production 1X2 XGBoost consumes bookmaker odds as ordinary features. It is therefore free to deform a strong market prior rather than proving an incremental football signal. Recent opened evidence showed that this can underperform the market on Brier, LogLoss and top-1 accuracy.

This experiment changes the architecture, not the production artifact.

## Fixed construction

The bookmaker prior is the de-vigged market distribution `m`.

A football-only residual model produces logits `r(x)`. Candidate probabilities are:

`p = softmax(log(m) + lambda * r(x))`

`lambda=0` is an exact identity fallback to `m`.

Football-only feature variants considered on validation are fixed before the final test:

- `FORM`
- `FORM_GOALS`
- `FORM_GOALS_CORNERS`
- `ALL_FOOTBALL`

The fixed lambda grid is:

`[0.00, 0.10, 0.25, 0.50, 0.75, 1.00]`

The residual is a regularized multinomial logit correction with the draw residual used as the reference level. Market probabilities are an offset and are not trainable football features.

## Temporal contract

Source: the existing Football-Data historical research path used by `historical_football_signal_runner.py` for EPL, La Liga and Serie A.

- train: 2016-2017 through 2023-2024
- validation: 2024-2025
- untouched OOT test: 2025-2026
- 2026-2027 is excluded
- the opened September 2026 EPL/replay outcomes cannot enter train, selection or final test

Within each league, feature variant and lambda are selected on validation only. A non-zero choice must improve **both** multiclass Brier and multiclass LogLoss against the raw de-vigged market on validation; otherwise that league selects lambda 0.

The final 2025-2026 test is then evaluated once.

## Fail-closed acceptance

The pooled residual candidate is accepted only when, on the untouched 2025-2026 OOT test:

- `candidate Brier < market Brier`, and
- `candidate LogLoss < market LogLoss`.

If either condition fails, active mode is `MARKET_FALLBACK` and active probabilities are exactly the de-vigged market. Accuracy is descriptive and cannot override the probabilistic gate.

Therefore "not worse than market" means an architectural fallback to equality with the market when incremental signal is not proven. It does **not** claim that any finite future realized sample is guaranteed to have lower loss than bookmakers.

## Prohibited uses

This protocol does not:

- use the opened September 2026 outcomes for tuning or selection;
- overwrite or promote any production `.pkl`;
- authorize a betting decision;
- authorize threshold tuning on the OOT test;
- relabel historical OOT evidence as prospective evidence.

Any future production promotion requires a separate explicit promotion protocol and fresh prospective validation.
