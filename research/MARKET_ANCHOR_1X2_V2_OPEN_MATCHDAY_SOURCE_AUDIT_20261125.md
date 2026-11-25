# Original MARKET_ANCHOR_1X2_V2 — open-matchday source audit

**Decision: HOLD.** This is a documentation-only candidate review. It does not authorize use, capture, feature construction, or inference.

## Why this source was examined

The public repository [oladeeayo/open-matchday](https://github.com/oladeeayo/open-matchday) advertises a daily refreshed 2026/27 football CSV dataset, including Serie A, match results, fixtures, shots, cards and corners. Unlike API-only candidates, it publishes a commit-pinned repository snapshot that could theoretically be archived before a later bookmaker quote.

The reviewed upstream commit is [968bc4fdb0adfd2a412962793b59fda2c39bdfd9](https://github.com/oladeeayo/open-matchday/commit/968bc4fdb0adfd2a412962793b59fda2c39bdfd9), whose build summary says it was generated at **2026-11-25 07:50:20 UTC**.

## Potential technical fit

The upstream catalogue identifies Serie A at `data/ITA_1_serie-a`. Its League Index lists `fixturedownload + ESPN + football-data.co.uk` as the competition's sources.

The pinned build summary reports:

| Serie A 2026/27 metadata | Value |
|---|---:|
| Finished result rows | 120 |
| Rows with corner totals reported | 120 |
| Upcoming fixture rows | 260 |
| Latest result date | 2026-11-23 |
| Build errors | 0 |

The README says the dataset includes full-time and half-time scores, shots, shots on target, fouls, cards and corners. It separately claims top-10-league first/second-half corner splits sourced from FotMob. This suggests useful overlap with the original V2 feature families, but it does **not** prove that all six required corner fields are present for every Serie A match. The per-match CSV was deliberately not downloaded or inspected.

The results schema also has no stable match ID; it documents joining results and goals by date and team names. The original V2 adapter would need exact identity and collision tests before any use.

## Blocking rights

The upstream repository explicitly limits its compilation to **informational, non-commercial use**. It prohibits selling, licensing, sublicensing, charging for access, or presenting the data as a commercial feed.

Its disclaimer says upstream rights remain with the publishers:
- football-data.co.uk — personal, non-commercial use;
- ESPN — personal, non-commercial use;
- fixturedownload.com — short free-feed summary, with exact reuse/retention terms not established in this audit;
- OpenLigaDB — German-league source, not the Serie A source listed in the League Index;
- FotMob — identified by the README as the top-10 corner-split source, but absent from the disclaimer's provider-terms table;
- Soccerway — listed as a possible merge source, with exact Serie A field-level contribution and rights unresolved.

No written permission was found for private raw-response retention or for using the compilation and its upstream fields in model training/evaluation. The public repository's non-commercial grant does not override upstream provider rights.

**This source is therefore not approved for the Football AI product or for V2 model use.** A future reconsideration requires written rights from the dataset maintainer and relevant upstream publishers, plus exact field-level Serie A coverage and retention terms. No assumption of permission is made from public accessibility.

## Source-before-quote and SHA

The repository offers a useful *local* chronology primitive: an exact Git commit, immutable blob IDs, and a daily build timestamp. If a rights-cleared copy were captured into a private project archive before a future quote, the project could prove that exact bytes were in its possession before that quote.

That would not prove upstream first-observed or correction times. The reviewed docs do not expose per-field first-seen timestamps, correction timestamps, or source publication times. A Git commit/build timestamp is the dataset repository's publication time, not the original upstream publisher's first-observed time.

Consequently, local source-before-quote evidence is technically possible, but the complete upstream chronology gate remains unresolved. The existing V2 rule must not be weakened.

## Frozen V2 invariants

The original candidate remains unchanged:
- candidate SHA-256: `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`;
- exactly 19 original features in their frozen order;
- original 20×2 weight matrix, scaler and imputer unchanged;
- `active_lambda=0` remains the market fallback;
- `shadow_lambda=1` remains research-only;
- historical stability gate remains FAILED;
- prospective outcome gate remains CLOSED at 0/30.

The current-season dataset is not a replacement for the original 2016/17–2025/26 training source window.

## What was not done

- No CSV or ZIP from open-matchday was downloaded, read, or archived.
- No upstream API was called and no account/key was created.
- No Supabase access, quote read, feature build, inference, target-outcome read, training/refit, or threshold tuning.
- No production `.pkl`, frozen weight, feature order, lambda, schedule, main branch, or other-agent setting was changed.
- No paid API or betting operation occurred.

## Reconsideration checklist

1. Written non-commercial/commercial scope clarification from the dataset maintainer for the intended Football AI use.
2. Written upstream permission for private retention and ML research/evaluation for the exact Serie A fields, including FotMob-derived corner splits.
3. Per-match completeness evidence for all 19 features, especially the six corner-derived features.
4. Stable fixture identity and correction/version chronology.
5. A private archive captured and SHA-attested before each later bookmaker quote.
6. Existing frozen 30-primary-completed-event evaluation gate remains separate and CLOSED until its own prospective forecast count is satisfied.

Until all blockers are resolved, keep the source on HOLD and do not integrate it.
