# Last-120-second goal audit — 2026/27 season snapshot

**Snapshot cutoff:** matches completed through 2026-10-19 inclusive.  
**Scope:** Premier League, La Liga, Bundesliga, Serie A, Ligue 1, Russian Premier League.  
**Research only:** no production model, Supabase, or production pickle changed.

## Definitions

- **Criterion A — actual final 120 seconds:** a goal between the actual final whistle and 120 seconds before it.
- **Criterion B — final two minutes of announced added time:** goal in the final two minute labels of the referee-announced added-time period (for example, with +5 announced, goals at 90+4 or 90+5 qualify). This is not interchangeable with criterion A.

## Combined table

| League | Matches | A: goal | A: no goal | A: unresolved | B: confirmed goal | B: confirmed no goal | B: announced-time unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|
| Premier League | 70 | 5 (7.1%) | 65 | 0 | 0 (0.0%) | 69 | 1 |
| La Liga | 88 | 1 (1.1%) | 87 | 0 | 5 (5.7%) | 77 | 6 |
| Bundesliga | 54 | 4 (7.4%) | 50 | 0 | 4 (7.4%) | 47 | 3 |
| Serie A | 70 | 4 (5.7%) | 66 | 0 | 4 (5.7%) | 60 | 6 |
| Ligue 1 | 63 | 6 (9.5%) | 57 | 0 | 3 (4.8%) | 57 | 3 |
| Russian Premier League | 88 | 2 (2.3%) | 82 | 4 | 1 (1.1%) | 77 | 10 |
| **Total** | **433** | **22 (5.1%)** | **407** | **4** | **17 (3.9% confirmed minimum)** | **387** | **29** |

## Interpretation

### Criterion A

- Five European leagues: 345 matches; 20 had a confirmed goal in the actual final 120 seconds and 325 did not. Event times and second-half end events were available at second resolution in the Opta archive.
- RPL: 88 matches; 2 confirmed goals, 82 classified no-goal, and 4 unresolved boundary cases. RPL event data is minute-level, so its boundary cases are not treated as exact-second results.
- Across all six leagues, among the 429 matches resolved for criterion A, 22/429 = **5.13%** had a confirmed goal in the window.

### Criterion B — announced added time

The public event archive does not include a reliable field for the number of added minutes announced by the fourth official. I checked match commentary/report pages for late-goal candidates. The 17 positives in the table are **confirmed positives**, not a final estimate of the true season rate. A further 29 matches with late goals remain unresolved because their announced added-time figure was not independently verified. Thus the final criterion-B count is between 17 and 46 matches (3.9%–10.6% of 433) until those 29 cases are resolved.

Examples showing why the criteria differ:
- Celta Vigo–Racing Santander: +3 announced, goal at 90+2 — criterion B qualifies.
- Málaga–Espanyol: +3 announced, goal at 90+3 — criterion B qualifies.
- Newcastle–Liverpool: +5 announced, goal at 90+9 — criterion B does not qualify, despite a very late goal.
- Union Berlin–Schalke: +12 announced, goal at 90+13 — criterion B does not qualify.

## Data sources

- Open Opta event archive: https://github.com/peteowen1/pannadata/releases/tag/opta-latest
- Earlier audited report for the season snapshot through 2026-10-14: https://github.com/MaksimBlud/football-ai/blob/research/last120-whistle-20261015/research/last120_20261015/FINAL_REPORT.md
- Example match timelines with announced added time:
  - Celta–Racing: https://ofstats.com/matches/view/celta-de-vigo-racing-santander-2026-09-19
  - Málaga–Espanyol: https://ofstats.com/matches/view/malaga-espanyol-2026-10-09
  - Newcastle–Liverpool: https://www.beinsports.com/en-us/soccer/premier-league/newcastle-united-vs-liverpool-2026-08-23
  - Union Berlin–Schalke: https://ofstats.com/matches/view/fc-union-berlin-schalke-04-2026-09-11
