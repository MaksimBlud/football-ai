# SERIE_A_CORNERS_PROSPECTIVE_V1

Status: **PREREGISTERED / COLLECTING ONLY**

## Purpose

This is a prospective replication of the post-result Serie A diagnostic observed in `FREE_CORNERS_SIGNAL_SCREEN_V1`.

The prior pooled five-league screen was closed as `NO_CLEAR_SIGNAL_SCREEN`. Serie A was the strongest positive league-level diagnostic, but that observation was opened after the pooled result and is therefore a hypothesis only. It must not be treated as a confirmed edge.

This V1 asks one narrow question:

> On genuinely new Serie A matches, does the same leakage-safe corner-state model add information beyond Bet365 opening corner-total prices?

## Frozen start and cohort

- league: **Serie A only**
- provider league id: `3405541143`
- prospective cohort start: **2026-09-19T00:00:00Z**
- only fixtures with kickoff at or after the prospective start are eligible
- bookmaker: **Bet365**
- market: full-time corner total
- market stage: **opening**
- a market row is admissible only if it was captured by this prospective collector before kickoff
- existing V1 fixtures are never reused as confirmatory rows
- the confirmatory cohort is the **first 30 eligible finished fixtures by kickoff time**
- once the first 30 eligible rows are fixed, later fixtures cannot replace them

## Football model

The football side is frozen to the same construction used by `FREE_CORNERS_SIGNAL_SCREEN_V1`:

- historical source: free Football-Data corner counts
- historical seasons: 2016-17 through 2025-26
- current 2026-27 matches may contribute only if they occurred before the target fixture
- point-in-time rolling corner features:
  - home corners for last 10
  - home corners against last 10
  - away corners for last 10
  - away corners against last 10
  - home venue corners for last 5
  - home venue corners against last 5
  - away venue corners for last 5
  - away venue corners against last 5
- minimum prior matches per team: 10
- model: PoissonRegressor with the same preprocessing and hyperparameters as the frozen free screen
- no odds are used to fit the football model

No feature, window, model class, regularization value, or team-history rule may be changed after prospective collection starts.

## Market baseline and fixed blend

For each admissible fixture:

- de-vig Bet365 opening Over/Under prices to obtain `p_market`
- obtain `p_football` from the frozen Poisson corner model at the same bookmaker line
- fixed blend:
  - **75% market**
  - **25% football**

Integer-line pushes are excluded. Quarter lines and unsupported line types are excluded.

## Confirmatory sample gate

No confirmatory aggregate performance metrics are opened before **30 eligible finished rows** exist.

Before 30 eligible rows the only allowed status is:

`COLLECTING`

Allowed pre-gate operational information:
- number of captured future fixtures
- number finished
- number provisionally eligible/excluded
- exclusion reasons
- provider request counts
- data-quality failures

Brier, LogLoss, residual alignment, bootstrap intervals, per-row directional performance, ROI, and betting returns must not be reported before the gate.

## Frozen metrics

At exactly the first 30 eligible rows:

1. Bet365 market Brier
2. fixed blend Brier
3. Bet365 market LogLoss
4. fixed blend LogLoss
5. residual alignment:
   `mean((y - p_market) * (p_football - p_market))`
6. 90% bootstrap interval for residual alignment using the frozen seed and 10,000 resamples

Football-only metrics may be recorded as diagnostics, but they are not required for the confirmatory gate.

## Frozen verdict

### REPLICATED_SIGNAL_SCREEN

Only if all are true on the first 30 eligible rows:

- blend Brier < market Brier
- blend LogLoss < market LogLoss
- residual alignment > 0
- 90% bootstrap lower bound for residual alignment > 0

### INDICATIVE_NOT_CONFIRMED

If:

- blend improves both Brier and LogLoss
- residual alignment > 0
- but the 90% bootstrap interval still includes zero

### NOT_REPLICATED

If the first 30 eligible rows fail the conditions above.

### COLLECTING

Used until 30 eligible finished rows exist.

The gate must not be weakened, broadened, retuned, or rerun with a different blend after results are opened.

## Collection policy

- free plan only
- no paid subscription
- maximum **20 provider HTTP attempts per scheduled run**
- minimum pacing **3.1 seconds** between provider requests
- collect scheduled Serie A fixtures up to 14 days ahead
- require at least 6 hours between capture time and kickoff
- opening market values become immutable once first captured
- finished result fields may be appended later
- no in-play prices are used
- no closing price is used as a model feature or confirmatory baseline
- rolling ledger is stored as GitHub Actions research artifacts
- no Supabase writes
- no The Odds API spend
- no production model writes

## Safety

- research-only
- `NO_BET`
- no production promotion
- no production `.pkl` changes
- no automatic betting or staking
- no paid data access

## Relationship to earlier work

The earlier result remains unchanged:

`FREE_CORNERS_SIGNAL_SCREEN_V1 = NO_CLEAR_SIGNAL_SCREEN`

This prospective experiment does not reopen or retune that experiment. It only tests whether the Serie A diagnostic replicates on new matches.
