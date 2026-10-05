# PROJECT CONTINUITY ADDENDUM — 2026-10-05 — ChatGPT Research Brain V1

## Architecture

The project now separates scientific planning from deterministic execution:

`ChatGPT Research Brain -> Research Program -> child [AGENT-RESEARCH] Issue -> Research V5 -> result -> Brain`.

Research V5 remains the no-API executor. ChatGPT is the scientific planner that
reviews all ACTIVE programs and chooses the next genuinely independent preregistered step.

Durable program source of truth:

`research/programs/registry.json`

Controller:

`research_program_controller.py`

Documentation:

`docs/CHATGPT_RESEARCH_BRAIN.md`

## Scheduler

An enabled ChatGPT task named **Football AI Research Brain** runs once per hour.

Each cycle reviews every ACTIVE program, all live child Issues, merged V5 results, and
existing experiments/continuity before creating a new follow-up.

The task is explicitly forbidden from automatically opting into V4 model APIs, using
paid data without fresh user approval, writing Supabase, touching/promoting production
`.pkl`, weakening frozen gates, or peeking reserved outcomes.

Duplicate detection was strengthened after the first Brain cycle: the Brain must search
existing experiments, continuity addenda, modules and closed Issues before proposing a
new child.

## Infrastructure merge

Research Program controller PR:

- PR #512
- merge: `dabc0ec2c53ab2c36de67f79441494c6046ab564`

The initial parent programs were:

- `cross_market_lead_lag`
- `kickoff_calendar_context`

## First Brain cycle — live proof

The Brain reviewed both ACTIVE programs in one cycle.

### Cross-market lead-lag

Initial follow-up Issue #513 proposed a temporal-stability audit.

Repository review then found that this was already answered by
`CROSS_MARKET_LEAD_LAG_REGIME_AUDIT_V1` / PR #468 and the continuity addendum
`PROJECT_CONTINUITY_ADDENDUM_20261004_LEAD_LAG_REGIME_AUDIT_V1.md`.

Issue #513 was closed as a duplicate before evaluator work.

The parent program then hit its stop rule:

- V1/V2 independent support remains rejected / NO_BET;
- seven-season temporal regime behavior is already audited;
- 2024/25 source/market anomaly audit found no broad explanation;
- remaining zero-cost follow-ups would be cosmetic transforms of the rejected signal;
- fresh timestamped/intraday paid data still requires explicit user approval.

Parent program status: **PROGRAM_DONE**.

Stop-rule PR:

- PR #519
- merge: `0a3a3f6f712919595b68cd5d9924e22c42dc2103`

### Kickoff/calendar context

Brain child Issue #514:

`kickoff_calendar_league_heterogeneity_v1`

The family was initially unsupported by V5, so V5 automatically created a no-API
recipe scaffold and did not invoke V4/Groq/Gemini.

The Brain implemented the deterministic evaluator and registered generic-pipeline recipe:

- PR #517
- merge: `19c57a914b842f22df0bb258b2ec1aabdc47c477`

V5 then ran autonomously:

- local passes: 3
- local iterations committed: 3
- model passes attempted: 0
- Groq passes: 0
- quota waits: 0
- final state: DONE

Frozen result:

`NO_STABLE_KICKOFF_CALENDAR_LEAGUE_HETEROGENEITY`

All three predeclared league-pair Bonferroni bootstrap intervals crossed zero in both
validation/OOT logic; no stable pairwise heterogeneity was confirmed.

The pooled kickoff/calendar null remains binding and was explicitly not rescued.

Final research result PR:

- PR #520
- merge: `bd40b0f513065ac3df782d561cdb586151893635`

Issue #514 is closed with `research-v5-done`.

## Current Research Brain frontier

`cross_market_lead_lag`: **PROGRAM_DONE**.

`kickoff_calendar_context`: **ACTIVE**.

Completed child Issues for kickoff/calendar:

- #428 — pooled incremental calendar OOS test: negative;
- #514 — preregistered three-league heterogeneity: no stable heterogeneity.

The next hourly Brain cycle may choose at most one new child for kickoff/calendar and only
from a genuinely independent allowed class such as temporal stability,
market-movement mechanism, cross-league transport, or an explicit close-direction
decision.

The Brain must not create another child merely to search arbitrary kickoff thresholds,
weekdays or favorable leagues.
