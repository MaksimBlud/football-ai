# Original MARKET_ANCHOR_1X2_V2 — PitchAPI free-source audit

**Audit date:** 2026-11-16  
**Decision:** `HOLD — free post-match candidate; not approved for ingestion, feature building, or inference`  
**Scope:** official PitchAPI API reference and the official Python SDK's PyPI page only. No account was created; no API key was requested; no endpoint was called; no response or match data was downloaded; no Supabase access, quote read, feature build, inference, target-outcome read, or paid request occurred.

## Executive result

PitchAPI is a technically interesting free football-data API, but it is **not currently a usable source for the original frozen V2**.

Positive documented properties:

- One free plan is advertised, with no paid tier, no request allowance and 77 leagues.
- The API documentation claims history back to 2021 and includes upcoming fixtures with null scores before kickoff.
- Played-match endpoints document match summaries, team statistics, shots, yellow-card and red-card events, and several advanced metrics.
- API timestamps are documented as RFC 3339 UTC.

Blocking gaps:

1. **Data rights are unresolved.** The API reference does not link a service Terms of Use or a data licence. The official PyPI page explicitly distinguishes the SDK's MIT licence from rights to the football data, which are governed separately by PitchAPI terms. Those terms were not located in the official public documentation. Therefore internal ML use, inference, private raw-response retention, and provenance archiving are not approved.
2. **Six of the frozen 19 features are not documented.** The original V2 requires corners-for and corners-against over 5 and 10 matches plus both venue-5 corner features. The published reference mentions corners as a set piece but does not document a match-level corner-count key or endpoint field. It cannot be assumed that corners are available.
3. **Serie A coverage is unverified.** The API advertises 77 leagues but does not publish the league catalogue on the documentation page. The official docs' example league is the Premier League. No API call was made to enumerate leagues.
4. **Statistics are post-match.** Upcoming fixtures expose fixture identity and kickoff with null scores. Team statistics, events, shots and analytics belong to played matches. They could at most be lagged history for a later fixture; they do not provide pre-match statistics for the same match.
5. **Source-before-quote cannot yet be proven.** The docs provide response timestamps and a `fetched_at` field for the live endpoint, but no per-field upstream observation/correction timestamps or immutable source-artifact provenance. A local receipt timestamp and SHA could prove when this project possessed a response only after lawful retention is established; they cannot prove when upstream statistics were first observed.
6. **No odds endpoint is documented.** PitchAPI cannot replace the existing saved pre-match market source.

## Frozen V2 contract coverage

The candidate is unchanged:

- Candidate SHA-256: `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`
- 19 frozen features, in their original order.
- Weight matrix: 20×2.
- `active_lambda=0` remains the market.
- `shadow_lambda=1` remains research-only.
- Stability gate remains failed; automatic promotion remains disabled.

| Feature family | Documented candidate evidence | Decision |
|---|---|---|
| Points and goals (7 features) | Completed match summary exposes home/away scores; points can be derived from 3/1/0 | Candidate mapping only; exact normal-time and identity parity unverified |
| Corners (6 features) | No match-level corner-count key documented | **Missing — blocks full 19-feature parity** |
| Yellow cards (2 features) | Yellow-card events and one live `yellow_cards` example | Candidate mapping only; event/stat semantics and historical completeness unverified |
| Red cards (2 features) | Red-card events documented | Candidate mapping only; second-yellow mapping and historical completeness unverified |
| Venue-specific goals/corners (4 features) | Can only be derived from correctly identified historical home/away fixtures | Goals candidate only; corner features missing |

This is a documentation-level mapping, not a source-concordance test. No data were fetched and no feature was computed.

## Provenance and storage requirements

Before any future use, the provider must publish or confirm in writing:

- service/data terms granting internal research, model inference, private raw-response retention, and use of timestamp/SHA provenance;
- the upstream data source and any required third-party licences;
- per-field observation/correction timestamps or another defensible source-before-quote mechanism;
- a private raw archive/retention arrangement compatible with the rights;
- exact Serie A 2026/27 match coverage and completeness;
- a documented corner-count field and unambiguous red-card/second-yellow semantics.

Only after those gates are independently satisfied may a separate owner-authorized, low-volume read-only sample be considered. Any sample must be archived privately with raw-response SHA-256 and receipt time before a later bookmaker quote; then test team identity, kickoff, stat definitions, missingness and the unchanged 19-feature builder. No provider connection or API key is authorized by this audit.

## Official sources

- PitchAPI API reference: https://pitchapi.dev/
- PitchAPI Python SDK on PyPI: https://pypi.org/project/pitchapi/

The PyPI description states that the MIT licence covers the SDK source only and that access to the service and returned football data is governed separately by PitchAPI terms. No such official service terms/data licence were found in the public API reference during this audit.

## Explicit non-actions

No account, API key, endpoint call, data download, raw response, odds, Supabase read/write/DDL, protected result, feature build, inference, model refit, production `.pkl` change, paid API request, schedule change, promotion, or bet.
