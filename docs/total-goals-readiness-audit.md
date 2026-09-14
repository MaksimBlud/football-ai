# Total Goals readiness audit — 2026-09-14

Status: **PROVISIONAL / MODEL-ONLY / NO BET**.

This document records the evidence established before any Total Goals activation. It does not promote a model, change a production `.pkl`, publish a prediction, call a paid provider, or relax any frozen research contract.

## Deployment prerequisite

The exact-main deployment gate that previously blocked product expansion is closed.

- GitHub `main` at proof time: `c96ccb772b38f9edf449ce3162d715f9c89b636e`.
- Exact Main Vercel Deployment run: `34767216889`.
- Successful job: `103750823774`.
- Vercel production deployment: `dpl_BGqFZMSVQz5g6gSqEfyCx7xCX7qq`.
- Staged `/health.deployment_git_sha`, staged product smoke, pre-promotion fresh-main recheck, promotion, and public `/health.deployment_git_sha` all matched `c96ccb772b38f9edf449ce3162d715f9c89b636e`.
- Public `/product-market-view`, `/portfolio-risk-view`, and `/production-readiness-view` returned successfully in the independent post-deploy read-only check.

Any later merge must restore this exact-main invariant before its runtime behavior is described as live.

## Goal inference lineage

Current goal inference is a four-artifact bundle, not a single model file:

1. `home_goals_model_no_odds.pkl`
2. `away_goals_model_no_odds.pkl`
3. `over_2_5_calibrator.pkl`
4. `btts_calibrator.pkl`

`goal_prediction_no_odds.py` loads all four artifacts. The two regression models produce expected home/away goals. `poisson_utils.py` derives raw goal-market probabilities from the score grid, then the two calibrators transform Over 2.5 and BTTS probabilities. Therefore the identity of a published goal prediction must cover all four binary artifacts.

The production goal `.pkl` binaries are intentionally not tracked in Git, so their current binary hashes cannot be reconstructed from GitHub `main` alone. Their identity must be captured at prediction publication time from the actual local/runtime files.

## Training and temporal provenance

`train_goal_models_no_odds.py` uses 18 no-odds pre-match football features and saves candidate artifacts through the artifact lifecycle instead of overwriting production artifacts. Its current 20% holdout depends on input row order rather than asserting an explicit chronological boundary inside the trainer. The normal upstream feature pipeline is chronological, but this remains a provenance-hardening opportunity; the trainer's holdout must not be treated as independently proven temporal evidence if its input ordering is unknown.

`evaluate_goal_markets_thresholds.py` is the producer of `data/goal_markets_oos_predictions.csv`. For each test season after the first, it trains fresh home/away goal regressors only on preceding seasons and writes predictions for the held-out season. Under the normal chronologically ordered upstream season sequence, these saved rows are expanding-season out-of-sample predictions.

The evaluator currently derives season order from first occurrence in the input frame. A future hardening should make chronological season ordering/boundaries explicit rather than relying on upstream order.

## Calibration provenance

`calibrate_goal_markets.py` uses:

- calibration seasons: `2017/18` through `2022/23`;
- method-selection seasons: `2023/24`, `2024/25`, `2025/26`;
- RAW / SIGMOID / ISOTONIC comparison by Brier score, separately for Over 2.5 and BTTS.

After method selection, the chosen calibrator is refit on all available OOS rows, including the method-selection seasons. That is a valid deployment refit pattern, but the method-selection metrics are not an untouched final generalization test of the refitted production calibrator and must not be presented as such.

## Bundle provenance contract

The durable schema currently has one `model_goals_sha256` column. No database migration is required to identify the complete inference dependency set.

`goal-artifact-bundle.v1` defines `model_goals_sha256` as SHA-256 of this exact UTF-8 payload:

```text
goal-artifact-bundle.v1
home_goals_model_no_odds.pkl:<sha256>
away_goals_model_no_odds.pkl:<sha256>
over_2_5_calibrator.pkl:<sha256>
btts_calibrator.pkl:<sha256>
```

with a final newline. Artifact order is fixed. Each component digest is SHA-256 of the corresponding binary file bytes.

Publisher behavior is fail-closed:

- any snapshot row carrying Total Goals / goal-model outputs requires a non-empty complete bundle identity;
- the CLI computes that identity from all four real files;
- the former single-file `--model-goals-artifact` option cannot be used as Total Goals provenance;
- 1X2-only rows with no goal outputs remain valid without a goal bundle;
- no artifact is modified or repackaged to compute the identity.

## Remaining readiness gates

This provenance hardening does **not** make Total Goals operational. The scope remains `PROVISIONAL / model-only` and `bet_decision = no_bet`.

Open gates established by the current product/runtime contract:

- current durable live prediction snapshots do not yet contain the required Total Goals model probabilities for the active fixtures;
- the stored odds contract currently transports 1X2 prices only, so there is no proven bookmaker Over/Under 2.5 price contract or live coverage;
- there is no proven Total Goals-specific settlement contract;
- there is no proven Total Goals lifecycle/reliability sample meeting the product evidence gate;
- even after objective gates pass, a new scope can automatically reach at most `REVIEWABLE`; `OPERATIONAL` requires explicit approval.

No live Total Goals publication should occur until the actual four-artifact bundle is available at the publication runtime, its composite SHA is recorded, and the remaining price/lifecycle/reliability contracts are implemented and proven without weakening current safety rules.
