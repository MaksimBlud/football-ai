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
- The pricing page says all plans auto-renew every billing period, lists Free as "$0/1 Month" and "$0/mo" in the comparison table, and the Refund policy explicitly says the Free plan has no time limit. Read together, the current public pages support a recurring $0 Free plan rather than a one-month-only trial.

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

The Terms permit indefinite internal retention but prohibit publishing or bulk-sharing raw responses. This repository is public, so public GitHub Actions artifacts or committed raw payloads are not acceptable. A verified private archive is a prerequisite. A read-only Supabase Storage metadata inventory on 2026-11-15 found one existing private bucket, `model-artifacts` (`public=false`). This proves that a private bucket exists, but not that it is approved or configured for raw SportsAPI response archives: its declared purpose is model artifacts, no object listing/content was inspected, and no source-archive write or DDL was authorized. The current V2 privacy gate still checks GitHub repository privacy, while this repository is public. Therefore private raw-source storage remains unverified and unauthorized. Supabase writes/DDL were not attempted.

The project currently has 113 Serie A 2026/27 finished-fixture metadata rows (date and team identifiers only; no scores/results selected in this audit). A conservative lower-bound plan would need one match-statistics request and one incidents request per fixture, plus approximately four 30-fixture season-event pages: about 230 calls. At 100 requests/day that is at least three days if the quota is dedicated to this task. This is a planning estimate, not an API test; no requests were made. Incremental collection might reduce later daily usage, but only after rights, privacy, coverage and card semantics are cleared.

## Conditions to reconsider HOLD

1. Before any future authorized request, verify the account dashboard still shows the $0 Free plan and 100/day allowance; no account has been created and no API key or request is authorized in this audit.
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


## Official documentation recheck — 2026-11-15

This recheck used only the provider's current public legal and API documentation. No account, key, API request, data download, odds endpoint, or Supabase operation was performed.

### Rights are clearer than the first audit recorded

The current Terms of Service (last updated 2026-09-01) state that they apply to paid and Free accounts. Section 3 says customers may use the API data for applications, analytics, research and commercial products, and says separate third-party-provider licences are not required for intended use. Section 4 expressly permits internal modelling, machine learning, backtesting and historical evaluation; indefinite private retention of raw responses; and retention of receipt timestamps and customer-generated hashes.

The separate Data Rights & Retention page (last modified 2026-10-24) repeats those rights. It also makes the restriction explicit: raw response bytes may be kept for internal audit/provenance but must not be published, bulk-shared, or exposed to third parties. The public GitHub repository and public Actions artifacts are therefore not acceptable storage for raw provider payloads.

The provider does not identify its upstream providers by field and does not guarantee accuracy or timeliness. That is a data-quality/provenance limitation, not a separate-licence requirement under the current Terms.

### Free-plan duration is documented as ongoing

The current pricing page says all plans auto-renew every billing period; it labels the Free plan "$0/1 Month" in the plan card and "$0/mo" in the comparison table. The Refund & Cancellation page explicitly says Free has 100 requests/day, no credit card, and no time limit. The Terms apply data-retention rights to all Free accounts.

Read together, these public statements support an ongoing $0 Free plan with a monthly billing period and 100 requests/day. The previous duration ambiguity is resolved by the current public documentation. This is not an authorization to create an account or make requests: project authorization remains false, and no account/key was created. No paid upgrade or paid request is permitted.

### Exact feature-surface evidence

The official Football V2 coverage page says Free, Pro, Ultra and Mega use the same endpoints and competitions; only daily request allowance differs. It documents a category-walk requirement because the flat tournament catalogue is incomplete.

The official match-statistics endpoint is available during live matches and after full-time, not pre-match. Its documented stat catalogue includes home/away `cornerKicks` and `yellowCards`; the incidents endpoint documents goal and yellow/red-card events. Match detail/scores provide completed goals and results.

This is a plausible lagged-history source for the frozen feature families, not a source for a target fixture's future statistics. The documentation examples are from a Bundesliga match. No current 2026/27 Serie A payload or field-completeness test was performed. Exact Serie A coverage, card conventions, and second-yellow treatment remain unverified. Missing values must still be rejected rather than converted to zero or imputed to manufacture source completeness.

### Source-before-quote interpretation

The Terms expressly permit retaining API receipt timestamps and customer-generated hashes. A private immutable archive can therefore prove project possession of exact response bytes before a later quote, provided it records the trusted receipt time, raw-byte SHA-256, API version, fixture identity, parent workflow run ID, exact commit SHA, and artifact creation time.

That local receipt proof does not claim to know when the provider first observed or corrected an upstream fact. The original V2 capture contract is enforced at the project boundary:

`private_source_capture_time_utc < quote_snapshot_time_utc < kickoff_utc`

The source-before-quote gate remains CLOSED until the private archive and exact workflow/artifact attestation exist. No public artifact may contain raw provider responses.

### Revised request-budget estimate

