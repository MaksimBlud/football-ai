# Global Football Data Lake — original V2 source-rights and as-of audit

**Decision: HOLD.** This is a documentation/offline-regression audit only. It does not authorize ingestion, use, inference, training, or publication for the original `MARKET_ANCHOR_1X2_V2`.

## Scope and evidence inspected

Reviewed the public repository documentation and pipeline source, the Hugging Face dataset page, and the two upstream providers' published terms. No dataset Parquet/CSV was downloaded. No provider account, key, API request, odds request, Supabase access, or target-outcome read was performed.

- Dataset repository: https://github.com/v-eatpizzanot/soccer-dataset
- Hugging Face dataset card: https://huggingface.co/datasets/eatpizzanot/soccer-dataset
- Repository data dictionary: https://github.com/v-eatpizzanot/soccer-dataset/blob/main/docs/data_dictionary.md
- Repository pipeline: https://github.com/v-eatpizzanot/soccer-dataset/blob/main/docs/PIPELINE.md
- Exact `known_at` implementation: https://github.com/v-eatpizzanot/soccer-dataset/blob/main/pipeline/materialize.py
- API-Football terms: https://www.api-football.com/terms
- Football-Data fair-use policy: https://football-data.co.uk/contact.php

## What makes the candidate interesting

The repository README reports 673,966 fixtures, 644,901 played fixtures, 271 leagues and a date range from 2008-06-07 through 2027-06-06. The data dictionary describes 283,834 `match_stats` rows and includes shots, shots on target, corners, yellow/red cards, goals and other match statistics. The Hugging Face page labels the published dataset CC-BY-4.0.

This is a potentially useful historical schema candidate, but those repository-reported totals are not a per-league or per-field V2 conformance result. The repository itself warns that league history is uneven and must be checked through `league_catalogue.history_status`.

## Rights are not cleared by the aggregate CC-BY claim

The dataset README and Hugging Face metadata claim CC-BY-4.0. That claim does not, by itself, demonstrate that the dataset publisher can sublicense every upstream field under that licence. The repository README identifies two upstream sources:

1. **API-Football.** Its terms say the data is obtained from partners, do not grant a general licence to publish the data, and place responsibility for third-party competition rights on the user. They do not expressly establish the project's internal AI-model use and private long-term raw-archive rights. Status: HOLD.
2. **Football-Data.co.uk.** Its current fair-use policy describes free use as private personal betting and/or academic research, allows light automated downloads at most twice per week, and expressly excludes commercial or AI data-training projects using automated bots/scrapers. The dataset identifies Football-Data as an upstream source and exposes a fixture-level `merged_football_data` flag, but the inspected schema does not provide a complete field-level rights/provenance map that would let this project safely isolate every Football-Data-derived statistic. Status: NOT APPROVED for this automated AI workflow.

No written upstream permission or field-level rights schedule was found in the inspected public documentation. Therefore no source-use permission is inferred from public accessibility or the aggregate CC-BY-4.0 label.

## Source-before-quote is not proven

The data dictionary says `match_stats.stats_fetched_at` records when statistics were fetched, but that field is null for **74.0%** of rows.

More importantly, `pipeline/materialize.py` creates `match_stats.known_at` as:

```sql
f.date_utc + INTERVAL 105 MINUTE
```

That is a derived kickoff-plus-105-minute availability heuristic, not the provider's observation time and not a timestamp proving when the exact source bytes were captured. It cannot establish that a later-corrected historical statistic was present in the form used by this dataset before a particular saved quote.

The candidate therefore fails the project's strict source-before-quote requirement. A future adapter would need actual archived response bytes, a per-capture UTC timestamp, SHA-256 over the exact bytes, authenticated capture-run provenance, and a quote strictly after that verified capture. A derived `known_at` field is not a substitute.

## Coverage and frozen-contract compatibility remain unverified

The dictionary reports null rates for relevant match-stat categories: total shots 23.1%, shots on goal 23.1%, corners 22.7%, yellow cards 20.9%, red cards 22.7%; `stats_fetched_at` is null in 74.0%. These aggregate rates do not prove complete Serie A coverage, venue-specific history, or exact parity with the original frozen 19-feature builder.

The checked-in `QUALITY_REPORT.md` is timestamped 2026-07-05. The README's date range includes future fixtures through 2027-06-06, but that does not prove that current 2026/27 completed-match statistics are present or freshly captured as of 2026-11-21. No data files were downloaded to test that claim.

## Required before reconsideration

- Written permission covering the actual upstream data owners/providers, internal ML/research use, and private raw-data retention.
- Field-level lineage that separates any Football-Data-derived values from other sources, or explicit permission for those values.
- Actual source-capture timestamps and raw-byte SHA-256 provenance; do not rely on kickoff+105-minute `known_at`.
- A read-only, rights-approved per-league/per-season coverage audit against the unchanged original 19-feature order and original feature builder.
- Explicit confirmation of current 2026/27 completed-stat freshness and coverage before any prospective use.

Until every requirement is independently established, keep the manifest at HOLD. Do not create an adapter, fetch the dataset, read odds, calculate features, or run V2 inference from this source.

## Frozen V2 invariants

The original candidate SHA, training fingerprint, 19-feature contract, original weights, scaler/imputer, `active_lambda=0`, `shadow_lambda=1`, NO_BET, and the separate 30-primary-completed-event evaluation gate are unchanged. This audit creates no model input or forecast and does not open the protected outcome gate.
