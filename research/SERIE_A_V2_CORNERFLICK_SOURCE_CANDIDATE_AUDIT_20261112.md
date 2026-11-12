# Original MARKET_ANCHOR_1X2_V2 — Cornerflick source-candidate audit

**Audit date:** 2026-11-12  
**Scope:** public data-use statement and upstream API terms only. No account, key, API request, CSV/JSON dataset download, Supabase access, quote read, feature build, inference, or target-outcome analysis.  
**Decision:** `CONDITIONAL_CANDIDATE_NOT_APPROVED`.

## 1. Summary

Cornerflick is a newly identified possible source of structured football match records. Its public data page describes:

- a full match JSON record with timeline, lineups, team statistics, and provenance metadata;
- separate event, lineup, and team-statistics CSV files;
- season-level results CSV and JSON files;
- absent fields as missing rather than zero;
- dated correction notes;
- a `last_updated_at` value for each published file; and
- a CC BY 4.0 licence for the compilation Cornerflick publishes.

This is useful metadata for a future source review. It is **not sufficient authorization or source-before-quote evidence for the original V2**.

## 2. Rights: the compilation licence does not clear underlying feeds

Cornerflick's data page explicitly limits its CC BY 4.0 statement to the compilation it publishes (selection, structure, and annotation). It separately says that underlying match facts come from data providers whose own terms apply.

The upstream API-Football terms reviewed for this audit state, among other things, that:

- the supplied data is obtained from partners;
- direct resale is prohibited without permission;
- API-Football does not itself provide a general licence for use and publication of the supplied data in user products;
- publication permissions must be obtained from the competent rights holders; and
- third-party league, federation, or event-organizer restrictions remain the user's responsibility.

Therefore Cornerflick's CC BY 4.0 compilation licence cannot be treated as a blanket licence for the underlying match statistics or their use as AI-model inputs. The public data overview does not identify the rights holder and licence applicable to every underlying field/provider.

**Binding decision:** do not download, retain, train on, build features from, or infer with Cornerflick records until Cornerflick and the relevant upstream rights holder(s) provide written clarification covering this project's intended use. No rights are inferred from public availability or the compilation licence.

## 3. Potential compatibility with the frozen 19-feature contract

The public data description suggests possible raw ingredients for the unchanged V2 input families:

| Original V2 input family | Publicly described Cornerflick material | Status |
|---|---|---|
| Points and goals for/against | Match score and result record | Structural possibility only |
| Corners for/against | Team-statistics CSV and match statistics | Structural possibility only |
| Yellow/red cards | Event timeline with event type and side | Structural possibility only |
| Home/away venue windows | Match date and home/away identity | Structural possibility only |

No file or match payload was downloaded or parsed. Consequently, no claim is made about actual field completeness, team identity consistency, second-yellow/red-card semantics, abandoned-match handling, or numerical parity with the original Football-Data training source.

The frozen feature builder must remain unchanged. Any future source adapter would require a separate preregistered concordance protocol and must reject missing, ambiguous, or definitionally incompatible fields rather than convert them to zero or silently substitute a new definition.

## 4. Source-before-quote and SHA assessment

Cornerflick says each file states when it was last refreshed and that a file is never fresher than the `last_updated_at` value in its metadata. It also describes dated correction notes.

That is a promising file-level freshness signal, but the public overview does not establish:

- whether `last_updated_at` is the upstream provider's observation time, Cornerflick's ingestion time, or only the publication time;
- whether the timestamp applies to every field in the file;
- whether each field has a separately identified upstream provider;
- whether corrections preserve the prior version and expose a field-level effective timestamp; or
- whether a later upstream correction can change the published file without a separately versioned source observation.

A locally captured immutable response plus SHA-256 and a successful parent-run timestamp could prove that **our copy** existed before a later quote. It cannot, by itself, prove when the upstream statistic was first observed or whether the field was revised after the quote.

Before reconsideration, require written confirmation of the timestamp semantics and a sample provenance schema containing, at minimum, immutable record/release identity, exact source/provider per field or field family, source-observed/ingested/updated timestamps, correction history, and a stable response version. The capture must then archive exact raw bytes and response metadata privately, hash the bytes before parsing, and require strict `source_capture_completed_at < quote_snapshot_time_utc < kickoff_utc`. No historical quote may be backfilled.

## 5. Protected prospective cohort and accidental search-snippet exposure

No 2026/27 match page, season CSV/JSON, or match `data.json` was opened or downloaded for this audit. No current-season score or result was recorded, compared, or used in any calculation.

During general web discovery, the search engine returned snippets from current-season match pages that included score-bearing text. Those snippets are excluded from this audit and must not be used for feature selection, model evaluation, threshold changes, or any other research inference. This is recorded as an exposure incident, not as an authorized outcome read. Keep the preregistered target-outcome gate closed; do not use the exposed snippets as evaluation evidence.

## 6. Frozen V2 invariants

- Original candidate SHA-256 remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`.
- Original feature-builder Git blob remains `401b3a0893371bfa4a488ec92a4a54af2678c8f7`.
- The original 19-feature order, rolling windows, weights, scaler, imputer, training fingerprint, and 20x2 matrix are unchanged.
- `active_lambda=0`: exact de-vigged market remains the active reference.
- `shadow_lambda=1`: research-only.
- Stability gate remains FAILED; NO_BET and automatic-promotion prohibition remain.
- The separate prospective outcome-read gate remains closed until 30 eligible prospective forecasts have completed under the preregistered contract.
- No legacy XGBoost production model, production `.pkl`, paid odds API, Supabase write/DDL, or schedule change is involved.

## 7. Actions taken and next admissible step

Actions taken:
- Read only Cornerflick's public data-use overview and API-Football's public terms.
- Did not create an account or API key.
- Did not call an endpoint or download any CSV/JSON data.
- Did not read Supabase, saved quotes, or target-outcome rows.
- Did not calculate features, run inference, alter the frozen candidate, or change any workflow.

Next admissible step: obtain written upstream rights and timestamp/provenance clarification. Only then may a separately approved, source-only concordance study be designed. Until then, Cornerflick is **not an approved source** for original V2 capture or inference.
