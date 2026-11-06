# Original Serie A V2 — zero-credit fixture feature-readiness probe (2026-10-28)

## Purpose

The verified Football-Data source archive currently contains completed Serie A rows only through 2026-10-25, and saved odds snapshots have no fresh future pre-kickoff rows. This separate probe tests whether the already configured The Odds API account can expose future Serie A event identities through its documented **free `/events` endpoint** without requesting odds or spending quota.

Official provider documentation says `/v4/sports/{sport}/events` returns event ID, teams, and commence time without odds and does not count against the usage quota: https://the-odds-api.com/liveapi/guides/v4/.

## Strict contract

- Manual `workflow_dispatch` only; no cron, no workflow-run trigger, no automatic provider call.
- Before the single provider request, query Supabase read-only for exactly `match_date, home_team, away_team` from the current Serie A feature-input gate; do not select scores, results, settlements, or target outcomes.
- Require the current metadata-only identity set to match the authenticated source archive's gate identities/count/SHA and require zero missing identities. Verify the successful `main` source parent, ZIP SHA-256, frozen candidate SHA, and fixed 24-hour source age before the provider request.
- The live path requires the identity/freshness verifier introduced by PR #699. If that guard or the read-only identity reader is not present on `main`, it fails closed before archive discovery/provider access.
- Make exactly one HTTPS request to `/v4/sports/soccer_italy_serie_a/events`, with redirects disabled and no retry. Do not call `/odds`, `/event odds`, `/scores`, or `/historical`.
- Require response header `x-requests-last: 0`; missing or nonzero cost fails closed. Do not print or serialize the API key or full provider URL/body.
- Accept only event identity metadata (event ID, sport key/title, home/away teams, commence time). Reject unexpected fields that could carry odds or outcomes; ignore in-play events.
- Reuse the exact original V2 feature builder pinned by Git blob SHA `401b3a0893371bfa4a488ec92a4a54af2678c8f7` and the unchanged frozen candidate `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`. Emit the 19 input features and missingness/history-age diagnostics only.
- Emit **no probability vector**, no market residual, no forecast eligibility, no Brier/LogLoss, and no target-outcome read. The preview is not an admitted prospective forecast and cannot count toward the 30-completed-forecast evaluation gate.
- Supabase access is limited to the read-only identity gate query above. No Supabase writes/DDL, no target-result columns, no production artifact/model load, no production `.pkl` mutation, no publication, no betting, and no promotion.

## Why this is separate

The fixture endpoint is a metadata source, not an odds source. Its output can help check upcoming event identity and prequote feature availability, but it cannot supply the market anchor. The metadata-only Supabase gate query is necessary because an archived gate can become stale if another primary fixture completes after source capture. The original V2 forward workflow continues to accept only saved, fresh, strictly pre-kickoff odds snapshots whose source archive and successful parent run completed earlier. No old October 13 quotes may be backfilled.

## Verification status

The unit tests use mocked provider responses and synthetic historical rows; they do not call the provider. The manual live workflow is not run from PRs. A real live artifact is required after human merge of PR #699 and this PR, followed by manual dispatch, before claiming fixture-source availability. If the provider reports no future events, the artifact records `NO_UPCOMING_FIXTURES`; this does not imply a model failure or permit a forecast.


## Independent source archive re-audit — 2026-11-03

This audit supersedes the earlier 90-row / 93-fixture completeness caveat for the newer **2026-11-03** source archive. It does **not** remove the requirement for a fresh post-#699 identity-attested capture before this preview can run.

### Existing archive integrity (read-only; no new Football-Data request)

