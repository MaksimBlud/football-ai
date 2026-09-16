# LA_LIGA_MULTIMARKET_ANCHOR_V5

V3 rejected a global football residual over the POWER 1X2 market. V4 found a tiny validation-only conditional improvement that reversed on untouched 2025-26. V5 therefore changes the information set rather than adding gate complexity.

Question: do historical pre-match totals and Asian-handicap prices contain incremental 1X2 information beyond the fixed POWER 1X2 prior?

Frozen design: La Liga only; train 2016-17..2023-24; selection 2024-25; untouched OOT 2025-26; no 2026-27 outcomes. Candidate feature sets are 1X2 only, 1X2+O/U2.5, 1X2+AH, and 1X2+O/U2.5+AH. Logistic regression regularization is fixed at C=0.1. Missing historical secondary-market prices are median-imputed using training data only. A candidate must beat POWER 1X2 on both Brier and LogLoss on validation and again on OOT; otherwise active mode is exact POWER market fallback.

This is a market-information diagnostic, not a football residual experiment and not a production candidate. NO_BET; no production promotion; no Supabase writes; no paid Odds API calls; production model hashes must remain unchanged.
