# Big Balls Sports Data free Serie A statistics audit — original MARKET_ANCHOR_1X2_V2

**Checked:** 2026-11-24 05:52 UTC  
**Provider:** [Big Balls Sports Data](https://bigballsdata.com/)  
**Decision:** **HOLD — no integration, account, API key, provider request, download, feature calculation or inference.**

## Executive finding

Big Balls Sports Data is the strongest newly reviewed free current-season statistics candidate in this pass. Its official Terms of Service expressly permit customers to store API responses privately and use stored data as input to internal models, including training, evaluation and backtesting; model outputs are the customer's. The Terms do not separately name inference, so this audit does not treat inference as an independently confirmed permission. Raw feed redistribution is prohibited. This is materially clearer than the ML/storage permissions found in several other free-source audits.

The provider advertises Serie A scores, standings and match statistics. Its documented soccer match-statistics schema includes corners, yellow cards and red cards; match scores provide goals, and points can be derived from completed match results. These fields map to the unchanged 19-feature families at schema level.

**It is not cleared for integration.** The provider aggregates many upstream sources but explicitly hides vendor identity behind an opaque source-tier label. The public coverage matrix marks soccer team statistics as partial, all fixture-stat fields are nullable, and exact 2026/27 Serie A per-fixture completeness is not established. The official pages also conflict on the Free plan's season scope. In addition, the official Serie A landing page visibly contains cross-sport contamination: its purported latest Serie A match tile shows Soldier Field, a 20–10 score and Q4/NFL-drive text; a Serie A fantasy tile includes NFL player names; and the page reports 4,941 total matches versus 4,671 finished games; the 270 difference is consistent with unplayed fixtures and is not treated as a contradiction. This is a severe data-integrity red flag, not a cosmetic issue to ignore. No provider API call was made.

## Free plan and contract

The official pages advertise:
- $0/month and no credit card;
- 1,000 requests/day and 100 requests/minute;
- scores, standings and statistics;
- a Free plan season window described as either "current + most-recent season" on the global pricing page or "current season" on the Serie A/coverage pages;
- no bookmaker odds on Free; odds begin at Edge, advertised at $149/month.

The season-window conflict is recorded rather than silently resolved. Neither stated Free scope replaces the original 2014–2026 historical training corpus. No paid tier is proposed.

## Mapping to the unchanged 19 features

The frozen candidate requires these exact features, in their original order:

`diff_points_5`, `diff_points_10`, `diff_points_venue5`,  
`diff_goals_for_5`, `diff_goals_for_10`,  
`diff_goals_against_5`, `diff_goals_against_10`,  
`diff_corners_for_5`, `diff_corners_for_10`,  
`diff_corners_against_5`, `diff_corners_against_10`,  
`diff_yellow_5`, `diff_yellow_10`,  
`diff_red_5`, `diff_red_10`,  
`diff_goals_for_venue5`, `diff_goals_against_venue5`,  
`diff_corners_for_venue5`, `diff_corners_against_venue5`.

| Required family | Officially documented field | Assessment |
|---|---|---|
| Goals for/against | Match score / linescore | Schema-level mapping |
| Points | Derived 3/1/0 from completed score | Schema-level mapping |
| Corners for/against | `corner_kicks` | Present, nullable |
| Yellow cards | `yellow_cards` | Present, nullable |
| Red cards | `red_cards` | Present, nullable |
| Venue splits | Home/away team sides plus match venue | Derivable if fixture/team mapping is complete |

The endpoint `GET /v1/matches/{id}/statistics` is documented as Free and returns post-match team statistics persisted hourly. It is stored-only; the documentation says upstream statistics commonly arrive within about 30 minutes after full time. The coverage page marks soccer `team_stats` as **Partial**. No per-fixture Serie A 2026/27 completeness matrix was reviewed or verified.

Therefore the source has **potential schema-level 19-feature compatibility**, not proven full feature parity. Missing values must remain missing; no zero-fill, median substitution outside the frozen imputer, feature substitution, reweighting or contract change is authorized.

## Rights and upstream provenance

The Terms of Service (effective 10 August 2026) state that customers may:
- store API responses in their own systems and keep them there;
- use stored data as input to internal models, including training, evaluation and backtesting;
- retain ownership of derived models, scores, predictions and aggregates.

The same terms prohibit reselling the raw feed or republishing raw field values as a feed, file, API or bulk export.

The unresolved issue is upstream provenance. The Introduction says the service aggregates 19+ free-tier upstream sources and 10 MCP scrapers. OpenAPI defines `meta.source` as an opaque source-tier label and explicitly says customers never see the vendor identity. The separate `FieldResult.source` string is not documented as a vendor identity and is not the schema used by the soccer match-statistics route. The provider's customer terms do not, by themselves, establish the rights of every upstream source for every required Serie A field.

Written confirmation is required that the provider has rights to license goals, corners, yellow cards and red cards for the intended private research and internal model use, and that the rights permit the exact retention period needed.

## Source-before-quote, timestamps and SHA

The soccer endpoint `GET /v1/matches/{id}/statistics` is documented as stored-only and refreshed hourly, but its response schema does not expose a per-record or per-field first-observed/correction timestamp.

A related endpoint, `GET /v1/stored/matches/{id}/stats`, documents `meta.as_of` and `oldest_as_of` as ingestion timestamps, not request time or upstream provider update time. The same documentation warns that soccer commonly returns an empty team-stat array there and points callers to `/v1/matches/{id}/statistics` for team-level soccer statistics. That related timestamp must not be misrepresented as a timestamp for the actual soccer statistics response.

If written upstream clearance and exact feature coverage are later established, a future-only authorized collector could preserve the exact response bytes, request path/parameters (excluding credentials), response headers, local receipt UTC time and SHA-256 in private storage **before** reading any later saved market quote. That would prove that the project possessed those exact bytes before the quote. It would not prove when the upstream source first observed or corrected each field.

No source capture, API request or SHA was created in this audit. The source-before-quote gate remains **unproven**.

## Public landing-page integrity warning

The provider's official [Serie A page](https://bigballsdata.com/serie-a-api) contains visible cross-sport contamination at the checked revision:
- The page's "Verified match event replay" identifies **Fiorentina 2–2 Juventus**; its "Latest served Serie A match" tile identifies the same fixture but shows **20–10**, **Soldier Field**, and **Q4 / NYG drive** American-football text.
- A tile labelled Serie A fantasy displays NFL player names and metrics (including CMC and NACUA).

The page reports 4,941 total Serie A matches and 4,671 finished games. The difference is 270, which is consistent with 270 scheduled fixtures remaining in a 20-team, 38-round season; it is not treated as a contradiction. The same-fixture 2–2 versus 20–10 score conflict and NFL content are direct public-page observations, not API-response tests. They do not prove every underlying API row is wrong, but they are severe data-integrity warnings that require a provider explanation before any data use.

## Frozen V2 invariants

This audit pins, without changing:
- candidate SHA-256: `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`;
- training fingerprint: `f27ab985ae90bb8e94ba8d548847695888c232f43b3e9be93074f39e1a7a5098`;
- 3,799 training rows;
- exact original 19-feature order and 20 × 2 weights;
- `active_lambda=0` (market anchor);
- `shadow_lambda=1` (research only);
- failed stability gate and no automatic promotion.

This provider could only be reconsidered as a future-only source of lagged inputs for the unchanged feature builder. It is not a replacement for the original historical training corpus and not a source of market odds.

## Required clearance before reconsideration

1. Written confirmation of upstream vendor identities and field-level rights for Serie A goals, corners and cards, including private research/model use.
2. Reconciliation of the conflicting Free-plan season scope.
3. A provider-supplied per-fixture 2026/27 Serie A completeness statement for the exact required fields.
4. A documented freshness/correction contract for the soccer match-statistics route, or explicit acceptance that only project receipt-time/SHA can be used for source-before-quote.
5. Confirmation that the Free-plan quota and retention period cover the intended future-only research capture.
6. Separate resolution of the original Football-Data historical training-corpus rights. This provider does not retroactively authorize that corpus.

## Official documents reviewed

- [Terms of Service](https://bigballsdata.com/legal/terms)
- [Pricing and plan scope](https://bigballsdata.com/)
- [API Introduction](https://bigballsdata.com/docs/introduction)
- [OpenAPI 3.1 specification](https://bigballsdata.com/openapi.json)
- [Coverage](https://bigballsdata.com/coverage)
- [Serie A API page](https://bigballsdata.com/serie-a-api)

**Bottom line:** keep Big Balls Sports Data on **HOLD_NO_INTEGRATION**. It is a promising free current-season statistics candidate with unusually explicit internal-ML and private-retention terms, but opaque upstream identities and incomplete/partial Serie A statistics coverage prevent an evidence-based integration decision. No provider access or model operation is authorized by this audit.
