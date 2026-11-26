# Lega Serie A report-derived dataset — original V2 source audit

**Checked:** 2026-11-21 22:53:56 UTC  
**Decision:** HOLD / NO INTEGRATION  
**Scope:** Potential free, lagged Serie A match-statistics source for the unchanged original `MARKET_ANCHOR_1X2_V2`. No data ingestion or inference is authorized by this audit.

## Why it looked promising

The public [Serie A Observatory repository](https://github.com/matteovezzoli/serie-a-observatory) describes a 2026/27 dataset extracted from official Lega Serie A Match Report PDFs and updated weekly. Its README lists:

- `matches.csv`: match result and home/away team statistics;
- `players.csv`: player match sheets;
- `reports.csv`: competition, report publication date and last-update date;
- 16 team-level statistics, plus player-level goals, shots, cards and other measures.

The README says reports may be corrected **0–12 days after a match** and the weekly pipeline re-downloads changed or republished reports. This makes the source technically interesting for lagged form reconstruction, but it also means a CSV revision can alter previously stored match statistics.

## Rights finding — decisive HOLD

The repository exposes an MIT `LICENSE`, but its text licenses the **Software and associated documentation**. It is not a separate upstream data license and cannot grant rights that the repository owner does not hold in the underlying Lega Serie A content.

The official [Lega Serie A Terms and Conditions](https://www.legaseriea.it/terms-and-conditions), updated **1 December 2025**, state:

- use of the platform tools is exclusively for personal and non-commercial purposes;
- extracting or using platform content, including data collections, is not permitted without express written consent;
- data mining, robots or similar acquisition/extraction devices are explicitly included in the restriction.

The Observatory README says its own weekly pipeline queries the public content API, downloads Match Report PDFs and republishes extracted CSVs. That third-party implementation is **not** permission for this project to repeat the extraction or use the derived dataset for internal ML. No express written consent or upstream data-rights grant was found.

## Source-before-quote limitations

The README says `reports.csv` records publication and last-update **dates**, but the inspected documentation does not establish exact per-stat first-observed timestamps. A local SHA-256 taken after an authorized copy could prove that the local bytes existed before a later quote; it would not prove when each upstream statistic first became available.

Because reports can be corrected 0–12 days after a match, the pipeline would also need immutable per-version bytes, publication/update provenance, and a strict as-of cutoff. None of that can be inferred from the weekly CSV alone.

## Frozen V2 compatibility

The candidate is technically interesting because match results and team/player statistics may overlap with the original goals, corners and card inputs. However, exact mapping to all **19 frozen features**, the original rolling windows, venue windows, imputation behavior and pre-quote availability has not been verified. No adapter should be built while rights remain unresolved.

The original candidate SHA, 19-feature order, weights, scaler/imputer, `active_lambda=0`, `shadow_lambda=1`, stability gate and both preregistered gates remain unchanged.

## Decision

**HOLD / NO INTEGRATION.** Do not scrape the official content API, download the PDFs or CSVs, fork the dataset into the project, or use it for V2 inference unless written permission explicitly covers automated extraction, internal ML use, private raw retention and the required timestamp/provenance chain.

No provider account or API key was created. No source file was downloaded. No Supabase access/write/DDL, quote read, protected-outcome read, inference, model change or production artifact change was performed.

## Evidence

- Repository and README: https://github.com/matteovezzoli/serie-a-observatory
- Repository LICENSE: https://github.com/matteovezzoli/serie-a-observatory/blob/main/LICENSE
- Official Lega Serie A terms: https://en.legaseriea.it/terms-and-conditions
