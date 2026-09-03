# Historical Football Signal Lab — Closure

Status: **CLOSED AS RESEARCH-ONLY**

This block tested whether leakage-safe football-state features derived only from pre-match team history add stable predictive value for 1X2 outcomes, and whether that value survives comparison with bookmaker market probabilities. No production model promotion, Supabase mutation, Structural activation, or `.pkl` modification is part of this block.

## Scope and data

The lab uses EPL, La Liga, and Serie A Football-Data history for 2016-2017 through 2025-2026. Features are built continuously across seasons while each match consumes only information available from prior matches. Expanding-season walk-forward evaluation trains on earlier seasons and tests on the next season.

Total feature rows: 11,400 (3,800 per league). The fixed-window OOS evaluation covers seven test seasons and 2,660 matches per league, except the Serie A market comparison where one row lacks usable market probabilities (2,659 matches).

## Football-only finding

A fixed 10-match football-state window with goals and corners (`CORNERS10`) is the strongest tested football-only specification in all three leagues.

Weighted OOS results:

| League | Accuracy | Brier | Log loss |
| --- | ---: | ---: | ---: |
| EPL | 0.524812 | 0.600803 | 1.007574 |
| La Liga | 0.504511 | 0.606647 | 1.013544 |
| Serie A | 0.519173 | 0.595107 | 0.996756 |

Paired season-by-season robustness is positive against both simpler 10-match baselines. Versus `GOALS10`, `CORNERS10` improves weighted Brier by 0.005147 in EPL, 0.004641 in La Liga, and 0.006509 in Serie A. Brier wins occur in 6/7, 5/7, and 7/7 test seasons respectively. The same direction holds for log loss.

Decision: **retain `CORNERS10` as the canonical football-only research signal**. The 10-match horizon is preferred to the 5-match horizon for this block. This is a research conclusion, not a production promotion.

## Incremental value over market

A fair paired expanding-season test compares a fitted market-only logistic model with the same model augmented by `CORNERS10`. Both variants use the same market-covered rows.

Adding `CORNERS10` does **not** improve the market model:

| League | Δ Accuracy | Δ Brier | Δ Log loss | Brier season wins |
| --- | ---: | ---: | ---: | ---: |
| EPL | -0.009398 | +0.003621 | +0.006270 | 0/7 |
| La Liga | -0.002256 | +0.005055 | +0.007899 | 0/7 |
| Serie A | -0.007898 | +0.003496 | +0.005427 | 2/7 |

Negative deltas are better for Brier/log loss; therefore all three aggregate Brier and log-loss deltas are adverse. The raw de-vigged market benchmark is also extremely strong and remains ahead of football-only specifications.

Decision: **do not add `CORNERS10` to the market model on the evidence from this block**. The football signal is real enough to retain for research, but the tested information is largely subsumed by historical bookmaker prices and does not demonstrate incremental predictive value.

## Injuries and suspensions decision

The historical Football-Data rows used by this lab do not provide a reliable point-in-time injury/suspension state with a verifiable publication timestamp. Retrofitting present-day or post-match squad availability would create unacceptable look-ahead risk. Historical bookmaker prices may also already encode some availability information, which makes an untimestamped injury feature especially difficult to interpret incrementally.

Decision: **do not add injuries or suspensions to this historical block**. A future injury/availability experiment is allowed only as a separate research block with a point-in-time source contract that records, at minimum, fixture identity, player/team, status, source timestamp, first-seen timestamp, and prediction cutoff. It must be evaluated prospectively or against genuinely archived pre-match snapshots before any production consideration.

## Safety and reproducibility evidence

The dedicated Historical Football Signal Lab CI executed the feature builder, fixed-window ablation, paired robustness audit, market incremental audit, and targeted tests. Production `.pkl` hashes were snapshotted before the run and verified unchanged afterward. The last incremental run completed with 10 targeted tests passing and uploaded the full research artifact bundle.

## Final block decision

1. `CORNERS10` is accepted as the strongest tested **football-only** historical signal.
2. It is **not accepted as an incremental market feature** because it degraded paired market-model Brier and log loss in aggregate in EPL, La Liga, and Serie A.
3. Injuries/suspensions are **deferred**, not rejected conceptually; they require a separate timestamp-safe data contract and prospective validation.
4. No production model, calibrator, threshold, live workflow, Supabase schema, or `.pkl` artifact is changed or promoted by this block.

The Historical Football Signal Lab is therefore closed. Further work should begin as a new research block rather than continue tuning this experiment after observing these results.
