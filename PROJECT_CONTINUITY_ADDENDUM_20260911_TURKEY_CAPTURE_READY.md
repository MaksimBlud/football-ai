# Continuity Addendum — Turkey Super Lig prospective MARKET_ONLY capture V1

Date: 2026-09-11
Protocol: `TURKEY_SUPER_LIG_MARKET_ONLY_V1`

## State

Turkey Super Lig now has a separate frozen prospective MARKET_ONLY capture contract.

- league: `TURKEY_SUPER_LIG`
- target: `100`
- current committed count: `0/100`
- `CAPTURE_READY=true`
- `MODEL_READY=false`
- `PROSPECTIVE_AI_READY=false`

The zero count is intentional and scientifically clean. A read-only live Supabase audit performed before the protocol freeze found no existing `odds_snapshots` rows for `TURKEY_SUPER_LIG` or `SUPER_LIG`. No historical/current fixture was backfilled into the prospective ledger.

## Existing infrastructure reused, not activated beyond authorization

The repository already contains:

- `turkey_super_lig_runtime_config.py` with canonical identifier `TURKEY_SUPER_LIG`, Football-Data code `T1`, timezone `Europe/Istanbul` and Odds API sport key `soccer_turkey_super_league`;
- shared Turkey/Portugal MARKET_ONLY snapshot code;
- an adaptive quota-safe Turkey/Portugal scheduler;
- a Turkey/Portugal MARKET_ONLY workflow that remains manual `workflow_dispatch`.

This change does not trigger or schedule a paid The Odds API request. The first observation may be appended only when an admissible pre-kickoff source snapshot already exists under the project's separate provider-budget authorization rules.

## Frozen capture guarantees

- exact league only;
- MARKET_ONLY only;
- strict pre-kickoff capture/source timing;
- source event/snapshot provenance mandatory;
- valid finite 1X2 decimal odds;
- outcome/result/score/winner/settlement forbidden;
- AI/model/Structural fields forbidden;
- canonical immutable fixture key;
- contiguous 1..100 sequence;
- idempotent identical replay only;
- conflicting rewrite/schema corruption/duplicate/overflow fail closed;
- no Supabase/provider/model dependency in the capture tool itself.

Existing frozen Serie A/La Liga, Bundesliga and Ligue 1 ledgers are checksum-protected by regression tests.

## Scientific boundary

This collection-readiness state does not admit a Turkish AI model. Any AI-readiness attempt must be a separate preregistered historical protocol. In particular, the abnormal 2022-23 Turkish season must not be silently treated as an ordinary complete observed double-round-robin season: after the February 2023 earthquakes, Hatayspor and Gaziantep withdrew and remaining fixtures were administratively awarded. Any historical protocol must freeze how that season is handled before the first model result.

## Next safe step

After this capture contract is merged and proven on `main`, run a separate Turkey Super Lig nested historical development protocol using completed Football-Data `T1` history only, with current 2026-27 forbidden and the 2022-23 evidence anomaly handled prospectively in the preregistration.