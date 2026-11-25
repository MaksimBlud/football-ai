# PitchAPI source-rights and frozen V2 coverage audit — 2026-11-25

## Decision

**`HOLD_NO_DOCUMENTED_CORNER_FEATURES_AND_UNCLEAR_DATA_RIGHTS_AND_UPSTREAM_PROVENANCE`**

PitchAPI is a technically interesting no-cost candidate, but it is **not approved** as an original `MARKET_ANCHOR_1X2_V2` source. Do not create an account or key, call the API, download responses, archive data, build features, or run inference unless the separate source-rights and coverage gates are resolved in writing.

This is an official-documentation-only audit. No API key was requested, no endpoint was called, and no match data was downloaded.

## What the official documentation claims

The [PitchAPI documentation](https://pitchapi.dev/) currently describes:

- one free plan, no paid tier, no card, no request allowance;
- 77 leagues and all documented endpoints;
- full history back to 2021;
- match listings with `played`, `upcoming`, and `all` status filters;
- match summary, team stats, shots, events, lineups and advanced analytics;
- RFC 3339 UTC response timestamps and UTC kickoff times.

The service therefore merits keeping on the candidate list: its published free scope is materially broader than several previously audited free tiers. However, the documentation does not independently establish that Serie A 2026/27 is in the current catalogue or that every required stat is available for every match.

## Frozen 19-feature contract check

The exact main-branch candidate was read from `research/models/market_anchor_v2_serie_a_frozen_candidate.json`:

- Git blob SHA: `ac1303f6b096664983fbf52443bd0a381b23ba21`
- Candidate SHA-256: `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`
- 19 ordered features; 20×2 weights;
- `active_lambda=0`, `shadow_residual_lambda=1`;
- historical stability gate remains failed.

The contract contains six corner-derived features:

1. `diff_corners_for_5`
2. `diff_corners_for_10`
3. `diff_corners_against_5`
4. `diff_corners_against_10`
5. `diff_corners_for_venue5`
6. `diff_corners_against_venue5`

PitchAPI's public team-stat examples document xG, possession, accurate passes and touches in the opposition box; its event list documents goals, cards, substitutions and penalties. The shot endpoint documents `is_on_target` and xG. **The public documentation inspected does not document a team corner-count field or corner events.** This is a documentation gap, not proof that no private or undocumented response contains corners. Until the exact field, definition, availability and coverage are documented and independently verified, full 19-feature parity is not established.

The published history starts in 2021, whereas the frozen candidate's training history spans 2016/17–2025/26. A 2021+ source cannot by itself reconstruct the full original training window. It could only be assessed as a prospective input source without changing the trained model or its feature contract.

## Source-before-quote and SHA feasibility

The docs provide UTC fixture times and RFC 3339 response timestamps. The live-match endpoint documents `fetched_at`, `age_seconds` and `stale`, but those are live-snapshot fields; the completed-match stats documentation does not identify a first-observed timestamp for each match/stat response or a per-field correction timestamp.

If written rights are later confirmed, a project-controlled raw-response receipt timestamp plus SHA-256 could prove that the project possessed a particular byte sequence before a later quote. It would **not** prove when the upstream provider first observed or published that data, nor whether it was subsequently corrected. The latter requires provider-side provenance or an independently timestamped version history.

## Rights and retention blocker

The [PitchAPI SDK page on PyPI](https://pypi.org/project/pitchapi/0.1.6/) explicitly distinguishes the MIT licence for the SDK code from the separate terms governing the API service and returned football data. The PitchAPI documentation page inspected links Docs, Plans and Support but does not link or reproduce the service terms, a data licence, upstream provider identities, AI/ML permission, or private long-term raw-response retention permission.

Therefore the SDK's MIT licence must not be treated as a data licence. Free access and unlimited requests do not grant permission to retain raw match data or use it to build/train/evaluate the frozen V2 candidate. Written confirmation is required for:
- the upstream rights chain for Serie A match facts and detailed statistics;
- private raw-response storage and retention duration;
- internal AI/model feature calculation, inference and research evaluation;
- any post-cancellation retention rights;
- the six missing corner features and their field-level coverage/definitions;
- Serie A 2026/27 season coverage and corrections/version history.

## Required next evidence before reconsideration

1. Public, versioned terms/data licence or written provider confirmation covering the exact internal research and private-retention use.
2. Identified upstream sources and their rights/attribution conditions.
3. Documented corner-count fields and exact semantics for all six frozen corner features.
4. Verified Serie A 2026/27 coverage and historical depth; no assumption from the aggregate 77-league claim.
5. A documented source-observation/correction chronology suitable for source-before-quote capture.
6. Only after those gates pass: an authorized, minimal, read-only capture of a pre-match source response, local receipt time, exact raw SHA-256, and a source archive created strictly before any later quote. No protected target outcomes are needed for this source audit.

## Safety and model invariants

No provider account/key/request/download, Supabase access/write/DDL, quote access, feature build, inference, protected 2026/27 outcome read, training/refit, threshold tuning, production `.pkl` change, main update, merge, promotion, bet, paid API call or cron was performed or authorized.

The original candidate, 19-feature order, weights, scaler/imputer, `active_lambda=0`, `shadow_lambda=1`, failed historical stability gate and CLOSED prospective outcome gate (0/30) remain unchanged. No Brier/LogLoss comparison or superiority claim is possible from this audit.

**Final status: HOLD.** This is a new source candidate for documentation only, not an approved V2 data source.
