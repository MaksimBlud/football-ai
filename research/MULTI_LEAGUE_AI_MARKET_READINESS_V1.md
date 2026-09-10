# Multi-League AI-vs-Market Readiness V1

Status: **OUTCOME-FREE READINESS CONTRACT / NO COHORT ACTIVATION**

## Finding

The live project has two distinct prospective layers that must not be conflated:

1. `league_prediction_ledger` is a broad multi-league operational ledger. Its current rows are intentionally `MARKET_ONLY`; Structural V2 remains fail-closed while calibration is unavailable.
2. `epl_ai_market_pair_ledger` is the existing paired Football-AI-vs-market research ledger. It stores model probabilities together with exact model artifact and code provenance and belongs to the frozen `EPL_AI_MARKET_PAIR_V1` experiment.

Therefore the number of multi-league operational events is not the sample size of the paired AI-vs-market experiment.

## Live outcome-free proof on 2026-09-10

Read-only Supabase inspection showed 190 unique operational league-events in `league_prediction_ledger`:

- BUNDESLIGA: 26
- EPL: 30
- EREDIVISIE: 30
- LA_LIGA: 30
- LIGUE_1: 26
- RPL: 15
- SERIE_A: 33

Every one of those league groups was `prediction_mode=MARKET_ONLY`, `structural_status=CALIBRATION_REQUIRED`, with zero Structural V2 applied rows.

The separate `epl_ai_market_pair_ledger` contains 12 unique EPL paired events. Its schema includes model probabilities, `model_artifact_sha256`, `code_commit_sha`, exact market timestamp, model generation timestamp and history cutoff. The generic multi-league ledger does not carry equivalent AI-model provenance.

No outcome/result/settlement table was read to make this determination.

## Methodological boundary

The 190 already-collected operational events MUST NOT be retroactively counted as a new prospective multi-league AI-vs-market primary sample.

A new multi-league paired primary experiment may start only after its activation manifest is frozen prospectively. For every admitted league that manifest must fix, before eligible future events are collected:

- league identity and eligibility rules;
- the AI model artifact and immutable artifact hash;
- the exact feature/history reconstruction contract;
- probability calibration semantics, if applicable;
- model/code provenance;
- market snapshot/cutoff identity and exact-price verification;
- pre-kickoff temporal gates;
- sample target and evaluation timing;
- no-peek / no-optional-stopping rules;
- primary metrics.

Existing pre-activation rows may be used for infrastructure/readiness validation, but not silently promoted into the future primary cohort.

## Current readiness decision

- `EPL_AI_MARKET_PAIR_V1` remains frozen and unchanged. Its existing 12/100 sample is authoritative for that experiment.
- EPL has a proven paired-AI collection path with explicit production-model provenance.
- The other live leagues currently have operational MARKET_ONLY coverage, not equivalent validated paired-AI provenance.
- Applying the EPL production model to another league merely to increase sample size is prohibited by this readiness contract. Cross-league model validity must be established before prospective activation.
- `PROSPECTIVE_MARKET_PATH_V1` is a separate market-trajectory contract and must not be reinterpreted as the paired AI-vs-market primary experiment.

## Next research unblocker

The safe way to accelerate AI-vs-market evidence is not to backfill the 190 operational events. It is to establish league-specific AI readiness on completed historical/OOS data and freeze a separate future-only multi-league paired experiment once one or more non-EPL leagues have defensible model/probability provenance.

The preferred first candidates are leagues with already-mature canonical history and live operational plumbing; league admission must follow evidence, not a desired event count.

## Safety

This readiness block:

- performs no provider request;
- spends no provider credits;
- writes no Supabase data;
- reads no prospective outcomes/settlements;
- changes no production model artifact;
- does not activate a new prospective cohort;
- does not alter `EPL_AI_MARKET_PAIR_V1`.
