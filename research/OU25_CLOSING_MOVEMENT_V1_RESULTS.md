# OU25_CLOSING_MOVEMENT_V1_RESULTS

## Frozen outcome

Decision: **SKIP**.

The preregistered football-state model did not beat the opening-price no-movement baseline on both required metrics in any league. League PASS count: **0/3**. `NO_BET` remains binding.

This result is from GitHub Actions run `35226803461`, artifact `10500025570`, digest `sha256:24a1d9744984ba32cb8d359dd3dc990b4a6170610c6d901a7beae22999a44d10`, executed on PR #365 head `8972fd3f67bd0927664ee4cdbf8a5e3653ce1a50` and merged by `a8bdf7859a5b7d08c3710d531b79897057fbf814`.

## League results

### EPL

Validation:
- baseline RMSE: `0.0283578979`
- candidate RMSE: `0.0280612990` (better)
- baseline MAE: `0.0220921867`
- candidate MAE: `0.0225151216` (worse)
- validation admissible: **false**

Untouched 2025-26 raw candidate diagnostic:
- baseline RMSE: `0.0296506222`
- candidate RMSE: `0.0299365221` (worse)
- baseline MAE: `0.0226878191`
- candidate MAE: `0.0236611137` (worse)
- movement-direction accuracy: `0.5034` on 294 non-zero movements
- status: **FAIL / NO_MOVEMENT_FALLBACK**

### La Liga

Validation:
- baseline RMSE: `0.0328842020`
- candidate RMSE: `0.0320848436` (better)
- baseline MAE: `0.0250057425`
- candidate MAE: `0.0250423556` (slightly worse)
- validation admissible: **false**

Untouched 2025-26 raw candidate diagnostic:
- baseline RMSE: `0.0328547079`
- candidate RMSE: `0.0329495361` (worse)
- baseline MAE: `0.0249089766`
- candidate MAE: `0.0256795218` (worse)
- movement-direction accuracy: `0.5436` on 298 non-zero movements
- status: **FAIL / NO_MOVEMENT_FALLBACK**

### Serie A

Validation:
- baseline RMSE: `0.0311089206`
- candidate RMSE: `0.0307824287` (better)
- baseline MAE: `0.0233234750`
- candidate MAE: `0.0237569290` (worse)
- validation admissible: **false**

Untouched 2025-26 raw candidate diagnostic:
- baseline RMSE: `0.0323162171`
- candidate RMSE: `0.0321548032` (slightly better)
- baseline MAE: `0.0245474841`
- candidate MAE: `0.0254227228` (worse)
- movement-direction accuracy: `0.5563` on 302 non-zero movements
- status: **FAIL / NO_MOVEMENT_FALLBACK**

## Pooled selected result

Because no league passed the frozen validation gate, selected OOT predictions are the exact no-movement opening baseline in all three leagues.

- pooled OOT n: `1140`
- league PASS count: `0/3`
- pooled baseline RMSE: `0.0316382106`
- pooled selected RMSE: `0.0316382106`
- pooled baseline MAE: `0.0240480933`
- pooled selected MAE: `0.0240480933`
- decision: **SKIP**

## Coverage note

The contract allowed train seasons `2016-17` through `2023-24`, but the resulting same-provider paired opening/closing eligible sample begins in `2019-20`. Earlier planned train seasons contributed zero eligible paired rows. Effective train coverage was therefore five seasons (`2019-20` through `2023-24`): EPL `1900`, La Liga `1900`, Serie A `1898` train rows. Validation and OOT each had 380 rows per league.

Price-source coverage was overwhelmingly Bet365: EPL `2659` Bet365 + `1` Pinnacle; La Liga `2660` Bet365; Serie A `2656` Bet365 + `1` Pinnacle + `1` Average.

## Interpretation

The tested football-state construction does **not** justify predicting O/U 2.5 closing probability movement beyond simply carrying the opening probability forward.

There is a weak direction-only diagnostic in La Liga and Serie A (~54-56%), but it did not satisfy the preregistered RMSE+MAE gate and must not be promoted or retuned against the opened 2025-26 OOT sample.

This does not prove that all market-movement signals are impossible. It closes this exact V1 construction: fixed O/U 2.5, these leakage-safe football-state features, fixed Ridge(alpha=1.0), this same-provider priority, and this temporal split.

## Safety / binding decision

- research-only;
- `NO_BET`;
- no production promotion;
- no production `.pkl` changes;
- no Supabase writes;
- no paid Odds API requests;
- no 2026-27 data used;
- do not retune V1 against the opened OOT result.
