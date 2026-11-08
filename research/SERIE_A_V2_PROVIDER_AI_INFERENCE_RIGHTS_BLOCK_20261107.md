# MARKET_ANCHOR_1X2_V2 — Football-Data source-scope review

Date: 2026-11-07 UTC  
Scope: research-only, original frozen MARKET_ANCHOR_1X2_V2; no production or model changes.

## Current official wording

The official [Football-Data fair-use page](https://football-data.co.uk/contact.php) is marked **Updated: 06/11/26**. It describes the free CSV/Excel files as intended for private individuals' personal betting and/or academic interest and research only, through manual download or at most two light automated download sessions per week. It says the files are not intended for commercial or AI data-training projects.

The current page does not separately define whether applying already-frozen model weights to data for noncommercial research is included in the research allowance. It also does not say that every such inference requires a provider-issued licence. The earlier draft's phrase “AI-usage” overstated the current page wording and has been removed.

## Conservative project decision

The project continues to block Football-Data-derived V2 inference until the narrow frozen-inference scope is clarified or a different source with an applicable explicit licence is identified. This is an internal fail-closed risk-control decision, not a legal conclusion that the provider expressly prohibits all inference.

The manifest therefore records:
- `research_use_permitted=true` for the page's stated personal/academic research scope;
- `research_inference_permitted=false` pending scope clarification;
- `provider_issued_ai_inference_license=false` and `authorization=null`;
- AI training, commercial use and public product use as forbidden;
- no more than two automated source-download sessions per rolling seven days.

The runtime guard blocks before network, Supabase, archive, quote, feature, or model access while this internal inference gate remains closed. The standalone frozen-shadow CLI also checks this gate before importing the database client or reading externally supplied feature JSON.

## Verification and safety

- Official page checked: 2026-11-07T01:56:17Z; page update date: 2026-11-06.
- No Football-Data CSV request was made for this review.
- No paid provider request, Supabase write/DDL, model inference, training, refit, or promotion occurred.
- No protected 2026/27 outcomes were queried from Supabase or passed to an evaluator.
- Original candidate SHA remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`; 19 features, 20x2 weights, active lambda 0 and shadow lambda 1 are unchanged.
- The 30-primary-completed-forecast outcome gate remains closed.


## 2026-11-07 addendum — separate source-only research capture from inference

The public page explicitly describes the free files as intended for private individuals' personal betting and/or academic interest and research, with at most two light automated downloads per week. The project now separates this stated research-use allowance from the unresolved inference question:

- Private, noncommercial source-only archival/validation is permitted internally under the stated research-use scope, but only after the private-repository check and shared two-session rolling-seven-day budget pass.
- This source-only scope does not authorize feature construction, frozen-model inference, AI training, commercial use, public product publication, or redistribution.
- The manifest adds research_source_capture_permitted=true with scope PRIVATE_NONCOMMERCIAL_RESEARCH_ARCHIVE_ONLY, while retaining research_inference_permitted=false, provider_issued_ai_inference_license=false, authorization=null, and the unresolved inference status.
- The current-season CSV is not requested or parsed until the identity-only 30-primary-completed-event gate passes. The separate 30-eligible-forecast evaluation gate remains closed.
- Original/current-form forward, free quote diagnostic, and evaluator paths continue to require the stricter frozen-inference gate. No V2 probabilities or forecasts are created by source capture.

This is a narrow internal interpretation of the public research-use wording, not a provider-issued inference licence or legal opinion. The repository is still public, so the privacy gate blocks live source capture until the owner makes a separate private-storage decision.
