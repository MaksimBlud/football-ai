# Corner Market Source Audit — 2026-09-08

## Scope

This is a research-only source audit for bookmaker corner lines after the preregistered The Odds API capability probe returned a clean negative result.

No production model promotion, Supabase writes, prospective outcome reads, or automatic paid-provider action are authorized by this document.

## The Odds API capability result — CLOSED / NEGATIVE

Manual GitHub Actions run `34246732050` (`Multi-Market Corner Capability Probe`) executed against the exact preregistered target:

- league: `BUNDESLIGA`;
- event: Union Berlin vs FC Schalke 04;
- kickoff: `2026-09-11T18:30:00Z`;
- event_id: `115c6679a72c5a360640b6baaa16e78c`.

Observed contract result:

- status: `CAPABILITY_MISS`;
- provider request attempted: `true`;
- paid provider requests: `1`;
- paid provider credits: `0`;
- quota before: remaining `193`, used `307`, last_cost `0`;
- quota after: remaining `193`, used `307`, last_cost `0`;
- corner market keys: `[]`;
- corner bookmaker count: `0`;
- writes performed: `false`;
- production model hash unchanged.

Artifact:

- id: `10064303200`;
- ZIP SHA256: `5a7de8b02e1b82a29dc71c2a8a94c6154a2485bbaa32dd30d8bd6d0ef78a0cfa`.

Decision: do not repeat the same The Odds API corner probe against the same target. This is sufficient negative capability proof for that provider/target combination.

## Zero-cost alternative-source audit

### 1. Sportmonks — PRIMARY NEXT CANDIDATE

Official Sportmonks documentation exposes a bookmaker market catalog containing:

- market id `69`;
- name `Alternative Corners`;
- developer_name `ALTERNATIVE_CORNERS`.

Official pre-match odds endpoints support fixture-scoped and fixture+market-scoped retrieval, so the provider has the API shape required for durable point-in-time corner line/price collection.

Sportmonks also offers a no-card, no-expiry free token. The forever-free football coverage is limited to the Danish Superliga and Scottish Premiership. That is still sufficient for a **free capability proof of schema + bookmaker corner market availability**, but it is not sufficient by itself to activate the existing top-league prospective research.

Decision:

- use the free plan only for capability proof;
- do not purchase a Sportmonks plan automatically;
- do not treat Scottish/Danish proof as evidence that Bundesliga/EPL/La Liga/Serie A corner coverage is commercially available at the required depth;
- any paid coverage expansion remains a separate explicit decision after a successful free capability proof.

Official references used in this audit:

- `https://docs.sportmonks.com/v3/tutorials-and-guides/tutorials/odds-and-predictions/markets`
- `https://docs.sportmonks.com/v3/tutorials-and-guides/tutorials/odds-and-predictions/pre-match-odds`
- `https://www.sportmonks.com/football-api/free-plan/`

### 2. OpticOdds — SECONDARY CANDIDATE

Official OpticOdds documentation exposes a general `/markets` discovery endpoint and extensive soccer corner statistics (`team_total_corners`, first-half and second-half team corners). It therefore has potentially useful data depth.

However, this zero-cost documentation audit did not yet produce equally direct proof of a currently offered bookmaker **corner odds market** plus a self-serve free credential path. Keep OpticOdds as a secondary candidate rather than assuming capability from statistics alone.

Official references:

- `https://developer.opticodds.com/reference/get_markets`
- `https://developer.opticodds.com/docs/statistics-api-guide`

### 3. Direct sportsbook-page scraping — REJECT FOR NOW

Do not build the research contract around scraping dynamically rendered bookmaker pages at this stage. It has materially weaker guarantees for:

- fixture identity;
- timestamp provenance;
- stable market naming;
- reproducibility;
- long-term maintenance;
- access/terms stability.

A stable documented API is preferred before considering scraping.

## Next implementation gate

The next safe implementation step is a **Sportmonks free-plan capability probe**, separate from The Odds API and separate from the frozen prospective experiments.

Required contract:

1. research-only;
2. token supplied through a secret/environment variable, never committed;
3. no purchase/subscription change;
4. start with Scottish Premiership or Danish Superliga free coverage;
5. discover and preregister one exact future fixture identity before probing its corner market;
6. query only the documented corner market path (`Alternative Corners`, id `69`) plus only the minimum fixture discovery needed;
7. no Supabase writes;
8. no production `.pkl` changes;
9. durable JSON artifact records fixture identity, market id, bookmaker ids/names, line/label/price fields, request counts, and errors;
10. capability confirmation requires at least one actual bookmaker corner line/price, not merely a corner statistic or market catalog entry.

If free capability is confirmed, the following step is a separate coverage/cost audit for leagues relevant to the existing research. If free capability misses, record the negative proof and move to the next documented provider; do not resume historical corner V1–V4 feature mining.
