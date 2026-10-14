# V2-only repair: Atalanta BC versus historical Atalanta

**Observed 2026-10-14 in real GitHub free-history run [38588541087](https://github.com/MaksimBlud/football-ai/actions/runs/38588541087); no paid bookmaker requests, no protected season outcomes.**

The first original V2 feature-sufficiency audit (merged [PR #665](https://github.com/MaksimBlud/football-ai/pull/665), main `3afc76d2ca056a31623b3c5ff9a22389dc3518e4`) read exactly 10 public pre-2026/27 CSVs / 3800 historical games and 20 **existing** Serie A bookmaker fixtures. It reported **18/20** full 19/19 original feature vectors and **2/20** missing all 19; no scored diagnostics because the Oct13 quote was >24h old, correct stale quote behavior.

The full SHA-archived real report (GitHub artifact ID **11906114191**) identified:
- **Atalanta BC — Frosinone**: no matching prior `Atalanta BC` history; Frosinone has 30 old prior matches, last May 2024.
- **AC Milan — Atalanta BC**: AC Milan has 30 prior matches through May 2026; no `Atalanta BC` history.
- Verified contents of all 10 pre-2026/27 original Football-Data CSVs use **`Atalanta`**, not `Atalanta BC`; the stored bookmaker prices use `Atalanta BC`. Therefore the missingness was caused by **identity mismatch**, NOT by unavailable club history. The original V2 candidate was silently imputing 19/19 features with training medians for these two fixtures before PR #665 blocked them.

## Fix without changing model

Local *V2-only* football-history identity adapter `V2_HISTORICAL_TEAM_ALIASES={"Atalanta BC":"Atalanta"}` resolves bookmaker label to historical club ID before building original 19 differences, while preserving the **exact original bookmaker home/away string and kickoff/event ID** for quote joining. Training weights, feature definitions/order, medians, lambda and fixed original candidate SHA unchanged. Do not modify global league runtime aliases, old models, production .pkl or other markets.

Regression uses synthetic **pre-2026/27** finished fixtures to verify both **Atalanta BC (home)** and **Atalanta BC (away)** match valid `Atalanta` historical stats, all 19 original inputs observed when both teams have venue history, original market lambda=0 unchanged, `NO_BET`, and aliased duplicate historical matches fail closed. CI coverage added to frozen V2 shadow, free public-history diagnostic and forward-only quote preview workflows.

## Remaining quality limitation — old data can masquerade as rich data

At the real historical archive's Oct 13 2026 quote timestamp, clubs absent in Serie A during 2025/26 may still appear with **30 old fixtures** and **19/19 numeric features** derived from 2023/24 or 2024/25. For example Frosinone's latest recorded match in the permitted historical files is May 2024, and Venezia May 2025; both are many months or years out of date, though numeric features appear complete. `history_coverage.days_since_last_historical_match` now exposes the precise age from quote time, without applying an arbitrary tuned freshness threshold or pretending to have protected 2026/27 results. The original protected outcome embargo remains absolute.

## Expected live proof after merge

Full exact-head CI, fresh-main exact-head merge, then auto-triggered free real-diagnostic workflow. Expected former 2/20 entirely-missing fixtures become **20/20 with all 19 historically computable** (not current 2026/27 form). Re-check actual result; do not claim it before observing. The original 20 saved market quotes are still **not eligible for prospective V2 evaluation** (their first source ZIP came after the quote and the quote itself is stale). No performance improvement or ROI is claimed; the original stability gate remains failed. No The Odds API calls without new express consent.
