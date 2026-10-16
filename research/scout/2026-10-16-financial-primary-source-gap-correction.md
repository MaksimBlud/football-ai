# Signal Scout — original-source recovery for missing finance fields (2026-10-16)

Status: IDEA / BLOCKED_BY_ASOF_AND_BASELINE_RIGHTS. Continuation of CLUB_FINANCIAL_DISCLOSURE_ASOF_V0, not a new candidate and not a verified predictive signal. Outcome-free.

## Context and dedup
Read fresh main 328bc3966c657976908acdce94809a11fdd18a24, research/programs/registry.json (13 PROGRAM_DONE, 1 BLOCKED), PROJECT_CONTINUITY.md, existing scout finance report and searched research/scout Issues. No exact finance candidate Issue found. The team-change, market-microstructure and market snapshot programs are not reopened.

## New primary-source discovery
1. Burnley FC Holdings Limited (company 08335231): the club's own official accounts page publishes the FY ended 2025-07-31 audited consolidated annual report, linked as a 37-page PDF. The strategic report states turnover GBP 71.7m (FY2024: GBP 133.6m) and wage/turnover ratio 114.65% (FY2024: 69.94%). The report was signed 2025-12-22. **Signature is not evidence of public availability that day.** This report is a real financial field source that the previous third-party index lacked. https://www.burnleyfootballclub.com/club-accounts ; https://assets.ctfassets.net/pxdskn6sumdq/2uiPtmo7L7iKIR0Bh607WH/6c334a259965795bf0f17a2523af768e/clubaccountsarticle.pdf
2. Nottingham Forest Football Club Limited (company 01630402): the official Companies House filing-history register contains full FY ended 2025-06-30 accounts, filed **2026-03-26**, with downloadable original PDF and iXBRL. A separate secondary extractor reports turnover GBP 221.746m but **the number has not yet been verified directly inside the original PDF in this run**, so it is not accepted as an audited extracted feature. https://find-and-update.company-information.service.gov.uk/company/01630402/filing-history ; https://fixtureshark.com/football/teams/nottingham-forest/finances
3. The original Burnley auditor report contains a material-uncertainty-going-concern paragraph. This is a *possible* qualitative accounting risk field within the same existing hypothesis family, not a separate signal; publication-time and comparability gates still apply. Do not interpret it as evidence of future match results.

## What changed and what did not
The prior Dragon Football index lacked turnover for Burnley and Forest, giving only an **index-specific theoretical ceiling** of 306/380 fixtures with two fully populated clubs. Official Burnley accounts demonstrably contain turnover; the Forest official filing is present and a second source reports turnover. Therefore the 306/380 index ceiling **must not be generalized to primary sources**. This does **not** prove 20/20 valid financial feature coverage, a new fixture count, historical PIT coverage, or permission to bulk extract any third-party index.

## Frozen feasibility before handoff
- Pin each original legal entity and consolidation basis; capture source URL, SHA256, first independently evidenced publication timestamp (date-only releases available no earlier than following UTC day), reporting period length, accounting basis, amendments and field definition.
- Match only already-public financial versions to each kickoff minus 24 hours, both clubs, with no outcomes read.
- For Burnley, signed 2025-12-22 is NOT a release timestamp. For Forest, 2026-03-26 is a conservative release floor absent proof of earlier publication. Neither FY2025 filing can be used for August 2025 forecasts.
- Audit the entire predeclared EPL cohort, historical season-by-season non-null fields, fair bookmaker baseline from an authorized source on identical fixture/time rows, and truly independent OOT. The Football-Data website explicitly restricts heavy AI/bot training downloads; third-party index usage also requires permissions.
- If feasible, Research Brain alone freezes matched market-only vs market+finance models, temporal train/validation/OOT, paired multiclass Brier and LogLoss, clustered CI and negative controls (club-shuffle, delayed release, matched market-only). SUCCESS only if both metrics improve in validation and independent OOT and OOT log-loss CI excludes zero; otherwise STOP. Scout must not test outcomes.

## Cycle result
One useful **source correction** to an existing hypothesis, zero new independent hypotheses, zero DATA_FEASIBLE, zero Research Brain handoffs, zero Issues, zero outcome reads, zero paid calls and zero production/Supabase/registry changes. Duration comparability not available. No profit claims.
