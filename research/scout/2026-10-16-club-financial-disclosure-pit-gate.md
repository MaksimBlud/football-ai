# Signal Scout — club financial disclosure as-of feasibility (2026-10-16)

Status: IDEA / BLOCKED_BY_SOURCE_COVERAGE_AND_ASOF. Research-only, not a signal. No candidate Issue; no outcome reads or tests.

## Independent mechanism
Filing-time financial resilience shock, not transfer counts or bookmaker microstructure: audited annual wage-to-revenue burden and operating cash-flow / liquidity disclosures may reveal a delayed constraint on squad stability and club operations that pre-match 1X2 market prices do not fully incorporate. Mechanism is speculative; wage bills strongly proxy club quality already priced by market.

Proposed strictly as-of features for each club: (a) most recent published accounts filing date; (b) lag in days between fiscal year end and publication; (c) wage/revenue ratio and operating cash-flow / revenue when separately reported and comparable; (d) change from previous published comparable accounts; (e) missing / non-comparable flag. Feature values must be null until the earliest independently evidenced public release, not fiscal year-end; no imputing private data or future filings. Keep financial entity mappings to exact registered club company and basis (group vs individual).

## Verified official dated evidence, outcome-free
- Manchester City Football Club Limited, Companies House company 00040946: FY2023 accounts filed 2024-04-04; FY2024 accounts filed 2025-03-10; FY2025 accounts filed 2026-03-06.
  https://find-and-update.company-information.service.gov.uk/company/00040946/filing-history
- The Arsenal Football Club Limited, company 00109244: FY2023 filed 2024-03-03; FY2024 filed 2025-03-03; FY2025 filed 2026-02-27.
  https://find-and-update.company-information.service.gov.uk/company/00109244/filing-history
- Brighton and Hove Albion Football Club Limited, company 00081077: FY2023 filed 2024-04-11; FY2024 filed 2025-03-06; FY2025 filed 2026-03-26.
  https://find-and-update.company-information.service.gov.uk/company/00081077/filing-history
- **Critical as-of discrepancy:** Brighton's official club site publicly posted FY2025 accounts on 2026-01-09, before its Companies House filing on 2026-03-26. Earliest release requires document-level independent evidence; Companies House filing date alone is conservative, not necessarily the true earliest available.
  https://www.brightonandhovealbion.com/media-article/club-news-annual-accounts-published-2024-25-season-january-2026
- Prior peer-reviewed motivation (not a bookmaker edge): Garcia-del-Barrio & Agnese, 2023, doi:10.1002/mde.3711; association of wage/revenue with sporting performance, not market-adjusted pre-match prediction.
  https://doi.org/10.1002/mde.3711

Verified here: dated filings for 3 identifiable EPL club entities across three reporting years; *not* verified: 20-club mapping, financial PDF field extraction, cross-club accounting comparability, season-by-season fixture eligibility, official licensing for bulk extraction, any independent OOT support. The verified sample is not a coverage estimate. No match outcomes examined.

## Outcome-free feasibility gate before any Research Brain candidate
1. Freeze EPL clubs and historical seasons BEFORE inspecting results; exact club -> company ID, consolidation basis and dated PDF SHA / publication provenance.
2. For every fixture, compute only the latest filing already public at forecast time (suggest 24h pre-kickoff), with timestamp precision documented. Treat same-day date-only publication as available only next day unless hour is proven.
3. Audit pre-kickoff feature non-null coverage and lag, accounting definitions, comparability, amendments, licensing and safe team identity. No outcomes or post-kickoff match data used in this audit.
4. Require prospectively frozen sufficient 2024/25 validation and 2025/26 independent test fixture support and comparable market 1X2 fair probabilities on exactly matched rows. If provenance/coverage fails: BLOCKED_BY_SOURCE, do not create Issue.

## Preregistered evaluator proposal (Research Brain ONLY, if gate passes)
- Baseline: fitted multinomial logistic calibration of bookmaker no-vig 1X2 only; also raw fair probabilities diagnostic.
- Candidate: same baseline + frozen 4 financial features, missingness indicators and same regularization. No feature/club/year selection on outcomes.
- Train chronologically on eligible earlier seasons, validation 2024/25, untouched independent OOT 2025/26 only if actually unexamined for this hypothesis; otherwise freeze a genuinely later prospective untouched cohort. Do not use protected 2026/27 outcomes.
- Metrics: multiclass Brier and LogLoss paired fixture deltas, season and club clustering / bootstrap. Negative controls: shuffled within-season club assignments; filing availability shifted forward one full year; market-only with same fixture coverage.
- SUCCESS requires validation and untouched OOT both improve both metrics, OOT paired log-loss CI entirely below 0, and no clear league/season instability. STOP on missing PIT, inadequate support, or failure of either metric/CI. No betting/profit/production claim.

## Duplicate/safety gate
Fresh main 328bc3966c657976908acdce94809a11fdd18a24 registry inspected: 13 PROGRAM_DONE and 1 BLOCKED. Team-change program closed for manager/lineup/availability/tactics; financial filings are a different source/mechanism. Searched GitHub issues for finance/wage and branch names for wage/salary/finance/accounts: no exact matches observed. This is not a proof of exhaustive nonduplication.
No GitHub Issue, registry modification, production model operation, Supabase write, paid Odds API request, future outcome read or outcome evaluation.
