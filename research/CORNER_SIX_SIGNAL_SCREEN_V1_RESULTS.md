# CORNER SIX SIGNAL SCREEN V1 — Results

Status: **FINAL RETROSPECTIVE SCREEN / 1 OF 6 PROMISING / NO_BET**

## Provenance

Authoritative workflow run:

`37179398571`

Authoritative result artifact:

- ID `11294063833`;
- digest `sha256:92b958e6f5f8c911236f5e6451ed2f974d4e02af727637644dc2ad037cd78aa0`;
- generating head `485f2c31cde8ec1adf1e79af2fc3ad5cbcaf6a87`.

Corner-market evidence:

- V1_55 = 55 fixtures;
- REP50 = 50;
- V1_46 = 46;
- V2B_43 = 43;
- total = **194 unique fixtures**.

These 2026/27 movement cohorts were already opened in earlier research. Therefore the
six-signal block is a **retrospective hypothesis screen**, not independent confirmation.

No new prospective match was collected.

No paid Odds API request, Supabase write, production model operation or production
promotion occurred.

---

## 1. Opening price pressure

Frozen feature:

`de-vig opening Over probability - 0.50`

Hypothesis:

- positive pressure -> UP;
- negative pressure -> DOWN.

### Pooled result

Direction-comparable rows:

**73**

Observed direction:

- UP = 58;
- DOWN = 15.

Signal:

- raw accuracy = **41.10%**;
- majority-direction baseline = **79.45%**;
- excess vs majority = **-38.36 pp**;
- UP recall = **39.66%**;
- DOWN recall = **46.67%**;
- balanced accuracy = **43.16%**;
- Pearson vs centre_delta = **-0.0924**;
- Spearman = **-0.1101**.

Positive Spearman cohorts:

**1 / 4**

By cohort balanced accuracy:

- REP50 = 25.00%;
- V1_46 = 33.64%;
- V1_55 = 58.33%;
- V2B_43 = 22.22%.

### Verdict

**`NO_PORTABLE_OPENING_PRICE_PRESSURE_DIRECTION_SIGNAL`**

Opening Over/Under price imbalance does not provide a portable direction signal in these
saved cohorts.

Do not reverse the sign after seeing this result.

---

## 2. Line-transition mechanics

Two frozen questions were tested:

1. does price-pressure sign predict the sign of an actual quoted line step?
2. does absolute price pressure predict whether the quoted line will move at all?

### Direction among actual line steps

Comparable non-zero line steps:

**51**

Observed:

- UP = 41;
- DOWN = 10.

Results:

- raw accuracy = **56.86%**;
- majority-direction baseline = **80.39%**;
- excess vs majority = **-23.53 pp**;
- balanced accuracy = **58.05%**;
- Pearson = **+0.2891**;
- Spearman = **+0.3121**.

The pooled directional diagnostic is mildly positive, but it is not portable:

- only **2/4** cohorts had balanced accuracy above 0.50;
- V2B_43 balanced accuracy = **35.00%**;
- V2B_43 Spearman = **-0.4786**.

### Does pressure predict whether the line moves?

Across all 194 fixtures:

- line moves = 54;
- ROC AUC of absolute pressure = **0.4792**;
- mean absolute pressure when line moved = **0.017666**;
- mean absolute pressure when stable = **0.017716**.

AUC above 0.50:

**2 / 4 cohorts**

### Verdict

**`NO_LINE_TRANSITION_MECHANICS_SIGNAL`**

The apparent pooled relationship for step direction does not survive the required
cross-cohort portability check, and pressure magnitude does not distinguish moving from
stable lines.

---

## 3. Cross-market match shape

This was the only family to pass its frozen screen.

### Construction

No corner history was used to generate the primary signal.

For EPL, La Liga and Serie A, a simple league-specific historical model used Bet365
opening:

- 1X2 no-vig probabilities;
- O/U 2.5 no-vig Over probability;
- Asian Handicap line;
- no-vig AH home probability.

Model:

`SimpleImputer(median) + StandardScaler + Ridge(alpha=1.0)`

Training:

2019/20–2024/25.

Untuned historical validation:

2025/26.

Target:

actual match total corners.

The model was required to beat the league historical mean before it was allowed to be
used as a corner-market direction hypothesis.

### Historical 2025/26 validation

EPL:

- baseline MAE = **2.66714**;
- match-shape MAE = **2.64341**;
- improvement = **0.02373**.

La Liga:

- baseline MAE = **2.73483**;
- match-shape MAE = **2.70340**;
- improvement = **0.03144**.

Serie A:

- baseline MAE = **2.65243**;
- match-shape MAE = **2.56037**;
- improvement = **0.09206**.

Historical MAE wins:

**3 / 3 leagues**

The model was then refit through 2025/26.

Frozen feature on the existing 2026/27 corner cohorts:

`match_shape_gap = expected corners from 1X2/O-U/AH - opening corner FAIR_CENTRE`

Hypothesis:

- positive gap -> corner market should reprice UP;
- negative gap -> DOWN.

### Existing corner-cohort screen

Usable corner-market rows:

**117**

Direction-comparable non-zero movement rows:

**56**

Observed:

- UP = 45;
- DOWN = 11.

Pooled:

- raw accuracy = **78.57%**;
- majority-UP baseline = **80.36%**;
- raw excess vs majority = **-1.79 pp**;
- UP recall = **86.67%**;
- DOWN recall = **45.45%**;
- balanced accuracy = **66.06%**;
- Pearson score vs centre_delta = **+0.6815**;
- Spearman = **+0.6239**.

Spearman was positive in:

**4 / 4 cohorts**

By cohort:

### V1_55

- comparable = 20;
- balanced accuracy = **71.43%**;
- Pearson = **+0.7154**;
- Spearman = **+0.7206**.

