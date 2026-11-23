# MARKET_ANCHOR_1X2_V2 — Football-Data policy recheck

- Review timestamp: 2026-11-21T11:52:37Z
- Official data page: https://football-data.co.uk/data
- Official fair-use/contact page: https://football-data.co.uk/contact.php
- Both pages displayed the update date 20/11/26 when reviewed.

## Observed scope

The current data page describes the free CSV/Excel material as intended for private individuals and excludes commercial or AI data-training products using automated bots, scrapers, or AI. The fair-use/contact page describes personal betting or academic research as the intended individual use and limits automated downloads to light use, at most twice per week. It also says permission should not be assumed for other uses when a request receives no response.

## V2 decision

The project has no provider-issued written permission or open licence for automated source capture, frozen-model inference, or AI model training. Therefore the manifest remains fail-closed:

- automated source capture: denied;
- frozen V2 inference: denied;
- AI model training: denied;
- commercial/public product use: denied;
- authorization evidence: null.

The two-downloads-per-week statement is a ceiling within the provider's described personal/academic use; it is not a grant for this AI workflow. The daily GitHub Actions schedules are not changed here. The separate workflow-level default-deny PR remains necessary until manually integrated.

This is a conservative project access-control decision, not a legal conclusion about every form of manual personal research.

## Non-actions

No Football-Data CSV was downloaded. No saved quote, target outcome, or protected 2026/27 score was read. No Supabase access/write/DDL, paid provider request, inference, training, refit, threshold tuning, production model change, schedule change, or merge was performed.
