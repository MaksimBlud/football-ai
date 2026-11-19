# Original frozen Serie A V2 — current-form forward-only contract (2026-10-18)

## Why a separate cohort is necessary

The restored original candidate is still the exact frozen artifact `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`: 19 features, active lambda 0, research-only, NO_BET, residual lambda 1 shadow-only, and its original stability gate has **not passed**. No weights, feature order, scaler, medians, or original protocol are changed.

The 20 saved October 13 bookmaker quotes were captured before the first verified source archive. The original old-season-only cohort remains immutable: these quotes are not backfilled and never become prospective evidence.

The old-season feature audit also showed that previous-season-only data is too stale for current form in October 2026. A new, versioned cohort is therefore preregistered in `experiments/market_anchor_1x2_v2_current_form_policy.json`. This addendum changes neither the original frozen model nor the original cohort.

## Two different gates — do not confuse them

1. **Feature-input gate:** before the current-season CSV is downloaded, read only `match_date, home_team, away_team` metadata from `public.league_finished_results` for Serie A 2026/27. Canonicalize aliases and count unique fixtures. At least 30 completed primary-league fixtures must exist. This query never selects goals, result, score, settlement, or prediction correctness. The read-only metadata audit on 2026-10-18 found 63 unique completed 2026/27 fixtures, so this input gate is currently open.
2. **Target-outcome evaluation gate:** unchanged scientific restriction. Do not read target outcome values for evaluation until **30 eligible, genuinely prospective V2 forecasts** from this new cohort have completed. The 63 ordinary league results do **not** count as prospective forecasts. The gate remains closed now because the old quotes were ineligible and the new cohort has not yet accrued completed forecasts.

The new source archive uses current-season match results **only as lagged input features for future fixtures**. It does not use target results to score, fit, select, tune thresholds, or promote a model. The model candidate's training fingerprint and original weights remain unchanged.

## Source and time-order rules

- The GitHub Actions source-capture workflow on current `main` is still scheduled daily (`50 5 * * *`) and its live step is not yet held there. This is an unresolved provider-rights risk, not authorization: the current official Football-Data page says files are updated at least twice weekly (Sunday/Wednesday); that is a publisher update cadence, not a maximum download limit. The same page limits its free CSV/Excel offering to private individuals for personal betting/academic research and excludes commercial/data-training products using automated bots/scrapers/AI. No affirmative permission for this automated AI-model pipeline is documented. PR #781 proposes a fail-closed live-access hold without changing the schedule; it is not merged. Do not dispatch or rely on live source capture until provider rights are clarified and the hold/private-artifact chain is integrated.
- The current-season CSV is requested only after the feature-input gate passes. Unplayed rows and incomplete matches are excluded. Since Football-Data match dates do not reliably contain kickoff clocks, all matches on the quote's UTC calendar day are excluded from the feature history.
- A future quote may use this archive only if the archive artifact **and its successful main-branch parent run** completed before the saved quote, all source hashes match, and source observation is no more than 24 hours before the quote.
- Quotes must themselves be no more than 24 hours old and strictly pre-kickoff. If a source is later than a quote, the quote is blocked. No backfill.
- Current-form feature generation reuses the exact frozen 19-feature builder, runtime-pinned to Git blob `401b3a0893371bfa4a488ec92a4a54af2678c8f7`, and the V2-only `Atalanta BC -> Atalanta` history alias. Same-day and future fixtures are not used as features.
- The forward workflow reads existing `odds_snapshots` only. It makes no paid provider calls and writes nothing to Supabase. The manual paid quote workflow remains dispatch-only and is not triggered by this new workflow.

## What the output means

When a valid new quote exists after a valid source archive, the workflow stores the original candidate's de-vigged market fallback and lambda-1 residual shadow probabilities, exact source provenance, feature missingness, and history ages before kickoff. It does **not** place bets, publish a product forecast, activate lambda 1, or claim superiority over market. The active lambda 0 output remains exactly the de-vigged market.

A preview is not yet a completed evaluation. Only after 30 eligible prospective forecasts have completed may a separate outcome reader compute Brier and LogLoss for diagnostic review, and then only under the original frozen contract: the residual must beat both the de-vigged market and the frozen production incumbent on **both** metrics; that signal still cannot promote or mutate the candidate.

## First post-merge proof to check

The first source run should show the feature-input gate count, 10 old CSVs plus the current-season CSV, matching SHA256s, and zero database writes/paid requests. The first forward run should correctly block the October 13 quotes as source-after-quote and stale, without backfilling them. A valid future quote captured after the source run is the first possible new-cohort observation.


## 2026-11-19 — provider-rights and public-artifact hold

The source archive's project receipt timestamp and SHA can prove that the project possessed exact bytes before a later quote; they do **not** prove when Football-Data or an upstream provider first observed or corrected each field. The provider documentation reviewed in [PR #868](https://github.com/MaksimBlud/football-ai/pull/868) says the files are updated at least twice weekly; this is an update cadence, not a download cap. It does not supply per-match first-observation/correction timestamps, and its free-use wording does not grant the intended automated AI data-training/inference pipeline. The daily 11-file capture described above therefore remains **HOLD** pending explicit rights/permission. This note does not change the workflow schedule, candidate, feature order, weights, lambda values, or evaluation gates.

As of main `40887ebb215730190d7a6c7a1693373ec4afcdfc`, the repository is public and the live source-capture step remains executable. Main run [#44326186511](https://github.com/MaksimBlud/football-ai/actions/runs/44326186511) on 2026-11-18 actually uploaded artifact `14438015203` (SHA-256 `0d4240f31418e206b36faf9e94d0782212a91cf6d51262c77b0349ab3f7fc852`) containing ten historical CSVs plus current-season CSV bytes. It recorded 110 lagged current-season rows, zero paid provider calls, zero Supabase writes, and no target-outcome scoring. The artifact is in a public repository; do not treat its availability as provider clearance.

[PR #781](https://github.com/MaksimBlud/football-ai/pull/781) proposes `MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED=false` by default, gates all live source/quote steps and artifact uploads, and preserves existing schedules. It remains open at exact HEAD `3a70a8648895076efec2a80dc10b1798ed0d9261` with 8/8 CI success. [PR #879](https://github.com/MaksimBlud/football-ai/pull/879) adds a read-only private-repository check before any live artifact access; it remains a Draft child of #781 at `b78010585c80b05ae5fc2a8b3572df14b32d9651`, with 4/4 CI jobs successful. Neither PR is merged. Until the hold is integrated and provider rights are explicitly cleared, no further live source capture or manual dispatch is authorized by this contract.
