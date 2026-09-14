# REPLAY_DIAGNOSTIC_V1

Status: **FROZEN OUTCOME-FREE ELIGIBILITY CONTRACT**

This contract was written before reading any settlement outcome values for this diagnostic. It is deliberately separate from `ALL_LEAGUES_MARKET_ONLY_V1_1` and from the already-frozen `EPL_AI_MARKET_PAIR_V1` prospective experiment.

## Question

Can any of the manually captured current-round multi-league `MARKET_ONLY` fixtures be honestly reconstructed as point-in-time Football-AI predictions using only model/code/history information that was fixed before kickoff?

If not, the diagnostic must fail closed rather than manufacture AI sample size retrospectively.

## Source state

- source main: `202d46796f031caa0c9d7138c402eefb0cc56971`
- capture window: `[2026-09-11T00:00:00Z, 2026-09-12T00:00:00Z)`
- current-round kickoff window: `prediction_time_utc <= kickoff_utc < 2026-09-15T00:00:00Z`
- scope leagues: `BUNDESLIGA`, `EPL`, `EREDIVISIE`, `LA_LIGA`, `LIGUE_1`, `SERIE_A`
- canonical inventory SHA-256: `4934dd8f5e6f287c79ecfad4e910158650fd171d26faae66d9000b23bc5e4828`

The inventory hash is over the 57 outcome-free rows ordered by `(league, event_id)` using league, event id, teams, kickoff, prediction time, snapshot time and H/D/A market probabilities. Outcome/result fields are not part of the inventory hash and were not read when it was produced.

## Outcome-free inventory

| League | Current-round MARKET_ONLY events | Genuine prospective AI pairs | Replay eligible | Eligibility decision |
|---|---:|---:|---:|---|
| BUNDESLIGA | 9 | 0 | 0 | no pre-kickoff immutable league-specific AI artifact |
| EPL | 10 | 10 | 0 | already genuine prospective `EPL_AI_MARKET_PAIR_V1`; do not relabel as replay |
| EREDIVISIE | 9 | 0 | 0 | no pre-kickoff immutable league-specific AI artifact |
| LA_LIGA | 10 | 0 | 0 | pre-kickoff historical candidate gate returned `REJECTED_NO_ARTIFACT` |
| LIGUE_1 | 9 | 0 | 0 | no pre-kickoff immutable league-specific AI artifact |
| SERIE_A | 10 | 0 | 0 | no pre-kickoff immutable league-specific AI artifact |
| **Total** | **57** | **10** | **0** | **reconstructed cohort is empty** |

The earlier approximate count of 66 was not a valid current-round cohort: it included 18 Eredivisie events spanning two rounds. The outcome-free current-round rule above yields nine Eredivisie fixtures and 57 events across the six originally targeted leagues.

## Provenance decision

### EPL

All ten current-round EPL `MARKET_ONLY` event IDs have a matching row in `epl_ai_market_pair_ledger` whose model generation time precedes kickoff. These are already prospective AI-vs-market observations. They remain in `EPL_AI_MARKET_PAIR_V1`; they are excluded from reconstruction so evidence classes are not duplicated or relabelled.

### La Liga

The only plausible pre-kickoff non-EPL candidate path was the research-only La Liga candidate builder. GitHub Actions run `34497901262` executed the historical candidate proof on 2026-09-10. At 2026-09-10T15:48:12Z the strict gate printed `REJECTED_NO_ARTIFACT`. The uploaded artifact contained only the historical report; no `model.joblib`, calibrator or candidate manifest was created. Therefore no immutable pre-kickoff La Liga AI artifact exists for this replay.

### Bundesliga, Eredivisie, Ligue 1, Serie A

The pre-capture repository readiness contract had no validated league-specific candidate artifact/provenance for these leagues. Reusing the EPL production model cross-league is explicitly prohibited. Historical/PIT infrastructure alone is not a fixed AI prediction algorithm with immutable model provenance.

## Frozen eligibility rule

A `MARKET_ONLY` event can enter a reconstructed AI cohort only if, independently of its result:

1. the league-specific model artifact existed before kickoff and has a provable SHA-256;
2. inference code/version was fixed before kickoff;
3. every feature can be reconstructed only from information available before kickoff;
4. a deterministic probability-calibration rule, if any, was fixed before kickoff;
5. the exact captured market snapshot is pre-kickoff;
6. temporal provenance can be demonstrated end-to-end.

Failure of any condition excludes the event. Existing prospective rows are not duplicated into replay. Applying this rule to the frozen 57-event inventory yields **zero reconstructed predictions**.

This zero is a research result, not an invitation to weaken eligibility after outcomes are known.

## Evaluation plan

Because `REPLAY_DIAGNOSTIC_V1` has no eligible reconstructed rows, no replay outcome evaluation will be manufactured. The immediate honest early diagnostic must instead use only already-genuine prospective paired evidence from the frozen `EPL_AI_MARKET_PAIR_V1` experiment.

For any pooled paired evaluation, the only primary metrics are:

- AI multiclass Brier score;
- Market multiclass Brier score;
- `delta_brier = AI - Market`;
- AI multiclass Log Loss;
- Market multiclass Log Loss;
- `delta_logloss = AI - Market`;
- AI accuracy;
- Market accuracy.

Interpretation is frozen before reading outcomes:

- `delta_brier < 0` **and** `delta_logloss < 0` → `EARLY_SIGNAL`;
- `delta_brier > 0` **and** `delta_logloss > 0` → `WARNING`;
- mixed/zero signs → `INCONCLUSIVE`.

With small N these labels are descriptive only, not claims of statistical proof. No subgroup fishing, threshold tuning, deletion of inconvenient matches, optional stopping, or betting recommendation is permitted. `bet_decision` remains `no_bet`.

## Boundary with frozen experiments

- `ALL_LEAGUES_MARKET_ONLY_V1_1` is unchanged and remains a MARKET_ONLY experiment under its original gate.
- `EPL_AI_MARKET_PAIR_V1` is unchanged and remains the true prospective paired experiment.
- This contract does not promote any MARKET_ONLY row into prospective evidence.
- This contract does not modify or promote any production `.pkl`.
- No paid provider request is required.

## Next action after freeze

After this outcome-free contract is merged, read canonical settlements only for already-existing valid prospective EPL pairs, evaluate the predeclared pooled metrics once, report the small-N status, and then harden future league capture so `AI_CAPTURE_READY` requires live durable AI-probability/provenance read-back rather than MARKET_ONLY success.
