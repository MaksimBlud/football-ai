# Original V2 public-source download budget

Audit timestamp: 2026-11-03 01:56 UTC  
Base main: `40887ebb215730190d7a6c7a1693373ec4afcdfc`

## Provider policy and unresolved rights

The official Football-Data.co.uk fair-use page says its free CSV/Excel data is intended for private individuals' personal betting and/or academic research, with manual downloads or at most light automated downloading (twice per week maximum). It also says users seeking commercial, AI-usage, or model-training use should assume no permission is granted.

Official references:
- https://www.football-data.co.uk/contact.php
- https://www.football-data.co.uk/italym.php

This is a source-use restriction, not merely a rate limit. The 170-hour workflow budget below is not a licence and does not grant AI-training, commercial, redistribution, or product-use rights. The separate V2 source-rights manifest currently records `NOT_GRANTED` for Football-Data AI model training. Do not interpret a valid ZIP/CSV SHA as permission to use the data.

## Existing main workflow activity

The existing schedules are unchanged:
- Current-Form Source Capture: `50 5 * * *` (05:50 UTC daily).
- Free Real-Quote Diagnostic: `13 6 * * *` (06:13 UTC daily).

The latest successful main runs observed in this audit were:

| Workflow | Run | Artifact | Artifact created (UTC) | Source requests |
|---|---:|---:|---|---:|
| Current-Form Source Capture | 41456825300 | 13147815874 | 2026-11-02 13:53:57 | 11 CSVs |
| Free Real-Quote Diagnostic | 41473879081 | 13155539394 | 2026-11-02 15:41:21 | 10 CSVs |

The Source Capture artifact reports 3,800 historical rows, 98 current-season rows, and a feature-input gate count of 90 at capture time. The subsequent Current-Form Forward run 41456979071 saw zero saved quotes and captured zero V2 shadow forecasts. The Free Diagnostic run recorded zero scored diagnostics and zero saved quotes. No paid provider request or Supabase write occurred in these runs.

Main does not contain this PR's guard yet. At the audit timestamp, the next unchanged scheduled attempts are 2026-11-03 05:50 and 06:13 UTC. If this PR is not manually merged before those times, the current main workflows remain unguarded and may make another source session. This PR does not disable or alter either schedule.

## Implemented guard at exact PR HEAD

Exact PR HEAD: `e368326ad52f728f1c3975989aa7a60de2be50c3`  
Exact-head CI: 8/8 SUCCESS; dedicated budget tests: 20 passed; frozen V2 shadow tests: 86 passed.

The implementation uses `MIN_DOWNLOAD_INTERVAL = 170 hours` **per approved workflow path**, not an 85-hour global cooldown:

- Current-Form Source Capture has its own 170-hour slot.
- Free Real-Quote Diagnostic has its own 170-hour slot.
- The two workflows share one GitHub Actions concurrency group and one marker artifact name, so reservations are serialized.
- Each path can reserve at most one attempt in any 170-hour interval; with exactly two allowlisted paths, the guard permits at most two workflow sessions in any rolling 168-hour week.
- The marker is uploaded before any public CSV request. If metadata validation, budget reservation, or marker upload fails, the public download step is skipped.
- Push events run offline validation only; they do not consume a source slot or request CSV bytes.
- The guard reads only GitHub Actions artifact/run metadata. It makes no Football-Data, Supabase, odds-provider, or outcome request.
- Malformed metadata, redirects, API failures, wrong workflow parents, or invalid timestamps fail closed.
- A reserved attempt remains counted even if the later download fails; there is no automatic retry.

### First-rollout bootstrap

If no new marker exists, the guard bootstraps each workflow's slot from its own latest legacy source artifact. It verifies the artifact's parent run path, main branch, head SHA, allowed event, and timestamps before using the artifact creation time.

The two existing artifacts therefore bootstrap independent cooldowns:

| Workflow | Last legacy artifact | Next permitted attempt (UTC) |
|---|---:|---|
| Current-Form Source Capture | 13147815874 | 2026-11-09 15:53:57 |
| Free Real-Quote Diagnostic | 13155539394 | 2026-11-09 17:41:21 |

Assuming no later attempt, the unchanged daily schedules next align after both cooldowns on 2026-11-10 at 05:50 and 06:13 UTC. These dates apply only after the guard is manually merged; main remains unguarded until then.

## Important limitations

- The 170-hour cap limits **workflow sessions**, not individual HTTP requests inside a session. Source Capture currently requests ten frozen historical CSVs plus the current-season CSV; Free Diagnostic requests ten historical CSVs. The provider page does not define whether “twice per week” is counted per workflow session or per individual CSV file. This PR does not claim that the per-session file count is approved.
- Reusing already verified frozen historical bytes and requesting only the changing current-season file would reduce requests, but that optimization is not included here.
- The separate source-use permission issue remains unresolved. Do not initiate another Football-Data request or use its bytes for V2 training/product purposes until the permitted use basis is established.
- The original 24-hour source-age rule is unchanged. Skipping a refresh does not make an old source fresh; current-form forecasts must report stale-source/no-forecast when the source is older than 24 hours.
- The latest source archive's feature-input gate count (90) is stale relative to the current metadata-only gate (98 canonical identities); count parity and exact identity/SHA attestation must be re-established before any feature preview is admitted.

## Frozen V2 and safety invariants

No model code, 19-feature order, coefficients, weights, candidate SHA, `active_lambda=0`, `shadow_lambda=1`, source/quote age rule, or evaluation gate is changed. No paid API call, Supabase write/DDL, production `.pkl` change, target-outcome read, promotion, or betting action is introduced.

HUMAN-MERGE only. No main update or merge is performed by this PR.
