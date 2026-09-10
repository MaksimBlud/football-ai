# NON-EPL league-specific AI readiness V1

Status: **historical/OOS readiness formalized; prospective activation remains fail-closed**.

This contract covers all eight non-EPL candidates: LA_LIGA, SERIE_A, BUNDESLIGA, LIGUE_1, EREDIVISIE, RPL, PRIMEIRA_LIGA, and SUPER_LIG.

The audit uses completed historical/OOS repository capabilities plus outcome-free market-path availability. It does not call The Odds API, write Supabase, read prospective outcome/settlement tables, reuse the EPL production model for another league, or promote a production model.

## Eight-league result

| League | Historical | PIT | Normalization | Chronological OOS | Candidate artifact | AI calibration/provenance | Market path | Prospective |
|---|---|---|---|---|---|---|---|---|
| LA_LIGA | READY, 10 completed seasons | READY | READY | READY, dedicated sweep + locked 2025-26 holdout | builder added; manifest required | fail-closed until candidate passes | READY | FALSE |
| SERIE_A | READY, 10 completed seasons | READY | READY | READY, generic historical walk-forward | missing | missing | READY | FALSE |
| BUNDESLIGA | READY, 10 completed seasons | READY | READY | not formalized | missing | missing | READY | FALSE |
| LIGUE_1 | READY, 10 completed seasons | READY | READY | not formalized | missing | missing | READY | FALSE |
| EREDIVISIE | READY, 9 completed seasons in durable audit | READY | READY | not formalized | missing | missing | READY | FALSE |
| RPL | NOT READY, historical source unresolved | NOT READY | NOT READY | NOT READY | missing | missing | operational market path only | FALSE |
| PRIMEIRA_LIGA | READY via public Football-Data foundation audit | READY | READY via identity audit | not formalized | missing | missing | repository market-only path | FALSE |
| SUPER_LIG | READY via public Football-Data foundation audit | READY | READY via identity audit | not formalized | missing | missing | repository market-only path | FALSE |

**LA_LIGA is the first implementation target.** It uniquely already has a dedicated league-specific model sweep whose model selection uses completed seasons `2020-2021` through `2024-2025`, with `2025-2026` locked as a final historical holdout.

SERIE_A is the closest second target but still lacks a league-specific candidate artifact/calibration lineage. RPL cannot be promoted in this ranking merely because operational market snapshots exist: historical model-development readiness and market readiness are separate evidence layers.

## Live outcome-free market proof, 2026-09-10

A read-only `odds_snapshots` check found current market evidence for BUNDESLIGA (26 unique events), EPL (40), EREDIVISIE (30), LA_LIGA (42), LIGUE_1 (26), RPL (15), and SERIE_A (33). No Portugal or Turkey rows were present in that table at the check. This is market/infrastructure evidence only and does not convert MARKET_ONLY observations into AI predictions.

## Readiness boundary

`DATA_READY`, `PIT_READY`, `NORMALIZATION_READY`, `OOS_READY`, and `MARKET_READY` describe infrastructure. They do not prove model validity. `MODEL_READY`, `CALIBRATION_READY`, and `PROVENANCE_READY` require a validated league-specific candidate manifest. `PROSPECTIVE_READY` is deliberately always false in this auditor and needs a separate reviewed future-only frozen activation manifest.

## La Liga candidate implementation

`train_la_liga_1x2_candidate.py` is research-only. It reuses the existing leakage-safe La Liga feature/model sweep, chooses the model using completed historical selection folds, fits temperature calibration only from those completed OOS predictions, and evaluates the fixed candidate on the locked `2025-2026` historical holdout. Any `2026-2027` row is rejected.

A candidate is written only under `artifacts/candidates/la_liga/` and only when calibrated AI improves raw log loss, is non-worse on Brier, and strictly beats the historical market benchmark on accuracy, log loss, and Brier. A failed gate yields `REJECTED_NO_ARTIFACT`; the gate must not be weakened to force an artifact.

A successful manifest records model SHA-256, calibrator SHA-256, code SHA, historical cutoff, feature-schema SHA-256, OOS validation, and calibration provenance. Even then prospective activation remains false until a separate future-only preregistration freezes artifact/code hashes, feature formula, market cutoff, sample/time gate, no-peek rules, and metrics before target outcomes exist.

## Non-negotiable boundaries

- EPL production artifacts are never used for non-EPL model inference or training.
- Historical/OOS development is not production promotion.
- No automatic promotion is introduced.
- Existing MARKET_ONLY rows are never backfilled as AI predictions.
- Structural/market calibration is not AI-model probability calibration.
- Prospective outcomes remain outside this readiness block.
