# Original MARKET_ANCHOR_1X2_V2 — Lega Serie A match-report source audit

**Audit date:** 2026-11-19  
**Decision:** **HOLD — official source extraction/use requires express written consent; no permission is recorded.**  
**Scope:** official Lega Serie A Terms and Conditions, the 28 August 2026 “TRUE DATA” notice, and the public README of a third-party Serie A Observatory repository. This is a source-rights/provenance screen only.

## Why this source was considered

The third-party [Serie A Observatory](https://github.com/matteovezzoli/serie-a-observatory) describes a weekly-updated 2026/27 dataset parsed from official Lega Serie A Match Report PDFs. It says its report log records publication and last-update dates, and that reports can be republished/corrected 0–12 days after a match. This makes it a technically interesting current-season source candidate for investigating point-in-time provenance.

The repository README explicitly says the match data belongs to Lega Serie A and is **not covered by the repository's MIT code licence**. The PDFs are not included in the repository because of size and rights. No dataset CSV, PDF, API, or source payload was downloaded or inspected for this audit.

## Binding rights blocker

The official [Lega Serie A Terms and Conditions](https://en.legaseriea.it/terms-and-conditions), updated 1 December 2025, section 5.2, state that extraction and/or use of content made available through the League's tools, in whole or in part, requires express written consent; the examples include data mining, robots, and similar data-gathering/extraction tools.

The League's [28 August 2026 TRUE DATA notice](https://www.legaseriea.it/serie-a/news/al-via-la-campagna-true-data-a-tutela-del-dato-ufficiale) further describes official competition data as a strategic asset and says commercial exploitation of official data is through official League data licences.

No written permission or data licence is present in this project context. Therefore this audit does **not** authorize automated capture, manual extraction, copying the third-party processed CSVs, internal ML training/inference, private raw retention, or commercial/product use. Public visibility and a third-party parser do not establish permission from the data owner. This is a conservative engineering eligibility decision, not legal advice.

## Feature and provenance limits

- The third-party README describes team/player statistics but does not establish complete fixture-level parity with all 19 frozen V2 features.
- Exact corners and red-card semantics, missing-value policy, and complete 2026/27 coverage have not been independently verified.
- The third-party reports log's publication/last-update fields are not a provider-guaranteed first-observation/correction API contract.
- A report can be corrected after the match. A third-party repository commit time or current CSV state cannot prove what value was available before an individual bookmaker quote.
- No source archive, SHA, or source-before-quote evidence was created.

## Decision

**HOLD. Do not scrape the League site, call its content API, download match reports, or ingest the third-party parsed dataset for V2 without express written permission covering the intended use.** If permission is later obtained, first verify the precise rights scope, 19-feature parity, per-field correction semantics, and a private immutable source archive with SHA-256 captured strictly before each quote.

## Frozen model invariants

The original candidate remains unchanged:

- Candidate SHA-256: `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`.
- Training fingerprint: `f27ab985ae90bb8e94ba8d548847695888c232f43b3e9be93074f39e1a7a5098`.
- 3,799 training rows; exact 19-feature order; 20×2 weights.
- `active_lambda=0`; `shadow_residual_lambda=1`.
- Stability gate remains FAILED; 30-primary-completed-event evaluation gate remains CLOSED; no automatic promotion.

## Validation and safety

This PR adds only a HOLD manifest, this audit note, and offline contract tests. It makes no provider/API request, downloads no source data, reads no Supabase data, accesses no protected outcomes, calculates no features, runs no inference, and changes no model, production artifact, schedule, or other agent. The validation workflow is PR/push-only, secret-free, and uses immutable GitHub Action commits.

**HUMAN-MERGE only. No main update or automatic merge.**
