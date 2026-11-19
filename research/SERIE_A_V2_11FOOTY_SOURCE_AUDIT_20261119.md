# Original MARKET_ANCHOR_1X2_V2 — 11footy Serie A source audit

**Audit date:** 2026-11-19 UTC  
**Decision:** **HOLD — promising schema and checksum design, but no source integration or inference is authorized.**  
**Scope:** public repository README, LICENSE, schema.sql, SHA256SUMS and GitHub release metadata only. No dataset asset, CSV row, SQLite database, API, Supabase record or protected outcome was downloaded or read.

## Executive finding

fm-devlab/11footy-dataset is a materially stronger *structural* candidate than several previously screened free sources. Its published schema contains match scores plus team-level corners, yellow cards and red cards, which can be mapped to the unchanged 19 inputs of the original Serie A MARKET_ANCHOR_1X2_V2. It also publishes a release checksum manifest and a signature asset.

It is **not approved**. Three independent blockers remain:

1. The declared dataset licence is **CC BY-NC 4.0**: non-commercial use with attribution only. Commercial use is not granted.
2. The README describes a league report layer as official match-report statistics and a feed layer as live-feed statistics, but does not identify the upstream provider for either layer. The existing Lega Serie A rights audit (#883) records that official League content extraction requires express written consent. We cannot assume the 11footy compilation licence clears upstream rights.
3. The latest public release is 11footy-2026-11-10, published 2026-11-11 00:13:37 UTC. At this audit time it is 212.667 hours old and no newer release was visible. This is a release-freshness warning; it does **not by itself prove** a violation of the frozen 24-hour project-archive-age rule. No authorized project archive exists and current completed-fixture coverage has not been checked.

No dataset asset was downloaded, so no match-level coverage, missingness, feature parity, source-before-quote, or local archive SHA has been established.

## Pinned public evidence

Repository: https://github.com/fm-devlab/11footy-dataset

- Main commit: 37db9c77c4509b9dcf4915b60b058cdeb1a6a772.
- Latest release: 11footy-2026-11-10, published 2026-11-11T00:13:37Z.
- Release assets include italy.serie-a.csv.zip (37,458,938 bytes) and italy.serie-a.db.xz (35,841,640 bytes).
- The release includes SHA256SUMS and SHA256SUMS.sig.
- The SHA-256 values in the public manifest agree with GitHub's release asset digest metadata for the Serie A CSV ZIP and database archive:
  - CSV ZIP: 58f473c1eba5bd7c291a6380dadd3aba8ae67a47d17b92828e6f9b5a3b50b0c6.
  - DB XZ: bf9179e4ecb44afeea7c434c938730cf5aa714d17286996bafb4ddbe2fcfb09a.
- This is a metadata cross-check only. The archive bytes were not downloaded or independently hashed. The repository tree contains no public-key file or verification instructions sufficient to independently verify SHA256SUMS.sig.

The README says the dataset is rebuilt after each round, not continuously. It also documents a format_version.built_at field shared by files in a release.

## Structural mapping to the frozen 19 features

The candidate on football-ai main remains unchanged:

- Candidate SHA-256: a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6.
- Training fingerprint: f27ab985ae90bb8e94ba8d548847695888c232f43b3e9be93074f39e1a7a5098.
- Training rows: 3,799.
- Exact feature count/order: 19.
- Weight matrix: 20 × 2.
- active_lambda=0; shadow_residual_lambda=1.

The public schema makes this mapping structurally possible without adding or changing a model feature:

| Original V2 input family | 11footy schema | Required interpretation |
|---|---|---|
| Points (last 5, last 10, venue last 5) | matches.home_goals, matches.away_goals | Derive the original 3/1/0 points from the full-time result |
| Goals for/against (last 5, last 10, venue last 5) | matches.home_goals, matches.away_goals | Orient goals by the team's home/away identity |
| Corners for/against (last 5, last 10, venue last 5) | match_team_statistics.corners | Join by match/team; use the documented league report layer only if rights and parity are established |
| Yellow cards (last 5, last 10) | match_team_statistics.yellow_cards | Join by match/team and frozen layer rule |
| Red cards (last 5, last 10) | match_team_statistics.red_cards | Join by match/team and frozen layer rule |

The audit manifest records a feature-by-feature mapping in the exact candidate order. It is a schema map, **not** proof that all 19 values are present for every historical match or definition-equivalent to the Football-Data training inputs.

### Layer and definition risk

The README documents:

- report: official match-report counts for shots, shots on target, corners, fouls, yellow cards and red cards; leagues only.
- feed: live-feed counts for the same items plus other statistics.
- The two layers can disagree because their counting conventions differ.
- The documented default is report for leagues and feed where it is the only layer.

Serie A is a league, so the documented default would be report. The README does not name the upstream report or feed vendor, provide field-level lineage, or prove equivalence to the frozen Football-Data corner/card definitions. Do not mix layers or choose whichever values improve results.

The existing [#883 Lega Serie A rights audit](https://github.com/MaksimBlud/football-ai/pull/883) independently records the official League's express-written-consent requirement for extraction/use of its content. This 11footy review does not assert that its report layer definitely comes from Lega; it records that the source identity is unresolved and therefore clearance cannot be assumed. The feed source is also unidentified.

## Licence and intended use

The repository's LICENSE declares **CC BY-NC 4.0** and requires attribution to 11footy. The licence is non-commercial. It does not establish the upstream rights for the underlying Serie A report/feed data.

Therefore:

- no commercial product use is authorized by the declared licence;
- non-commercial research is not automatically cleared of upstream restrictions;
- written upstream rights and a clear attribution/retention scope are still required;
- no raw data may be integrated or redistributed based solely on public visibility.

## Source-before-quote and freshness

The schema exposes:

- matches.kickoff_utc and matches.status;
- format_version.built_at, a release-level build timestamp;
- applied_corrections.applied_at, which records corrections but is not a per-match first-observation timestamp.

The match_team_statistics rows have no documented per-row first-observed timestamp or field-level correction timestamp. A pinned release plus a private archive and SHA could prove which exact release the project possessed before a later quote. It would not prove the provider's first observation time for every statistic.

The current release was published 212.667 hours before this audit. This is a warning that its current-season fixture coverage may be stale; no dataset rows were inspected, so completeness cannot be asserted. The frozen V2 policy's 24-hour limit applies to the age of the project's private source archive relative to quote admission, not automatically to the upstream release publication age. No project archive exists here, so that local age gate is not yet testable. A future authorized capture could satisfy the local archive-age rule only if the release's fixture identities cover every completed fixture in the current metadata-only gate and the archive is completed before the quote. Do not relax the 24-hour limit or mislabel local retrieval time as a provider first-observation timestamp.

If a future release is within the frozen 24-hour limit and all rights are cleared, the safe sequence would be:

1. pin the exact release/tag and asset metadata;
2. verify the release signature using a provider-published public key;
3. download only the authorized Serie A asset into private storage;
4. verify the downloaded bytes against the release SHA-256 manifest and GitHub asset digest;
5. write an immutable source manifest with release build/publish time, retrieval time, parent-run SHA and archive SHA;
6. complete that source archive before reading any quote;
7. admit only quotes satisfying the existing source-before-quote and kickoff cutoffs;
8. validate every required field and source definition against the frozen 19-feature contract before feature construction.

No step above is authorized by this audit.

## Reconsideration conditions

Keep approval_status=HOLD until all of the following are independently verified:

1. upstream provider identity and written rights for the Serie A report/feed layers, including internal research, ML inference, private retention and any intended product use;
2. confirmation that the non-commercial licence matches the actual project use; commercial use would require a different explicit licence;
3. a public verification key and successful signature verification for SHA256SUMS.sig;
4. a release whose completed-fixture identities cover every fixture in the current metadata-only gate, with no missing current-season match rows;
5. a private immutable archive completed and SHA-verified strictly before the quote and still within the frozen 24-hour project-archive-age limit at quote admission;
6. complete fixture-level coverage and field-definition parity for all 19 original features, without zero-filling unknowns or changing the original feature builder;
7. exact original candidate SHA, feature order, weights, scaler, imputer and lambda semantics remain unchanged.

## Safety record

This PR adds only a source-rights HOLD manifest, this audit note, an offline regression test and a PR-only validation workflow.

- Dataset CSV/SQLite assets downloaded: 0.
- Provider/API requests: 0.
- Supabase reads/writes/DDL: 0.
- Protected 2026/27 outcomes read: 0.
- Feature calculations/inference/training/refit: 0.
- Production .pkl changes: 0.
- Main changes/merges: 0.
- Schedules and other agents: unchanged.

**HUMAN-MERGE only. No live ingestion or model inference is authorized by this PR.**
