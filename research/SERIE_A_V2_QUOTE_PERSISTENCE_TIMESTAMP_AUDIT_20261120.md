# Original MARKET_ANCHOR_1X2_V2 — quote persistence timestamp audit

**Audit time:** 2026-11-20 03:54 UTC  
**Scope:** pre-match timestamp provenance only. No scores, results, settlement fields, or protected target outcomes were queried.

## Finding

The live `public.odds_snapshots.created_at` column is `timestamptz NOT NULL DEFAULT now()`. Row-level security is enabled. The only observed policy is an anonymous SELECT policy for upcoming odds; no anonymous or authenticated INSERT/UPDATE policy was present. There are no triggers on `public.odds_snapshots`.

The read-only privilege audit reports INSERT/UPDATE column privileges for `service_role` (and SQL column privileges for `authenticated`, although the latter has no matching RLS write policy). Therefore the column is **not database-immutable**: a service-role writer can explicitly supply or update `created_at`. The default alone is not a cryptographic or tamper-proof persistence attestation.

## Trusted repository collector path

The current Serie A collector `save_serie_a_odds_snapshot.py` imports the shared `DB_COLUMNS` from `save_odds_snapshot.py`. That list contains the market snapshot fields but deliberately excludes `created_at`. Both `build_db_rows()` and `save_supabase()` project the outgoing upsert to exactly those columns. The collector therefore leaves `created_at` to the Postgres `DEFAULT now()` on a new insert and does not overwrite it on conflict.

The new offline regression file `tests/test_serie_a_v2_quote_persistence_timestamp_contract.py` pins this narrow repository-writer invariant:
- the shared odds payload schema excludes `created_at`;
- a hostile caller-supplied `created_at` is dropped by the Serie A DB-row builder;
- the fake-client upsert receives no `created_at` field;
- the snapshot builder emits only the shared DB columns.

No real Supabase client is instantiated by these tests.

## Read-only live pre-match aggregate

The query used only `snapshot_time_utc`, `commence_time_utc`, `created_at`, and `event_id` from `public.odds_snapshots`:

| Measure | Result |
|---|---:|
| Total rows | 3,966 |
| Snapshot timestamp strictly before kickoff | 3,915 |
| Row-created timestamp strictly before kickoff | 3,915 |
| Both timestamps strictly before kickoff | 3,915 |
| Snapshot timestamp at/after kickoff | 51 |
| Row-created timestamp at/after kickoff | 51 |
| Unique events with both timestamps pre-kickoff | 327 |

No row had a pre-kickoff snapshot timestamp paired with a row-created timestamp at/after kickoff. The latest eligible snapshot was `2026-10-13T14:48:53.042620Z`; its row-created timestamp was `2026-10-13T14:48:53.157404Z`.

These counts are descriptive database evidence, not a proof that every historical row was created by the current repository collector.

## Binding limitation and safe interpretation

The V2 reader's new requirement `snapshot_time_utc < kickoff` **and** `created_at < kickoff` is a useful fail-closed filter. However, because there is no database trigger/immutable ledger and `service_role` can override the column, `created_at` alone must not be described as an immutable persistence proof.

This PR does not add DDL, policies, triggers, writes, or any new database access. A stronger database-level guarantee would require a separately authorized append-only/server-attested persistence mechanism; that is outside the current no-DDL instruction. Until then, source-before-quote evidence must continue to include the authenticated source artifact digest, exact successful parent workflow identity/completion time, quote snapshot time, and the limited trusted-collector code-path assumption.

## Frozen V2 invariants

No change to the original candidate SHA `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, 19-feature order, 20x2 weights, scaler/imputer, training fingerprint, `active_lambda=0`, `shadow_lambda=1`, NO_BET, stability gate, or 30-primary-completed-event outcome-read gate.

No paid API calls, no Supabase writes/DDL, no production `.pkl` changes, no model refit/promotion, no target-outcome reads, no schedule changes, and no HUMAN-MERGE bypass.
