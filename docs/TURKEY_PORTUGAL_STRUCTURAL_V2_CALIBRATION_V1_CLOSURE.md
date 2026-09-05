# Turkey / Portugal Structural V2 Calibration V1 — Closure

Status: **HISTORICAL CALIBRATION RESEARCH CLOSED / RESEARCH-ONLY / NO RUNTIME ACTIVATION**

The preregistered `TURKEY_PORTUGAL_STRUCTURAL_V2_CALIBRATION_V1` protocol was evaluated only after the preregistration had been merged to `main`. The successful post-merge evaluation was GitHub Actions run `33965220775` on commit `385331fcb1799749fd053e9dc67393c9a35db9e4`. The uploaded result artifact is `turkey-portugal-structural-v2-evaluation` (artifact id `9969216176`, SHA-256 `2fc4f5f5dd4f8d95466cfafb4b37b5f6e5c1ce89276abff756f9ced3ce2b29b5`). A compact immutable summary is stored in `research/turkey_portugal_structural_v2_calibration_v1_result.json`.

## Safety and protocol proof

- The frozen completed-season sample remained 2016/17 through 2025/26; 2026/27 was excluded.
- Turkey and Portugal were evaluated independently; no cross-league parameter transfer was used.
- Candidate selection used only prior-season inner folds. Outer-test outcomes were not supplied to candidate selection.
- No The Odds API requests or Supabase operations were used.
- Production `.pkl` hashes were unchanged.
- No runtime configuration was mutated and there was no automatic promotion.
- Market argmax changed on exactly zero evaluated rows in both leagues.
- Runtime calibration status remains `CALIBRATION_REQUIRED` for both leagues.

## Turkey Super Lig

The frozen nested walk-forward evaluation found a small but positive historical OOS probability-quality signal.

Across five outer folds (1,716 market-valid test rows), all five inner selectors chose a Structural V2 candidate. Weighted aggregate deltas versus no-vig BET365 market probabilities were:

- LogLoss delta: `-0.0010542716010495574`
- Brier delta: `-0.0004530200963225977`
- Accuracy delta: `0.0`
- Argmax changes: `0`

Four of the five outer seasons improved both LogLoss and Brier. The latest 2025/26 outer fold was slightly worse (`LogLoss +0.0001409343`, `Brier +0.0002627742`), so the result is evidence of a historical OOS signal, not a justification for automatic activation or a claim of stable production edge.

Research conclusion: **`HISTORICAL_OOS_SIGNAL_OBSERVED`**.

Decision: keep the Turkey result as research evidence only. Do not mutate Turkey runtime calibration in this closure. Any future runtime calibration proposal must be a separate explicitly reviewed PR with its own evidence and safety checks.

## Primeira Liga

Portugal did not satisfy a consistent two-metric OOS improvement interpretation.

Across five outer folds (1,528 market-valid test rows), weighted aggregate LogLoss improved slightly (`-0.0005029266108470644`), but weighted aggregate Brier worsened (`+0.0001820944975439356`). Three of five outer seasons worsened on both reported probability-quality metrics. Market argmax remained unchanged throughout.

Research conclusion: **`CALIBRATION_NOT_SUPPORTED_OR_INCONSISTENT`**.

Decision: do not calibrate Structural V2 for Primeira Liga from this historical sample. Retuning on the same seen sample is prohibited.

## Governance closure

This historical calibration block is now closed. A negative or mixed result is treated as a valid research outcome. Neither league is activated by this research, and no final parameters are copied into runtime configuration. The frozen preregistration file remains unchanged as the protocol-of-record.
