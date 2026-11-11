# Original MARKET_ANCHOR_1X2_V2 — open-matchday current-form source candidate audit

**Audit date:** 2026-11-11  
**Scope:** public repository metadata, README, data dictionary, disclaimer, league index and build-summary metadata only. No CSV data file was downloaded or parsed. No quote, Supabase row, target outcome, model inference or paid provider was accessed.

## Decision

`oladeeayo/open-matchday` is a **potential current-season source candidate for a separate rights and source-concordance review only**. It is **not approved** as an original V2 input, current-form archive, training source, inference source, or quote source.

The repository advertises useful 2026/27 Serie A fields, but its own documentation identifies mixed upstream providers, non-commercial-only terms and upstream rights that remain with each provider. It does not document field-level source provenance sufficient to prove that all original V2 statistics have the same definitions as the frozen training source. The published aggregate coverage also indicates substantial missingness for card statistics.

Do not connect it to the frozen feature builder, download its CSVs, or generate V2 forecasts until upstream permissions and a feature-by-feature parity protocol are independently established.

## Pinned public repository evidence

Repository: https://github.com/oladeeayo/open-matchday

- Default branch: `master`.
- Pinned master commit: `e1ec9773df8030a3e0c613f52eb3bd85437c21ab`.
- Commit time: `2026-11-10T06:45:05Z`.
- README blob: `b50fe89e1735e6d306ea6dc8eae5169cb6f47a7e`.
- DATA_DICTIONARY blob: `640dc58c2de961afbdb9b3960a71216ecb230223`.
- DISCLAIMER blob: `198a9cc33cfe25534213a38346d7f10e07e6a1a9`.
- LEAGUE_INDEX blob: `e3f18cd3e9a5d7b38e4ce6cfd1d592251c06e79c`.
- build_summary blob: `8395faf27aae706650cb862552129522191f3d1d`.
- CITATION blob: `68676b873baeedbc49f24683749c7cdbcdf5a75c`.
- No root `LICENSE` file was present in the pinned repository tree. CITATION declares `license: other` and points to DISCLAIMER.md.

The exact files should be re-pinned if this candidate is reconsidered; `master` is mutable.

## Serie A 2026/27 metadata coverage

The pinned LEAGUE_INDEX identifies Serie A as:

`fixturedownload + ESPN + fd.co.uk`

The README and data dictionary separately state that FotMob supplies first-/second-half corner splits for the top ten leagues, including Serie A.

The pinned build summary was generated at `2026-11-10T06:44:59Z` and reports for Serie A:

- 110 result rows;
- 270 fixture rows;
- `corners=110`;
- latest completed match date `2026-11-08`;
- no build errors in that summary entry.

These are repository-published summary counters, **not an independent inspection of the CSV rows**. They do not prove that yellow/red-card fields or every other required statistic are complete for all 110 matches. No raw CSV was downloaded or parsed in this audit.

The README's aggregate coverage section reports approximately 19% of result rows with shots/fouls/cards and approximately 19% with corner totals, while separately claiming first-/second-half corner splits for every played match in the top-ten leagues. The documentation does not provide a Serie A per-column completeness matrix. The data dictionary explicitly says blank cells mean unavailable, never zero.

## Frozen V2 feature compatibility

The original candidate on football-ai main remains:

- candidate SHA-256: `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`;
- original feature-builder Git blob: `401b3a0893371bfa4a488ec92a4a54af2678c8f7`;
- 19 unchanged features, in their original order:

1. `diff_points_5`
2. `diff_points_10`
3. `diff_points_venue5`
4. `diff_goals_for_5`
5. `diff_goals_for_10`
6. `diff_goals_against_5`
7. `diff_goals_against_10`
8. `diff_corners_for_5`
9. `diff_corners_for_10`
10. `diff_corners_against_5`
11. `diff_corners_against_10`
12. `diff_yellow_5`
13. `diff_yellow_10`
14. `diff_red_5`
15. `diff_red_10`
16. `diff_goals_for_venue5`
17. `diff_goals_against_venue5`
18. `diff_corners_for_venue5`
19. `diff_corners_against_venue5`

At schema level, open-matchday documents plausible ingredients:

| Frozen V2 inputs | open-matchday fields documented | Assessment |
|---|---|---|
| Points and goals for/against | `ft_home`, `ft_away`, `ft_result` | Derivable in principle; source semantics and completeness still need validation |
| Corners for/against | `home_corners`, `away_corners`; 1H/2H splits | Plausible, but corner provider and field-level provenance need reconciliation |
| Yellow cards | `home_yellow`, `away_yellow` | Not proven complete; aggregate documentation reports sparse card/stat coverage |
| Red cards | `home_red`, `away_red` | Not proven complete or definition-equivalent to frozen source |

