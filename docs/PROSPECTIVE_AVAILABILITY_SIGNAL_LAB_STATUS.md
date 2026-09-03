# Prospective Availability Signal Lab — Status

Status: **TECHNICAL CONTOUR COMPLETE / ACTIVATION GATED / WAITING FOR PROSPECTIVE SAMPLE**

Phase 1 froze the information-time contract before any availability outcome comparison. The operational implementation now completes the provider bootstrap, immutable full-poll persistence contract, canonical fixture reconciliation, COUNT_ONLY_V1 feature semantics, prospective readiness gates, and the autonomous paired evaluation cycle for EPL, La Liga, and Serie A.

The collector remains research-only. It does not train or load a production model, does not modify market observations or prediction ledgers, and does not change any `.pkl` artifact. Scheduled collection is additionally gated by repository variable `PROSPECTIVE_AVAILABILITY_ENABLED=true`; manual workflow dispatch remains available for bootstrap verification.

Durable storage is additive: `prospective_availability_polls` stores complete provider states, including zero-item states, while `prospective_availability_observations` stores poll membership rows and state-level `first_seen_timestamp_utc`. A player disappearing from a later full poll is therefore represented without rewriting prior observations.

Prediction-time feature eligibility is frozen to the latest complete poll whose `observed_at_utc` is not later than the selected market row's `snapshot_time_utc`. The selected market row is itself frozen to the latest snapshot at or before kickoff minus six hours. COUNT_ONLY_V1 contains only injury, suspension, and total unavailable-player counts for home/away teams plus their differences. Player-importance weighting remains disabled.

The Phase 4 evaluator was frozen before prospective availability outcomes were inspected. It mirrors the closed market-incremental model family: median imputation, standard scaling, and logistic regression. It refuses to calculate any outcome score until every research league independently has at least 100 paired finished fixtures, at least four calendar months of coverage, and at least two valid expanding-window monthly evaluation blocks, with at least 60 prior training fixtures and 20 fixtures in each test block.

Database activation is **not assumed** by the code merge. The additive migration `202609030002_prospective_availability.sql` must exist in the connected Supabase project and live API-Football credentials, provider identity, `coverage.injuries`, and fixture reconciliation must pass bootstrap before scheduled collection is enabled. Repository service-role credentials are intentionally not used to emulate database DDL.

Once activation passes, the four-hour collector accumulates immutable prospective availability states automatically. The weekly research cycle tracks coverage/readiness automatically and emits no outcome scores while the frozen sample gate is unmet. When all three leagues become ready, it runs only the pre-registered paired `MARKET_MODEL` versus `MARKET_AVAILABILITY` comparison and writes research artifacts; no production promotion is automatic.

No outcome-based availability result has been inspected and no empirical conclusion is currently claimed. The implementation is complete; the remaining state is intentionally time-dependent prospective accumulation, not unfinished feature development.
