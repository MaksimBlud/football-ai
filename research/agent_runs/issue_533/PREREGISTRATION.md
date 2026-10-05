# Frozen de-vig method OOS protocol

Status: **PREREGISTERED / TEMPORAL OOS / RESEARCH ONLY / NO_BET**.

Question: which standard 1X2 margin-removal transform is most accurate for Football AI: Multiplicative, Additive, Power, or Shin?

Frozen source scope: EPL, La Liga, Serie A; free Football-Data historical transport only. Frozen bookmakers: Bet365 and Pinnacle (PS columns). Opening and closing 1X2 are both evaluated. A bookmaker is eligible only when its required opening+closing columns exist for every validation/test league-season. Source/header audit is completed before reading FTR outcomes. No proxy bookmaker, interpolation, paid API, Supabase or production source is permitted.

Temporal design: 2019/20-2023/24 reference only; 2024/25 validation selects at most one alternative candidate; 2025/26 is untouched confirmation and must not select the winner.

Transforms are exact standard definitions. Invalid rows are reported, never silently clipped. Method coverage must be at least 99%.

Primary horizon: closing. The validation candidate is the eligible alternative with the lowest pooled validation closing Log Loss, but only if it beats Multiplicative. If no alternative beats Multiplicative in validation, final status is NO_STABLE_DEVIG_WINNER.

Untouched 2025/26 confirmation requires all of:
1. candidate closing Log Loss delta vs Multiplicative < 0;
2. fixture-cluster paired-bootstrap 95% CI upper bound < 0;
3. closing Brier and RPS deltas <= 0;
4. opening Log Loss sensitivity delta <= 0;
5. negative Log Loss delta in both frozen bookmakers;
6. negative Log Loss delta in at least two of three frozen leagues;
7. candidate validity coverage >= 99%.

Passing returns PROJECT_BEST_DEVIG_CANDIDATE. Failing returns NO_STABLE_DEVIG_WINNER. Missing multi-bookmaker source coverage returns BLOCKED_BY_SOURCE_GAP.

Even a pass creates only a research candidate for a separate untouched promotion study. No production replacement, automatic promotion or betting claim.
