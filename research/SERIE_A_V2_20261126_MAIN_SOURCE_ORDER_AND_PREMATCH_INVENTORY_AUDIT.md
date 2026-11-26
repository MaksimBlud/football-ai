# Original MARKET_ANCHOR_1X2_V2 — main source-order and pre-match inventory audit

**Audit time:** 2026-11-26 05:51 UTC  
**Scope:** Original frozen MARKET_ANCHOR_1X2_V2 only. Read-only GitHub and Supabase inspection. No source/API request, quote write, Supabase DDL, target-outcome read, inference, refit, promotion, production change or merge.

## Fresh main and frozen candidate

- Main commit: `40887ebb215730190d7a6c7a1693373ec4afcdfc`.
- Main `PROJECT_CONTINUITY.md` blob: `2ce2b5f8a60333f3cc4a0cfdc9c27e7fbdb9741b`; its latest dated execution entry remains 2026-10-18.
- Main original forward workflow `.github/workflows/serie-a-v2-forward-preview.yml` blob: `48ce3b0d8e31c4cf293b94500e9c320047311467`.
- Main `serie_a_v2_forward_capture.py` blob: `5db02cbd1367ed25b994b152acf371421859a014`.
- Main `serie_a_v2_current_form_forward_capture.py` blob: `326ac1921ce901a31aa6d73e6cbddb0782071964`.
- Frozen candidate JSON blob: `ac1303f6b096664983fbf52443bd0a381b23ba21`; candidate SHA-256 remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`.
- Contract remains 19 ordered features, 20×2 weights, 3,799 training rows, `active_lambda=0`, `shadow_lambda=1`; stability gate FAILED, target-outcome evaluation gate CLOSED at 0/30.

## Concrete source-before-quote defects still present on main

1. In main `serie_a_v2_forward_capture.py::main()`, the current call order is:
   - `fetch_saved_upcoming_serie_a_quotes(...)`;
   - then `discover_archives(...)`;
   - then `prepare_forward_capture(...)`.

   Therefore the original forward CLI reads saved quote rows before it discovers and authenticates a source archive. The separate workflow attestation step does not change this in-process call order. The source-first implementation is already present in the #938 → #939 → #940 → #943 → #944 → #945 → #946 → #947 ancestry, with #951 adding persisted quote chronology, but that chain is not on main.

2. Main current-form forward verifies the latest source archive, but its CLI still proceeds to construct a Supabase client and read quotes even when the source verification result is `NO_SOURCE_ARCHIVE` or otherwise not admissible. PR #957 adds a lazy quote reader and fail-closed source/inference gate. It remains unmerged.

3. Main original forward workflow still uploads the source directory in an `if: always()` artifact step on this public repository. Root hold #781 and private-repository guard #879 remain necessary before any further live collection or raw archive publication.

## PR ancestry and exact-head CI — checked 2026-11-26

| PR | Exact head | Current relationship | Verified run |
|---|---|---|---|
| #781 | `5552bec363ae72ad7aef04c598d2ce861f33eb42` | Open, Ready, base main | 8/8 SUCCESS |
| #938 | `14d765ca2b55e939d9ab5790abbbecd3a29f2614` | Draft, child of #879 | source-first restack |
| #947 | `3839f256ac7c910d914d70cb0781cf58b55f82fa` | Draft, child of #946 | provenance writer / gate integration |
| #951 | `f1ad14e783b4f03e8887516f6805d4650233fead` | Draft, child of #950 | run #45390159817 SUCCESS |
| #953 | `2fa0aa46e79966075ed911052a9c6dfa9f19888f` | Draft, child of #936 | run #45421249205 SUCCESS |
| #957 | `6ec18204ffc8195074cbbbfe6aa3247b87965e2b` | Draft, child of #956 | run #45497512529 SUCCESS |
| #975 | `40db78fa5a09eccaca3d4702ed3b3ecbeeb36c26` | Draft, child of #947 | #45752343002 and #45752342926 SUCCESS |

**New ancestry warning:** #975 is based directly on #947 (`3839f256...`), not on the later #951 head (`f1ad14e...`). It therefore does not include the downstream #948 outcome-embargo, #949 immutable action pins, #950 source-first validator pins, or #951 persisted-quote chronology commits. Its exact-head CI is valid for its own branch, but #975 is not a merge-ready substitute for the complete newer chain. Restack its candidate-freeze delta onto the #951 descendant chain before considering integration; preserve the #948 preview embargo and #950 workflow changes. Do not merge #975 as-is.

PR #839 remains the current documentation/source-rights audit branch, but is open and unmerged. Its larger 95-commit / 22-file diff still needs full review. This checkpoint is added to that branch; no main ref was changed.

## Supabase — metadata-only, read-only pre-match query

Queried only `public.odds_snapshots` metadata fields: league, event ID, home/away names, `snapshot_time_utc`, `created_at`, and `commence_time_utc`. No odds prices, scores, results, settlement or target outcomes were selected.

Strict validity predicates:

`snapshot_time_utc < commence_time_utc`  
`created_at >= snapshot_time_utc`  
`created_at < commence_time_utc`

Result at `2026-11-26 05:51:01 UTC`:

- 3,966 rows total;
- 327 distinct events;
- 3,915 strictly pre-kickoff rows across 327 events;
- 0 currently future-eligible rows and 0 future-eligible events;
- latest strictly valid saved quote observation: 2026-10-13 14:48:53 UTC (Serie A).

League-level strictly pre-match rows/events: Bundesliga 394/35; EPL 1,135/70; Eredivisie 410/39; La Liga 798/52; Ligue 1 387/35; Primeira Liga 9/9; RPL 153/15; Serie A 620/63; Turkey Super Lig 9/9.

No future quote is available for a new prospective Original V2 run. The 120 current-season completed fixtures previously used for lagged feature-input history are not 120 prospective predictions and do not open the separate 30-event evaluation gate.

## Binding safety and scientific interpretation

- No approved free source has yet cleared upstream rights, private raw retention, all-19-feature coverage and point-in-time source chronology. Existing provider audits remain HOLD; local receipt time + SHA proves project possession, not the provider's first-observed/correction time.
- Do not infer V2 superiority from V1 stability evidence or from input-completeness tests.
- No Brier/LogLoss comparison is admissible until the frozen prospective gate is validly opened after 30 eligible completed primary forecasts.
- No paid The Odds API request/cron, no Supabase writes/DDL, no protected target-outcome read, no production `.pkl` modification, no weight/feature/lambda change, no bet or auto-promotion.
- HUMAN-MERGE remains binding. No PR was merged and main was not changed in this audit.
