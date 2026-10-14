# Frozen Serie A V2 — archive integrity and source-before-quote gate (research-only)

## Purpose

The existing daily, zero-Odds-API workflow already captures **ten** original public Football-Data Serie A CSVs for seasons 2016/17–2025/26 and preserves their raw bytes, SHA256 values and collection clock timestamps as a GitHub Actions ZIP artifact. On 2026-10-13 these public sources were collected **after** the 20 already-archived bookmaker quotes. Those first 20 V2 diagnostic forecasts remain **ineligible as frozen prospective evidence**. They must not be backfilled into a scorecard or used for production promotion.

The new offline-only `serie_a_v2_prequote_source_archive_gate.py` verifies a downloaded GitHub Actions artifact *before* contemplating later quotes:
- exact 10 archived source names and original-season list; no 2026/27 sources even temporarily;
- every source URL, original file bytes, per-file SHA256, row count, 19-feature frozen candidate SHA, scores and basic historical match sanity, with an explicit **2026-07-01** hard cutoff;
- fail closed for malformed/extra/duplicate files, tampered metadata, future timestamps, invalid/duplicate quote identities and kickoff order;
- optional check that the **whole GitHub ZIP's** SHA256 and creation timestamp match separately obtained GitHub Actions artifact metadata;
- **for each individual quote** require every source observation time, and the independently reported ZIP upload time, to be **strictly earlier** than its saved bookmaker snapshot.

The printed `source_archive_prequote_ready` figure is **source-byte/time ordering only**, not evidence that V2 beats market and not entry into any frozen prospective cohort. The script cannot authenticate its own caller-supplied GitHub metadata. It explicitly reports `independently_authenticated_github_metadata=false`; an independent and contemporaneous GitHub API read with the original artifact digest/time is required for any external audit. Without both values it marks all quote-source matches ineligible.

It never reads current-season outcomes, never calls a paid odds provider, never writes to Supabase, never retrains or promotes original V2, and never modifies production `.pkl` models. Even a passing time-order check does **not** provide missing 2026/27 form, prove incumbent forecast was collected at the same information time, overturn V2's failed stability gate, or authorize bets. All results remain `eligible_for_frozen_prospective_cohort=false`, `eligible_for_product_publication=false`, `no_bet=true`.

## How to run safely with a **later** quote

Download the already-created GitHub Actions artifact from [existing free diagnostic workflow](https://github.com/MaksimBlud/football-ai/actions/workflows/serie-a-v2-free-real-quote-diagnostic.yml); get its ZIP SHA256 and creation UTC via the independently authenticated GitHub Actions API. Save the existing, non-result-bearing bookmaker snapshot identities as JSON. Then:

```bash
python serie_a_v2_prequote_source_archive_gate.py \
  --archive /path/to/unchanged-github-artifact.zip \
  --quotes-json /path/to/saved-serie_a_quotes.json \
  --github-artifact-sha256 <exact-64-char-GitHub-artifact-digest> \
  --github-artifact-created-at-utc 2026-10-13T15:22:55Z \
  --output /tmp/serie_a_v2_archive_time_audit.json
```

The `--quotes-json` contains only `league, event_id, snapshot_time_utc, commence_time_utc` and **must not include outcomes**. Date in this example is the **actual first safe artifact** upload time, not a fabricated pre-quote timestamp. Since its upload occurred **after** the 2026-10-13 14:48:53Z quote, those original 20 must yield `source_archive_prequote_ready=0`.

Next step: independently capture and anchor the actual incumbent's probabilities with exact same quote information-time, and establish an allowed **current form** source whose 2026/27 prospective outcomes are not opened before the frozen gate. The source-order tool cannot waive either requirement.

## Verification

- Exact original V2 files remain unchanged.
- Both research and free-diagnostic workflows include the new source-archive verifier tests.
- Negative tests cover old quote/new source, missing GitHub proof, hash tamper, injected protected files/results, invalid kickoff/future quotes and duplicate quote identity.
- Preserve 100-credit hard reserve. No new The Odds API requests are authorized.
