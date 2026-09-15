# LA Liga Market Anchor prospective micro-cohort — 2026-09-15

## Status

`PREREGISTERED / OUTCOME-BLIND / RESEARCH-ONLY / NO_BET`

Experiment: `LA_LIGA_MARKET_ANCHOR_PROSPECTIVE_20260915_V1`.

This is a deliberately tiny forward diagnostic on three La Liga fixtures. Its purpose is to answer one narrow question: **before seeing these results, does the fixed football residual move the saved market probabilities in a direction that later improves probabilistic accuracy?**

It is not a production-promotion gate and must not be enlarged, retuned, or reinterpreted after outcomes.

## Frozen cohort

All identities and the market baseline were durable before the experiment was created. Market snapshot time for all three rows: `2026-09-11T15:45:28.192487Z`; each snapshot had `19` bookmakers.

1. `b9a6e597fd597637efa24b92d51dda62` — Rayo Vallecano vs Espanyol — kickoff `2026-09-15T17:00:00Z`.
2. `d6474326396cdd0e300afd0193c7c93d` — Alavés vs Valencia — kickoff `2026-09-15T18:00:00Z`.
3. `0b57607f4a514ee24df31b0c2db9ddc5` — Elche CF vs Real Madrid — kickoff `2026-09-15T19:30:00Z`.

Frozen market probabilities H/D/A:
- Rayo Vallecano–Espanyol: `0.46932048598728 / 0.275291229511983 / 0.255388284500737`;
- Alavés–Valencia: `0.447759791488515 / 0.304537995169928 / 0.247702213341557`;
- Elche–Real Madrid: `0.104522793893611 / 0.165700942434781 / 0.729776263671608`.

No paid refresh is required or authorized for the baseline.

## Frozen candidate recipe

This is a **new La Liga analogue** of the previously frozen Market Anchor residual architecture. It is not the Serie A V2 artifact transferred across leagues.

Before any target outcome is read:
- league: `LA_LIGA`;
- feature set: exact historical `ALL_FOOTBALL` feature set from source commit `df19777087fb89af049eedce44ff93f0aa6e6360`;
- L2 penalty: `1.0`;
- training seasons: La Liga `2016-2017` through `2025-2026` only;
- training data cutoff: `2026-06-30T23:59:59Z`;
- target feature history cutoff: `2026-09-15T00:00:00Z`;
- market combination: `softmax(log(P_market) + lambda * residual_logits)` using the frozen implementation primitive;
- active lambda: `0.0` (exact market fallback);
- diagnostic shadow lambda: `1.0`;
- no lambda sweep, feature search, threshold search, consensus-method search or subgroup selection is permitted on these three outcomes.

Exact frozen source blobs are verified before generation:
- `historical_football_signal_lab.py` = `401b3a0893371bfa4a488ec92a4a54af2678c8f7`;
- `market_anchor_1x2_v1.py` = `58c35bf3768f7bf2b951f19a37b9a5f46b6b9801`.

## Prospective freeze rule

The prediction runner must complete before the first kickoff (`2026-09-15T17:00:00Z`). It fails closed at or after that time.

The canonical freeze must contain:
- exact three event IDs;
- capture time;
- historical source hashes;
- candidate artifact SHA256;
- exact market probabilities;
- exact active `lambda=0` probabilities;
- exact shadow `lambda=1` probabilities;
- no result/score/outcome fields.

Once the canonical freeze JSON is committed, it is immutable evidence. CI validates it instead of regenerating it.

## Outcome gate and metrics

Results must not enter the evaluation path before `2026-09-15T21:30:00Z`, and evaluation requires all three final H/D/A labels at once. No one-match early peek is part of the contract.

Primary metrics:
1. pooled multiclass Brier score;
2. pooled multiclass LogLoss.

Secondary metric: top-1 1X2 accuracy.

Report also includes per-match Brier and LogLoss deltas. Negative candidate-minus-market delta is better.

A **directional micro-cohort win** requires both pooled Brier and pooled LogLoss to beat market. Even if that happens, `n=3` is explicitly insufficient for production promotion, betting activation, lambda activation, or retuning. Failure is equally informative and must not trigger same-cohort tuning.

## Safety

- research only;
- `NO_BET`;
- no production `.pkl` read/write/promotion;
- no automatic model promotion;
- no Odds API call;
- no target outcomes in prediction runner or freeze file;
- active output remains exact market fallback (`lambda=0`).
