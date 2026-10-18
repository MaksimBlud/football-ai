# Original Serie A V2 — audit historical feature coverage and median imputation

**Research-only, 2026-10-14.** This work does not alter original frozen weights, feature order, training data or lambda. Original candidate `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, 19 input differences, `active_lambda=0`, frozen stability gate FAILED, `shadow_lambda=1` inactive, `NO_BET`.

## Practical issue

The frozen V2 uses original `SimpleImputer(strategy="median")` semantics. With sparse historical data, the 19 differences are partially missing and filled by the original candidate's training medians. If **neither team appears in the available 2016/17–2025/26 sources**, all 19 fields can be missing: the residual model would then return probabilities based solely on its training medians, **not football evidence for these teams**. Previously the shadow code still marked this as a scored diagnostic preview, and did not disclose how much data had been imputed.

## Deterministic research-only changes

- `serie_a_v2_asof_feature_manifest.py` exposes exact per-fixture **0–30 prior-match exposure per home/away team**, counts of matches at the corresponding future fixture venue, and last historical match date (from date-only Football-Data source). Exposes original **19 observed-vs-missing counts**. These are **audit metadata**, never added to V2's trained input matrix.
- `serie_a_v2_frozen_shadow_preview.py` appends original-feature observed count, median-imputed count and names of the imputed features, plus optional explicitly diagnostic source-history coverage metadata. If **all original 19 features are missing**, it does **not** call candidate inference; increments `ALL_FEATURES_MEDIAN_IMPUTED` instead. **No arbitrary history-length or probability threshold is introduced.** Existing valid partial-missing inputs still use the exact unchanged medians and original weights.
- `serie_a_v2_live_diagnostic_report.py` includes a per-fixture completeness table and counts for fully observed, partially missing and all-median rows. The existing free GitHub Actions daily real-quote diagnostic automatically records and prints these counts after merge, without paid provider API, protected 2026/27 outcome reads or Supabase writes.
- Negative tests: unseen promoted/renamed clubs with zero prior source history are blocked instead of misleadingly scored; partial original missingness and five venue features are explicitly audited; prequote date-only cutoffs, original `active_lambda=0` market identity and strict `NO_BET` preserved.

## Scientific limits

All public history remains **pre-2026/27 only**. Missing current-season form is NOT repaired by these diagnostics. The original 20 saved Oct 13 2026 quotes were recorded before the first proven GitHub historical archive; **none are admissible frozen V2 prospective forecasts** even if the day-after diagnostic computes their features. No protected 2026/27 results are read, no original frozen thresholds are modified, no pre-existing results are retroactively admitted, no promotion to production. Next use live coverage statistics to identify exact team/history deficits and then plan a truly prequote **current-form** capture source that does not violate frozen outcome embargo.

## Expected checks

The resulting original V2 forward-only source archive workflow continues to reject any fixture with no preceding source ZIP, regardless of feature coverage. The separate offline/date-only diagnostic can calculate research-only probabilities for matches with at least one nonmissing V2 feature, and provides explicit count of median-imputed inputs. Partial missingness is not proof of model quality, only transparency.

## Original-builder parity regression

A new deterministic regression constructs one synthetic pre-match state twice:

1. through the exact original `historical_football_signal_lab.build_point_in_time_features` plus `add_difference_features` path used by the frozen V2 recipe;
2. through the current read-only `serie_a_v2_asof_feature_manifest.build_manifest` path.

It requires identical feature names/order and numerical equality for every one of the original 19 inputs (absolute tolerance `1e-12`), including identical missing-value semantics. This closes an implementation-equivalence gap without fitting coefficients, changing medians/weights, reading 2026/27 outcomes, or claiming current-form/prospective validity.

The test is structural evidence only. It does not make the date-only source fresh, validate the six stale-form fixtures, admit the existing October quotes, or establish Brier/LogLoss superiority over market.

The online manifest additionally pins the original feature-builder Git blob
`401b3a0893371bfa4a488ec92a4a54af2678c8f7` at runtime and fails closed on source drift. This prevents a misleading case where both compared current code paths change together while the frozen candidate weights remain unchanged.

