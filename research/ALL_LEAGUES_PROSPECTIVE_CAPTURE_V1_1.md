# All-Leagues Prospective MARKET_ONLY Capture V1.1

Status: FROZEN ON FIRST MERGE TO `main`
Protocol: `ALL_LEAGUES_MARKET_ONLY_V1_1`
Predecessor: `ALL_LEAGUES_MARKET_ONLY_V1`
Frozen seed manifest: `research/ALL_LEAGUES_MARKET_ONLY_V1_1_MANIFEST.json`
Scope: 8 leagues

Leagues:
- `EPL`
- `LA_LIGA`
- `SERIE_A`
- `BUNDESLIGA`
- `LIGUE_1`
- `EREDIVISIE`
- `TURKEY_SUPER_LIG`
- `PRIMEIRA_LIGA`

## Why V1.1 exists

V1 remains frozen and is not edited or reinterpreted. Its atomic T0 was deliberately conservative and excluded all 133 rows from the 2026-09-11 readiness pass because those rows already existed before V1 was merged.

Immediately after V1 activation, a read-only audit showed that this conservative rule also excluded 127 events whose matches had **not yet kicked off**. Those 127 events already had immutable, valid pre-kickoff MARKET_ONLY predictions. Excluding them would discard genuine forward evidence even though no match outcome could yet exist at the time this successor cohort was frozen.

V1.1 therefore creates a separate successor cohort rather than weakening V1 retroactively.

## Successor freeze

`ORIGINAL_T0_UTC = 2026-09-12T01:51:19Z`

`V1_1_FREEZE_UTC = 2026-09-12T02:04:34Z`

The first kickoff in the frozen V1.1 seed manifest is `2026-09-12T12:00:00Z`, strictly after `V1_1_FREEZE_UTC`.

At freeze time:
- all 127 selected prediction records already existed immutably;
- every selected prediction and source snapshot was strictly pre-kickoff;
- all selected rows were `MARKET_ONLY` with `structural_applied=false`;
- all probability vectors were valid/normalized;
- no result, score, winner, settlement or other outcome source was read to choose, filter, rank or relabel these events;
- selection depended only on already durable prediction identity, the 2026-09-11 readiness pass, and kickoff being strictly after the freeze.

## Frozen seed rule

The V1.1 seed is exactly the 127 immutable `prediction_key` values in `research/ALL_LEAGUES_MARKET_ONLY_V1_1_MANIFEST.json`.

No additional pre-freeze prediction may be added later. No seed prediction may be removed because of its eventual result. Any future correction to fixture identity must preserve the original immutable evidence and must follow the repository's existing fail-closed reschedule/revision rules.

Frozen league counts:
- `BUNDESLIGA = 17`
- `EPL = 20`
- `EREDIVISIE = 18`
- `LA_LIGA = 19`
- `LIGUE_1 = 17`
- `PRIMEIRA_LIGA = 9`
- `SERIE_A = 19`
- `TURKEY_SUPER_LIG = 8`
- total = `127`

The six 2026-09-11 matches that had already kicked off before V1.1 freeze are explicitly excluded from the V1.1 seed and remain bootstrap/league-specific evidence only. They must never be backfilled into V1.1.

## Future-capture rule

After `V1_1_FREEZE_UTC`, V1.1 may append new observations only when all original V1 evidence rules pass and the immutable durable prediction is created before kickoff.

Thus V1.1 consists of:
1. the exact frozen 127-key seed manifest; plus
2. future qualifying MARKET_ONLY captures created strictly after `V1_1_FREEZE_UTC`.

The seed rule is a one-time prospective bridge. It is not a general license to backfill older predictions into future cohorts.

## Evidence rules inherited from V1

V1.1 inherits, without weakening, all evidence-safety rules from `research/ALL_LEAGUES_PROSPECTIVE_CAPTURE_V1.md`, including:
- exact eight-league scope;
- `MARKET_ONLY` evidence only;
- `structural_applied=false`;
- `prediction_time_utc < kickoff_utc`;
- `snapshot_time_utc < kickoff_utc`;
- immutable provider/event/snapshot provenance;
- valid normalized 1X2 probabilities;
- fail-closed identity conflicts;
- no outcome/result input to capture, inclusion, retry, relabeling or tuning;
- production `.pkl` artifacts remain read-only;
- paid-provider collection remains separately authorized and budget-guarded;
- stricter league-specific frozen contracts always take precedence.

## Completeness and anti-circularity

The existing `all_leagues_capture_gate.py` contract remains authoritative for future capture batches. Expected event IDs must be frozen independently of rows later read back from `odds_snapshots`; circular completeness remains forbidden.

The frozen 127-key seed is different: its membership is fully enumerated in the immutable manifest before the first seed kickoff. Membership is no longer derived dynamically after freeze.

## No-peek / outcome embargo

No prospective outcome may be used to:
- change the 127-key seed;
- decide whether V1.1 continues;
- change league inclusion;
- change snapshot selection;
- change weighting or thresholds;
- change evaluation metrics;
- relabel a prediction after kickoff.

Outcome access remains governed by the applicable frozen evaluation gates. This V1.1 freeze does not open any result table or authorize interim performance analysis.

## Evaluation contract

V1.1 inherits the common V1 metrics when the applicable frozen sample/time gate permits evaluation:
- multiclass log loss;
- multiclass Brier score;
- 1X2 argmax accuracy.

Metrics must be reported per league and pooled. A stricter existing league-specific gate wins.

## Paid-provider / production boundary

This protocol grants no paid API permission. It performs no provider request by itself. The 127-key seed uses only already durable evidence from the authorized 2026-09-11 readiness pass.

No production model promotion is authorized. Production `.pkl` artifacts remain outside this research capture path.

## Scientific status

After this file and its manifest are merged into `main` before the first seed kickoff:

`ALL_LEAGUES_MARKET_ONLY_V1_1 = FROZEN / 127-SEED + FUTURE CAPTURE`

This successor contract preserves V1 as historical provenance while avoiding unnecessary loss of 127 events that were still fully prospective at V1.1 freeze.
