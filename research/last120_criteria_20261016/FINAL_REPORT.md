# Football AI — selection criteria for NO GOAL in the actual last 120 seconds

**Research status: DONE for public event-based candidates; RESEARCH-ONLY.**  
**Snapshot:** 16 October 2026; matches through 14 October 2026.  
**Source:** public Opta fixture and event data via [pannadata GitHub releases](https://github.com/peteowen1/pannadata/releases/tag/opta-latest), downloaded read-only. No paid odds data, no changes to production model, Supabase, or main branch.  
**Reproducibility:** [full longitudinal CI run](https://github.com/MaksimBlud/football-ai/actions/runs/38927461294), [independent multiplicity and league robustness CI run](https://github.com/MaksimBlud/football-ai/actions/runs/38928297759). Runnable scripts: `research/last120_criteria_20261016/analyze.py` and `robustness.py`. GitHub Action artifacts (`no-goal-120s-selection-criteria` and `last120-criteria-robustness`) contain match-level and statistical JSON/CSV, retained 10 days.

## 1. Frozen label / availability

`Y=1` only if at least one verified type-16 goal event happened between `(type-30 period-2 final whistle elapsed second - 120)` and the final-whistle elapsed second, inclusive. No fixed 90+4/90+5 assumptions. Same clock source on both sides. One row per completed match.

5 European leagues, 5 seasons: `2022-2023`, `2023-2024`, `2024-2025`, `2025-2026`, partial `2026-2027` through 14 October. Opta fixture universe 7358, valid exact-second outcomes **7350**, with **412 goal-bearing matches and 6938 matches without such goals**. Exactly 8 failed goal-count/final-whistle quality checks: four implausible final timestamps, three goal count mismatches, one inconsistent end timestamps.

**587 of 7350 matches have team attribution of goal events that disagrees with final home/away split**, often involving own goals. They **remain in the total outcome sample** but are deliberately **excluded from LIVE85/90 score-gap comparisons**, because reconstructing the 85' score from these team IDs would be unreliable. They remain eligible for pre-match factors and non-score events. This filtering uses a postmatch *data quality check* and could induce selection bias; score-based results therefore apply to the reliable subset, not all 7350 matches. Never claim independent live trading validation.

Outcome (all seconds-verified games) by season:

| Season | Eligible games | YES in final 120s | Goal rate |
|---|---:|---:|---:|
| 2022/23 | 1805 | 111 | 6.15% |
| 2023/24 | 1752 | 94 | 5.37% |
| 2024/25 | 1747 | 93 | 5.32% |
| 2025/26 | 1749 | 94 | 5.37% |
| 2026/27 to Oct 14 | 297 | 20 | 6.73% |
| **Total** | **7350** | **412** | **5.61%** |

## 2. Strict availability timestamps / no leakage

- **PRE (before kickoff):** only preceding fixtures from the same league season strictly dated before fixture date; minimum 5 completed past games *for each team*. Same-day matches are not retrospectively used as earlier form data. Form proxies: historical goals per game, conceded per game, recent points per game, last-10 draws. Thresholds fixed before reading held-out labels.
- **LIVE85:** score and attempts/goals already occurred by exactly elapsed 85:00. Live snapshots never use the final score, events after the snapshot, final whistle duration, or late-goal label.
- **LIVE90:** analogous state already known by exactly elapsed 90:00. Can be used only if a *matching, actually offered* market permits entry at that moment. No claim the unknown future last 120 seconds can be traded directly.
- **NOT actionable/POSTMATCH:** actual stoppage length, final whistle time, final goal-minute condition, score at match end; these cannot be used to select a match before the outcome.
- **Unavailable/NOT TESTED:** genuine bookmaker in-play odds at a comparable settlement market, liquidity/suspension, realized ROI, accurate RPL second-level historical own-goal and shot events, verified in-game xG/possession/corners/red-card signals, referee/weather/competition motivation, approved added time prior to bet. Do NOT label these criteria tested or validated.

Splits frozen by season:

- Feature development **2022/23–2023/24** (3557 games, 205 late-goal games);
- Separate validation **2024/25** (1747 games, 93 positives);
- Out-of-time test **2025/26** (1749 games, 94 positives);
- Most recent additional small holdout **2026/27** (297 games, 20 positives).

28 individual fixed-hypothesis filters were checked for pregame points/attack/defence/draws and at 85/90 score state, recent shot volume/goals. Raw Fisher tests and pooled heldout BH FDR correction of 28 comparisons provided in `robustness.json`. Newly combined filters were formed **after observing holdout results**, so should be regarded as *exploratory* and not claim independent validation.

## 3. Main candidate: tied score at 85:00

Meaning `home goals == away goals` at exactly 85:00 (0:0, 1:1, 2:2, etc.), assessed in matches with reconcilable Opta goal-team attribution.

| Split | TIED at 85 (goal/matches) | Goal rate | NOT tied at 85: goal rate | Evidence |
|---|---:|---:|---:|---|
| 2022/23–2023/24 DEV | 39/910 | 4.29% | 6.21% | directional |
| 2024/25 VALIDATION | 10/411 | 2.43% | 6.26% | Fisher p=0.00199 |
| 2025/26 TEST | 12/434 | 2.76% | 6.38% | Fisher p=0.00407 |
| 2026/27 fresh small holdout | 3/73 | 4.11% | 8.25% | same direction, p=0.296 |

**Combined 2024/25+2025/26:** tied **22/845 = 2.60%**, not tied **151/2389 = 6.32%**; approximate relative risk **0.412**, absolute difference **3.72 percentage points**. Pooled Fisher **p=0.0000162**; Benjamini–Hochberg corrected **q=0.000231** among 28 screened criteria; Mantel-Haenszel stratified across ten independent season×league tables **common OR≈0.399, p≈0.0000492**. Direction of effect holds in all 5 leagues over 2024/25+2025/26 combined. This is an **association**, not a bookmaker value edge.

95% Wilson descriptive binomial interval for risk in tied group: approximately **1.73%–3.91%**. New season 2026/27 3/73 has much wider bounds, about **1.4%–11.4%**. Do not overstate precision.

Detailed 2024/25+2025/26 by league:
| League | Draw at 85: matches with late goal / eligible | Goal rate | Non-draw late-goal rate |
|---|---:|---:|---:|
| EPL | 4/186 | 2.15% | 4.77% |
| La Liga | 6/190 | 3.16% | 6.26% |
| Bundesliga | 2/133 | 1.50% | 8.26% |
| Serie A | 6/194 | 3.09% | 5.14% |
| Ligue 1 | 4/142 | 2.82% | 7.67% |

The 2026/27 Serie A small early slice runs **opposite**, 2 goals in 14 tied-at-85 games versus 2 in 44 non-tied: 14.3% vs 4.5%. This cautions strongly against turning conditional rates into guarantees by league.

## 4. Other observed and rejected criteria

- **Tied at 90:00:** validation+test **22/839 = 2.62%** versus 6.30% otherwise, pooled q≈0.000231. Highly correlated with tied-at-85; do not count it as independent confirmation or enter a differently-settled market on this evidence.
- **0:0 at 85:00:** validation+test **5/286 = 1.75%** vs 5.67% for others; pooled BH q≈0.0164. Only five late goals in the selected group and just 21 such matches in 2026/27 (one late goal), so treat as **secondary small-sample refinement**, not mandatory.
- **Lead margin ≥2 goals at 85:00:** **72/1022 = 7.05%** late-goal matches, against 4.57% among remaining reliable-gap matches, pooled BH q≈0.0237. New season 2026/27 **10/90 = 11.11%**, versus 5.08% otherwise. This is a reasonable **caution/exclusion** for conservative no-late-goal candidate screening, not proof of higher bookmaker edge against the line.
- **Draw at 85 + no goal in preceding 15 min:** exploratory **13/622 = 2.09%** on the combined 2024/25+2025/26 sample; 2026/27 **1/47 = 2.13%**. This combination was checked after seeing held-out single-feature results, so is **NOT independently validated**. It may be a watch-list criterion only.
- **Draw at 85 + ≤2 attempts in preceding 10 min:** exploratory **8/447 = 1.79%**, but early 2026/27 **2/33 = 6.06%**; this is not stable enough to claim improved selection.
- **Low or high shot rates alone, goals in preceding 15 minutes, total goals at 85, generic attack/defence/points/form proxies**: no sufficiently stable, independently validated directional filter after correction for multiple tests. Do not hard-reject a match purely on these.
- **Prematch L2 model** tested on future dates: AUC≈0.505 (2024/25), ≈0.492 (2025/26), and Brier score worse than constant training prior in both; **not predictive enough** to recommend selecting before kickoff from tested data alone.
- **LIVE85 L2 model**: AUC≈0.523 and 0.541 on two held-out full seasons, negligible/negative Brier improvement. Does not justify replacing a transparent score-state screen.

## 5. Practical frozen protocol (research-only signal, NOT an executable betting system)

1. Before kickoff, select **matches to watch** (not to bet) from available leagues. The tested historic PRE filters are too weak to justify preferring particular clubs or matches.
2. At exactly 85:00 elapsed match time, check **score is level** (any tie: 0:0,1:1,2:2). Flag as **LOWER OBSERVED LAST120 GOAL RISK**. Do not use information that only becomes available after the match.
3. Matches with **score difference ≥2** at minute 85 should **not** be treated as lower-risk selections; observed conditional late-goal rates were higher. 0:0 at 85 may receive descriptive priority but its sample is small.
4. At 90:00 level scores also associate with lower final120 goal incidence, but the actual final-120 segment starts at *an unknown point in the future*. A bookmaker may offer markets such as "goal after 90" or "no more goals", with **different settlement** and a much longer risk interval. The 2.60% is **not** the risk of "no goal from 85 to final".
5. Check **real market wording, entry clock, suspended prices, settlement, effective offered decimal odds** BEFORE interpreting a filter as a bet. No verified tradeable in-play market or real odds were collected; **no tested EV, no demonstrated profit**.
6. No production model overwrite, no auto-promotion. For a credible strategy, prospectively log at least multiple rounds with immutable 85:00 snapshot, quoted in-play prices, and closing/settlement convention, then evaluate draw-at-85 vs all eligible markets and the bookmaker implied probability net of margin.

### Indicative break-even reference, **not executable odds**
For the *hypothetical* exact-final120 event, empirical 2024/25–2025/26 P(no final120 goal | tied at 85)=823/845 ≈97.40%; fair no-margin decimal odds ≈**1.0267**. Early 2026/27 ties gave 70/73 (95.89%), fair ≈**1.0429**, illustrating uncertainty. These numbers **must not** be applied to different markets covering all time after minute 85/90.

## 6. RPL exception

The RPL 2026/27 research covers just 80 matches with four cases lacking decisive seconds for the 120s event. No matched multi-season second-resolution RPL late-goal/shot stream was available in this work. Thus **do not transfer the EPL/La Liga/Serie A tie-at-85 risk percentages directly to RPL** or assert a validated combined four-league portfolio. Draw-at-85 for RPL is a **hypothesis to collect and test**, not a proven RPL criterion.

**Do not merge into production automatically.** This is a completed research-only result plus a prospective validation recipe.
