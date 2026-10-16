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


## Independent follow-up: 2026-10-16 UTC (scheduled Scout cycle)

**Status: WAITING / BLOCKED_BY_MARKET_1X2_ASOF_SCHEMA.** No new candidate, no outcome test, no Research Brain handoff. This is source-feasibility evidence for an already-known source, **not a new signal**.

### Source-of-truth and dedup
- Fresh main `328bc3966c657976908acdce94809a11fdd18a24` checked via GitHub commit search; `research/programs/registry.json` read: **13 PROGRAM_DONE / 1 BLOCKED**; `PROJECT_CONTINUITY.md` and current open issues/scout branch names checked.
- Existing Scout source audit is already in this branch, 1 commit ahead / 0 behind main before this update. No new Issue: source is not a new independent mechanism.
- Do not reopen the closed market microstructure/de-vig/margin/lead-lag programs (#481/#482/#532/#533/#535/#548/#553 and others). Their OOT cannot be recycled.

### Newly verified direct historical snapshots — outcome-free field/schema audit
Official immutable ledger repository: https://github.com/tipsaudit/track-record-public

| Immutable snapshot | Manifest row count | Parsed prediction objects | Rows with full `pin_open_home/draw/away` | Rows with full `fair_prob_home/draw/away` |
|---|---:|---:|---:|---:|
| [2026-07-17T04-40-01Z](https://github.com/tipsaudit/track-record-public/blob/main/data/track-2026-07-17T04-40-01Z.json) | 481 | 481 | **0** | **0** |
| [2026-07-18T04-40-01Z](https://github.com/tipsaudit/track-record-public/blob/main/data/track-2026-07-18T04-40-01Z.json) | 498 | 498 | **0** | **0** |
| **Two sampled daily exports (not deduplicated)** | **979** | **979** | **0** | **0** |

- GitHub blobs: July 17 `9fa19db828f4e851b09ad9e424ea7c0c39cdaeaf`; July 18 `0125dfcbeb589a00bcb32cd3d1d322c2344744a0`.
- Both parsed JSONs contain `source, note, generated_at, count, predictions`; per-row keys include `prediction_pick`, `prediction_probability`, `prediction_odds_taken`, `logged_at_utc`, `kickoff_utc`, `hash` — **not** a 1X2 price triplet.
- This is schema/field presence inspection only; no match outcomes, wins, CLV or profitability inspected or evaluated. Counts refer to snapshots of the same rolling ledger and **must not** be interpreted as 979 unique matches.
- [Official datasets caveats](https://github.com/tipsaudit/track-record-public/blob/main/datasets/README.md) expressly state consolidated `pin_open_*` can be filled **after a match** with the first quote after logging and before kickoff. Therefore neither `logged_at_utc < kickoff` nor later consolidated triplets prove the **whole price vector existed at the pre-kickoff decision time**.
- [Official ledger README](https://github.com/tipsaudit/track-record-public/blob/main/README.md) states some same-day predictions or quotes added after logging first appear in the public ledger **after kickoff**. OpenTimestamps proves the export existed by a time, not that its later-filled quote existed before kickoff.
- Two snapshots alone do not prove the schema of all 119 snapshots; do not claim a universal impossibility. But the provider's documented export contract and verified 0/979 full vectors make this **ineligible for historical as-of 1X2 bookmaker baseline without new direct price evidence**.

### Research Brain admission / stop contract
- Gate remains **BLOCKED_BY_SOURCE**. Do not use single-pick `prediction_probability` as bookmaker fair-probabilities baseline; it is not three contemporaneous market prices. Do not use after-the-fact `pin_open_*` from consolidated CSV.
- Only reconsider on externally attested **pre-kickoff** snapshots containing *all three* raw prices, same bookmaker, source time, match identity and exact lead-time, with sufficient five-league coverage, rights and independent OOT cohorts. Freeze full rules before any outcomes.
- If feasible, Research Brain alone owns pre-registration and paired Brier/LogLoss vs fair bookmaker baseline, negative controls (timestamp-shift/shuffled team IDs), season/league OOT, CI and STOP/SUCCESS. Scout must not evaluate outcomes.
- No candidate Issue or handoff this cycle. No paid Odds API, Supabase writes, protected 2026/27 outcome reads, production changes or main writes.

### 24h / durability evidence
- This cycle has **0** new nonduplicate DATA_FEASIBLE hypotheses, **0** Research Brain handoffs and **0** new Issues. Prior accessible cycles also report 0 handoffs.
- Previous report commit `21db305f3c76d52069c1a0086bb24b77441e877d` persisted on this branch and was independently compared against main. This update should be considered durable only if the returned commit SHA and fresh branch read/compare confirm it.
- Exact prior wall-clock durations are unavailable; no claim that a 40-minute budget increased productivity.
