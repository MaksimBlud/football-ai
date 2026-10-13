# EPL_POISSON_MARKET_BLEND_V1 — completed dated historical replay

Status: **REJECTED FOR PROMOTION / RESEARCH ONLY**. Date: 2026-10-13.

## Hypothesis

Could a lightweight *independent-Poisson goals model*, with fixed optional
Dixon–Coles correction for 0-0/1-0/0-1/1-1 and a small blend into the
bookmaker no-vig three-way probability, improve multi-class Brier **and**
log loss versus bookmaker no-vig probabilities?

No: the historical 2019/20 validation-selected candidate lost on both metrics
in subsequent 2020/21–2021/22 history. This result does **not** establish
that the current XGBoost product model is calibrated or profitable. The
fallback equals the market exactly because it **IS the market**, NOT an AI
prediction. It must never appear on the website as an AI forecast or be
automatically promoted.

## Data and chronology

Read-only `public.matches` from live Supabase, `league='EPL'`,
`2016-08-01 <= match_date < 2022-08-01`. **2,280 completed** old-season
fixtures, including 2016/17–2018/19 used solely as unpriced historical
form/goals context. **1,140** matches with complete three-way prices from
2019/20–2021/22.

Unlike a random train/test split, *all matches on the same date* share
a frozen as-of-prior-day team and league state. Outcomes of the same date
are added to the context only after all that day's probabilities have
been constructed, including when kick-off hour is unknown.

League goal priors are sequential: smoothed home/away goal rate based
on previous completed matches only, 150 pseudo-fixtures (home 1.5 and
away 1.1 goals), minimum base rate 0.5. Each team's prior **home** scoring
and conceding records and opponent's prior **away** records produce
expected-goal rates with smoothing and caps 0.15–4.5.

Dixon–Coles low-score correction uses the standard tau rules at
0-0/0-1/1-0/1-1, score grid 0..10 goals and normalization. No candidate
is fit using any future outcome. Fixed candidates:

- team rate smoothing pseudo-games: `{5,12,25}`;
- DC low-score rho: `{-0.08,0,+0.08}`;
- blend weight from Poisson into no-vig bookmaker probability:
  `{0.1,0.25,0.4,0.6}`.

This is **36 total predefined alternatives**. Rank by 2019/20 validation
log loss (then Brier and parameter values) **only among** alternatives
that improved *both* Brier and log loss over no-vig bookie probabilities
on those same 380 fixtures. The subsequent 760 historical matches
(2020/21–2021/22) are not used to retune parameters.

**Important limitation:** The 2020/21–2021/22 years have already appeared
as model-training data in previous research, and bookmaker observations
in `matches` have **no timestamped pre-kickoff quote provenance**.
This is a **forward historical sensitivity replay**, not pristine untouched
or prospective evidence. Do not claim CLV, ROI, bookmaker exploitation,
or tradable probabilities.

## Result

| Period and metric | Margin-free bookmaker baseline | Fixed validation-selected goal blend |
|---|---:|---:|
| 2019/20 (380) — Brier | 0.575034 | **0.572696** |
| 2019/20 (380) — Log loss | 0.972590 | **0.967385** |
| 2019/20 (380) — accuracy | 53.16% | **53.95%** |
| Later 2020/21–2021/22 (760) — Brier | **0.575253** | 0.577015 |
| Later 2020/21–2021/22 (760) — Log loss | **0.970092** | 0.972675 |
| Later 2020/21–2021/22 (760) — accuracy | **54.74%** | 53.82% |

Frozen validation-selected parameters:

- goal-rate smoothing **5** pseudo-fixtures;
- **rho = 0** (the low-score Dixon–Coles modification wasn't selected);
- Poisson probability contribution **40%**, market no-vig 60%.

Later 760-match Brier worsened by **+0.001762**; log loss worsened by
**+0.002583**. Therefore **FAILED_FORWARD_HISTORICAL_EVAL**.

This is the third failed improvement family after the price temperature
and multinomial market residual experiments documented in
[EPL_MARKET_FLOOR_V1_20261012.md](EPL_MARKET_FLOOR_V1_20261012.md).
An in-sample or single-season improvement is not sufficient.

## Reproducible research artifact

```bash
python epl_poisson_market_blend_v1.py --read-only-historical-supabase
python -m pytest -q tests/test_epl_poisson_market_blend_v1.py
```

Read-only Supabase with existing credentials; it does not call the
paid The Odds API, write SQL, mutate `.pkl`, use frozen prospective outcomes,
alter production algorithms, or publish a model.
The report includes exactly the selected parameters, reference metrics,
failed later comparison, and `market_fallback_is_ai: false` in a
machine-readable fail-closed JSON.

## Decision

**NO_GO: GOAL_BLEND_DID_NOT_MATCH_MARKET_FORWARD.**

No new production inference and no automatic promotion. To achieve a
genuine independent market-beating model, first freeze an architecture
and a **new, not previously inspected** prospective observation period.
Use the existing Odds API budget and authorization rules, consistent
timestamped pre-kickoff model/market pairs, and separately authorized
event settlement. Require Brier, log loss and uncertainty comparison
with a true same-time market reference, not just top-pick accuracy.
Existing product gate (>=100 settled, >=4 months) and all frozen research
eval gates are unchanged.
