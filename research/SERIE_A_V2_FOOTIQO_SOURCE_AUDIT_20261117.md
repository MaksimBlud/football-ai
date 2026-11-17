# Original MARKET_ANCHOR_1X2_V2 — Footiqo free-source audit

**Audit date:** 2026-11-17  
**Decision:** `HOLD — relevant free Serie A tables and non-commercial ML permissions exist, but automated capture and complete frozen-feature provenance are not cleared**  
**Scope:** Footiqo's public Terms of Use, Dataset Licence & Data Access Policy, Italy Serie A database page, current-season statistics pages and dataset overview. No account was created, no export/download was performed, no website scraping or private endpoint was used, and no API exists in the reviewed documentation.

## Executive result

Footiqo is a materially more promising research-only candidate than a fixtures-only feed. Its Dataset Licence (last updated 2026-10-08) explicitly permits personal non-commercial research, predictive-model development/testing, machine-learning experiments, calculated features/probabilities and private storage of legitimately obtained files. Manual CSV/Excel exports through normal website controls are permitted.

The public Serie A 2026/27 match table visibly contains:
- full-time home/away goals and result (`FTHG`, `FTAG`, `FTR`);
- full-time home/away corners (`HCFT`, `ACFT`);
- full-time home/away yellow cards (`HYCFT`, `AYCFT`).

Those fields provide candidate mappings for **17 of the original 19 frozen features**. The reviewed Serie A table does not expose red-card counts, leaving `diff_red_5` and `diff_red_10` unsupported. This is only a visible schema mapping; it is not proof that every 2026/27 match has complete, stable values.

**The decisive blocker is automated access.** The 2026-10-08 policy permits manual exports but expressly prohibits automated scraping/crawling, automated CSV/Excel/export downloads and bulk extraction unless Footiqo gives separate written authorization. There is no public API. This hourly research process therefore cannot collect the data automatically under the current public policy.

## Positive evidence

- The official Dataset Licence permits personal, non-commercial research and internal analysis, including predictive-model development/testing, ML experiments, calculated features and probabilities.
- Legitimately downloaded data may be stored locally or in private databases and retained after the included update period.
- The public Italy Serie A database page exposes current-season 2026/27 match rows and offers CSV/Excel exports through normal website controls.
- The Scores table documents `FTHG`, `FTAG`, `FTR`, match date and home/away identities.
- The Corners & Cards table documents `HCFT`, `ACFT`, `HYCFT`, `AYCFT`, plus first/second-half splits.
- Public Serie A corner-statistics pages are labelled free and updated daily.

## Blocking gaps

1. **Automated collection is not permitted by default.** The Dataset Licence allows manual exports, but says automated scraping/crawling, automated CSV/Excel exports, automated dataset downloads and private endpoint extraction require separate written authorization. A low request rate does not create an exception. No automated fetch, browser-driven export or hidden endpoint may be used.
2. **Two frozen red-card features are not mapped.** The reviewed Serie A Corners & Cards table contains yellow-card fields but no red-card fields. Do not infer red cards from yellow-card totals or from a generic "Cards" label.
3. **Per-match source timing is missing.** Public statistics pages say they are updated daily, but the reviewed match rows do not include a per-match/per-field source-observation time or correction timestamp. A manual export receipt timestamp and SHA could prove when our exact copy existed before a later quote, but no such export was performed and the provider's upstream first-observation/correction time would remain unknown.
4. **Coverage and null semantics are not fully verified.** The terms state that coverage varies by competition, season, match and field, and that sources/methodologies can vary. The public page proves candidate fields exist; it does not prove 100% match-level completeness or consistent missing-value semantics for all Serie A 2026/27 fixtures.
5. **Upstream rights are not fully identified.** The policy grants only permissions Footiqo is entitled to provide and notes that football facts/third-party content may carry separate rights. The reviewed pages do not identify the upstream provider or rights for every required field.
6. **Commercial use is not covered by the standard permission.** The standard licence is for personal, non-commercial research/internal analysis. Any public/commercial product use would require separate written permission.
7. **Free downloads are samples.** The dataset overview describes four free samples. The comprehensive multi-season historical database is a paid product. No paid product was used; the frozen V2 training artifact was not changed.

## Frozen V2 feature mapping

The original candidate JSON was re-read from main and is pinned in the offline regression. The manifest preserves the exact 19-feature order and original candidate identity.

| Frozen feature family | Count | Visible candidate fields | Audit status |
|---|---:|---|---|
| Points/goals, including venue splits | 9 | `FTHG`, `FTAG`, `FTR` | Candidate mapping only; coverage/semantics unverified |
| Corners, including venue splits | 6 | `HCFT`, `ACFT` | Candidate mapping only; coverage unverified |
| Yellow cards | 2 | `HYCFT`, `AYCFT` | Candidate mapping only; coverage unverified |
| Red cards | 2 | None in reviewed Serie A table | Unsupported |

No feature was built or calculated. No original weight, scaler, imputer, candidate SHA, training fingerprint, lambda or evaluation gate was changed.

## Source-before-quote and SHA

A future *manually permitted* export could be hashed immediately and retained privately with a trusted UTC receipt time. If that receipt precedes the quote, it can establish that the project possessed that exact export before the quote. It does not establish when Footiqo or its upstream provider first observed or corrected each field.

No export was performed, so there is no source SHA, receipt timestamp, parent-run attestation or source-before-quote proof for this candidate.

## Decision and required clearance

Keep Footiqo on **HOLD** for the automated V2 workflow. Reconsider only after:
- written permission for automated, low-rate collection of the normal public export/API-equivalent data;
- confirmation of upstream rights for all required statistics;
- documented red-card counts with stable semantics;
- exact Serie A 2026/27 per-match completeness and missing-value rules;
- an acceptable source timestamp/correction policy and private archive process;
- confirmation that any intended use remains within the non-commercial research licence, or separate commercial permission.

No account, key, API request, website scraping, automated/manual export, data download, odds request, Supabase read/write/DDL, feature calculation, inference, training/refit, target-outcome read, production `.pkl` change, schedule change, promotion or betting occurred.
