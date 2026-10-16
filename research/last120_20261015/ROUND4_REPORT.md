# Football AI — 4 randomly selected matches per league round (2026/27)

**Status:** DONE, research-only, no production deployment.  
**Definition of event:** A match is positive if at least one goal was scored within the final 120 seconds before its actual full-time whistle, established by the independent same-provider Opta event clock (goal event type 16, second-half end type 30).  
**Source match evidence:** validated [297-match final-120-seconds GitHub Actions run](https://github.com/MaksimBlud/football-ai/actions/runs/38764264517), `all_opta_matches.json`.  
**Round assignment:** independently retrieved `general.matchRound` from FotMob matchDetails for **every** match; identity and final score checked against the frozen evidence, zero missing round identifiers.  
**Reproduction:** [per-round four-selection CI run](https://github.com/MaksimBlud/football-ai/actions/runs/38919719912), `round4_probability.py`. Download the `last120-four-random-matches-202627` artifact for the row-level `round4_matches.json` and `round4_summary.json` proof.

## Research question and estimand

What is the historical probability that *at least one of four distinct random matches from a single league's round* had a late goal in the **actual** final 120 seconds?

Within a round of `n` completed matches and `g` matches with late goals, enumerate all `C(n,4)` unordered four-match subsets. Their exact positive fraction is

`q = 1 - C(n-g,4)/C(n,4)`.

This computes combinations without replacement; no independence assumption. For the combined headline, select one **fully completed league-round uniformly from observed rounds** and then choose four matches uniformly within that round. Each round counts equally; each league is weighted by the number of complete observed rounds.

## Verified results — full rounds only

| League | Fully completed rounds | Matches | Matches with late goal | Average probability ≥1 late-goal match among 4 |
|---|---:|---:|---:|---:|
| Premier League | 6 | 60 | 5 | 33.333% |
| La Liga | 6 | 60 | 1 | 6.667% |
| Bundesliga | 5 | 45 | 4 | 32.222% |
| Serie A | 6 | 60 | 4 | 26.667% |
| Ligue 1 | 6 | 54 | 6 | 38.889% |
| **Total** | **29** | **279** | **20** | **27.3946%** |

Therefore probability all four avoid late goals = **72.6054%**. Risk of ≥1 = **27.3946%**, approximately one losing fourfold in 3.65 such hypothetical equal-round selections.

Among the 29 full league-rounds, **12 rounds** had zero late-goal matches, **14** had one, and **3** had two. A 10-match round with one such event has `4/10=40%` risk. A 9-match round with two such events has `1-C(7,4)/C(9,4)=72.222%`.

### Exact observed per-round outcomes and combination risks

| League | Round 1 | Round 2 | Round 3 | Round 4 | Round 5 | Round 6 | Round 7 | Round 8 |
|---|---|---|---|---|---|---|---|---|
| Premier League | 1/10; 40% | 1/10; 40% | 1/10; 40% | 1/10; 40% | 1/10; 40% | 0/10; 0% | — | — |
| La Liga | 0/10; 0% | 0/10; 0% | 0/10; 0% | 0/10; 0% | 1/10; 40% | 0/9; partial | 0/10; 0% | 0/9; partial |
| Bundesliga | 1/9; 44.44% | 2/9; 72.22% | 1/9; 44.44% | 0/9; 0% | 0/9; 0% | — | — | — |
| Serie A | 1/10; 40% | 1/10; 40% | 0/10; 0% | 1/10; 40% | 0/10; 0% | 1/10; 40% | — | — |
| Ligue 1 | 1/9; 44.44% | 2/9; 72.22% | 1/9; 44.44% | 0/9; 0% | 0/9; 0% | 2/9; 72.22% | — | — |

Notation: `g/n` = goal-bearing matches / finished matches in round. La Liga rounds 6 and 8 each contain only 9 confirmed completed matches versus the standard 10, and were excluded from the **primary full-round result**, not treated as 10-game rounds.

## Sensitivity — incomplete rounds and alternative sampling schemes

- If all **31** rounds containing at least four recorded matches are considered, including the two partial La Liga rounds, average risk under *uniform choice of a round* = **25.6272%** and success for all four = **74.3728%**. This has the disadvantage of conditioning on incomplete round membership.
- If instead you choose **uniformly among all individual four-match combinations pooled across full rounds** (this weights rounds containing 10 matches more heavily because 10 choose 4 > 9 choose 4), you obtain **1337 / 5166 = 25.8808%**. This is a **different sampling scheme**, not a contradictory answer.
- Former pooled, *independent-match* approximation based on 20/297 gives `1-(277/297)^4 = 24.3353%`; it is not the preferred historical within-round estimator.
- Small sample, especially 6/5/6 rounds per league; differences between leagues and between rounds may be noise. No OOS / forward value validation, live market quotes, execution availability, suspension risks, or bookmaker settlement checks.

## Interpretation for wagering

The probability that all four selections succeed ≈ 72.6054% under the empirical equal-round sampling plan **does not imply a profitable strategy**. If they form a four-leg accumulator and stakes/market rules are uniform, empirical no-margin break-even combined decimal odds ≈ `1 / 0.726054 = 1.3773` (not a guaranteed or forecast price). Four individual singles have a different payout structure; one late-goal match does not wipe out all four singles. No post-hoc threshold optimization.

**Safety:** read-only data retrieval. Do not write Supabase; do not change production `.pkl`, do not use The Odds API, do not auto-promote or merge.
