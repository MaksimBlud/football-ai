# Signal Scout — 2026-10-15 — manager touchline sanctions, point-in-time source gate

**Status:** `IDEA / WAITING_BY_FULL_COVERAGE_AND_MARKET_PIT`. Not DATA_FEASIBLE or SIGNAL_FOUND.

## Mechanism
`MANAGER_TOUCHLINE_RESTRICTION_MATCHDAY_1X2_V0`: an *active*, publicly announced head-coach touchline/ground ban may constrain in-game instructions and tactical adjustments. A suspended sanction, a charge, and a pending appeal are **not** equivalent to actual absence. This is a hypothesis only, not an observed effect.

## Fresh main, dedup, scope
Read `research/programs/registry.json` and `PROJECT_CONTINUITY.md` on GitHub main. Registry: 13 PROGRAM_DONE, 1 BLOCKED. `team_change_faster_than_market` is PROGRAM_DONE for lack of timestamp-safe historical manager/coach availability; do not reopen by renaming its mechanism. The proposal differs from permanent manager replacement and referee discipline, but its overlap with manager availability is unresolved. GitHub issue searches for scout/candidate/touchline/coach suspension/manager ban found no named candidate; this is not proof of exhaustive report-level uniqueness. No 2026/27 protected outcomes were accessed.

## Primary-source examples (outcome-free, NOT exhaustive)
1. FA **2025-02-26**: Arne Slot and assistant Sipke Hulshoff received two-match touchline bans: https://www.thefa.com/news/2025/feb/14/everton-and-liverpool-charges-140225 . PL article lists Newcastle **2025-02-26** and Southampton **2025-03-08**: https://www.premierleague.com/en/news/4257666 . Same-day first fixture is not verified at a 24h pre-kickoff cutoff; second may qualify, subject to source/version audit.
2. FA **2026-04-09**: Marco Silva's announced ban was **paused pending appeal**: https://www.thefa.com/news/2026/apr/09/marco-silva-sanctioned-090426 . FA **2026-04-17**: ban made **suspended** through 2026/27: https://www.thefa.com/news/2026/apr/17/marco-silva-update-170426 . Mandatory **negative control**: announcement != effective absence.
3. FA monthly report published **2026-04-07** retrospectively includes Daniel Farke's March suspension: https://www.thefa.com/news/2026/apr/07/fa-charges---march-2026-080426 . Cannot assign retrospective report a March as-of timestamp. Contemporaneous **2026-03-06** coverage places his absence in a **FA Cup** fixture, not an EPL fixture: https://www.bbc.co.uk/sport/football/articles/cq5798g64y9o .
4. PL rules distinguish standard, extended touchline and ground suspensions, and allow some communications during standard bans: https://www.premierleague.com/en/news/4257747 . No blanket `coach_absent=1` proxy.

## Proposed features (NOT frozen)
At decision time `kickoff_utc - 24h`, separately for home/away: effective head-coach standard/extended/ground restriction (mutually exclusive); simultaneous assistant restriction; appeal/stay/conditional-suspension state; applicable competition and remaining eligible matches; earliest independently proven public timestamp. Unknown is not zero. Never use subsequent reports or appeals retroactively.

## Required feasibility BEFORE candidate Issue
1. Enumerate **all** EPL fixtures 2023/24–2025/26 including no-ban matches from permitted free sources. No case-control sampling by eventual outcome.
2. Reconstruct first-seen times, active/stayed bans, appeals, competition-specific eligibility and postponements strictly as-of 24h before kickoff. Report exact coverage, independent effective exposures, unknowns and negative controls. Date-only same-day publications do not establish 24h availability.
3. Independently prove legally reusable **24h timestamped** 1X2 bookmaker fair probabilities for the same fixtures; opening/closing without observed-at is insufficient.
4. Check prespecified sample sufficiency and whether this is truly independent of PROGRAM_DONE manager availability. If not, STOP.
5. If and only if passed, Research Brain alone freezes validation: chronological train/validation/untouched OOT; fair-market-only vs market-plus-ban; multiclass Brier and LogLoss; fixture-cluster paired CI; placebo controls (stayed bans, future publication, shifted timing, wrong competition); stable OOT improvement as SUCCESS, insufficient coverage/no improvement as STOP. No Scout outcome tests.

**Decision: WAITING.** No candidate Issue, Research Brain transfer, paid Odds API, Supabase mutation, protected outcome read, production change or promotion. Source examples are not a complete cohort or a betting edge.

## Cycle accounting
One new direction screened; zero admitted candidates; zero DATA_FEASIBLE; zero new Issues; zero Research Brain transfers; zero outcome tests. Previous visible reports also show no verified transfer, but exact 24h cycle durations are not instrumented, so no speed claim.
