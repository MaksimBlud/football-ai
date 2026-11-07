# MARKET_ANCHOR_1X2_V2 — provider AI-inference rights gate

Date: 2026-11-07 UTC  
Scope: research-only, original frozen MARKET_ANCHOR_1X2_V2; no production or model changes.

## Finding

The official [Football-Data fair-use policy](https://football-data.co.uk/contact.php) currently states that requests for commercial, AI-usage, and model-training purposes should assume no data-use permission is granted. It separately describes the free CSV/Excel data as intended for private individuals' personal betting and/or academic interest/research, with at most two light automated download sessions per week.

The previous project manifest recorded `authorization=null` and `provider_issued_ai_inference_license=false`, but still treated frozen-weight AI inference as a narrow operational interpretation of personal/academic research. Because the original V2 uses these data as input to an AI model, that inference interpretation is not sufficiently supported by the provider's explicit AI-usage language.

## Fail-closed correction

The research branch now:
- marks `research_inference_permitted=false`;
- marks `research_inference_scope=NONE_PENDING_PROVIDER_AUTHORIZATION`;
- records `provider_issued_ai_inference_license=false`;
- requires a provider-issued written permission or open licence specifically covering `FROZEN_AI_INFERENCE` and `NONCOMMERCIAL_RESEARCH`;
- requires the permission evidence to be stored inside the repository, reviewed, within its validity window, and SHA-256 verified;
- blocks source capture, source attestation, quote reads, feature construction, original/current-form forward inference, and secondary evaluation before external access while permission is absent.

This is deliberately stricter than the provider's general personal/academic research wording. It does not claim legal advice or imply that permission has been granted.

## Exact code provenance

- New rights helper blob: `4caa66c672181dd7babd2d1da7dd28ad2831ca16`
- New rights manifest blob: `513336b0b04634a6bbb16f944c9d374a08e9f8ac`
- Original forward script blob after pin update: `8db52d151f9734a9c2485aab613ccf08ee5f6519`
- Current-form forward script blob after pin update: `e966286949a7df24a3728be8365382d0c17188eb`
- Candidate SHA unchanged: `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`

## Required downstream integration

PR #718 must not be merged by itself with the older conditional-inference interpretation. The quote-preflight PR #719 and the market-only evaluator/runner PRs #716/#717 still carry earlier rights/helper/source-loader pins. After the rights branch is reviewed and integrated, rebase in order and update each exact blob pin; never disable provenance checks to make the stack green.

## Validation boundary

- Synthetic rights tests only; no provider request.
- No new CSV downloads.
- No paid provider calls.
- No Supabase reads/writes in this branch's validation; no DDL.
- No 2026/27 target outcomes read.
- No model inference, training, refit, or promotion.
- No production `.pkl`, weights, 19-feature order, scaler, imputer, or lambda semantics changed.
- Original 30-primary-completed-forecast evaluation gate remains closed.

The next permissible path is either provider-issued written AI-inference permission recorded with evidence and SHA, or a different source whose licence expressly permits this frozen-model research use. Until then, do not run V2 against Football-Data-derived data.
