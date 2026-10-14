# Original frozen Serie A V2 — actual 20-fixture feature coverage proof (2026-10-14)

**Scope:** Original `MARKET_ANCHOR_1X2_V2` only. Research-only, NO_BET, NO model activation, NO protected 2026/27 results read.

## Verified runtime state after actual repairs

| Step | GitHub evidence | Actual result |
|---|---|---|
| Original frozen V2 feature missingness audit | [PR #665](https://github.com/MaksimBlud/football-ai/pull/665), [run 38588541087](https://github.com/MaksimBlud/football-ai/actions/runs/38588541087) | 46 tests PASS. On 20 saved real Serie A bookmaker fixtures, 18 full 19-feature vectors and **2 all-median**. Raw ZIP artifact `11906114191`. |
| Fix source identity `Atalanta BC` / `Atalanta` only in original V2 adapter | [PR #666](https://github.com/MaksimBlud/football-ai/pull/666) squash-merged `ab6fa8b3010ad81d34c719afa77adf3f76c8fe46` after 8/8 CI | Frozen original 19 input definitions, weights, medians, lambda, original candidate SHA unchanged. |
| Real source + feature diagnostic AFTER fix | [run 38589939799](https://github.com/MaksimBlud/football-ai/actions/runs/38589939799) | **SUCCESS; 49 tests PASS; 20/20 fixtures now have all 19 historical features; 0/20 all-median.** Exact 10 public old-season CSVs, 3800 historical games, SHA-archived report `11906648084` (ZIP SHA `6ebbf25d230b580135c8138a535b66f3c61a3962f9125802d68659fd3f0c8e3a`). No paid calls, DB writes, or production changes. |
| Actual forward-only original V2 workflow AFTER fix | [run 38589939938](https://github.com/MaksimBlud/football-ai/actions/runs/38589939938) | **SUCCESS; 58 tests PASS.** Real GitHub source/archive run attested, all 20 old quotes correctly blocked `NO_EARLIER_SOURCE_ARCHIVE`, 0 eligible new V2 previews; NO_BET. |

## Corrected actual-source identity bug

All ten verified pre-2026/27 Football-Data Serie A historical files use **`Atalanta`**, while existing bookmaker 2026/27 data use **`Atalanta BC`**. This incorrectly made both `Atalanta BC–Frosinone` and `AC Milan–Atalanta BC` look entirely without football history in V2 (0/19 features). The V2-only local canonicalization now reconciles those names without changing bookmaker identities or another league's config. Both now have **19/19** historical features in the real-source report.

## CRITICAL: complete historical fields are NOT current football form

At the existing quote timestamp on **2026-10-13**, the publicly permitted V2 history stops before 2026/27. All 20 current fixture pairs now have 19 numerical historical features. This does not make them fresh: 6 of 20 have at least one club whose last included match is **at least 365 days earlier**. This is descriptive exposure, NOT a new betting/performance threshold:

| Historical-data deficient fixture | Last available old-season age (days) |
|---|---|
| Atalanta BC — Frosinone | Frosinone: **870**, Atalanta: 144 |
| Frosinone — Sassuolo | Frosinone: **870**, Sassuolo: 142 |
| Torino — Monza | Monza: **507**, Torino: 142 |
| Monza — Cagliari | Monza: **507**, Cagliari: 142 |
| Venezia — Napoli | Venezia: **506**, Napoli: 142 |
| Genoa — Venezia | Venezia: **506**, Genoa: 142 |

The actual 20 source-backed quote-audit records also include `last_historical_match_date`, `days_since_last_historical_match`, last-30 prior sample count and same-venue sample count for each side. Six games relying on prior-season data older than 12 months require **independent newer input sources with verified prequote observation timestamps**, NOT an assumption of sufficient recent form from feature_count=19.

## Frozen scientific gates remain CLOSED

- The Oct 13 14:48 UTC 20 bookmaker snapshots were taken **before** the first verified current GitHub history archive, and are older than the original `MAX_QUOTE_AGE=24h` at the post-fix diagnostics on Oct 14. Accordingly the **daily diagnostic scored 0** (20 correctly blocked as stale), and the **forward-only prospective capture scored 0** (20 correctly blocked for no source ZIP before quote). Do not bypass these gates or relabel research diagnostics as prospective.
- Candidate `active_lambda=0` still **equals de-vigged market**. Frozen `lambda=1` residual is research-only, previously failed its stability gate. **No V2 > market claim**, production promotion or betting. No saved incumbent predicted at same information time, no legitimate new prequote cohort.
- Never read protected Serie A 2026/27 finished outcomes until predeclared 30-completed-primary-event gate permits a diagnostic read. No further The Odds API credit without the owner's NEW explicit approval; original single-use 1-credit authorization is fully consumed.
- Do not revive the old XGBoost model or modify production `.pkl`; original frozen V2 weights/feature contract remain unchanged. All 20 enriched features are historical metadata **not current 2026/27 form**.

## Next needed real proof

A strictly future, independently captured source ZIP **before a NEW bookmaker quote** followed by original V2 probabilities saved before kickoff; bookmaker collection remains user-manual and separately consented if it costs a credit. After outcomes become lawfully available under the frozen protocol, use independent match-level LogLoss and Brier vs market; future model selection must be separately preregistered. The system should not be called fully scientifically completed before those facts exist.
