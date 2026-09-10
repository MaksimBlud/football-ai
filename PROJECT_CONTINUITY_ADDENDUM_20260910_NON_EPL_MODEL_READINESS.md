# PROJECT CONTINUITY ADDENDUM — 2026-09-10 — NON-EPL MODEL READINESS

This addendum supersedes the previous execution pointer for the current safe research block once its containing PR is merged.

## Durable finding

The eight-candidate historical/OOS readiness audit selects **LA_LIGA** as the first non-EPL league-specific AI implementation target.

Reason: La Liga uniquely already has the dedicated leakage-safe historical model sweep, completed selection seasons `2020-2021` through `2024-2025`, locked completed historical holdout `2025-2026`, canonical normalization, PIT feature path, and market comparison path needed to attempt a separate candidate artifact without using the EPL production model.

SERIE_A is the next-closest foundation. Bundesliga, Ligue 1 and Eredivisie still need league-specific OOS model formalization. RPL remains historical-source fail-closed. Primeira Liga and Super Lig have historical/identity foundations but not dedicated league-specific OOS candidate pipelines.

## Implemented in this block

- `non_epl_model_readiness.py`: deterministic, fail-closed readiness matrix for all eight leagues.
- `train_la_liga_1x2_candidate.py`: research-only La Liga candidate builder using completed history and locked `2025-2026` holdout.
- strict candidate gate versus raw AI and historical market benchmark.
- candidate output only under ignored `artifacts/candidates/la_liga/`.
- explicit model/calibrator/code/feature-schema/historical-cutoff provenance in a passing manifest.
- `PROSPECTIVE_READY` remains hard false in the readiness auditor.
- regression tests and dedicated zero-cost CI/historical candidate proof.

## Safety state

No paid Odds API request is authorized or required by this block. No prospective experiment outcome/settlement data is read. No existing MARKET_ONLY row becomes AI evidence. No EPL production artifact is reused for non-EPL inference. No production `.pkl` promotion is introduced.

## Next execution pointer

1. Complete this PR through full CI, fresh-main exact-head merge, and post-merge proof.
2. Inspect the zero-cost La Liga historical candidate proof result.
3. If the strict candidate gate is `REJECTED_NO_ARTIFACT`, keep La Liga model readiness fail-closed and use the diagnostics to choose the next preregistered historical-only model improvement; do not weaken the gate.
4. If it is `CANDIDATE_ARTIFACT_WRITTEN`, verify manifest hashes/provenance, but still keep `PROSPECTIVE_READY = FALSE`.
5. Only after a valid candidate exists may a separate reviewed change preregister a future-only prospective cohort before any target outcomes exist.
