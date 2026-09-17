# BOOKMAKER_CORNERS_BLOCK_CLOSURE_V1

## Status

`CLOSED / COLLECT / EXTERNAL_CREDENTIAL_REQUIRED`

This closes the current bookmaker-corners research block without claiming a model-vs-market result that has not been measured.

## What is established

- `CORNERS10` remains a football-state signal from prior historical research.
- That football-state result is **not** evidence of bookmaker-corner market edge.
- The project did not have stored historical bookmaker corner line+price data suitable for a proper market comparison.
- `BOOKMAKER_CORNERS_SOURCE_AUDIT_V1` identified TotalCorner as the primary historical source candidate because it exposes historical corner line, Over/Under prices and timestamped line changes through an official API.
- The source client/parser is implemented fail-closed: no `TOTALCORNER_TOKEN` means no TotalCorner network request.
- `TOTALCORNER_CORNER_HISTORY_PILOT_V1` is frozen and implemented as an acquisition-only 30-match pilot: 10 EPL, 10 Serie A, 10 La Liga fixtures, with per-league PASS requiring at least 8/10 fixtures with valid strictly pre-kickoff bookmaker corner snapshots.
- A manual-only GitHub Actions runner is merged and reads the credential only from the `TOTALCORNER_TOKEN` repository secret. It does not run on push or pull request.

## What is NOT established

- The TotalCorner live 30-match pilot has not been executed because no `TOTALCORNER_TOKEN` has been supplied.
- The source therefore has not yet earned `SOURCE_QUALIFIED` status from the frozen pilot.
- No bookmaker-corners model-vs-market experiment has been run.
- No bookmaker-corners betting edge, ROI, calibration advantage, closing-line advantage or production readiness has been demonstrated.

## Decision

Current market decision for bookmaker corners: **`COLLECT`**.

This block is considered complete for the current research cycle. Do not spend further engineering or research time on bookmaker-corners until new external data become available.

Reopen condition:

1. an explicitly authorized TotalCorner VIP token is made available as GitHub repository secret `TOTALCORNER_TOKEN` (or an equivalent lawful historical line+price dataset is supplied);
2. run the already-frozen `TOTALCORNER_CORNER_HISTORY_PILOT_V1` once;
3. only if the pilot returns `SOURCE_QUALIFIED`, freeze a separate bookmaker-corners model-vs-market experiment before opening any predictive result.

If the pilot returns `SOURCE_NOT_QUALIFIED`, keep bookmaker corners closed and do not broaden or retune the acquisition gate after seeing the result.

## Completed implementation record

- PR #367: source audit + TotalCorner fail-closed parser/client.
- PR #368: frozen 30-match acquisition pilot + tests/CI.
- PR #369: manual-only live pilot workflow.
- PR #370: closed as duplicate of the already-merged live-runner change.

Source-of-truth `main` at closure start: `77ab0c10529272fb7090f67c0dc25b164577dfbb`.

## Safety

- research-only;
- `NO_BET`;
- no production model promotion;
- no production `.pkl` modification;
- no Supabase writes;
- no paid request without explicit credential authorization;
- no website scraping around a paid API;
- no claim of bookmaker-corners edge until a separately frozen market experiment is executed.