# Football AI Research Orchestrator V4

Research Orchestrator V4 turns one guarded research Issue into a persistent autonomous
research run that can continue across multiple GitHub Actions jobs while the user's
computer is off.

## Goal

The user should not need to repeatedly write "continue". For one research direction,
V4 keeps working until one of three terminal states is reached:

- `DONE` — the direction is reasonably exhausted and a final report exists;
- `BLOCKED` — a genuine external blocker requires human action;
- `QUOTA_WAIT` — a transient free-tier/model-capacity problem; V4 stays quiet and retries later.

Intermediate `CONTINUE` and `QUOTA_WAIT` states do not post progress comments to the
Issue.

## Persistent state

Every issue gets one persistent branch:

`agent/v4-issue-<ISSUE_NUMBER>`

Each successful research iteration must write:

`research/agent_runs/issue_<N>/STATE.json`

with:

```json
{
  "status": "CONTINUE|DONE|BLOCKED",
  "summary": "short factual status",
  "next_step": "required for CONTINUE, otherwise null",
  "blocker": "required for BLOCKED, otherwise null"
}
```

A `DONE` state is valid only if this file also exists and is non-empty:

`docs/agent_runs/issue_<N>/FINAL_REPORT.md`

The final report must begin with a simple-language conclusion and may include a
technical appendix after it.

## Autonomous loop

1. Owner-created `[AGENT-RESEARCH]` Issue is checked through the existing deterministic
   registry/intake rules.
2. V4 creates or resumes the issue-specific branch.
3. Gemini gets file read/search/edit tools only.
4. One coherent research iteration is performed inside the issue sandbox.
5. Deterministic gates validate changed paths, syntax, issue-focused tests, `git diff
   --check`, and production `.pkl` hashes.
6. The iteration is committed to the persistent issue branch.
7. `CONTINUE` dispatches the next V4 run automatically.
8. `DONE` opens one final PR and posts one final completion message.
9. `BLOCKED` posts only the real blocker.

A hard cap of 24 committed iterations prevents runaway loops.

## Dynamic minute-quota retry

When all model attempts fail with a transient quota/capacity error, V4 now reads the
provider's retry hint from the captured Gemini stderr. For errors such as
`Please retry in 56s`, it waits for that delay plus a small safety buffer and
redispatches the same Issue automatically.

Short retries are bounded to three consecutive attempts. If Google reports a daily
quota, or the short-retry budget is exhausted, V4 remains in `research-v4-waiting`
and the three-hour scheduler becomes the fallback. This prevents a normal one-minute
TPM/RPM reset from turning into a multi-hour pause while still avoiding runaway loops.

## Free-tier resilience

The model order is intentionally spread across separate Gemini model quotas:

1. `gemini-3.5-flash-lite`
2. `gemini-3.1-flash-lite`
3. `gemini-3.5-flash`

Each model pass is limited to 16 session turns. If all model attempts fail with transient
quota/capacity signals such as HTTP 429, HTTP 503, `RESOURCE_EXHAUSTED`, high demand,
or retry-after messages, V4 captures the action's real `gemini-artifacts/stderr.log`, classifies that evidence, and adds `research-v4-waiting` while leaving
`research-v4-running` in place.

The scheduler wakes every three hours and redispatches open Issues carrying
`research-v4-running`. No paid fallback is configured.

## Labels

V4 creates and maintains these labels automatically:

- `research-v4-running`
- `research-v4-waiting`
- `research-v4-done`
- `research-v4-blocked`

## Safety boundary

V4 does not:

- promote or replace production models;
- modify production `.pkl` artifacts;
- write to Supabase;
- call paid Odds API endpoints;
- deploy runtime changes;
- auto-merge the final PR;
- retune closed hypotheses on seen data;
- bypass prospective/frozen gates.

Old V3 live Issue execution is disabled when V4 is installed so V3 and V4 do not spend
quota in parallel. V3 remains as a PR contract-validation workflow.

## User-visible behavior

Normal autonomous progression is silent. The Issue receives a message only when:

- the deterministic intake cannot start safely;
- a non-transient API/model failure occurs;
- the research reaches `BLOCKED`;
- the research reaches `DONE`.

This is intentional: the user should return to a final result rather than a stream of
intermediate progress messages.
