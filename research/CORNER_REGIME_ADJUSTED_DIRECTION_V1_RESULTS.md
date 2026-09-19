# CORNER_REGIME_ADJUSTED_DIRECTION_V1_RESULTS

Status: **SAMPLE_TOO_SMALL / FROZEN THIRD-SAMPLE RESULT / RESEARCH ONLY**

## Provenance

- implementation PR: #387;
- final tested PR head before this result record: `8c7f163567f9f1c24dd69f916d896f6ec3acb32c`;
- initial full live run: `35361459609`;
- initial live artifact: `10557603810`;
- initial live artifact digest: `sha256:5530abd643fa4bac1c6ca25609bd9979dd3e0e90ce1c05601d234aca807e406b`;
- same-sample resume run: `35369631434`;
- final immutable result artifact: `10557706131`;
- final artifact digest: `sha256:5ff43199cdf1bb73e6b87649c3e68aa57bac628c68888a06a809c5df473b8d1f`;
- production `.pkl` hash guards: PASS before/after both bounded live execution and final resume;
- paid subscription used: **false**;
- match outcomes used: **false**;
- football-state/CORNERS10 used: **false**.

## Frozen question

After the prior fresh 50-row replication showed a broad market-wide upward regime, V1 asked a stricter question:

> within the same league and UTC kickoff date, does lower opening `FAIR_CENTRE` identify the individual corner market whose reconstructed Bet365 centre subsequently moves farther upward relative to its contemporaneous peers?

The only primary score remained:

`direction_score = -opening_lambda`

The primary statistic remained within-regime unordered pairwise concordance.

Frozen confirmation requirements:

- at least 30 eligible rows;
- at least 4 leagues with a comparable pair;
- at least 8 contributing regime blocks;
- at least 40 comparable pairs;
- observed concordance >= 0.60;
- one-sided regime-preserving permutation p < 0.10.

The permutation test was frozen at 20,000 permutations with seed `20260918`.

## Frozen third sample

The final immutable selected cohort contains **46 previously unused fixtures**:

- EPL: 10;
- La Liga: 10;
- Serie A: 10;
- Bundesliga: 6;
- Ligue 1: 10.

All 46 produced eligible normalized Bet365 corner opening+closing market rows.

The reduced Bundesliga count was a metadata-only amendment frozen before any third-sample odds were opened: the provider Free inventory contained only six unseen Bundesliga fixtures after excluding the original 55 discovery rows and prior 50 replication rows.

No cross-league backfill was allowed.

## Timeout and immutable same-sample resume

Run `35361459609` froze all 46 selected fixture IDs before odds acquisition, preserved 17 successful raw odds responses, then hit the preregistered 75-minute GitHub Actions timeout while waiting on the provider rate-limit path.

No aggregate `report.json` or statistical verdict had been produced at timeout.

Because closing data were then partially opened, the sample identity became immutable. The only allowed continuation was an acquisition-only resume:

- reuse the exact 46 selected IDs;
- reuse all 17 raw odds responses from artifact `10557603810`;
- perform no fixture-list/discovery request;
- request only the 29 missing fixture odds;
- make no feature, sign, regime, sample-gate, concordance or p-value change.

Regression tests were added to enforce this behavior before the resume was authorized.

Run `35369631434` completed that exact same-sample resume successfully.

Final acquisition report:

- `acquisition_mode = IMMUTABLE_SAME_SAMPLE_RESUME`;
- selected fixtures = 46;
- reused raw odds responses = 17;
- missing odds files at resume start = 29;
- provider requests in resume = 29;
- final eligible rows = 46.

## Frozen result

Sample-gate components:

- eligible rows = **46** — PASS vs minimum 30;
- contributing leagues = **5** — PASS vs minimum 4;
- contributing regime blocks = **9** — PASS vs minimum 8;
- comparable within-regime pairs = **30** — **FAIL** vs minimum 40.

Therefore the binding frozen verdict is:

**`SAMPLE_TOO_SMALL`**

Because the sample gate failed, the contract correctly did **not** compute the 20,000-permutation p-value:

- `permutation_pvalue = null`;
- `direction_discrimination_confirmed = false`.

No lower pair-count threshold may be substituted after seeing this sample.

## Diagnostic-only effect size

Although it cannot be used for confirmation because the sample gate failed:

- concordant pairs = **21**;
- comparable pairs = **30**;
- observed concordance = **0.70**.

By league:

- EPL: 4/11 = **0.3636**;
- La Liga: 4/6 = **0.6667**;
- Serie A: 5/5 = **1.00**;
- Bundesliga: 4/4 = **1.00**;
- Ligue 1: 4/4 = **1.00**.

These values are diagnostics only. In particular, the high pooled 0.70 cannot be called statistically confirmed because the preregistered minimum comparable-pair gate was not met and no frozen permutation p-value was opened.

## Movement-regime diagnostics

Across all 46 eligible rows:

- positive `centre_delta`: **13**;
- negative: **5**;
- zero: **28**;
- positive share among non-zero moves: **0.7222**.

This is materially less one-sided than the preceding 50-row fresh replication, where non-zero movement was 20 up / 1 down. The regime-adjusted design therefore did observe a less extreme broad directional environment, but the available same-day pair structure was insufficient for the preregistered confirmation gate.

Top-minus-bottom direction-score regime-adjusted mean diagnostic:

`+0.1252142136`

Again this is descriptive only and does not override the primary sample gate.

## Interpretation

Supported:

1. The previously replicated **repricing magnitude/risk** result remains intact: opening `FAIR_CENTRE` contains out-of-sample information about whether the corner market will later be materially repriced.
2. In this third sample, the frozen direction ordering had a descriptive pooled concordance of 0.70 after comparing only matches inside the same league-day regime.
3. The third sample did **not** contain enough comparable within-regime pairs to run the preregistered confirmation test.

Not supported:

- no claim that individual direction discrimination replicated;
- no claim that it failed statistically;
- no p-value may be imputed or approximated post hoc;
- no weakening of the 40-pair gate;
- no betting, ROI, staking or production claim.

The correct status is **inconclusive because the preregistered sample gate was not reached**, not a positive confirmation and not a negative statistical rejection.

## Binding next step

Do not retune or reuse this 46-row third sample for threshold/sign selection.

If direction work continues, it must use a separately frozen future-data continuation that preserves the core regime-adjusted question and obtains enough new untouched contemporaneous blocks to satisfy its declared sample requirement before confirmation metrics are interpreted.

The already-replicated repricing-magnitude signal must remain separate from this unresolved direction question.

## Safety

- research-only;
- `NO_BET`;
- no production promotion;
- no production `.pkl` changes;
- no Supabase writes;
- no paid subscription;
- no match outcomes;
- no CORNERS10/football-state inputs;
- no post-result retuning;
- no further V1 provider run is authorized.
