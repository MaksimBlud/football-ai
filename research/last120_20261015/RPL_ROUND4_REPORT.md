# Football AI — RPL 2026/27, goal/no goal in the last 120 seconds and four random matches per round

**Research-only. Snapshot: 2026-07-24 through 2026-10-14 inclusive.** Russian Premier League, league ID 63 (FotMob). Zero changes to Supabase/production/PKL; no paid API.

## What was actually verified

The FotMob 2026/27 Russian Premier League schedule lists **80 completed fixtures (rounds 1–10, eight fixtures each)**, all found and inspected individually. There are no missing fixture days or rounds. Each inspected game is checked against its final score; the number of confirmed goal events matches the score. Second-half start and game-ended timestamps are available. Recorded goals provide *minute only*, not the exact goal second.

The final 120-second boundary is estimated from the second half started time and the actual game-ended timestamp, with a 45:00 base for the elapsed match clock. Events whose entire minute lies inside the last 120 seconds are labelled **GOAL**; matches whose last goal's entire minute lies earlier are labelled **NO_GOAL**; events where the minute overlaps the final-120s boundary are labelled **UNKNOWN**, never guessed. This is a different evidence standard from the fully second-resolved Opta Big 5.

### Per-match counts

| Status | Matches |
|---|---:|
| GOAL certainly falls inside last 120 sec | 2 |
| NO_GOAL established | 74 |
| UNKNOWN: goal minute overlaps 120-second cutoff | 4 |
| **Total** | **80** |

Confirmed goal matches:
- **Round 5, 2026-08-24:** Baltika — Rubin Kazan, 1–1. Minute 90+4.
- **Round 8, 2026-09-12:** Fakel — Baltika, 2–2. Minute 90+5.

Unresolved marginal matches:
- Round 1, 2026-07-26, Rubin — Krasnodar 1–3. Goal on 90+4. Last-120 cutoff estimated at match clock 93:52. Need actual goal second.
- Round 3, 2026-08-09, Dinamo Moscow — Dynamo Makhachkala 3–1. Goal on 90+3. Cutoff ~92:43. Need goal second.
- Round 4, 2026-08-16, Krylya Sovetov — Dynamo Makhachkala 1–4. Goal on 90+3. Cutoff ~92:15. Need goal second.
- Round 6, 2026-08-30, Rubin — Dynamo Makhachkala 3–1. Goal on 90+5. Cutoff ~94:25. Need goal second.

All four goals corroborated at minute resolution by match reports / match trackers, but no independently confirmed exact goal second found. Therefore the RPL late-goal match rate is bounded **2/80 = 2.5% to 6/80 = 7.5%**; no valid single-number point estimate can be justified without further timing data.

## Random 4 distinct matches within a single league round

For a round with 8 matches, `P(at least one selected late-goal match) = 1 - C(8-g,4)/C(8,4)`, with `g` the number of eligible matches whose final 120 seconds contain a goal. For each round, compute minimum using only confirmed positives and maximum treating all unresolved as positives. 10 complete eight-game rounds. `C(8,4)=70` combinations per round.

| RPL round | Verified GOAL | Verified NO_GOAL | UNKNOWN | Selection risk, min–max |
|---|---:|---:|---:|---:|
| 1 | 0 | 7 | 1 | 0–50% |
| 2 | 0 | 8 | 0 | 0% |
| 3 | 0 | 7 | 1 | 0–50% |
| 4 | 0 | 7 | 1 | 0–50% |
| 5 | 1 | 7 | 0 | 50% |
| 6 | 0 | 7 | 1 | 0–50% |
| 7 | 0 | 8 | 0 | 0% |
| 8 | 1 | 7 | 0 | 50% |
| 9 | 0 | 8 | 0 | 0% |
| 10 | 0 | 8 | 0 | 0% |
| **Average (uniform random round)** | **2** | **74** | **4** | **10–30%** |

RPL probability that all four randomly selected matches will have **no late goals** = **70–90%**. This is the historical exact-combination risk interval conditional on observed finite fixture set, *not* a 95% statistical confidence interval or a prospective guarantee.

## Addition to the existing five-league study

Prior completed Big 5 research: **29 complete rounds**, **279 verified games**, and **27.3946%** empirical risk for four random games in a uniformly selected full league round. The two partially played La Liga rounds are excluded. Adding **10 complete Russian Premier League rounds** gives:

| League | Complete rounds | Probability of at least one GOAL among 4 randomly chosen matches |
|---|---:|---:|
| Premier League (England) | 6 | 33.33% |
| La Liga | 6 | 6.67% |
| Bundesliga | 5 | 32.22% |
| Serie A | 6 | 26.67% |
| Ligue 1 | 6 | 38.89% |
| Russian Premier League | 10 | **10–30%** |
| **Six-league total; uniform choice among 39 full rounds** | **39** | **22.93–28.06%** |

The sampling procedure chooses one of the observed 39 full league rounds uniformly, then 4 of its matches uniformly *without replacement*. It is not a prediction of all bookmakers, and not the same weighting as 4 random matches from a pool of all 377 finished games (including the partial La Liga rounds).

For match-level outcomes, prior 297 games + new 80 = **377 distinct fixtures**, with **22 certain positives, 351 negatives, 4 uncertain**. That gives an empirical possible late-goal frequency of **5.84–6.90%**, using the full observed fixture set.

## Provenance

- All 80 RPL fixtures: FotMob Russian Premier League `/api/data/leagues?id=63`.
- Individual event/source checks: FotMob `/api/data/matchDetails?matchId=...` read-only, source provider 'enet'.
- Independent minute-level checks: FC Krasnodar official match account for Rubin–Krasnodar 26 July; FC Dynamo Moscow official account of Dinamo–Dynamo Makhachkala 9 August; Dynamo Makhachkala official account Krylya–Dynamo 16 August; Championship match log Rubin–Dynamo 30 August.
- Reproducible script: `research/last120_20261015/rpl_round4.py`, run with GitHub Actions workflow `.github/workflows/research-rpl-round4.yml`.
- [Completed CI and frozen individual-match evidence](https://github.com/MaksimBlud/football-ai/actions/runs/38921339010); downloadable 7-day artifact `rpl-final120-round4-evidence` with `rpl_results/matches.json`, `summary.json`.

**Limitation:** The exact seconds of four late goals and same-provider final whistle times are not independently available in this RPL feed. Unlike the Big 5 Opta study, RPL has four unresolved matches; do not silently treat UNKNOWN as NO_GOAL or GOAL.

No market coefficients, account bet limits, realized returns, or out-of-sample testing were supplied. The historical chance that all four win is not a profitable strategy claim.
