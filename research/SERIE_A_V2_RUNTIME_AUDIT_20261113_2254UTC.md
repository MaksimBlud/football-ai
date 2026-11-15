# Original MARKET_ANCHOR_1X2_V2 runtime audit — 2026-11-13 22:54 UTC

## Scope and safety

This audit covers only the original frozen `MARKET_ANCHOR_1X2_V2` candidate, its pre-match source/quote pipeline, open V2 PRs, GitHub Actions evidence, and read-only Supabase pre-match metadata. It does not inspect target scores/results/outcomes. The Supabase feature-input query selected only `match_date`, `home_team`, and `away_team`; market/prediction queries selected only timestamps, event identity, league, and candidate SHA aggregates.

No paid provider request, odds API request, source download, Supabase write/DDL, model inference, refit, threshold change, production artifact change, schedule change, merge, or target-outcome read was performed.

## Fresh main and frozen candidate

- Repository: `MaksimBlud/football-ai` (public).
- Fresh `main`: `40887ebb215730190d7a6c7a1693373ec4afcdfc`.
- Main `PROJECT_CONTINUITY.md` blob: `2ce2b5f8a60333f3cc4a0cfdc9c27e7fbdb9741b`; latest dated main entry remains 2026-10-18.
- Frozen candidate file blob: `ac1303f6b096664983fbf52443bd0a381b23ba21`.
- Candidate SHA-256: `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`.
- Original feature builder blob: `401b3a0893371bfa4a488ec92a4a54af2678c8f7`.
- 19 ordered football features; 20×2 weight matrix; 3,799 training rows.
- Training fingerprint: `f27ab985ae90bb8e94ba8d548847695888c232f43b3e9be93074f39e1a7a5098`.
- Training cutoff: `2026-06-30T23:59:59+00:00`.
- `active_lambda=0` (exact market fallback); `shadow_lambda=1` (research only).
- Stability gate remains FAILED; NO_BET; automatic promotion disabled.
- Protocol blob: `65729e9639720e67624c1481190aa22ae606f151`.
- Current-form policy blob: `394a426c7ced81e27e12de61087a349bb972b612`.
- The separate first target-outcome read gate remains 30 eligible completed primary prospective events. Current evaluation evidence remains 0/30.

## Current main workflow state

The five live source/quote workflow files remain on main without the hold added by PR #781:

- `.github/workflows/serie-a-v2-current-form-source-capture.yml`
- `.github/workflows/serie-a-v2-current-form-forward-preview.yml`
- `.github/workflows/serie-a-v2-forward-preview.yml`
- `.github/workflows/serie-a-v2-free-real-quote-diagnostic.yml`
- `.github/workflows/recover-market-anchor-v2-candidate.yml`

Main still permits the live steps and artifact uploads. The repository is public, so GitHub Actions artifacts uploaded before a hold are not private. Their contents were not downloaded in this audit.

## Exact main-branch runtime evidence

### Current-form source capture

