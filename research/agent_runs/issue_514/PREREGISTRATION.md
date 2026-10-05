# Frozen kickoff/calendar league-heterogeneity protocol

Status: **PREREGISTERED / DIAGNOSTIC / POOLED NULL NOT RESCUABLE**.

Fixed leagues: EPL, La Liga, Serie A.
Reference/train: 2019/20–2023/24; validation: 2024/25; untouched test: 2025/26.
Use exactly the parent market baseline and calendar feature design.
Compute per-match calendar-minus-baseline log-loss deltas for all three leagues.
Test all three predeclared league pairs; no pair may be selected after seeing results.
Use Bonferroni familywise alpha 0.05 across the three pairwise comparisons (98.3333% bootstrap CI per pair).
Stable heterogeneity requires the same pairwise difference to exclude zero in both validation and OOT with the same sign.
Any league-specific result is diagnostic only and cannot rescue the rejected pooled kickoff/calendar hypothesis.
No arbitrary kickoff cutoffs, league selection, paid data, Supabase, production operation or promotion.