The latest read-only Supabase metadata query counted 113 unique completed Serie A 2026/27 fixture identities using only `match_date, home_team, away_team`; no scores or result fields were selected. The official coverage guide states that season event pages already contain the full match row, including home/away scores and status. Therefore a conservative plan is two per-fixture calls (match statistics and incidents): 226 fixture calls, plus four 30-fixture season-event pages, or about 230 calls. At 100 requests/day this is at least three quota days. This is only a planning estimate; no provider request or free credit was spent. If event pages fail to carry the exact score/identity fields needed, the estimate must be revised before any authorized collection.

### Decision

**HOLD remains.** The updated public Terms materially improve the documented rights position for internal ML and private raw retention, and the documentation covers the required corners/yellow-card fields plus card incidents. But unverified Serie A 2026/27 payload completeness, red/second-yellow parity, the absence of an authorized private archive, and the provider's no-guarantee accuracy/timeliness clause still prevent ingestion or inference. The original V2 candidate, 19-feature order, weights, scaler/imputer, lambdas, and 30-event outcome gate are unchanged.

## Read-only private-storage inventory — 2026-11-15

A read-only query of `storage.buckets` returned exactly one bucket: `model-artifacts`, with `public=false`. No storage objects or payloads were inspected. The bucket name/purpose does not establish approval for raw provider archives, and no Supabase write, upload, policy change, or DDL is authorized. The existing V2 privacy helper still requires a private GitHub repository; the project repository remains public. This is a useful infrastructure lead, not a cleared storage destination. The source audit remains **HOLD**.


## 2026-11-18 official-documentation follow-up — event change stamps and exact match-stat schema

Re-read the current official Football V2 documentation, the Terms, and the Data Rights & Retention page. This was a documentation-only check: no account/key was created, no provider endpoint was called, no free quota was spent, and no payload was downloaded.

### What is now explicitly documented

- The Football V2 coverage guide identifies Serie A as `uniqueTournament.id = 23`, labels Serie A a premium-depth competition, and says Free/Pro/Ultra/Mega share the same competitions and endpoints; only daily request allowance differs. It describes season-event pages with fixtures, scores and status and states major competitions have multi-season history. This establishes catalogue-level access, not actual completeness of every Serie A 2026/27 match payload.
- The match-statistics catalogue (last modified 2026-11-14) lists match-level `cornerKicks` and `yellowCards`. It does **not** list a match-level `redCards` key. The team-season catalogue has `redCards` and `yellowRedCards`, but season aggregates are not a substitute for the frozen per-match red-card history.
- The match incidents endpoint is documented as returning goals and yellow/red-card events. The public example does not expose a card-event payload schema or a second-yellow discriminator. Therefore direct-red versus second-yellow counting cannot yet be mapped to the original Football-Data red-card field without an assumption; the four red-card form features remain unverified.
- The coverage guide now documents an event-level `changes` object on season-page, schedule and match-detail event records. It contains a changed-field list and `changeTimestamp` in Unix seconds. This is useful fixture-metadata change detection. The documentation does not establish that this stamp is present on the separate `/match/{matchId}/statistics` response or that its changed-field list captures every corner/card statistic correction. It is not a per-field statistics observation timestamp and does not prove the provider's first observation time.
- The Terms and Data Rights page expressly permit internal analytics, research, machine learning, backtesting, private raw-response retention, receipt timestamps and customer-generated hashes for Free accounts. Raw responses must remain private and must not be published, bulk-shared or exposed to third parties.

### Consequence for the original V2 source gate

The local source-before-quote proof remains implementable as:

`private_source_capture_time_utc < quote_snapshot_time_utc < kickoff_utc`

with exact raw-response bytes, local receipt time, SHA-256, API/version identifiers, parent workflow run ID and exact commit SHA. The newly documented event-level `changeTimestamp` may be retained as supplemental metadata, but it must not replace local receipt time or be treated as a statistics-specific correction clock.

The candidate remains **HOLD** for the same decisive reasons:

1. No authorized private raw archive is available. The repository is public; the existing private `model-artifacts` bucket has not been approved for raw provider responses, and no storage write is authorized.
2. The public schema does not establish match-level red-card / second-yellow parity with the original frozen feature semantics.
3. Actual 2026/27 Serie A per-match statistics completeness has not been verified with a permitted payload.
4. The provider disclaims accuracy/completeness/timeliness guarantees, so any later data must be validated and missing values must fail closed.

No API request, account creation, key use, data download, Supabase access/write/DDL, odds read, target-outcome read, feature build, inference, refit, production artifact change, schedule change, main update or promotion occurred.

### Official documentation rechecked

- https://docs.sportsapipro.com/api-reference/football-v2/coverage
- https://docs.sportsapipro.com/api-reference/football-v2/stats-catalogue
- https://docs.sportsapipro.com/api-reference/football-v2/match
- https://docs.sportsapipro.com/data-rights
- https://www.sportsapipro.com/terms
- https://www.sportsapipro.com/pricing