[Run 43433793441](https://github.com/MaksimBlud/football-ai/actions/runs/43433793441), main SHA above, 2026-11-13 13:27:26–13:28:24 UTC:

- 19 tests passed.
- Metadata-only feature-input gate: 110 canonical completed Serie A 2026/27 fixture identities.
- 10 old-season CSVs plus one current-season CSV; 3,910 historical match rows.
- Source artifact ID `14041720658`, ZIP SHA-256 `fd0f01fde281e37711a748aed01fe630c760d9d2879e06470893955e8e5e2932`.
- No paid calls, no Supabase writes, no target outcomes scored.

### Current-form forward-only preview

[Run 43462612434](https://github.com/MaksimBlud/football-ai/actions/runs/43462612434), 2026-11-13 16:25:40–16:26:23 UTC:

- 53 tests passed.
- Independently verified source artifact `14041720658` and SHA above.
- Authenticated source parent run `43433793441`, exact main SHA, workflow path `.github/workflows/serie-a-v2-current-form-source-capture.yml`.
- Parent completed at `2026-11-13T13:28:24Z`; source archive created at `13:28:21Z`; source observation recorded at `13:28:20.165321Z`.
- Source was 10,673 seconds old at verification (within the fixed 24-hour freshness rule).
- `status=VERIFIED`, `feature_input_gate_count=110`, 11 source files, 3,910 historical rows.
- `quotes_seen=0`, `v2_current_form_shadow_captured=0`, target outcomes not read/scored, paid calls 0, production/Supabase writes 0.
- Forward artifact ID `14056932388`, ZIP SHA-256 `4bf6643c52a8d1ecbeccc95825c3cbb921fc614509df71c90ea2fca4e7799fa5`.

This proves the real source archive, parent workflow, SHA, and freshness checks passed. It does **not** prove a source-before-quote pair: there was no quote to admit and no prediction was created.

### Original old-season forward-only preview

[Run 43459529173](https://github.com/MaksimBlud/football-ai/actions/runs/43459529173), 2026-11-13 16:07:37–16:08:18 UTC:

- 71 tests passed.
- Real historical source attestation verified 10 pre-prospective files and 3,800 historical results.
- `quotes_seen=0`, `forecasts_created=0`, `v2_diagnostic_previews_captured=0`.
- Paid calls 0, Supabase writes 0.
- Artifact ID `14055691475`, ZIP SHA-256 `911ccebd74897c1e9b4932365031a574eb5027726ee6508f3b0a38c068e055eb`.

The latest V2 main-branch runs visible at audit time are the source capture above, the free diagnostic run `43443186259`, the original forward run `43459529173`, and the current-form forward run `43462612434`. No newer V2 run was present in the latest Actions listing.

## Read-only Supabase pre-match aggregates

Project queried read-only. No result/score/outcome fields were selected.

### Saved strict pre-match odds

Query condition: `snapshot_time_utc < commence_time_utc`.

- Across all listed leagues: 3,915 strict pre-match rows, 327 unique events.
- Serie A: 620 strict pre-match rows, 63 unique events.
- Latest Serie A snapshot: `2026-10-13 14:48:53.042620+00`.
- Serie A rows in the last seven days: 0.
- Future-kickoff Serie A quote rows/events: 0.

### Feature-input identity gate

Query table: `public.league_finished_results`; selected only `match_date`, `home_team`, `away_team`, filtered to Serie A 2026/27 and dates before the current UTC date.

- Raw rows: 113.
- Canonical unique fixture identities after V2-local `Atalanta BC → Atalanta` normalization: 110.
- Date range: 2026-08-22 through 2026-11-08.

This opens only the lagged feature-input gate. It does not open the target-outcome evaluation gate.

### Existing product prediction snapshots

Strict pre-match condition: `generated_at_utc < commence_time_utc`.

- EPL: 40 rows / 40 unique events.
- Serie A: 0 rows.
- Exact original candidate SHA `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`: 0 rows / 0 events.
- Latest generation among the existing EPL rows: `2026-10-09 15:29:33.136613+00`.

There is no eligible original-V2 prospective prediction cohort in these records.

## Rights and private-storage blockers

The open rights stack remains unmerged. On the #787 branch, `research/source_rights/football_data_co_uk.json` (blob `b138d29f98e4cf3071d4c6a35a01dbb4e80e5afd`) records:

- `research_source_capture_permitted=false`;
- `research_inference_permitted=false`;
- `ai_model_training_permitted=false`;
- `provider_issued_ai_inference_license=false`;
- authorization is null.

This is the project's conservative internal rights gate pending provider clarification, not a legal conclusion about every form of manual personal research.

A second independent blocker is storage privacy. The GitHub repository metadata confirms `MaksimBlud/football-ai` is public. The #787 branch's `market_anchor_v2_artifact_privacy.py` checks the `GITHUB_REPOSITORY` target and requires that repository itself to be private. `market_anchor_v2_direct_access.py` calls that check without a separate archive-repository argument. No separate private archive destination/uploader is implemented in that branch. Therefore the privacy gate will fail closed for the current public repository; private storage must be designed and authorized separately. Do not change repository visibility or create another storage service automatically.

## Open V2 PRs and exact CI

- [#781 — Live Access Hold](https://github.com/MaksimBlud/football-ai/pull/781): OPEN, non-draft, mergeable; exact HEAD `27da7c204d402b76f1f0a52fc1a3bef845fcc5d2`; 8/8 PR workflow runs SUCCESS. It gates all five live source/quote/recovery steps and their artifact uploads while retaining offline tests and existing cron strings. HUMAN-MERGE only; not merged.
- [#720 — Source Rights](https://github.com/MaksimBlud/football-ai/pull/720): OPEN; HEAD `1b9464834dd5256b7d69499c1443378518dde256`. Compare with #781 is DIVERGED: 118 commits ahead, 43 behind. Rebase onto the post-#781 main before integration.
- [#727 — Private Storage / Quote Preflight](https://github.com/MaksimBlud/football-ai/pull/727): OPEN, based on #720; HEAD `057cacbcd031c4b878dd87c7f45258e2c23d5151`.
- [#780 — Updated Football-Data policy hold](https://github.com/MaksimBlud/football-ai/pull/780): Draft, stacked on #727; source rights remain HOLD.
- [#787 — Direct EntryPoint Rights](https://github.com/MaksimBlud/football-ai/pull/787): Draft, HEAD `272a0dc2d6a97fedc7964e8cc2614ba670220fae`; adds direct-call rights and private-storage gates.
- [#793 — Market-only evaluator](https://github.com/MaksimBlud/football-ai/pull/793): Draft, HEAD `a7eeb519d967a05bc528c878b0a8fc458cfbe016`; synthetic/offline evaluator only, no real predictions or quality claim.
- [#796 — Atomic source archive](https://github.com/MaksimBlud/football-ai/pull/796): OPEN, HEAD `e69ad9c2700b999ef186e4771a2fe06fd010155d`; must be revalidated after #781 and only considered after rights/privacy clearance.
- [#806 — SportsAPI Pro audit](https://github.com/MaksimBlud/football-ai/pull/806): Draft; exact HEAD `0f2ce92f654cf5eee914b02111142366bcc3a3c3`; 7/7 exact-head CI SUCCESS; source remains HOLD.
- [#807 — API-Football Free audit](https://github.com/MaksimBlud/football-ai/pull/807): Draft; exact HEAD `03120311ceb38da4d404430f64ef386c20a96cdf`; 7/7 exact-head CI SUCCESS; Free season window does not cover 2026/27.
- Existing #791 Soccer Data and #794 Big Balls audits remain conditional candidates, not approved integrations. Other source audits (#798, #802, #803, #804) are also research-only; no provider account/key/API request was made.

## Required next sequence

1. Owner manually merges #781 at the exact verified head; no autonomous merge.
2. Re-read fresh main and all five V2 workflows. Confirm live steps and artifact uploads are skipped before any other action.
3. Rebase #720 onto that fresh main, then revalidate #727 and the downstream rights/direct-access stack in ancestry order.
4. Resolve provider rights in writing. Current branch manifest explicitly blocks automated source capture, inference, and training.
5. Design and authorize a genuinely private source archive. The current public repository cannot satisfy the #787 private-repository check.
6. Only after both rights and privacy are cleared, capture a genuinely new source archive and wait for a new strictly pre-kickoff quote. Require exact source SHA, authenticated parent run, parent completion before quote, quote before kickoff, and unchanged 24-hour freshness rules.
7. Keep the original 19-feature candidate, weights, scaler/imputer, training fingerprint, `active_lambda=0`, `shadow_lambda=1`, NO_BET, and 30-event outcome-read gate unchanged.
8. Do not read target outcomes or report Brier/LogLoss until 30 eligible unique completed primary prospective forecasts exist. Then compare the frozen shadow with the de-vigged market under the preregistered evaluator; no threshold tuning or promotion.

