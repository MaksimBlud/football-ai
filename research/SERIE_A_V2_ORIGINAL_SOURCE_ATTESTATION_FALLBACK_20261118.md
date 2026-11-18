# Original V2 source attestation: reject partial newest artifact, fall back only to verified archive

Date: 2026-11-18

## Live evidence

- Original forward workflow run 44138236517 on main SHA 40887ebb215730190d7a6c7a1693373ec4afcdfc passed 71 offline tests, then failed in serie_a_v2_attest_real_source.py with source artifact parent run is not the verified original V2 collector. The quote-read and inference step was skipped.
- The newest matching source artifact was published by failed source workflow run 44119690306. That parent run concluded failure, but its final artifact-upload step succeeded because the workflow uses if: always(). Artifact ID: 14345106143, digest sha256:65b3d07e941ff9bb34040f14adcf715d93e7da6de78edeac1dfd29ee29d89153.
- The source workflow path is the expected .github/workflows/serie-a-v2-free-real-quote-diagnostic.yml; the failure is not a wrong workflow name. It is a failed parent execution whose partial artifact was nevertheless uploaded.
- Existing PR #830 adds a robust source preflight to the forward-capture module, but the workflow runs serie_a_v2_attest_real_source.py first. That earlier attestation still selected only the newest artifact and therefore stopped before the #830 fallback logic could execute.

## Change

The attestor now orders all source artifacts newest-first and validates each candidate's artifact identity, parent run identity and SHA, exact workflow path, successful completion time, ZIP bytes, independent GitHub SHA-256, ten frozen historical CSV members, source row counts, original frozen V2 candidate identity, and old-season-only embargo.

A candidate-specific failed parent, missing GitHub resource, invalid ZIP, malformed CSV, or digest mismatch is recorded and skipped. Transient/non-404 GitHub HTTP failures are not swallowed. The attestor chooses the newest fully verified candidate and reports rejected artifacts and whether fallback was used. If no candidate verifies, it still fails closed.

## Safety boundary

This is source-archive attestation only. It does not read odds, query Supabase, read protected 2026/27 outcomes, download from the football-data provider, generate forecasts, alter weights/features/lambdas, train, settle, publish predictions, or write to production. It does not authorize the daily source workflow; provider-rights/default-deny PR #781 remains a separate prerequisite. Existing October 13 quotes remain ineligible if no independently verified source archive predates each quote.

## Regression coverage

Added tests for skipping a newer failed parent, skipping a newer archive with a bad digest, rejecting a parent completion time that is not strictly before attestation, and retaining fail-closed behavior when no candidate verifies.

The PR is based on #830 and must remain unmerged until its parent chain and exact-head CI are reviewed.