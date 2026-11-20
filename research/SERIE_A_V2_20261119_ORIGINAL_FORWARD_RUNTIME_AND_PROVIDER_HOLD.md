# Original MARKET_ANCHOR_1X2_V2 — 2026-11-19 runtime and provider-rights checkpoint

## Scope and immutable contract

This report covers only the original `MARKET_ANCHOR_1X2_V2` Serie A research candidate. It is an audit/reporting change only. It does not alter model code, features, weights, scaler, medians, lambdas, training data, thresholds, workflow schedules, Supabase, production artifacts, or other agents.

- Main audited: `40887ebb215730190d7a6c7a1693373ec4afcdfc` (repository visibility: public).
- Frozen candidate SHA-256: `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`.
- Training fingerprint: `f27ab985ae90bb8e94ba8d548847695888c232f43b3e9be93074f39e1a7a5098`.
- Original feature vector: 19 inputs; original weight matrix: 20 × 2.
- `active_lambda=0` remains the de-vigged market; `shadow_lambda=1` remains research-only.
- Stability gate: FAILED. Target-outcome evaluation gate: 0/30. No performance superiority is established.

## Actual main-branch runtime evidence

### Current-form source capture — 2026-11-18

[Run #44326186511](https://github.com/MaksimBlud/football-ai/actions/runs/44326186511) completed SUCCESS on the exact main SHA above.

- 19 offline tests passed.
- Feature-input gate: 110 completed Serie A current-season metadata identities.
- Source files: 10 frozen historical CSVs + current 2026/27 CSV (11 files total).
- Historical rows: 3,800 in the source manifest's prior-season cohort; current-season lagged rows: 110.
- Paid provider calls: 0; Supabase writes: 0; target outcomes scored: false.
- Uploaded artifact ID: `14438015203`.
- GitHub artifact ZIP SHA-256: `0d4240f31418e206b36faf9e94d0782212a91cf6d51262c77b0349ab3f7fc852`.

The workflow still has a daily `05:50 UTC` schedule and `upload-artifact@v4` on current main. Because the repository is public, the uploaded artifact is publicly accessible. This is not provider-rights clearance.

### Original Forward — 2026-11-18

[Run #44355495841](https://github.com/MaksimBlud/football-ai/actions/runs/44355495841) completed SUCCESS.

- 71 regression tests passed.
- Real GitHub source attestation succeeded: source artifact `14441402737`, parent run `44336997243`, 10 pre-prospective CSVs and 3,800 historical results, source ZIP SHA verified.
- `future_quotes_checked=0`; `quotes_seen=0`; `v2_diagnostic_previews_captured=0`.
- Paid provider calls: 0; Supabase writes: 0.
- Small diagnostic artifact: `14451725631`, SHA-256 `8625d2f3cd3d2601be7394287ffa904b101da329306b64db20a0d269c38f0809`.

This is real source-attestation/runtime proof, not a new prediction or quality result.

### Current-Form Forward — 2026-11-18

[Run #44356799888](https://github.com/MaksimBlud/football-ai/actions/runs/44356799888) completed SUCCESS.

- 53 regression tests passed.
- Verified current-form source artifact `14438015203` and its successful main parent; artifact SHA matched.
- Source manifest: 110 current-season lagged rows and 3,910 historical rows; source age at verification 9,561 seconds.
- `quotes_seen=0`; `v2_current_form_shadow_captured=0`.
- `target_outcomes_read=false`; `target_outcomes_scored=false`; paid calls 0; Supabase writes 0.
- Forward diagnostic artifact: `14452497083`, SHA-256 `67badae205c4b5d414e3dcf5d79b831b5f8bf4bfc62654893067ca366ce9ea75`.

The current-form code verified a real archive before quote access; it had no saved quotes to score.

## Read-only Supabase evidence (2026-11-19 UTC)

Queries were SELECT-only and limited to pre-match quote metadata/probabilities and feature-gate identity metadata.

- `odds_snapshots`: 3,915 rows satisfying `snapshot_time_utc < commence_time_utc`, across 327 distinct league/event pairs. Latest such snapshot: 2026-10-13 14:48:53 UTC. Latest associated kickoff: 2026-10-25 19:45 UTC. All nine stored leagues have zero future events with a strict pre-kickoff quote.
- `product_prediction_snapshots`: zero upcoming rows; zero upcoming rows carrying the exact frozen V2 candidate SHA.
- Serie A 2026/27 feature-input query selected only `match_date, home_team, away_team`: 113 raw rows, 110 canonical event identities after the frozen V2-local Atalanta alias; latest date 2026-11-08. No score/result columns were selected.
- Feature-input gate is open (110 ≥ 30). This does not open the independent target-outcome gate, which remains 0/30.

## Provider-rights and privacy blocker

[PR #868](https://github.com/MaksimBlud/football-ai/pull/868) records the current official page's statement that files are updated at least twice weekly (Sunday/Wednesday). That is the publisher's update cadence, not a maximum download frequency. The HOLD instead rests on the page's private-individual/personal-betting or academic-research framing and its explicit exclusion of commercial/data-training products using automated bots/scrapers/AI; the intended automated AI-model pipeline has no affirmative permission documented. The provider also does not document per-match first-observation/correction timestamps. Project receipt time + SHA proves possession of exact bytes before a later quote, not upstream first observation. Therefore daily live capture remains on HOLD pending explicit rights/permission.

- [PR #781](https://github.com/MaksimBlud/football-ai/pull/781): Ready, exact HEAD `3a70a8648895076efec2a80dc10b1798ed0d9261`, 8/8 CI success. It defaults live access to false, gates live reads and artifact uploads, and preserves existing schedules.
- [PR #879](https://github.com/MaksimBlud/football-ai/pull/879): Draft, exact HEAD `b78010585c80b05ae5fc2a8b3572df14b32d9651`, 4/4 CI jobs success. It adds a read-only private-repository guard before live artifact access.
- Neither is merged. Main remains public and its daily source-capture step remains executable until the HUMAN-MERGE chain is integrated.

## Next admissible work

1. HUMAN-MERGE #781; then re-read fresh main and restack/revalidate #879.
2. Keep live capture disabled until provider rights and private artifact storage are both cleared; do not alter schedules.
3. Continue V2-only offline source, SHA, feature-parity, and source-before-quote regressions in separate branches.
4. Obtain a genuinely new authorized pre-kickoff quote only after a verified source archive; no backfill of old quotes.
5. Preserve the 30-primary-completed-prospective-forecast gate. Only after it opens may an independent evaluator read target outcomes and calculate Brier/LogLoss.

No paid API calls, Supabase writes/DDL, production `.pkl` changes, protected target-outcome reads, merge, or main changes were performed for this report.


## API-Football Free statistics-source audit — 2026-11-20

A new official-pages-only candidate was screened for **fixture statistics only**, not for a new quote source. The Free plan is listed at $0 with 100 requests/day and includes a Statistics endpoint; the documented endpoint is per fixture. The documentation lists shots, corners, fouls, offsides, possession, cards, saves and passing fields, but does not verify complete parity with the original 19-feature contract or Free coverage for Serie A 2026/27.

At one request per fixture, a full 380-fixture season would require at least 380 requests (four 100-request daily quotas), excluding fixtures/coverage calls and retries. The inspected statistics documentation does not establish a per-stat first-observed timestamp; local receipt time + SHA would prove local possession before a later quote, not upstream first-observation time.

The provider's terms say data comes from partners, no publication license is granted for user applications/websites/products, users must obtain required third-party permissions, and the provider grants no commercial rights on covered competitions. No upstream rights chain or written internal-ML permission was established.

**Decision: HOLD / NO INTEGRATION.** No account/key/API request, odds endpoint, source download, Supabase write/DDL, model or weight change, production .pkl change, or protected-outcome read. The existing frozen source/quote contract remains unchanged. Machine-readable audit: `research/market_anchor_1x2_v2_api_football_free_stats_source_audit_20261120.json`; regression is embedded in the existing frozen-shadow test module.
