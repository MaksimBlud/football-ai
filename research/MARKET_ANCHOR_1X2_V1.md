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

## First untouched OOT execution

The first final-OOT execution occurred on PR #325 at head `9898fdea005b6344d638fb65c39e394886bced28`, before any result-specific tuning of this V1 construction.

GitHub Actions run: `34917928502`.
Artifact: `10376584443` (`market-anchor-1x2-v1`).
Artifact digest: `sha256:d015b35f305fe934e99559184425ec3b69f165e1f85e57294eddb5a06b771746`.
Frozen report: `experiments/market_anchor_1x2_v1_report.json`.

Pooled untouched 2025-2026 test (`n=1140`):

- Market: Brier `0.5889962354`, LogLoss `0.9881046788`, accuracy `0.5263157895`.
- Gated residual candidate: Brier `0.5886577614`, LogLoss `0.9877190855`, accuracy `0.5271929825`.
- Delta candidate - market: Brier `-0.0003384740`; LogLoss `-0.0003855933`.
- Formal V1 gate result: `residual_accepted=true`, `active_mode=RESIDUAL`.

League selection remained fail-closed:

- EPL: `MARKET`, `lambda=0.0`; test delta exactly zero.
- La Liga: `MARKET`, `lambda=0.0`; test delta exactly zero.
- Serie A: `ALL_FOOTBALL`, `lambda=1.0`; test Brier delta `-0.0010154220`, LogLoss delta `-0.0011567799`; accuracy `0.5421052632` vs market `0.5394736842`.

Interpretation is deliberately conservative: the sign is positive under the preregistered gate, but the pooled magnitude is very small. This is historical temporal OOT evidence for the market-anchored architecture, **not** production-quality proof, a betting signal, or permission to tune V1 on the opened 2025-2026 test. Any further model changes require a new version/protocol and fresh evidence.

## Post-selection robustness diagnostic

The robustness pass is diagnostic-only and does not alter V1. A regression discovered and fixed an initial implementation error where validation 2024-2025 would have been included in a post-hoc final refit. The corrected robustness path now exactly replays the frozen Serie A V1 training split: 2016-2017 through 2023-2024 only; validation is selection-only.

Corrected run: `34918346551`.
Artifact: `10377595106` (`market-anchor-1x2-v1-robustness`).
Artifact digest: `sha256:56ebad616726e6c3f690a4b2c05949e4a5971d1a3a60d828bf65bb054b9b4734`.
Frozen corrected report: `experiments/market_anchor_1x2_v1_robustness_report.json`.

For the exact frozen Serie A 2025-2026 OOT (`n=380`):

- Brier mean delta `-0.0010154220`, paired bootstrap 95% interval `[-0.0051650435, +0.0032368771]`, bootstrap probability better than market `0.6831`.
- LogLoss mean delta `-0.0011567799`, paired bootstrap 95% interval `[-0.0080689479, +0.0060389577]`, bootstrap probability better than market `0.6317`.
- Candidate beats market on per-match Brier in `53.68%` of fixtures and on per-match LogLoss in `57.63%`.
- The fixed post-selection configuration wins both metrics in only `2/6` earlier retrospective seasons.

Therefore robustness does **not** provide strong independent evidence of persistent superiority. The first OOT sign remains positive, but uncertainty spans zero and historical consistency is weak. V1 stays research-only / `NO_BET`; no production promotion follows from these results.

## Prohibited uses

This protocol does not:

- use the opened September 2026 outcomes for tuning or selection;
- overwrite or promote any production `.pkl`;
- authorize a betting decision;
- authorize threshold tuning on the OOT test;
- relabel historical OOT evidence as prospective evidence.

Any future production promotion requires a separate explicit promotion protocol and fresh prospective validation.
