# Football AI Research Agent V2 — Issue Intake

V2 adds unattended GitHub Issue intake on top of the constrained V1 coordinator.

## Trigger

Create or edit an issue whose title begins with:

`[AGENT-RESEARCH]`

Example body:

```text
hypothesis_family: weather_match_conditions
independent_information_justification: Uses pre-match weather information not represented by the existing football-form or market-path families.
research_question: Does pre-match weather add incremental OOS information for total-goal probabilities?
```

`research_question` is optional when the title after the prefix already contains
the question.

## What happens automatically

GitHub Actions:

1. checks out current main;
2. validates the signal research registry;
3. parses the issue using repository code, not shell interpolation;
4. rejects exact already-registered hypothesis families;
5. requires an independent-information justification for novel retrospective families;
6. emits a structured JSON plan;
7. posts the deterministic decision back to the issue.

The user's computer does not need to remain on.

## V2 safety boundary

Issue intake does not read outcomes, execute arbitrary generated commands, write to
Supabase, spend Odds API credits, modify production artifacts, deploy, merge, or
promote models.

V2 is an unattended **planner/intake layer**, not yet an unrestricted code-writing
agent.
