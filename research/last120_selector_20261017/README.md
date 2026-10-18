# LAST120 offline fixture selector (research-only)

**Open [index.html](index.html) locally in a browser.** Self-contained, no backend, paid APIs, tracking, bets, model changes or Supabase writes. Embedded frozen 231-fixture schedule for 17 October–8 November 2026 covering EPL, RPL, La Liga, Serie A, Bundesliga and Ligue 1, originally sourced from [open-matchday](https://github.com/oladeeayo/open-matchday). Check real fixture dates and time zones; the RPL source has no clock times. Add subsequent fixtures using CSV import.

**What it selects:** after a manually verified **score snapshot from exactly 85:00**, tied matches in the five Opta-validated European leagues become research candidates, with 0:0 flagged as a smaller-sample subcategory. A lead of 2+ is excluded from the lower-risk group; a one-goal lead gives no signal. For the RPL a tie is clearly marked **UNVALIDATED HYPOTHESIS**. Blank or unverified 85:00 inputs cannot produce a candidate. No automated live collection is performed; one explicit manual score check is necessary.

**Strict outcome definition:** goal in the **actual final 120 seconds** relative to the second-half whistle, measured using Opta type-16 goal and type-30 end-event timestamps, not any fixed 90+ minute. The exact future final two-minute start cannot be identified at 85:00; the tied-at-85 criterion is a tested association with a future outcome, not an entry-time or betting claim.

**Validated research:** [original last-120 seconds audit](https://github.com/MaksimBlud/football-ai/blob/research/last120-whistle-20261015/research/last120_20261015/FINAL_REPORT.md) lives in another research branch `research/last120-whistle-20261015`; [selection criteria report](https://github.com/MaksimBlud/football-ai/blob/research/last120-criteria-20261016/research/last120_criteria_20261016/FINAL_REPORT.md) is in `research/last120-criteria-20261016`. They find 412/7350 exact final-two-minute positives over five seasons; for 2024/25–25/26 ties at 85:00 are 22/845 (2.60%) vs nonties 151/2389 (6.32%). The pretrained **prematch-only** models gave AUC near random (0.505/0.492), hence no credible pre-kickoff match ranking is claimed. 2026/27 RPL coverage has seconds-uncertain events; no transfer of the tied-at-85 effect is warranted.

**Import CSV columns:** `league,date,time,home,away,round,score85_home,score85_away,verified85`. Date YYYY-MM-DD; leave scores empty / verified85=false until exactly 85:00. All data is locally stored where the browser permits, with full CSV export for a durable backup.

**Checks:** no premature selections; invalid 85:00 confirmation rejected; 0:0 tie selects; RPL tie marked hypothesis; 3:0 excludes; candidate filtering; CSV export/import; reset; no JavaScript runtime errors. Static fixture count 231 (original browser smoke tests used 52). Browser-run persistence could not be verified under the sandbox's restricted origin; CSV export is supported independently.

**Safety:** no production .pkl changes; no paid Odds API; no auto-promotion or merge; no pretense that this is a no-live pregame model.

## 2026-10-17 hardening and expanded fixture release

- Schedule expanded from 52 to **231 fixtures** dated 17 October to 8 November 2026, across six leagues, pinned to public `open-matchday` source commit `e523e0903fabf60ef2d05a704ad8553cca9b5dde`. The source may change match dates/lineups after this snapshot; times may not be in the viewer's timezone and RPL kickoff times are blank. The tool does **not** automatically refresh fixture data.
- Confirmed **five validated leagues only** (EPL, La Liga, Serie A, Bundesliga, Ligue 1). The Russian league remains an explicitly marked *research hypothesis*, excluded from confirmed-candidate CSV; unknown imported leagues fail closed.
- Manual score changes **clear prior confirmation immediately**, refreshing shortlist. Re-imports of changed scores no longer keep an old verified marker. CSV import is **atomic**: invalid dates and duplicate identities abort the whole batch before saving.
- Built-in CSV export and import, zero paid API / continuous polling / bookmaker integrations. Only the result at **exactly 85:00** can be manually confirmed. Score read later than that must not be treated as genuine 85:00 live evidence.
- Added `test_selector.cjs` based on built-in Node modules and its own GitHub Actions workflow `research-last120-selector.yml`; checks key selection/unknown state/atomic imports. Earlier headless Chromium end-to-end smoke checks passed on the smaller 52-fixture variant. Research only, PR remains draft, no production changes.
