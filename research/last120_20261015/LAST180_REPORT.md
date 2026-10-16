# Football AI — final 180 seconds before the actual final whistle, season 2026/27

**Status:** DONE (research-only). **Data cut-off:** 14 October 2026 inclusive.  
**Reproduction:** [successful full six-league GitHub Actions run 38923089332](https://github.com/MaksimBlud/football-ai/actions/runs/38923089332).  
**Executable:** `research/last120_20261015/last180.py`. The action stores a seven-day downloadable evidence artifact `final180-six-leagues-202627` containing `last180_results/matches.json` and `summary.json`.  
**Inputs:** Frozen, previously validated 297-match Opta/FotMob fixture+event evidence with round identifiers from run 38919719912; 80 RPL fixture/goal-minute/whistle records from run 38921339010. These are the same fixtures as the earlier final-120-second study. No Supabase writes, model changes, paid APIs, or automatic promotion.

## The precise event

For every match, look backward **180 elapsed match-clock seconds from its actual final second-half whistle**, not at a fixed 90+3 / 90+4 minute label. A goal is in-window when `0 <= whistle_second - goal_second <= 180`. Different games end at different timestamps. A match with two late goals counts as **one** positive match for a bet on no goal.

Five European leagues: exact Opta event types `16` (goals) and `30` (period-2 end) in one elapsed-time source. All 297 matched games have second-level records and a verified score match. RPL: FotMob goals have **whole-minute** labels only, while second-half start and game-end walltime allow an approximate elapsed-game cutoff; classify a match as positive only when the entire minute containing a goal is inside the 180-second window, negative only when all goal minutes are before the cutoff. Otherwise report `UNKNOWN` (never count as a no-goal success). A game whose *all* goals finished by minute 87 can be classified as no-goal even when its final whistle timestamp is missing, since the game finished in regulation.

## Match-level historical incidence

| League | Matches | YES: goal in final 180s | NO: no such goal | Unknown | Rate for YES |
|---|---:|---:|---:|---:|---:|
| Premier League | 60 | 7 | 53 | 0 | 11.67% |
| La Liga | 78 | 5 | 73 | 0 | 6.41% |
| Bundesliga | 45 | 6 | 39 | 0 | 13.33% |
| Serie A | 60 | 5 | 55 | 0 | 8.33% |
| Ligue 1 | 54 | 7 | 47 | 0 | 12.96% |
| **Big Five** | **297** | **30** | **267** | **0** | **10.10%** |
| Russian Premier League | 80 | 6 | 71 | 3 | **7.50–11.25%** |
| **Six leagues** | **377** | **36** | **338** | **3** | **9.55–10.34%** |

Ranges are logical uncertainty bounds over three RPL goal-minute overlaps, NOT formal statistical confidence intervals. Six-league no-goal empirical success range is **89.66–90.45%**. Do not silently assume the three UNKNOWN games all contained goals or none did.

## Four randomly selected distinct matches within one same-league round

We include only full rounds: 29 complete Big Five league rounds (279 games) and 10 complete RPL rounds (80 games), **39 rounds, 359 games**. La Liga rounds 6 and 8 each have 9 matches in the frozen set (versus standard 10) and are excluded from the primary four-match sample; their 18 matches are included in the match-level rates above.

For a round with `n` matches and `g` YES events, the proportion of the `C(n,4)` possible unordered four-match selections containing at least one YES is `1-C(n-g,4)/C(n,4)`. For RPL lower/upper bounds use `g` and `g+unknown`. Sample a *completed league-round uniformly*, then a four-match combination uniformly within it. Every complete round has identical weight in the combined headline; this is not the same as sampling uniformly among all pooled four-match combinations.

| League | Full rounds | 2-minute risk (prior study) | **3-minute risk** |
|---|---:|---:|---:|
| EPL | 6 | 33.33% | **42.22%** |
| La Liga | 6 | 6.67% | **20.00%** |
| Bundesliga | 5 | 32.22% | **46.67%** |
| Serie A | 6 | 26.67% | **31.11%** |
| Ligue 1 | 6 | 38.89% | **46.30%** |
| **Five leagues** | **29** | **27.39%** | **36.93%** |
| RPL | 10 | 10–30% | **30–42.86%** |
| **Six leagues** | **39** | **22.93–28.06%** | **35.16–38.45%** |

Therefore the rate of four successful no-goal selections within a uniformly chosen complete league round is **61.55–64.84%** for final 3 minutes (versus 71.94–77.07% for final 2 minutes).

**Do not conflate sampling rules:** pooling all `C(n,4)` choices across the 39 complete rounds instead of weighting each round equally gives **34.61–36.14%** risk. For all 41 observed rounds, including two partial La Liga rounds, yet another statistic applies and is not the main comparable result.

## RPL full rounds — 3-minute window

| Round | GOAL confirmed | NO GOAL | UNKNOWN | Probability selected four contain a GOAL |
|---|---:|---:|---:|---:|
| 1 | 1 | 6 | 1 | 50–78.57% |
| 2 | 0 | 8 | 0 | 0% |
| 3 | 1 | 7 | 0 | 50% |
| 4 | 1 | 7 | 0 | 50% |
| 5 | 1 | 7 | 0 | 50% |
| 6 | 1 | 7 | 0 | 50% |
| 7 | 0 | 7 | 1 | 0–50% |
| 8 | 1 | 7 | 0 | 50% |
| 9 | 0 | 7 | 1 | 0–50% |
| 10 | 0 | 8 | 0 | 0% |
| **Mean** | **6** | **71** | **3** | **30–42.86%** |

Unresolved RPL match list (exact goal seconds not recorded in free native source):
- 26 July, round 1: **Orenburg — Rostov, 2–1**, goal reported 90+4, exact goal-second vs 93:30 cutoff unknown.
- 5 September, round 7: **Zenit — CSKA, 1–2**, goal reported 90+8, boundary near 97:04, exact second unknown.
- 16 September, round 9: **Spartak — Fakel, 1–0**, goal recorded in 91st minute, cutoff near 90:46, exact second unknown.

Six definitively positive RPL matches and minute details are in the machine-readable `matches.json`. The fourth RPL borderline from the first pass, **Zenit — Lokomotiv 2–1 (12 Sept)**, is now safe to classify `NO_GOAL`: all goals were scored by minute 70, far outside any final 180-second window.

## Interpretation

- Five-league match-level late-goal frequency: **10.10%**, so approx. one late-goal match per ten games. RPL is **7.50–11.25%** pending three exact seconds.
- For 4 selections **in the same league round** across six leagues, a losing no-goal accumulator is observed in **35.16–38.45%** of uniformly sampled completed-round combinations; all four no-goal outcomes in **61.55–64.84%**.
- Indicative no-margin break-even *fourfold combined odds* from the observed fraction: **~1.542–1.625**, depending on three uncertain RPL goals. Indicative no-goal single-event break-even odds for the pooled 377 matches: **~1.106–1.115**. These are sample-dependent illustrative estimates, not actual executable lines, and assume a four-leg combined bet with no voids.
- The empirical 2-minute and 3-minute risks are correlated and all comparisons here are descriptive. Only 39 complete league rounds were observed, with varying league counts. **There is no demonstrated bookmaker edge**, market execution validation, independent forward backtest, or claim of a profitable betting strategy.

**Research-only; production .pkl, Supabase, main branch unchanged.**
