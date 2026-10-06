# Direction 3 duplicate audit — independent tactical-source disagreement

Status: **INDEPENDENT PREREGISTRABLE PATH FOUND**

This audit was completed after roadmap Direction 2 reached `PROGRAM_DONE`. It does not
open match outcomes and does not define a post-hoc disagreement winner.

## Roadmap question

When a football estimate built from a genuinely independent information source disagrees
with the bookmaker 1X2 consensus for a mechanistically specified reason, does the
independent estimate identify a stable class of market errors?

The market consensus must remain the control. Direction 3 is a source-disagreement test,
not the correction-model architecture reserved for Direction 4.

## Existing work that must not be repeated

The following evidence is binding but not equivalent to the proposed experiment:

- existing EPL and cross-league AI-vs-market evaluations used the project model, whose
  architecture consumes bookmaker odds; it is not an independent football source;
- `TEAM_STRENGTH_TRAJECTORY_V1` used Elo/result residuals;
- `SHOT_QUALITY_PROXY_V1` and Issue #562 used Football-Data shots/SOT families;
- `LA_LIGA_CONDITIONAL_RESIDUAL_V4` selected a gate over an already market-anchored
  residual plus market entropy and failed its untouched-OOT activation gate;
- historical cross-book disagreement tested bookmaker-versus-bookmaker information and
  was closed after a later structural break;
- the Understat deep/deep_allowed mapping already evaluated a corner-market direction
  question, not 1X2 outcome probabilities.

No new child may reselect thresholds, leagues, disagreement quantiles or source families
from those opened results.

## Independent path

`V2B_UNDERSTAT_TACTICAL_PRESSURE5_FEASIBILITY_V1` previously established a free,
point-in-time prior-match source for:

- `deep`;
- `deep_allowed`;
- `PPDA`;
- `PPDA_allowed`.

The fields were available across EPL, La Liga, Serie A, Bundesliga and Ligue 1. Their
prior-match timing is reconstructable before the next fixture. This source is independent
of bookmaker odds and differs from Football-Data shots/SOT and Elo/result trajectories.

The allowed follow-up is one symmetric, mechanistically frozen test:

1. construct a football-only 1X2 probability estimate from fixed same-season prior-five
   Understat tactical-pressure features;
2. construct a multiplicatively de-vigged Football-Data average-bookmaker 1X2 consensus;
3. define disagreement without selecting a league, outcome side or quantile after results;
4. compare the football estimate and market consensus on the same temporally held-out
   fixtures;
5. require validation, untouched-test, uncertainty and cross-league consistency gates.

The mechanism is tactical territorial/pressing pressure. It must not be described as
lineup, injury, manager, true xG or causal tactical intent.

## Separation from Direction 4

Direction 3 may report which source is more accurate under its frozen disagreement rule.
It must not train a model to predict a probability correction, tune blend weights or
deploy a residual architecture. Those operations belong only to roadmap Direction 4 and
are unavailable unless an independent source family earns support here.

## Safety

- research-only / NO_BET;
- no paid Odds API;
- no Supabase writes;
- no production model operations or `.pkl` changes;
- no 2026/27 outcome inspection;
- no post-hoc disagreement type, quantile, threshold, league or sign selection.