The original V2 adapter currently expects Football-Data-style fields `Date, HomeTeam, AwayTeam, FTHG, FTAG, FTR, HC, AC, HY, AY, HR, AR` and rejects missing required statistics before building features. open-matchday uses a different normalized schema. A future adapter would need to be V2-local and prove exact semantics and completeness; it must not alter the frozen 19-feature order, rolling windows, weights, scaler, imputer or candidate.

### Specific source-concordance blockers

1. **Mixed upstream providers.** The winning row's `source` field documents `openligadb`, `fixturedl`, `espn`, `fd.co.uk` or `soccerway`. The README separately identifies FotMob as the source of top-ten corner splits, but the documented row-level source enum does not include FotMob and no per-column source/timestamp fields are documented. This is insufficient field-level provenance for the corner inputs.
2. **Card completeness.** The published aggregate documentation says shots/fouls/cards occur in only about 19% of result rows. The original V2 feature builder requires the six corner/card statistics to be present and valid; blank cannot be converted to zero or silently imputed as a source repair.
3. **Provider-definition drift.** The repository warns that upstream providers retain their own data rights and that the compilation does not override them. Similar field names do not prove that corner, yellow-card or red-card definitions match the Football-Data training source.
4. **No historical-season replacement.** The pinned release is 2026/27. It does not supply the 2016/17–2025/26 history used by the frozen candidate's 3,799 training rows or the existing 30-match rolling history. At most, it could be considered as a supplementary current-season source after approval.
5. **Date/time limitations.** The data dictionary describes match date as UTC and kickoff time using a fixed CET-1 convention, noting summer fixtures may be one hour off local time. The original V2 date-only feature contract excludes all matches on the quote's UTC calendar day; any adapter must preserve that strict exclusion.

## Rights and confidentiality gate

The repository's README states that there is no OSI-approved license file because the upstream data is non-commercial. Its stated compilation terms are informational/non-commercial only; sale, sublicensing, paid access and commercial data-feed use are prohibited. DISCLAIMER.md says upstream provider terms remain in force and that the compilation does not override them.

The listed upstreams include football-data.co.uk, fixturedownload.com, OpenLigaDB, ESPN, Wikipedia/Wikidata, Soccerway and FotMob. Permission from the compilation author alone would not establish permission from every upstream rights holder. In particular, the separate football-ai source-policy review dated 2026-11-10 keeps automated Football-Data source capture and V2 inference fail-closed pending clarification.

Therefore:
- no permission is inferred for automated retrieval, model inference, AI use, retention, redistribution or publication;
- obtain written provider/rightsholder clarification for each upstream field actually used;
- require a row/field-level source manifest and immutable release/commit pin;
- preserve the separate private-artifact-storage requirement;
- do not treat a public URL, no-API-key claim, or repository-level non-commercial statement as an upstream licence.

## Source-before-quote requirements if reconsidered

The pinned repository commit is dated `2026-11-10T06:45:05Z`, and its build summary says `2026-11-10T06:44:59Z`. These timestamps are useful provenance metadata, but do not by themselves prove upstream rights or per-field observation time.

Any future authorized test must:
1. pin an immutable upstream commit, exact CSV path and blob SHA;
2. archive the exact bytes in an approved private location;
3. record the archive creation time and successful parent workflow identity;
4. require both the pinned source commit and successful private archive to precede each quote strictly;
5. reject same-day historical matches under the existing date-only feature rule;
6. reject stale, incomplete, conflicting or source-ambiguous rows before feature construction;
7. never backfill old quotes or read protected target outcomes before the preregistered 30-primary-completed-event gate.

## V2 contract and explicit non-results

No candidate bytes, 19-feature order, weights, scaler/imputer, training fingerprint, protocol, lambda, source code or production artifact was changed.

- `active_lambda=0`: exact de-vigged market remains the active reference.
- `shadow_lambda=1`: research-only, not activated.
- Stability gate: FAILED.
- Automatic promotion and betting: disabled.
- Prospective completed-event outcome-read gate: still 0/30 in the current evidence record.
- Brier/LogLoss superiority: not established.

No dataset CSV was downloaded or parsed. No source request, quote read, Supabase query/write, target-outcome read, inference, refit, paid API call, production `.pkl` change, workflow schedule change or main-branch update was performed.

## Final disposition

**Do not integrate open-matchday into original V2 yet.** It is a promising metadata-level lead for 2026/27 match statistics, but the present evidence fails the upstream-rights, field-level provenance, complete-card-coverage and exact-source-parity requirements. Reconsider only after those blockers are resolved in writing and a separately frozen source-concordance protocol is approved.
