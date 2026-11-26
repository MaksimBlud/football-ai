# Original MARKET_ANCHOR_1X2_V2 — API-Football free-plan source and rights audit

**Audit refresh:** 2026-11-26 UTC  
**Decision:** **HOLD — the public Free season window excludes 2026/27; model-use rights, private retention and upstream rights are not cleared.**  
**Scope:** official public API-Football terms, pricing, documentation, dated provider guide and coverage page only. No account, API key, API request, source download, odds request, Supabase access, feature calculation, inference or protected 2026/27 outcome read was performed.

## Executive result

API-Football is technically relevant: its public documentation lists fixture results, points/standings, corners, yellow cards and red cards. The Free plan advertises $0 and 100 requests/day, and includes the documented endpoint families, but season availability is restricted.

The decisive current-form blocker is explicit in the provider's **2026-10-26** guide: the Free plan in 2026 covers only Year-4 through Year-2 — **2022, 2023 and 2024**. It therefore does not provide the required **2026/27** Serie A cohort. The coverage page was refreshed on 2026-11-26 and lists Italy Serie A, but a league listing does not override the Free-plan season restriction or establish Free access to 2026/27 fixture statistics.

The provider's terms also leave internal ML use, model inference, private raw-response retention and upstream field rights unresolved. API-Football obtains data from partners, prohibits resale, does not grant a general license for use/publication in user products, and warns that third-party rights may apply. Silence is not treated as permission.

## Free-plan and current-season evidence

- Pricing: Free is $0/month, 100 requests/day, with Statistics listed; the pricing page says Free access is limited by available seasons.
- Provider guide dated 2026-03-13: Free has 100 requests/day and access to all endpoint families, while paid plans unlock deeper historical archives.
- Provider guide dated **2026-10-26**: the 2026 Free season window is Year-4 through Year-2, explicitly 2022, 2023 and 2024. This excludes 2026/27.
- Coverage page last updated **2026-11-26**: Italy Serie A is listed, but the public league listing is not proof that the Free plan can access 2026/27.
- No account, dashboard, authenticated coverage response or API request was used. The 2022–2024 season window is the latest explicit Free-plan range found in the reviewed provider material; re-check it if the provider publishes a later change.

## Frozen 19-feature compatibility

The original candidate's ordered features are unchanged:

1. `diff_points_5`
2. `diff_points_10`
3. `diff_points_venue5`
4. `diff_goals_for_5`
5. `diff_goals_for_10`
6. `diff_goals_against_5`
7. `diff_goals_against_10`
8. `diff_corners_for_5`
9. `diff_corners_for_10`
10. `diff_corners_against_5`
11. `diff_corners_against_10`
12. `diff_yellow_5`
13. `diff_yellow_10`
14. `diff_red_5`
15. `diff_red_10`
16. `diff_goals_for_venue5`
17. `diff_goals_against_venue5`
18. `diff_corners_for_venue5`
19. `diff_corners_against_venue5`

The public documentation describes fixture score/result fields and standings, plus match-level Corner Kicks, Yellow Cards and Red Cards. This is a plausible raw-field mapping only; it is **not** proof of exact source parity, 2026/27 Free coverage, complete per-match statistics, stable definitions or valid missingness semantics. Null must never be converted to zero. No feature vector was built.

## What is and is not pre-match

The provider guide says `/fixtures/statistics` is available once a match is underway or completed. It is not a source of statistics for the target fixture before that fixture starts. In principle, statistics from a previously completed match could become lagged input for a later target match if the exact response bytes were lawfully captured and privately stored before the later bookmaker quote and target kickoff.

The documentation describes live statistics refreshes but does not document a per-match historical first-observation timestamp or per-field correction timestamp. A project-side receipt timestamp plus SHA-256 over exact response bytes could prove that the project possessed those bytes before a later quote; it would not prove when API-Football or its upstream partner first observed or corrected the values. No such source-before-quote capture exists now.

The 100-request/day ceiling is a hard Free-plan budget. The guide documents batching up to 20 fixture IDs only where the plan supports the `ids` parameter; Free-plan support for that batching mode was not independently confirmed. No request-budget estimate is used to imply feasibility.

## Rights assessment — not cleared

The provider's current public Terms of Service state that:
- data is obtained from partners;
- resale of provider data to third parties is prohibited;
- the provider does not grant a general license for use and publication of the data in user applications, websites or products;
- the user is responsible for obtaining required authorizations from competent authorities;
- third-party intellectual-property or commercial restrictions may apply, and the provider does not grant commercial rights on competitions.

The reviewed terms do **not expressly grant**:
- internal ML/model training or feature derivation;
- model inference using retained match statistics;
- private raw-response retention for an audit period or after account closure;
- upstream field-level rights for Serie A scores, corners, yellow cards and red cards.

This is an absence of an explicit grant, not a legal conclusion that every internal use is prohibited. Written clarification from API-Football and, where applicable, the relevant upstream rights holders is required before account creation, automated access, data retention, feature engineering or inference for this project.

The Terms page states it was last updated **2025-05-21**. Re-check the live terms before any future reconsideration.

## Required clearance before reconsideration

1. A Free-plan season window that explicitly includes Serie A 2026/27.
2. Written confirmation that internal non-commercial ML research, feature derivation, inference and private raw-response retention are permitted.
3. Written identification/clearance of upstream rights for Serie A scores, corners, yellow cards and red cards.
4. Exact season-level fixture-statistics coverage and per-match field completeness, with null semantics preserved.
5. A documented correction policy and any source timestamps available for the required raw inputs.
6. A request-budget design under 100 requests/day, with no paid upgrade, overage or billing fallback.
7. Only after all gates: a separately reviewed V2-only adapter that archives exact bytes privately with SHA-256 and UTC receipt time, proves capture completed before each quote, and passes exact 19-feature parity tests without changing the original contract.

Until every requirement is independently established, keep API-Football at **HOLD**. Do not create an account, request a key, call the API, fetch odds, download data, calculate V2 features or run inference from this provider.

## Original V2 invariants

The main candidate remains unchanged:
- candidate SHA-256: `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`;
- training fingerprint: `f27ab985ae90bb8e94ba8d548847695888c232f43b3e9be93074f39e1a7a5098`;
- 3,799 training rows;
- exact 19-feature order and 20 × 2 weights;
- `active_lambda=0` (market anchor);
- `shadow_residual_lambda=1` (research only);
- stability gate FAILED; no automatic promotion.

No feature substitution, refit, threshold tuning, candidate or contract change, production .pkl change, Supabase write/DDL or evaluation-gate change is proposed.

## Official documents reviewed

- Terms of Service: https://www.api-football.com/terms
- Pricing: https://www.api-football.com/pricing/
- Current documentation: https://www.api-football.com/documentation-v3
- Coverage (last updated 2026-11-26): https://www.api-football.com/coverage/
- Free-plan guide (2026-03-13): https://www.api-football.com/news/post/how-to-get-started-with-api-football-the-complete-beginners-guide
- Free season-window guide (2026-10-26): https://www.api-football.com/news/post/how-to-get-all-data-from-a-league-with-api-football

**Bottom line:** API-Football has technically relevant match statistics and a $0 Free plan, but the documented Free season window excludes 2026/27. Rights, private retention and upstream field permissions are also unresolved. No integration or live access is authorized by this audit.