### REP50

- comparable = 14;
- balanced accuracy = **96.15%**;
- Pearson = **+0.9133**;
- Spearman = **+0.8418**.

Important: only one DOWN occurred in this subset, so the very high balanced diagnostic
must not be overinterpreted.

### V1_46

- comparable = 14;
- balanced accuracy = **62.50%**;
- Pearson = **+0.6208**;
- Spearman = **+0.5171**.

### V2B_43

- comparable = 8;
- balanced accuracy = **41.67%**;
- Pearson = **+0.6147**;
- Spearman = **+0.5476**;
- DOWN recall = **0%**;
- UP recall = **83.33%**.

### Frozen screen verdict

**`PROMISING_CROSS_MARKET_CORNER_DIRECTION_SIGNAL`**

### Critical interpretation

This is **not** a confirmed direction edge.

Reasons:

1. the 2026/27 corner movement cohorts were already opened in previous research;
2. the pooled raw hit rate still does not beat always-UP because the period is strongly
   UP-skewed;
3. DOWN discrimination remains weak, especially in V2B;
4. the strong feature/centre_delta rank association is the interesting part, not a claim
   of 78.6% betting accuracy.

What is genuinely encouraging is that:

- the match-shape model first improved held-out 2025/26 numerical corner MAE in all three
  historical leagues;
- the frozen gap then had positive centre-delta Spearman in all four saved corner cohorts;
- pooled Spearman was materially positive.

This family deserves preservation as a hypothesis for a later untouched replication.
It must not be retuned on these opened samples.

---

## 4. Referee corner effect

Frozen historical signal:

`n/(n+20) * (referee mean total corners - league mean)`.

Before any direction interpretation it had to improve 2025/26 corner prediction versus
the league mean.

### Historical validation

EPL:

- league-mean MAE = **2.66706**;
- referee model MAE = **2.67471**;
- delta = **+0.00764** — worse.

La Liga:

- referee field absent in the source.

Serie A:

- referee field absent in the source.

Historical MAE wins:

**0 / 1 evaluable league**, with the other two source-gapped.

The later direction diagnostic therefore cannot rescue the signal.

Saved-cohort direction diagnostic:

- comparable rows = 15;
- balanced accuracy = **65.0%**;
- Spearman = **+0.0504**;
- positive Spearman cohorts = **1/4**.

### Verdict

**`NO_PORTABLE_REFEREE_CORNER_SIGNAL`**

The available historical source does not support a useful portable referee signal.

Do not use the small direction diagnostic to override the failed historical/source gate.

---

## 5. Corner-environment volatility

This deliberately tested instability rather than another CORNERS10 mean.

Feature:

- previous 10 top-flight matches per team;
- standard deviation of total-match corner environment;
- fixture volatility = mean of home and away SD10.

Target:

material corner-market repricing using the already-frozen threshold
`0.362835012901983`.

Baseline:

FAIR_CENTRE only.

Candidate:

FAIR_CENTRE + volatility.

Evaluation:

four leave-one-corner-cohort-out folds.

Eligible rows:

**84**

### Continuous diagnostic

Volatility vs movement magnitude:

- Pearson = **-0.0077**;
- Spearman = **-0.0122**.

Essentially zero.

### Held-out fold results

Candidate Brier wins:

**0 / 4**

Candidate LogLoss wins:

**0 / 4**

Every held-out cohort got worse.

Pooled:

- baseline Brier = **0.19235**;
- candidate Brier = **0.19783**;
- delta = **+0.00548** — worse;
- baseline LogLoss = **0.58466**;
- candidate LogLoss = **0.59690**;
- delta = **+0.01224** — worse.

### Verdict

**`NO_INCREMENTAL_VOLATILITY_REPRICING_SIGNAL`**

Variance/instability adds no useful information over FAIR_CENTRE in this screen.

Do not search alternative SD windows or replace the frozen feature with skew after seeing
this result.

---

## 6. Coach / tactics / lineup / availability regime changes

This family was treated as a source-capability question rather than fabricating a proxy.

Existing Football-Data schema:

- EPL columns inspected = 178;
- La Liga = 177;
- Serie A = 177.

Explicit manager/coach/lineup/starting-XI/injury/suspension fields detected:

**none**

Existing project constraints also remain binding:

- historical lineup-strength capability = DATA_GAP unless explicit fields exist;
- prospective availability implementation exists but is externally gated;
- retrospective injury reconstruction from later start/end dates is not permitted.

### Verdict

**`EXISTING_SOURCE_DATA_GAP_FOR_REGIME_CHANGE_SIGNAL`**

This is not evidence that manager changes, lineups or injuries are useless.

It means the existing historical source cannot test them honestly without introducing a
new source or leakage.

---

# Overall decision

Exactly one of the six frozen screens passed:

**3. CROSS-MARKET MATCH SHAPE — PROMISING**

The other five:

1. opening price pressure — **closed negative**;
2. line-transition mechanics — **closed negative**;
4. referee — **closed negative / inadequate portable source**;
5. volatility — **closed negative**;
6. regime changes — **not testable from existing source, data gap**.

The promising cross-market result remains **hypothesis-generating only** because its
corner movement samples are already-opened research cohorts.

Do not:

- claim 78.57% betting accuracy;
- tune its coefficients or threshold on these 2026/27 movements;
- select only V1_55/REP50/V1_46 and drop V2B;
- alter the direction sign;
- fit league-specific corner-direction thresholds;
- promote to production;
- enable betting.

## Safety

- research-only;
- NO_BET;
- new prospective matches collected = false;
- paid Odds API requests = 0;
- Supabase writes = 0;
- production model operations = 0;
- production .pkl hashes unchanged.
