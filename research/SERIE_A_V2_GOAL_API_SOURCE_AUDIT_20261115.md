# Original MARKET_ANCHOR_1X2_V2 — GOAL API free-source audit

**Audit date:** 2026-11-15 UTC  
**Decision:** `HOLD — FREE-TIER CANDIDATE; NOT APPROVED FOR INGESTION OR INFERENCE`  
**Scope:** official public terms, privacy, pricing/FAQ, coverage and API documentation only. No account, API key, endpoint call, response download, odds read, feature build, inference, target-outcome read, paid request or Supabase write was made.

## Executive result

GOAL API is a plausible *coverage candidate*, but it is not an approved source for the original frozen V2.

Positive evidence:

- The provider advertises a free tier without a credit card and publishes a 1,000-request/day allowance in its FAQ/overview material. The pricing page was client-rendered and did not expose a static plan table during this audit, so the quota needs confirmation at account/plan level before any future use.
- Its Italy Serie A coverage page currently reports the range 2005–2027, 3,148 fixtures, 2,872 finished and 276 upcoming. It reports 1,986 matches with statistics and 2,587 with goals/cards/substitutions. These are aggregate counts, not a 2026/27 per-fixture completeness matrix.
- The vendor's match-statistics guide describes corners, shots on target, yellow cards and red cards. Its API reference exposes fixture statistics, events and cards endpoints. These are candidate field families, not proof of exact source semantics or parity with the frozen 19-feature builder.

The source remains **HOLD**. The terms do not grant the customer a licence to the underlying sports data, do not explicitly authorize internal model training/inference or private raw-response retention, and place responsibility for obtaining any required third-party rights on the customer.

## 1. Rights and legal scope

The current Terms of Service (last updated November 2026) say the provider obtains football data from third-party providers and redistributes it under its own authorizations. However, the same Terms explicitly state that GOAL API grants **no licence or representation about IP rights in the underlying sports data**, and that the customer is responsible for obtaining any authorization required to use or publish that data in its own products and territories.

The Terms permit access to the service and incorporation of returned data into applications, websites and products subject to those restrictions. They do **not** expressly grant:
- internal research rights for this project;
- AI/ML training or model-inference rights;
- a private raw-response archive/retention term;
- the upstream data providers' identities or field-level rights.

Raw-data resale, sublicensing and redistribution as a standalone feed are prohibited. The Terms also say coverage and refresh frequency are not guaranteed and that free-plan data may change without prior notice.

This is not a legal conclusion that use is impossible. It is a conservative project gate: API access is not treated as a substitute for the underlying data licence or an explicit model-use/retention grant.

### Entity identity needs clarification

The current Terms and Privacy Policy identify **Devuslab LLC**. The Italy Serie A coverage page footer identifies **DEVARA SARL**. The contracting/data-licensing entity and its authority to grant rights over the upstream football data should be confirmed in writing before use.

## 2. Free plan and request budget

The provider's FAQ/overview material advertises:
- price: $0;
- 1,000 requests per day;
- no credit card required.

The pricing page is dynamically rendered; its static HTML did not expose the current numeric plan table at audit time. No account or key was created to inspect dashboard entitlements. Free-plan duration and whether the exact statistics/cards endpoints remain included for Serie A are therefore not independently confirmed.

No API calls were made and no free quota was consumed.

## 3. Serie A coverage and original V2 feature fit

The live coverage page reports:

| Coverage item | Published count |
|---|---:|
| Fixtures/results | 3,148 |
| Finished | 2,872 |
| Upcoming | 276 |
| Lineups | 3,143 |
| Match statistics | 1,986 |
| Goals, cards and substitutions | 2,587 |

The displayed range is 2005–2027. The counts are aggregate across that range; they do not establish the percentage of 2026/27 Serie A matches with every required field. The page itself warns that data coverage varies by competition and endpoint.

The vendor's statistics guide describes corners, shots on target, yellow cards and red cards. The API documentation lists separate fixture statistics, events and cards endpoints. Before mapping any response into V2, the exact JSON keys and semantics would need to be verified against an authorized real payload, especially:
- straight red versus second yellow;
- whether card counts include staff/bench cards;
- whether corrections can revise a completed match's totals;
- neutral-venue and team-identity handling;
- exact per-match availability of corners and cards in 2026/27.

No endpoint response was requested. The feature mapping remains documentary only.

## 4. Source-before-quote and SHA requirements

The reviewed API documentation identifies UTC kickoff fields and live-clock freshness fields, but does not document a statistic-level upstream observation timestamp or correction history.

If the provider later authorizes use, the project can record its own response-received time and SHA-256 of the exact raw response bytes. That proves the project possessed that exact response before a later quote; it does not prove when the provider first observed the statistic or whether an upstream correction was already pending.

Any future source capture must therefore preserve:
1. exact raw response bytes and SHA-256;
2. provider/competition/fixture identity and endpoint;
3. source capture UTC time;
4. successful parent workflow ID and exact commit SHA;
5. quote snapshot UTC time;
6. kickoff UTC time;
7. the strict ordering `source_capture_time_utc < quote_snapshot_time_utc < kickoff_utc`.

This source-before-quote path is **not approved** until rights, retention and private storage are cleared.

## 5. Private storage is still a hard prerequisite

Raw source responses must not be placed in public GitHub repository files or public Actions artifacts. The repository is public. The existing private Supabase bucket `model-artifacts` was observed in a read-only metadata inventory, but it has not been approved for raw provider archives. No objects were inspected and no Supabase writes or DDL are authorized.

No storage integration is proposed by this audit.

## 6. Binding original V2 invariants

This audit does not change or load the model weights. It pins the existing candidate identity for regression purposes only:

- candidate SHA-256: `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`;
- 19 original features in the original order;
- weight matrix: 20 × 2;
- training rows: 3,799;
- training fingerprint: `f27ab985ae90bb8e94ba8d548847695888c232f43b3e9be93074f39e1a7a5098`;
- `active_lambda=0` remains the market;
- `shadow_residual_lambda=1` remains research-only;
- stability gate remains FAILED;
- automatic promotion remains disabled;
- 30-primary-completed-event target-outcome gate remains closed.

No old XGBoost production model is involved.

## 7. Clearance required before reconsideration

A future review would require all of the following, in writing or verifiable official documentation:

1. Confirmation from the correct contracting entity and upstream licensors that private internal research, derived-feature construction, model training/inference and private raw-response retention are authorized for the free account and Serie A data.
2. Clarification of the Devuslab LLC / DEVARA SARL entity discrepancy and identification of upstream data providers or the scope of the provider's sublicensing authority.
3. Confirmation that the exact statistics, events and cards endpoints are included in the free tier for Serie A 2026/27.
4. Per-fixture completeness evidence for the 19 frozen input families, including corner and red/second-yellow semantics.
5. A permitted private raw-response store and a source-before-quote collector that records exact bytes, SHA, parent run/commit, receipt time, quote time and kickoff.

Until then: **HOLD**. Do not create an account/key, call an endpoint, download data, build features, infer, read target outcomes, or evaluate this provider for the V2 cohort.

## Official references reviewed

- Terms: https://goal-api.com/terms
- Privacy: https://goal-api.com/privacy
- Pricing: https://goal-api.com/pricing
- Free-plan overview: https://goal-api.com/what-is-goal-api
- Italy Serie A coverage: https://goal-api.com/coverage/italy-serie-a-api
- API reference: https://goal-api.com/documentation
- Match-statistics guide: https://goal-api.com/blog/football-stats-api
