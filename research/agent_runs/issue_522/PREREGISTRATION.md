# Frozen corner match-shape falsification protocol

Status: **PREREGISTERED / SAME OPENED SAMPLE / FALSIFICATION ONLY / NO_BET**.

Source: authoritative artifact 11294063833, SHA-256 92b958e6f5f8c911236f5e6451ed2f974d4e02af727637644dc2ad037cd78aa0. Use all 117 usable rows; the 56 non-zero movement rows are the frozen primary direction-comparable set. No new prospective rows.

Frozen score and sign are unchanged: match_shape_gap = historical Ridge expected corners minus opening FAIR_CENTRE; positive predicts UP and negative predicts DOWN. No threshold search, sign reversal, alpha/feature changes, cohort/league selection, or V2B exclusion.

Primary falsification residualizes both match_shape_gap and centre_delta against opening_lambda plus fixed cohort and league effects. Support for future confirmation requires positive residual Spearman on both the 56 non-zero rows and all 117 rows; a one-sided 10,000-draw within-cohort-and-league permutation p <= 0.05 on the non-zero rows; and positive residual Spearman in every predeclared leave-one-cohort-out and leave-one-league-out diagnostic. Diagnostics cannot rescue a failed gate.

Report binary direction separately against always-UP, including UP/DOWN recall and class counts. The shared negative opening_lambda component is reported explicitly. Because outcomes were already opened, even a passing result is only SUPPORTED_FOR_FUTURE_CONFIRMATION and requires a genuinely untouched sample. Otherwise return WEAK_OR_INCONSISTENT_CROSS_MARKET_CORNER_DIRECTION_HYPOTHESIS; unavailable or unverifiable frozen evidence returns BLOCKED_BY_EXISTING_SOURCE_GAP. No paid API, Supabase, production operation, betting claim, or promotion.
