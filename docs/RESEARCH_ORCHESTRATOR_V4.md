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

Before each worker pass, an existing persistent Issue branch is refreshed by merging the
current `main` into it. This keeps long-lived research state while ensuring newly merged
orchestrator/provider code is available to the next iteration. The refresh is pushed back
to the Issue branch before model execution.

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

## Global Gemini queue

All V4 worker jobs share one GitHub Actions concurrency group:

`research-v4-global-gemini`

The group uses `queue: max`, so only one Gemini worker runs at a time while up to
100 additional workers may wait in GitHub's FIFO concurrency queue. This prevents
different research directions from competing for the same project-level Gemini TPM/RPM
quota.

Each eligible Issue receives `research-v4-queued` before entering the queue. The label
is removed only after the worker actually obtains the global queue slot. This gives a
simple visible distinction:

- `research-v4-queued` — waiting behind another research direction;
- `research-v4-running` without `research-v4-queued` — currently active or between
  autonomous continuation steps;
- `research-v4-waiting` — waiting for provider quota/capacity recovery.

The three-hour safety sweep now redispatches only `research-v4-waiting` Issues, rather
than every running Issue, so it cannot create duplicate queue entries for healthy
research loops.

## Per-Issue quota and work accounting

Each persistent research branch now also contains:

`research/agent_runs/issue_<N>/USAGE.json`

This file is updated deterministically by the orchestrator, not by Gemini. It records:

- `runs_started` — V4 worker runs started for the Issue;
- `model_passes_attempted` — total Gemini model passes;
- `groq_passes` plus historical Gemini `primary_passes` / fallback counters;
- `successful_model_runs`;
- `quota_waits`;
- `short_retries_scheduled`;
- `research_iterations_committed`;
- `done_runs` and `blocked_runs`;
- `last_updated_utc`.

Quota-only runs persist this file even when Gemini produces no research edits. These
usage-only commits have subjects beginning with `Research V4 usage #` and do not count
toward the 24 research-iteration safety cap. The cap counts only commits beginning with
`Research V4 issue #<N> iteration`.

This makes it possible to calculate actual free-tier consumption per research direction
after several real tasks instead of estimating only from provider limits.

## Dynamic minute-quota retry

When all model attempts fail with a transient quota/capacity error, V4 now reads the
provider's retry hint from the captured Gemini stderr. For errors such as
`Please retry in 56s`, it waits for that delay plus a small safety buffer and
redispatches the same Issue automatically.

Short retries are bounded to three consecutive attempts. If Google reports a daily
quota, or the short-retry budget is exhausted, V4 remains in `research-v4-waiting`.

Waiting tasks are now woken by a separate `Research V4 Heartbeat` workflow. It keeps
its own hourly cron, but does not depend on that cron alone: it also listens for
completion of several repository workflows whose scheduled execution has been observed
live. Before dispatching V4, the heartbeat atomically moves an Issue from
`research-v4-waiting` to `research-v4-queued`, preventing duplicate wakeups. If the
dispatch itself fails, the waiting label is restored.

This provides an independent cloud wake-up path even when the V4 workflow's own
`schedule:` event is delayed or absent.

## Free-tier resilience

V4 is now provider-diversified and **Groq-first**.

1. Primary: Groq `openai/gpt-oss-120b` through a repository-local file-only agent.
2. Emergency fallback: `gemini-3.6-flash` only when the Groq pass fails.

The Groq agent uses the OpenAI-compatible Chat Completions API and exposes only
repository read/search tools plus write/replace tools constrained to the current
Issue sandbox. It cannot write production artifacts, runtime code, Supabase, or
deployment state. Its conversation is deliberately compact and capped at four
turns. A dedicated `record_progress` tool appends a short evidence-backed checkpoint
to the current Issue's `PROGRESS.md`; a `CONTINUE` iteration is not considered
complete until both substantive sandbox progress and a fresh `STATE.json` exist.
This prevents repeated state-only commits that merely rephrase the same next step.
The final state write uses the dedicated `write_state` tool with structured
status/summary/next-step/blocker fields, avoiding long nested JSON strings that can
cause provider-side `tool_use_failed` errors.
Successful Groq responses also expose TPM reset headers; V4 paces subsequent turns
when the remaining token bucket is low.

V4 no longer fires three Gemini models in sequence. Groq failures are classified by
the **last decisive provider error** as `TRANSIENT_QUOTA`, `TOOL_FORMAT_RETRY`, or
`PERMANENT_BLOCKED`. This prevents an older TPM/429 line from masking a later
HTTP 400 `tool_use_failed`.

Short Groq TPM/429/503 conditions are retried through Groq and do **not** invoke
Gemini. When Groq supplies a long `retry-after` window (for example a TPD window
measured in many minutes), the worker fails fast into quiet `research-v4-waiting`
instead of sleeping/re-dispatching every minute; heartbeat recovery handles the
later wake-up. A `tool_use_failed` response first gets an immediate state-only Groq retry
that exposes only `write_state`; repeated format failures use bounded quick
redispatches and never fall back to Gemini. Gemini is reserved only for
`PERMANENT_BLOCKED`, preventing normal minute-window throttling or tool
serialization failures from burning the tiny Gemini daily quota.

If a transient quota/capacity signal remains after retries, or repeated tool-format
retries are exhausted, V4 records the evidence and returns to
`research-v4-waiting` for heartbeat recovery.

The original three-hour V4 scheduler remains as a secondary safety path. The independent
heartbeat is the primary recovery path for `research-v4-waiting` tasks. No paid fallback
is configured.

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
