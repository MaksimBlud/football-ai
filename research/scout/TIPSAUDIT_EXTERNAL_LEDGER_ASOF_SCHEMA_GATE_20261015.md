# Signal Scout — TipsAudit immutable-ledger as-of feasibility audit (2026-10-15)

Status: **WAITING / BLOCKED_BY_MARKET_1X2_ASOF_SCHEMA**. Research-only, source audit, **not** a new hypothesis or Research Brain candidate.

## Repository safety and dedup
- Fresh main: `328bc3966c657976908acdce94809a11fdd18a24` (read-only compare).
- Read `research/programs/registry.json` (13 PROGRAM_DONE, 1 BLOCKED), `PROJECT_CONTINUITY.md`, and existing [AGENT-RESEARCH] issues. No reopened PROGRAM_DONE.
- Scout Issue search `in:title "[SIGNAL-SCOUT]"` returned 0. No Issue created.
- Prior Scout directions include TipsAudit market-as-of source audits, so this is **follow-up source feasibility only**, not a newly discovered signal.

## Evidence newly verified, outcome-free
1. External repository: https://github.com/tipsaudit/track-record-public
2. Public manifest: https://github.com/tipsaudit/track-record-public/blob/main/manifest.csv
   - 120 manifest data rows, including 119 timestamp-suffixed snapshot entries from 2026-06-20T06-16-15Z to 2026-10-15T04-40-01Z (118 distinct UTC dates).
   - Manifest row for 2026-10-15T04-40-01Z: 6,560 ledger entries (NOT 6,560 independently verified pre-kickoff bookmaker 1X2 vectors).
3. README: https://github.com/tipsaudit/track-record-public/blob/main/README.md
   - Snapshot files are daily, with SHA256 manifest and OpenTimestamps proofs; newer OTS attestations may still be pending. Pre-kickoff existence requires an **external snapshot before kickoff**, not merely `logged_at_utc < kickoff`.
   - Earlier pre-2026-07-28 `logged_at_utc` used server UTC+3 and requires -3h correction; `logged_before_kickoff` accounts for it.
   - The snapshot record is described as *one prediction pick and its probability/price*, not a full three-way market vector.
4. Exact file/schema sampled without outcome evaluation:
   - https://github.com/tipsaudit/track-record-public/blob/main/data/track-2026-06-20T06-16-15Z.json
   - https://github.com/tipsaudit/track-record-public/blob/main/data/track-2026-07-05T04-40-01Z.json
   - Fields observed: `prediction_pick`, `prediction_probability`, `prediction_odds_taken`, `kickoff_utc`, `logged_at_utc`; **no per-selection home/draw/away bookmaker price triplet in these sampled snapshot schemas**.
   - October 15 large snapshot could not be read via available line-limited GitHub fetch; its schema is **not independently verified**.
5. Dataset caveats: https://github.com/tipsaudit/track-record-public/blob/main/datasets/README.md
   - Monthly consolidated CSV *does* include `fair_prob_home/draw/away` and `pin_open_home/draw/away`, but `pin_open` may be filled **after the match** with the first price quoted before kickoff. Consolidated CSV alone does **not** establish three prices existed in a pre-kickoff externally anchored snapshot.
   - Before 2026-07-18 fair probabilities used proportional de-vig; after, power de-vig; cannot silently pool the transforms.
   - `record_hash` does not seal closing prices, soft prices or results.
6. License: https://tipsaudit.com/data and https://tipsaudit.com/api explicitly say CC-BY-4.0/commercial use with attribution. License is not the blocker.

## Gate and next steps
- **No Research Brain candidate**: no independent new mechanism and no verified full 1X2 timestamp-safe bookmaker vector from external snapshots. Do not substitute a single pick probability or a later-backfilled consolidated triplet for a full fair-probability baseline.
- Feasibility-only next action: inspect the first pre-kickoff snapshot containing each fixture and verify it has *all three bookmaker prices* (or raw, timestamped source quote) and matching bookmaker ID; verify proof timestamp < kickoff, 5-league coverage, identity mapping, corrections, and exact as-of horizon. If absent, stop this source.
- If source gate eventually passes, Research Brain alone freezes OOT/Brier/LogLoss evaluation; Scout performs no outcome tests.
- No The Odds API calls, no Supabase writes, no protected 2026/27 outcome access, no production operations.

## Measured cycle result
New independent hypotheses: **0**; DATA_FEASIBLE: **0**; candidate Issues: **0**; Research Brain transfers: **0**. No duration comparison asserted without reliable per-run timestamps.
