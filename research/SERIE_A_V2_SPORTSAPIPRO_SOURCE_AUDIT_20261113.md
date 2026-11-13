# Original MARKET_ANCHOR_1X2_V2 — SportsAPI Pro free-source audit

**Audit date:** 2026-11-13 UTC  
**Decision:** `HOLD — CONDITIONAL FREE-TIER CANDIDATE; NOT APPROVED FOR INGESTION OR INFERENCE`  
**Scope:** official public terms, pricing and API documentation only. No account, API key, endpoint call, response download, odds read, Supabase access, feature build, inference, target-outcome read or paid request was made.

## Executive result

SportsAPI Pro is a stronger *documented rights candidate* than several previously reviewed free feeds:

- The current pricing page advertises a $0 plan with 100 requests/day, 10 requests/minute, all endpoints and all competitions, without a credit card.
- The Football V2 coverage documentation lists Serie A as a premium-depth competition (unique tournament ID 23) and says endpoint/competition access is the same on Free; only the daily request allowance differs.
- The Terms, last updated 2026-09-01, apply the retention provisions to Free accounts. They expressly permit internal analytics, research, modeling, machine learning, backtesting and historical evaluation. They permit indefinite private retention of raw responses and retention of source/API-version identifiers, receipt timestamps and customer-generated hashes.
- The same Terms prohibit publishing or bulk-sharing raw responses. The provider's upstream sources are not named, and the Terms disclaim accuracy/timeliness guarantees.
- The pricing page labels the free plan "$0/1 Month". It is not clear from the reviewed public pages whether the free entitlement renews or remains available after that period.

This is a **conditional candidate**, not an approved source. The project currently has no verified private raw-response archive, no provider API account/key, and no authorization to make requests.

## Frozen 19-feature compatibility

The original candidate is unchanged:

- Candidate SHA-256: `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`
- Feature builder Git blob: `401b3a0893371bfa4a488ec92a4a54af2678c8f7`
- Exact 19-feature order and 20×2 weight matrix preserved.
- Training rows: 3799; training fingerprint: `f27ab985ae90bb8e94ba8d548847695888c232f43b3e9be93074f39e1a7a5098`.
- `active_lambda=0`; `shadow_residual_lambda=1`; stability gate remains FAILED; automatic promotion remains false.

The official Football V2 match-statistics endpoint documents `cornerKicks` and `yellowCards` for home and away, and says match statistics are available during live matches and after full-time (not pre-match). Match details/scores provide goals and results. The incidents endpoint documents chronological goals and yellow/red-card events.

| Frozen feature family | Documented candidate source | Remaining issue |
|---|---|---|
| Points last 5/10 and venue last 5 | Completed scores, converted to 3/1/0 | Exact W/D/L and team/venue parity still needs a bounded payload test |
| Goals for/against last 5/10 and venue last 5 | Match details/scores | Current Serie A 2026/27 per-match completeness is unverified |
| Corners for/against last 5/10 and venue last 5 | Match statistics `cornerKicks` | Current-season completeness and exact source parity unverified |
| Yellow cards last 5/10 | Match statistics `yellowCards` | Exact Football-Data convention parity unverified |
| Red cards last 5/10 | Match incidents | The match-stat catalogue has no match-level red-card key; second-yellow treatment is not documented |

No missing field may be replaced by zero, median imputation or a different provider to make the source appear complete. The original feature builder and order must remain untouched.

## Source-before-quote and SHA

The Terms expressly allow retaining receipt timestamps and customer-generated hashes. A private capture of the exact raw response bytes, with a trusted UTC receipt time and SHA-256, can prove that the project possessed those bytes before a later quote.

However, the reviewed API docs do **not** document a per-field upstream observation timestamp or correction history. The sample match response includes a status-change timestamp, not a documented source-observation time for match statistics. A local receipt timestamp therefore proves project possession before quote; it does not prove when the upstream provider first observed or corrected each fact.

Any future protocol must at minimum enforce:

`private_source_capture_time_utc < quote_snapshot_time_utc < kickoff_utc`

and retain the raw bytes, SHA-256, API version, fixture identity, parent workflow run ID, exact commit SHA and artifact creation time. If the frozen protocol requires upstream-observation time rather than project receipt time, provider clarification or a formally approved protocol interpretation is still required. This audit does not relax that gate.

## Privacy and free-tier request budget

The Terms permit indefinite internal retention but prohibit publishing or bulk-sharing raw responses. This repository is public, so public GitHub Actions artifacts or committed raw payloads are not acceptable. A verified private archive is a prerequisite. The project storage inventory was not inspected, so this audit does not claim that no private bucket exists. No private archive has been verified or authorized for this workflow. Supabase writes/DDL are not authorized and were not attempted.

The project currently has 113 Serie A 2026/27 finished-fixture metadata rows (date and team identifiers only; no scores/results selected in this audit). A conservative lower-bound plan would need one match-statistics request and one incidents request per fixture, plus approximately four 30-fixture season-event pages: about 230 calls. At 100 requests/day that is at least three days if the quota is dedicated to this task. This is a planning estimate, not an API test; no requests were made. Incremental collection might reduce later daily usage, but only after rights, privacy, coverage and card semantics are cleared.

## Conditions to reconsider HOLD

1. Confirm in writing whether the Free plan's "$0/1 Month" entitlement is renewable/ongoing and whether the 100/day limit applies to all required endpoints for Serie A 2026/27.
2. Confirm current-season Serie A match-stat coverage and exact per-match availability for every required prior fixture.
3. Confirm yellow/red-card and second-yellow semantics match the original source convention; otherwise red-card features are not compatible.
4. Provide a private raw-response archive with access controls, retention and auditability. Public GitHub artifacts are prohibited by the provider's own terms.
5. Preserve exact source response bytes, SHA-256 and trusted UTC receipt time; enforce strict source capture < quote < kickoff. Do not call this upstream observation time.
6. Only after all gates are cleared may a separate offline adapter be considered, with parity tests against the original frozen feature builder. No changes to the original candidate, weights, scaler, imputer or feature definitions.

## Safety record

- Provider account/API key created: **no**.
- API requests / free credits spent / paid requests: **0 / 0 / 0**.
- Raw data downloaded or stored: **no**.
- Supabase reads/writes: **none for this source audit**; project-level pre-match counts were inspected separately, without selecting target outcomes.
- Feature build / inference / evaluation: **not performed**.
- Original candidate, 19 features, weights, scaler/imputer, lambda values, production `.pkl` and promotion gate: **unchanged**.
- Status: `HOLD`; no provider integration or prediction is authorized.
