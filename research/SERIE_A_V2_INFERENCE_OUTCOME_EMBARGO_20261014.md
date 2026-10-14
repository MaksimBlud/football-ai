# Serie A MARKET_ANCHOR_1X2_V2 — calculation-time outcome embargo

Decision 2026-10-14: prioritize **the restored original V2** exclusively for this model recovery and test stream. Do **not** investigate, revive, compare with, re-train or promote the obsolete product XGBoost. This is not a retroactive modification of frozen research metrics or a claim that V2 already outperforms bookmakers.

## Found V2-only safety defect

The automatic free-source downloader in `serie_a_v2_live_diagnostic_report.py` rejects the 2026/27 `2627/I1.csv` URL before HTTP. However, the public `make_report(quotes, history, source_audit, as_of_utc=...)` API previously accepted arbitrary caller-supplied `history` and `source_audit` values, including rows dated **2026/27**. It could calculate V2 previews even with a protected result embedded in memory and still mark `2026_27_public_results_downloaded=false`. The 2026/27 outcomes embargo must apply *at inference entry*, not solely at network fetch.

## Completed independent guard

`_assert_original_v2_source_embargo()` executes **before** as-of feature construction or model inference and now rejects:

- Any historical Date on/after `2026-07-01`, including the first day of the 2026/27 season, whether or not the row would otherwise be excluded by the quote-day cutoff.
- Any missing, additional, duplicated or protected season in the list of **exact ten 2016/17–2025/26 source audit entries**.
- Source URL/archived CSV name inconsistent with the configured historical source, invalid SHA256 metadata, nonpositive/computed-free row count, and source observation timestamps in the future.
- Empty/missing or unparseable historical date inputs.

The original frozen artifact, **19 feature order**, its SHA, trained weights, median-imputation semantics, `active_lambda=0`, `shadow_residual_lambda=1`, failed stability gate, `NO_BET` and 30-event outcomes gate are unchanged. No production model or old-model files touched.

**Important limitations:** this guard checks the allowed source manifest shape and dates; it does **not** cryptographically link the in-memory `history` to raw CSV SHA (the dedicated offline [PR #657](https://github.com/MaksimBlud/football-ai/pull/657) archive verifier checks original ZIP members) and does not prove information-time availability before quote. Both are required separately. Diagnostic scores remain explicitly nonprospective and nonpublishable.

## Expected regression

The original positive test fixtures previously contained 2026/27 results and a fake `2627` source audit. They have been replaced with **pre-freeze source rows** and the exact ten allowed audit records. Negative tests add:
- reject injected protected-season score before any preview;
- reject protected or missing season in source audit;
- reject malformed SHA, wrong source URL, future observation time;
- reject the boundary `2026-07-01`;
- existing no-paid-provider, 19 original features and not prospective claims still pass.

This is research-only and free: **zero The Odds API calls, zero Supabase writes, no old-model testing, no model promotion**. Follow the agreed **HUMAN-MERGE** rule for scheduled agents after exact-head CI. Do not alter existing frozen experiment admission rules retroactively.
