# Serie A original frozen V2: first real-quote diagnostic, corrected protected-season embargo

**Run date:** 2026-10-13 UTC. **Research only / NO_BET / not prospective or production**.

## Completed source-to-model evidence

- Existing user-approved market snapshots captured at `2026-10-13T14:48:53Z`: 20 upcoming Serie A events.
- Frozen original candidate SHA `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`; exact 19 football features; `active_lambda=0` (market) vs `shadow_residual_lambda=1`.
- Safeguarded history archive: **10** configured free Football-Data I1 files, seasons 2016/17–2025/26, exactly **3,800** completed matches, original CSV bytes and SHA256 captured on GitHub Actions. **No 2026/27 public results downloaded.**
- [Safe execution run 38421462384](https://github.com/MaksimBlud/football-ai/actions/runs/38421462384) **SUCCESS** on main `ede9dfa9b71d7611a7dd17c83d8cda0e9448861d`: 28 offline tests PASS, 20/20 actual original V2 research previews, zero blocked, zero Odds API calls, zero Supabase writes, no production .pkl changes.
- Immutable job artifact `serie-a-v2-free-real-quote-diagnostic`, artifact **11827095266**, SHA256 ZIP `3ebc99cee27895662745620d01c915d75f45598ad3b60b7607511d1cd2a0fc22` (GitHub reports archive digest), includes machine-readable all-20 market/shadow outputs and 10 original public CSVs. Retained until 2027-01-11 per Actions metadata.

## Real-quote directional diagnostic

Market and shadow most-likely 1X2 outcome **identical for 20/20** fixtures. Mean of per-match maximum absolute change across H/D/A probabilities: **3.20 percentage points**, maximum **6.34 pp**. This does **not** establish higher hit rate, better LogLoss/Brier, or economic value.

Examples, probabilities ordered **H / D / A**, rounded to one tenth of one percent:

| Fixture | De-vigged market | Original V2 inactive residual shadow |
|---|---|---|
| Fiorentina — Como | 27.5 / 26.0 / 46.5 | 21.5 / 25.6 / 52.9 |
| Venezia — Napoli | 19.8 / 23.2 / 57.0 | 15.5 / 21.6 / 62.8 |
| Frosinone — Sassuolo | 38.1 / 26.4 / 35.5 | 41.0 / 29.2 / 29.8 |
| Juventus — Lazio | 57.5 / 24.5 / 17.9 | 61.7 / 25.4 / 13.0 |
| Bologna — Inter Milan | 17.0 / 23.3 / 59.7 | 13.5 / 23.3 / 63.2 |

## Critical frozen boundaries

1. First technical pipeline execution [run 38420548335](https://github.com/MaksimBlud/football-ai/actions/runs/38420548335) fetched 2026/27 public finished scores; it is **SUPERSEDED / DO NOT USE** for any frozen V2 evidence. This is an audit finding, not permission to analyze protected outcomes. Do not incorporate that old artifact in any evaluation or model update.
2. [PR #655](https://github.com/MaksimBlud/football-ai/pull/655) now enforces a *pre-HTTP* hard embargo on the entire current season; even downloading before filtering is forbidden. Corrected diagnostic uses **stale pre-2026/27 form**, so it is not genuine up-to-date model forecasting.
3. The historical raw source observed in the GitHub run **after** the saved bookmaker snapshot; thus source information-time as of the earlier quote **is not attested**. The reported feature-history date is a historical date filter, NOT source capture time.
4. No point-in-time frozen production-incumbent probability has been captured for this exact set. All reports explicitly say `eligible_for_frozen_prospective_cohort=false`, `eligible_for_product_publication=false`, `NO_BET`; prior 30-event outcomes embargo and failed V2 stability gate unchanged.
5. Re-evaluating actual 2026/27 frozen prospective outcomes before the preregistered gate, retraining or promoting V2, or interpreting the shadow as an active production model remains prohibited.

## Operational continuity

The new `.github/workflows/serie-a-v2-free-real-quote-diagnostic.yml` observes historical public sources daily at 06:13 UTC and on relevant pushes; it has **no paid API credential** and stores auditable source bytes. It can run without an active ChatGPT session, but **autonomous software/research decisions and merging are not scheduled by this workflow**. A paid new bookmaker snapshot still requires a fresh separate authorization.

**Next safe research gate:** plan immutable forward-only independent feature source availability, upstream data-time proofs and genuine pre-match frozen incumbent comparison. The 20 saved market predictions are real `MARKET_ONLY`, but do not mislabel as live V2 prospective.
