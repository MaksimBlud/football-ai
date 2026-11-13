# MARKET_ANCHOR_1X2_V2 — source-policy recheck and capture block

Date: 2026-11-10  
Scope: original frozen V2 only; source access and inference remain fail-closed.

## New official policy observation

The official Football-Data data page at https://football-data.co.uk/data displays
`Updated: 10/11/26`. Its current wording describes the free CSV/Excel data as
intended for private individuals and excludes commercial or data-training products
using automated bots, scrapers, or AI.

The previous project rights review was recorded on 2026-11-07 against a page date
of 2026-11-06. It is superseded by this newer official-page update.

## Conservative project decision

The project does not infer that an automated GitHub Actions source collector for
an AI-model research pipeline is permitted by the revised wording. Therefore:

- `research_source_capture_permitted=false`;
- `research_source_capture_scope=NONE_PENDING_PROVIDER_CLARIFICATION`;
- automated Football-Data source downloads and source-archive uploads are blocked;
- the two-session weekly limit is a ceiling, not a grant of permission;
- frozen-model inference remains independently blocked;
- AI training, commercial use, public product use, and redistribution remain disabled.

This is a conservative internal control pending provider clarification, not a legal
conclusion about all manual personal or academic research.

## Preserved V2 contract

No change to the original candidate SHA, 19-feature order, weights, scaler/imputer,
training cutoff, `active_lambda=0`, `shadow_lambda=1`, market fallback, source-before-quote
logic, 24-hour quote-age rule, 30-primary-event target-outcome gate, NO_BET policy,
or production model artifacts.

## Runtime and data-access limits

This change reads only the public policy page and repository metadata already in
GitHub. It does not download Football-Data CSVs, read Supabase, inspect quote values
or target outcomes, call paid providers, write Supabase, change schedules, or
change repository visibility. Private repository storage remains a separate
requirement if a future provider clarification permits source archival.
