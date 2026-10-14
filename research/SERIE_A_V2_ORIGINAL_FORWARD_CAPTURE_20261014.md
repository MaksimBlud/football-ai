# Football AI V2 — forward-only pre-match research capture on actual stored quotes

## Purpose

**Only original Serie A MARKET_ANCHOR_1X2_V2.** Never revive old product-model training, compare to old AI model for this recovery path, alter frozen weights, open protected 2026/27 results, promote V2 to production or spend The Odds API credits.

The original V2 candidate exists, trained through June 2026 on the original 19 football differences. Frozen `active_lambda=0` equals bookmaker probabilities; `shadow_residual_lambda=1` is only research shadow and originally failed the stability gate. The 20 stored October 13 matches have market-only ledger entries and old-season V2 postquote diagnostics, but are **NOT** a genuine prospective V2 study.

## What was missing

We already capture 10 historical old-season CSV originals daily for free (2016/17–2025/26), including each SHA256 and observation time as a GitHub Actions source artifact. We already store 1X2 quotes in Supabase. But the V2 diagnostics were generated using source data downloaded **after** that quote; the original 20 could not be enrolled. The missing step is **forward binding of the prior source artifact to later actual quotes** and recording resulting V2 probabilities before kickoff.

## Implementation

`serie_a_v2_forward_capture.py`:

1. Reads **only** upcoming actual Serie A `odds_snapshots`, no finished-score tables and no paid odds API.
2. Via authenticated GitHub Actions API, reads the repository's recent artifact metadata (main-branch only, exact source workflow artifact name, GitHub SHA256 ZIP digest and archive creation UTC).
3. For each quote, chooses the latest main-source artifact whose **ZIP creation time is strictly earlier than bookmaker snapshot time**. If none exists, returns `NO_EARLIER_SOURCE_ARCHIVE`; no 2026/27 results ever read.
4. Downloads only the chosen ZIP and uses the independent offline verifier from merged PR #657 to check the **full GitHub ZIP SHA256, exact 10 member names, each CSV content/hash, season embargo, date, original frozen model SHA, source capture time, archive upload before bookmaker quote**, and quote-before-kickoff.
5. Uses these exact historical original bytes and merged PR #659 pre-inference season embargo to compute V2's unchanged 19-feature market and inactive residual shadow probabilities.
6. Saves a distinct immutable `source-check` research artifact containing only prediction inputs, event/timestamps, model hash, forecast probabilities, source artifact ID/hash, capture timestamp and explicit non-prospective status. No update/insert to Supabase, no bet or product publication.

New `.github/workflows/serie-a-v2-forward-preview.yml` runs at 08:08 UTC daily (after 06:13 UTC free source capture), on relevant code pushes and manually. `GITHUB_TOKEN` is limited to actions/read + contents/read, and Supabase is read-only in this job. It has **no THE_ODDS_API_KEY**.

## Scientific boundary

For the first 20 saved Serie A quotes (2026-10-13 14:48:53Z), the first acceptable historical source archive was created later (2026-10-13 15:22:55Z), so they **remain 0/20 source-prequote-verifiable**. Do not relabel these forecasts as eligible.

New matching records, if any after a prior source archive, remain tagged:
- `SOURCE_BEFORE_QUOTE_V2_DIAGNOSTIC_ONLY`;
- `eligible_for_frozen_prospective_cohort=false`;
- `eligible_for_product_publication=false`;
- `no_bet=true`.

Valid archived source-before-quote is necessary but insufficient: the model remains **without 2026/27 current-season form** and the separately frozen incumbent at matching information time. Do not read any protected 2026/27 prospective results until the original 30-completed-primary-event preregistered outcome gate. Do not treat this free infrastructure as proof of V2 accuracy or ROI.

## How to verify

Workflow run should show zero paid calls and zero database writes, with `v2_diagnostic_previews_captured=0` if there are no independently earlier quote-time sources. After **a separately user-authorized** new bookmaker quote is saved and sufficient verified older source archive exists, the next free job can produce forward V2-only research previews. Tests cover synthetic historical ZIP -> synthetic later quote, original model hash and market identity, rejecting old quotes, tampered ZIP, outcome leaks, future quotes and non-main GitHub source metadata. The workflow uploads the exact source ZIPs used for third-party audit.

This is the maximum safe V2 inference plumbing achievable with the current protected-season information restrictions. Achieving a proven model better than market remains blocked by original failed stability gate, current-form availability and frozen prospective evaluation; never assert it is 'complete for production' before these gates.