- Main source-capture run: [#41640753996](https://github.com/MaksimBlud/football-ai/actions/runs/41640753996), main SHA `40887ebb215730190d7a6c7a1693373ec4afcdfc`.
- GitHub artifact: `13231843819`; independently downloaded ZIP SHA-256: `4e6fb5531a2206a353fe00fa1ebb0b4d20b3c6ae41ab49a7c672f8dab6d29cd8` (matches the GitHub artifact digest).
- All **11/11** CSV member SHA-256 values match the archived manifest. The current-season member `serie_a_2627.csv` SHA-256 is `4138a4f01e96312a7a5dc07450c7a520c3861a479620fe3d102f12d42a6678ba`.
- The current-season CSV contains **100 rows / 100 unique canonical fixture identities**. Its identity-set SHA-256, computed only from `Date, HomeTeam, AwayTeam` after the frozen V2 alias mapping, is `9efdf19fcc44fb1959210cae16805131fc65fb523b4b11be18a3024d8c8f8a3d`.
- A separate read-only Supabase query selected only `match_date, home_team, away_team` for Serie A 2026/27 through 2026-11-02. It returned 103 raw rows / 100 unique canonical identities and the **same** identity-set SHA-256 `9efdf19fcc44fb1959210cae16805131fc65fb523b4b11be18a3024d8c8f8a3d`.
- The original manifest's count-only feature gate recorded **98** identities at `2026-11-03T13:02:46.498639Z`. A retrospective reconstruction using rows with `persisted_at_utc` no later than that timestamp yields 101 raw rows / 98 canonical identities (identity SHA-256 `32b92fb9eef0a84e8fdc7f4c3d539af6107e66dc22786999ae58d841a3f79819`), matching the recorded count. Two further identities—Atalanta–Parma and Sassuolo–Fiorentina—were persisted in Supabase at 19:25 UTC, after the source capture, but were already present in the downloaded CSV. Thus the 100-row source identity set covers both the 98-identity capture-time gate and the current 100-identity metadata set.

**Attestation limitation:** the pre-#699 manifest did not persist the capture-time identity list or its SHA. The `persisted_at_utc` reconstruction is independent corroboration, not a contemporaneous cryptographic gate attestation. The next post-#699 capture must persist the identity list/count/SHA and independently verify full source coverage; do not retrofit the reconstructed digest into the old manifest.

### Actual forward runs (no quote, no forecast)

- Current-Form Forward [#41640881317](https://github.com/MaksimBlud/football-ai/actions/runs/41640881317): **53 tests passed**; source artifact `13231843819` verified, source age 33 seconds, but `quotes_seen=0` and `v2_current_form_shadow_captured=0`. Target outcomes were not read/scored; paid calls and Supabase writes were zero.
- Original Forward [#41670482076](https://github.com/MaksimBlud/football-ai/actions/runs/41670482076): **71 tests passed**; verified 3,800 historical rows from source artifact `13236383688`, but `quotes_seen=0`, `forecasts_created=0`, and `v2_diagnostic_previews_captured=0`. Target outcomes were not read/scored; paid calls and Supabase writes were zero.

### Fresh pre-match-only Supabase status

- `odds_snapshots`: 3,915 strictly pre-match rows; zero in the last seven days; zero future events with a saved strict pre-match quote. Latest strict pre-match snapshot: **2026-10-13 14:48:53.042620 UTC**.
- `league_structural_v2_observations`: 2,387 strictly pre-match rows; zero future events; same latest snapshot timestamp.
- `product_prediction_snapshots`: 40 strictly pre-match rows; **zero** rows carry the frozen original V2 candidate SHA; zero future original-V2 snapshots.

### Readiness and remaining order

The original candidate remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, with the unchanged 19-feature order, `active_lambda=0`, and research-only `shadow_residual_lambda=1`. This preview still emits no probabilities and cannot count toward the 30-event outcome gate.

The live preview remains blocked until HUMAN-MERGE of #718 and a fresh successful source capture on the resulting main SHA that includes the new identity-list/count/SHA attestation. Then rebase this PR, rerun exact-head CI, and only afterward consider its separate manual `workflow_dispatch`. That workflow is manual-only, has no cron, makes one `/events` metadata request (no odds), and requires `x-requests-last: 0`; it does not create forecasts or read target outcomes.

No new provider request, paid The Odds API call, Supabase write/DDL, production `.pkl` change, merge, main update, schedule change, or other-agent change occurred in this audit.


## Source-rights enforcement added before live access — 2026-11-06

The manual entry point now calls `require_personal_research_inference_scope()` before reading Supabase credentials, creating a Supabase client, discovering/downloading GitHub source artifacts, or requesting the zero-credit `/events` endpoint. If the local rights gate denies the configured scope, it writes a `SOURCE_RIGHTS_BLOCKED_NO_NETWORK_NO_INFERENCE` report and exits before any external access.

The returned rights-manifest SHA and scope attestation are included in the fixture-readiness artifact. This remains an operational personal/academic research interpretation only; the manifest explicitly records that no provider-issued AI-inference licence exists. AI training, commercial use and public-product publication remain prohibited. The offline contract workflow now runs the source-rights regression suite and is triggered when the rights helper or manifest changes.

No live workflow dispatch or provider request was made while implementing this guard.
