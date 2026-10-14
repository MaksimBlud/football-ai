# Signal Scout — 2026-10-14 — TipsAudit open PIT market-source gate (outcome-free)

Status: **WAITING / SOURCE_PARTIAL_PIT_CONFIRMED / NOT_DATA_FEASIBLE**.
Scope: **source/provenance feasibility only**. This is **not** a new independent football signal, not a candidate, and not a request to reopen any PROGRAM_DONE family.

## Fresh-main duplication guard
- Read `research/programs/registry.json` and `PROJECT_CONTINUITY.md` on main commit `328bc3966c657976908acdce94809a11fdd18a24`.
- Registry: 13 PROGRAM_DONE, one BLOCKED (`point_in_time_snapshot_cadence`). Existing price-formation, devig, margin, repricing, team-change and snapshot-cadence families are not reopened.
- Queried repository Issues for `TipsAudit`, `referee`, and Scout candidates; no matching candidate found. Source audit is not a research Issue.

## New externally inspectable evidence (2026-10-14)
1. Publisher: https://tipsaudit.com/data — declares CC-BY-4.0, 5,202 rows in the **2026-10-01** CSV snapshot, coverage 2026-06 through 2026-10, three 1X2 fair probabilities, `pin_open_*`, `pin_close_*`, `record_hash`. The public page was last rebuilt 2026-10-01, so **do not call 5,202 a current count**.
2. Public Git archive: https://github.com/tipsaudit/track-record-public ; README: https://github.com/tipsaudit/track-record-public/blob/main/README.md ; data schema: https://github.com/tipsaudit/track-record-public/blob/main/datasets/README.md ; manifest: https://github.com/tipsaudit/track-record-public/blob/main/manifest.csv .
3. **Metadata-only** GitHub read confirmed manifest header `snapshot_utc,sha256,predictions,ots`, **119 manifest entries** (excluding header), with `2026-10-14T04-40-01Z` row: SHA256 `bf69d16a794e5ec07b3ba78e3aa4a10d9658e8bd2dae870ba4a7dd8bf0005934`, `predictions=6430`, `ots=data/track-2026-10-14T04-40-01Z.json.ots`. This is **ledger row count, not matched eligible fixtures or pre-kickoff market coverage**. `data/` directory contains the named JSON and .ots. **Cryptographic OpenTimestamps verification was not executed**.
4. Publisher explicitly says public snapshots occur once daily at 04:40 UTC. A logged prediction is **not independently timestamped pre-kickoff** unless a public snapshot captured it after publication but before kickoff. A prediction logged on match day may first appear in the ledger after kickoff. The `record_hash` can include a Pinnacle quote obtained **after logging** and filled later, sometimes after the match. See README and https://tipsaudit.com/data .
5. Provenance corrections: https://github.com/tipsaudit/track-record-public/blob/main/CORRECTIONS.md — `logged_at_utc` before 2026-07-28 was actually UTC+3 (subtract 3h); 2026-09-30 correction reverses mistaken late-log flags. Soft-book best-price fields before 2026-09-21 are historical maxima and not guaranteed executable at logging. Value flags before 2026-09-26 were reconstructed, not live. **No outcomes, scores, ROI, CLV or reserved 2026/27 labels were read from the dataset**; only schema/README/manifest/correction text were inspected.
6. https://tipsaudit.com/methodology says fair probability may come from Pinnacle *or* an Elo/form model where sharp coverage is absent. Therefore the fair-probability vector must not be assumed to be an independent market-only baseline without a per-row source proof.

## Outcome-free baseline acceptance gate (for future Research Brain, NOT performed here)
- Freeze a match universe, league(s), cutoff T-kickoff (e.g. T-24h), data licence, and exact eligible columns **before** any outcome read.
- Enumerate all fixtures independently of this selected-prediction feed; join by canonical fixture ID + kickoff timestamp, not team-name guessing.
- For each candidate row require: published archive version strictly before cutoff; `logged_at` timezone corrected; raw three-way Pinnacle quote **observed by cutoff**; no after-log/backfilled Pinnacle fields; source tag showing market-only not fallback Elo; nonvoid and unique fixture; complete three-way prices; valid timestamps; bookmaker snapshot age; license and source attribution.
- Reconstruct fair probabilities from a single contemporaneous 1X2 quote vector with a frozen de-vig method. Do not trust mutable `fair_prob_*` blindly, and do not use closing odds, margins reconstructed after kickoff, soft historical maxima, predictions, flags or outcomes as features.
- Publish **outcome-free** per-league/per-month denominators: fixture universe, eligible rows, missing quote/source, cutoff failures, after-log price, timezone ambiguity, snapshot not pre-kickoff, collisions, licence.
- If coverage is too low, source tags unavailable, timestamps ambiguous, or complete fixture universe absent: **BLOCKED_BY_SOURCE**, no candidate Issue.
- Only Research Brain can preregister a genuinely independent feature, frozen train/validation/untouched OOT, market-anchored paired Brier and LogLoss, fixture-cluster bootstrap, placebo/shuffled timestamp controls, and STOP/SUCCESS. Never reuse previously opened OOT or claim profitability.

## This cycle
- Independent football hypotheses admitted: **0**.
- `DATA_FEASIBLE`: **0**; Research Brain handoffs: **0**; Scout candidate Issues: **0**.
- No paid The Odds API, no Supabase, no outcome dataset read, no production, no registry mutation.
- The useful new finding is a **potentially reusable CC-BY-4.0 market source with independently archived daily metadata, but NOT yet a valid pre-kickoff baseline**. Existing program outcomes and gates remain binding.
