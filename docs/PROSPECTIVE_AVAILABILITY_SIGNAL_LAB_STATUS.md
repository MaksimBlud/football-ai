# Prospective Availability Signal Lab — Status

Status: **PHASE 2 — OPERATIONAL CONTRACT READY / ACTIVATION GATED**

Phase 1 was merged after CI validation. Phase 2 now freezes the provider bootstrap, immutable full-poll persistence contract, canonical fixture reconciliation, and COUNT_ONLY_V1 feature semantics for EPL, La Liga, and Serie A.

The collector remains research-only. It does not train or load a production model, does not modify market observations or prediction ledgers, and does not change any `.pkl` artifact. Scheduled collection is additionally gated by repository variable `PROSPECTIVE_AVAILABILITY_ENABLED=true`; manual workflow dispatch remains available for an explicit bootstrap run.

Durable storage is additive: `prospective_availability_polls` stores complete provider states, including zero-item states, while `prospective_availability_observations` stores the poll membership rows and state-level `first_seen_timestamp_utc`. A player disappearing from a later full poll is therefore represented without rewriting prior observations.

Prediction-time feature eligibility is frozen to the latest complete poll whose `observed_at_utc` is not later than the paired market row's `snapshot_time_utc`. COUNT_ONLY_V1 contains only injury, suspension, and total unavailable-player counts for home/away teams plus their differences. Player-importance weighting remains disabled.

Database activation is **not assumed** by this commit. The additive migration `202609030002_prospective_availability.sql` must be applied to the connected Supabase project and live provider credentials/coverage must pass the bootstrap before scheduled collection can be enabled. Until those gates pass, the honest operational state is READY-BUT-NOT-ACTIVE.

No outcome-based availability result has been inspected. Phase 3 is prospective accumulation after activation; Phase 4 is the pre-registered paired `MARKET_MODEL` versus `MARKET_AVAILABILITY` evaluation.
