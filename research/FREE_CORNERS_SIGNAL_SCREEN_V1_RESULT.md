# FREE_CORNERS_SIGNAL_SCREEN_V1 — Final Result

Status: **CLOSED / NO_CLEAR_SIGNAL_SCREEN**

## Scope

This is the immutable result record for the preregistered free-only corner-market screen.

The experiment tested whether leakage-safe football corner state added information beyond Bet365 opening corner-total prices on the currently available free window.

Frozen design:
- leagues: EPL, La Liga, Serie A, Bundesliga, Ligue 1;
- football history: 2016-17 through 2025-26, free Football-Data data;
- test window: 2026-27 only;
- 11 most recent finished fixtures per league, 55 selected fixtures total;
- bookmaker baseline: Bet365 opening corner-total line and de-vigged Over/Under prices;
- model: fixed per-league Poisson corner model;
- fixed blend: 25% football / 75% market;
- metrics: Brier score, LogLoss, residual alignment;
- no ROI gate, no betting, no production use.

The final evaluation was executed offline from the already-frozen 55-match market artifact and fixed public Football-Data GitHub mirrors. It made **zero new provider requests** and used **no paid subscription**.

## Final sample

- selected fixtures: **55**
- market rows available: **55**
- eligible evaluation rows: **44**
- sample gate: **PASS**
- leagues with at least 5 eligible rows: **5**
- exclusions: 10 insufficient-prior-top-flight-history rows and 1 integer-line push row

## Pooled result

Bet365 market:
- Brier: **0.2511361669**
- LogLoss: **0.6954253591**

Football-only:
- Brier: **0.2527333343**
- LogLoss: **0.6985438218**

25% football / 75% market blend:
- Brier: **0.2507327218**
- LogLoss: **0.6946150411**

Blend delta vs market:
- Brier: **-0.0004034451**
- LogLoss: **-0.0008103180**

Residual alignment:
- pooled: **0.0013420482**
- bootstrap 90% interval: **[-0.0067517886, 0.0096309293]**
- positive-alignment leagues: **2 / 5**

Frozen verdict: **NO_CLEAR_SIGNAL_SCREEN**

The tiny pooled metric improvement from the fixed blend is not accompanied by a stable residual-alignment signal; the bootstrap interval spans zero and only two of five leagues show positive alignment. The preregistered screen therefore does not establish a robust transferable edge over the Bet365 opening market.

## Per-league diagnostic

| League | Eligible | Market Brier | Football Brier | Blend Brier | Market LogLoss | Football LogLoss | Blend LogLoss | Residual alignment |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| EPL | 10 | 0.246992 | 0.265971 | 0.251120 | 0.687127 | 0.725347 | 0.695390 | -0.007846 |
| La Liga | 8 | 0.250444 | 0.280307 | 0.257083 | 0.694042 | 0.755849 | 0.707428 | -0.012727 |
| Serie A | 11 | 0.247446 | 0.216168 | 0.237987 | 0.688044 | 0.623325 | 0.669024 | 0.020013 |
| Bundesliga | 6 | 0.264651 | 0.265665 | 0.264725 | 0.722479 | 0.724592 | 0.722629 | -0.000028 |
| Ligue 1 | 9 | 0.251856 | 0.249584 | 0.250908 | 0.696862 | 0.692393 | 0.694966 | 0.002150 |

Serie A is the strongest positive diagnostic in this small free sample. Ligue 1 is mildly positive. EPL and La Liga are negative, and Bundesliga is effectively flat. These league-level results are diagnostics only; they were opened after the frozen pooled test and must not be used to retune V1.

## Decision

For the current free window:

**Do not claim a general corner-market signal.**

`FREE_CORNERS_SIGNAL_SCREEN_V1` is closed as **NO_CLEAR_SIGNAL_SCREEN**.

The result does not prove that no corner signal exists. It says the currently frozen CORNERS10-derived total-corner construction did not show a stable cross-league advantage over Bet365 opening prices on the available free OOT sample.

The Serie A result may justify a **separate future preregistered replication** on new matches only. It must not be treated as a confirmed edge and V1 must not be retuned after seeing this result.

## Provenance and safety

- implementation PR: #379
- final replay workflow run: `35296673025`
- final replay artifact: `10527949187`
- artifact digest: `sha256:20128a36af5cd5f74240461571566133ab8a6b44462ed3f0d87b4d8085498ad4`
- implementation merge: `9a5c29a0b65ff67a191440ddd64907ca75da69d5`
- research-only
- NO_BET
- no paid subscription
- zero new provider requests in final replay
- no Supabase writes
- no production `.pkl` changes
- no model promotion
