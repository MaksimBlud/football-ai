# Schedule Load Signal Lab — Closure

Status: **CLOSED AS RESEARCH-ONLY / NO INCREMENTAL MARKET VALUE**

The preregistered `SCHEDULE_LOAD_SIGNAL_LAB_V1` experiment was frozen before outcome inspection and then executed once across EPL, La Liga, and Serie A using the already-established Football-Data historical source.

## Frozen signal

`SCHEDULE_V1` used only calendar information available before the current match: capped days since each team's previous completed match, completed-match counts in the prior 7 and 14 days, and home-away differences. The current match was snapshotted before being appended to team history; future fixtures, current-match statistics, and current-match outcomes were not used.

The model family and evaluation were fixed in advance: expanding-season walk-forward with at least three prior training seasons, median imputation, standard scaling, logistic regression, and the primary paired comparison `MARKET_SCHEDULE` versus `MARKET_MODEL` on multiclass Brier and log loss. No threshold search or post-result feature selection was permitted.

## Result

The frozen schedule signal failed the incremental-information test in all three leagues on aggregate metrics:

| League | Matches | Seasons | Δ Brier | Δ Log loss | Brier-win seasons | Log-loss-win seasons |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| EPL | 2660 | 7 | +0.002728 | +0.005058 | 1/7 | 1/7 |
| La Liga | 2660 | 7 | +0.002919 | +0.004742 | 2/7 | 2/7 |
| Serie A | 2659 | 7 | +0.001677 | +0.002764 | 1/7 | 1/7 |

Positive deltas mean `MARKET_SCHEDULE` was worse than the comparable fitted `MARKET_MODEL`. Schedule-only performance was also materially weaker than market-based models in every league.

## Decision

Do **not** add `SCHEDULE_V1` to the market model and do not tune rest-day caps, congestion windows, league-specific thresholds, or subsets on these already-seen outcomes. Such changes would be post-selection tuning on the same sample.

The signal family is retained only as a documented negative research result. A future schedule-related experiment would need to be a genuinely new preregistered hypothesis with independent information, such as verified travel distance, competition-specific load, or point-in-time future fixture congestion from a timestamp-safe schedule source; none is inferred from this closed experiment.

## Safety

The run changed no production `.pkl`, model, calibrator, threshold, inference path, Supabase row, market ledger, prediction ledger, or live selection logic. Production hashes were identical before and after the experiment.
