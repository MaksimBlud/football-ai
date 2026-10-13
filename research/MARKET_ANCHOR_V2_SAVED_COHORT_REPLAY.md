# MARKET_ANCHOR_V2_SAVED_COHORT_REPLAY

## Purpose

This is a research-only post-outcome diagnostic replay of the exact frozen `MARKET_ANCHOR_1X2_V2` Serie A residual on the saved Serie A portion of `POINT_IN_TIME_CROSS_LEAGUE_REPLAY_V1`.

It is **not** untouched OOT evidence and is **not** a prospective activation test. The outcomes were already known before this replay was executed. No replay outcome was used to select the feature set, lambda, L2 penalty, or training window.

## Frozen provenance

- Frozen V2 commit: `df19777087fb89af049eedce44ff93f0aa6e6360`
- Primary league: `SERIE_A`
- Feature variant: `ALL_FOOTBALL`
- Shadow residual lambda: `1.0`
- Active lambda: `0.0`
- L2 penalty: `1.0`
- Training seasons: 2016-2017 through 2025-2026
- Training cutoff: 2026-06-30
- Target feature-history cutoff: before 2026-09-11
- Exact historical source modules are restored from Git and pinned by Git blob SHA before the replay runs.

The frozen V2 residual was defined for Serie A only. Therefore only the ten Serie A events inside the saved 47-event cross-league cohort are contract-valid here. Applying the same residual to EPL, La Liga, Bundesliga, Eredivisie, or Ligue 1 would be off-contract and is intentionally not done.

## Result

| Comparator | Accuracy | Brier ↓ | LogLoss ↓ |
|---|---:|---:|---:|
| Saved market | **0.6000** | 0.5662948174 | 0.9674878847 |
| Frozen old production model | 0.5000 | **0.5265153874** | **0.9062022313** |
| Frozen V2 shadow, lambda=1 | **0.6000** | 0.5616083081 | 0.9612922294 |

Frozen V2 shadow versus the saved market:

- accuracy delta: `0.0000` — same 6/10 top-pick accuracy;
- Brier delta: `-0.0046865093` — better;
- LogLoss delta: `-0.0061956553` — better;
- relative Brier improvement: about `0.83%`;
- relative LogLoss improvement: about `0.64%`;
- dual probabilistic metric comparison: **shadow better than market on both metrics**.

The old production model is probabilistically better than both market and V2 shadow on this very small ten-match Serie A subset, despite lower 1X2 accuracy. This does not reverse the broader saved-cohort result where the old model underperformed the market across roughly 58 unique fixtures. It is a reminder that a ten-match subset is too small for activation decisions.

## Interpretation

This replay is encouraging because the already-frozen football residual moved the market in a direction that improved both Brier and LogLoss without changing top-pick accuracy on the ten eligible Serie A matches.

It does **not** prove sustainable edge. The sample is only ten matches and the outcomes were already known when this diagnostic was run. The original V2 stability gate remains failed, so the active V2 contract remains exact market fallback with `active_lambda=0`.

No betting is enabled, no production model is promoted, and no production `.pkl` artifact is modified.

## Decision

- Keep `MARKET_ANCHOR_1X2_V2` active lambda at `0.0`.
- Keep the `lambda=1` Serie A residual as research evidence only.
- Do not generalize this residual to other leagues.
- Do not tune lambda or features on these ten outcomes.
- Use this result only as motivation to continue the already-planned **prospective** evaluation on fresh, strictly pre-kickoff data.
- The next meaningful proof must come from a fresh prospective cohort, ideally against the stronger bookmaker-consensus baseline now being captured at bookmaker level.

Canonical machine-readable result: `experiments/market_anchor_v2_saved_cohort_replay_report.json`.

## Research artifact restoration from abandoned PR #337 — 2026-10-13

The earlier PR #337 contained the exact frozen replay and **passed** its
dedicated historical reconstruction check, but also shipped an unrelated
`pr337-continuity-append.yml` that failed with a Python multiline-string
syntax error. The result never entered `main`. Rather than rewrite or
retune the research, this recovery branch copies the identical frozen
report, cohort, loader and tests from PR #337 onto fresh `main`, **without**
the broken continuity-writing workflow.

The new `Recover Frozen Market Anchor V2 Candidate` workflow:
1. Restores the 15 September frozen source commit and validates the three
   exact Git blob hashes.
2. Refits the **unchanged Serie A** 2016–2026 residual from the public
   historical files only, with pinned dependencies.
3. Verifies all saved source-file SHA256 hashes, the exact `3799` training
   observations, the training fingerprint, the candidate artifact SHA256,
   every fixed event and its saved result, and all three comparator metrics.
4. Writes the actual **JSON candidate weights**, including scaling and
   imputation, only to the ignored path
   `artifacts/market_anchor_v2_saved_cohort_replay/candidate_model.json`.
   This is a research candidate, **not** a `.pkl` promotion.
5. Uploads those weights and the replay report to a GitHub Actions artifact
   (30-day retention); the weights can be deterministically regenerated
   later from the frozen recipe if the temporary download expires.
6. Refuses promotion, paid provider requests, SQL writes or changes to
   production model files. Verifies production `.pkl` hashes before/after.

**Frozen expected candidate SHA256:**
`a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`.

**Frozen training fingerprint:**
`f27ab985ae90bb8e94ba8d548847695888c232f43b3e9be93074f39e1a7a5098`.

A passing artifact-recovery job proves that the previously built V2 weights
can be recovered. It **does not** reopen the failed V2 stability gate, turn
the shadow into production or claim model outperformance on unseen games.
The artifact applies only to Serie A, not to EPL or all five leagues.
