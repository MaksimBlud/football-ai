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

## Recovering the real September V2 model weights — 2026-10-13

The earlier PR #337 **passed** its original exact frozen Serie A reconstruction
but never merged. Its unrelated continuity-write workflow failed from a Python
multiline-string syntax error. This branch recovers its original research code,
test fixtures, frozen report and provenance on current `main` **without** the
broken workflow.

A fresh attempt to re-run the *full* historical replay on 2026-10-13 did not
match all the originally recorded input-file SHA256 hashes. The public
Football-Data `2026/27` season CSV changes as new games are appended, so its
full-file September digest is no longer a valid fixed identifier for a
download performed in October. **The old September replay report is not
modified or passed off as a new prospective result.**

Importantly, the frozen residual's **training ends June 2026**. The ongoing
2026/27 CSV is relevant to the later target-feature replay, **not to
recovering the trained model's weights**.

The dedicated recovery job therefore:

1. Restores the **exact September Git source commit** and validates all three
   frozen Git blob hashes.
2. Downloads **only the original ten training seasons** 2016/17–2025/26,
   compares **each original SHA256** against the archived report, and fails if
   any archived training input has changed.
3. Refits the exact **3,799-row training recipe**, validates the frozen
   training-fingerprint SHA256 and model-artifact SHA256. No model is accepted
   without byte-identical model-digest proof.
4. Saves the **actual learned coefficients, scaler and imputer** into
   `artifacts/market_anchor_v2_saved_cohort_replay/candidate_model.json`,
   plus `recovery_manifest.json`. Those paths are research-only and ignored
   by Git; a successful GitHub Actions recovery uploads both as an artifact
   for 30 days. The artifact can be regenerated from the pinned training
   recipe later.
5. Does **not fetch 2026/27 data, score known target outcomes, evaluate a
   new candidate or modify any production model or database.**

Frozen expected candidate SHA256:
`a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`.

Frozen training fingerprint:
`f27ab985ae90bb8e94ba8d548847695888c232f43b3e9be93074f39e1a7a5098`.

Recovering the original training artifact **does not reopen** the failed
MARKET_ANCHOR V2 stability gate: `active_lambda=0`, `shadow_lambda=1`,
`NO_BET` and **Serie A scope only** are unchanged. A full September target
replay is still a separate historically versioned exercise, and a genuinely
new prospective evaluation is needed before production promotion.
