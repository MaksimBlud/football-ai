# V2B CORNER MARKET-PATH SOURCE AUDIT V1 — Results

Status: **FINAL SOURCE AUDIT / NO_TIME_ALIGNED_PATH_SOURCE / NO DIRECTION TEST**

## Provenance

Workflow run:

`37025543210`

Authoritative audit artifact:

- ID `11234538332`;
- digest `sha256:7b7be3476112b6f1cb2811d5d249c9cfb3f8bebc72c2752f47b533e07e4461d8`;
- generating head `61f78423fd92b85d12d4bd488d98ccb94f1c6cec`.

Immutable V2B raw source:

- artifact ID `10899611444`;
- digest `sha256:c2f5313efad4afb8663d9980f5ea004f52fe02827a83b5c99a8b775c35498a57`;
- raw fixture payloads = **43**.

No provider request, outcome read, direction statistic or opening-to-closing delta was
performed by this audit.

## Structural result

Raw fixtures:

**43 / 43**

Fixtures with `corner_line`:

**43 / 43**

Bookmaker count distribution:

- exactly 1 bookmaker = **43 / 43**;
- multiple bookmakers = **0 / 43**.

Bookmaker identity:

- Bet365 = **43 / 43**.

Named corner states:

- `opening` = **43 / 43**;
- `closing` = **43 / 43**;
- `inplay` = **43 / 43**.

Temporal/path structure:

- fixtures with any timestamp/date/update field = **0 / 43**;
- fixtures with any history/snapshot/timeline/sequence field = **0 / 43**;
- discovered timestamp field paths = **none**;
- discovered history field paths = **none**.

## Source verdict

`NO_TIME_ALIGNED_PATH_SOURCE`

The already-paid V2B artifact does not contain repeated timestamped corner-market
observations.

Therefore it cannot support honest features such as:

- pre-move slope;
- speed of movement;
- acceleration;
- number of pre-move revisions;
- path volatility;
- time since last change;
- lead/lag among bookmakers.

The named `opening`, `closing`, and `inplay` values are endpoint labels, not a
timestamped path.

## Why closing/inplay cannot repair the gap

For a Stage-B feature intended to predict later movement, the input must be known at the
frozen decision time.

Without observation timestamps:

- `closing` is later/future information relative to an early decision;
- `inplay` is post-kickoff information;
- neither can be re-labelled as an early trajectory point.

Using them that way would create leakage.

## Cross-book implication

Cross-book microstructure is also unavailable in this artifact because every fixture
contains exactly one bookmaker.

Therefore this raw source cannot provide:

- bookmaker dispersion;
- consensus-vs-outlier position;
- bookmaker lead/lag;
- stale-book detection.

## Relationship to existing prospective market-path work

The repository already contains `PROSPECTIVE_MARKET_PATH_V1`, but that frozen protocol
uses timestamped **1X2** snapshots and tests outcome prediction. It is not a corner-market
path dataset and its frozen feature contract must not be expanded post hoc.

## Next permitted direction

Do not buy or re-request the same 43 V2B fixture endpoint payloads.

If corner-path research is continued, it requires a genuinely new prospective source that
stores repeated timestamped corner observations **before** the evaluation target is
opened.

A future source-feasibility block should first determine whether current multi-market
corner collection can persist:

1. fixture/event identity;
2. observation timestamp;
3. corner line;
4. over/under prices;
5. bookmaker identity;
6. at least three pre-kickoff observations per fixture across a meaningful time span.

No directional formula should be defined until such prospective path coverage exists.

## Safety

- research-only;
- NO_BET;
- market direction evaluated = false;
- opening/closing delta computed = false;
- outcomes read = false;
- Odds API requests = 0;
- Supabase operations = 0;
- production model operations = 0;
- production `.pkl` hashes unchanged.
