# Football AI Research Agent V3 — Gemini Free

V3 replaces the paid GitHub Copilot cloud coding-agent dependency with the official
Google Gemini CLI GitHub Action.

## Goal

After one-time credential setup, an owner-created `[AGENT-RESEARCH]` Issue can run
entirely in GitHub Actions while the user's computer is off:

Issue -> V2 deterministic intake -> Gemini file-edit pass -> deterministic safety/test
gates -> isolated branch -> pull request.

## Disabled by default

The Gemini execution job runs only when all of these are true:

1. the event is an Issue event;
2. the Issue author is the repository owner;
3. V2 returns `READY_FOR_PREREGISTRATION`;
4. repository variable `RESEARCH_GEMINI_ENABLED` equals `true`.

Until the variable is explicitly enabled, V2 continues to work but Gemini is skipped.

## One-time setup

Under **Settings -> Secrets and variables -> Actions**:

- add repository secret `GEMINI_API_KEY` using a Google AI Studio API key;
- add repository variable `RESEARCH_GEMINI_ENABLED` with value `true`.

Optional:

- add repository variable `GEMINI_MODEL` to select a supported Gemini model.
  If omitted, the Gemini CLI/action default is used.

Never commit or paste the API key into Issues, source files, logs, or documentation.

## Security boundary

The Gemini action receives only file read/search/edit tools. It does not receive shell,
GitHub, web, Supabase, deployment, or paid Odds API tools.

Gemini may edit only these issue-specific roots:

- `research/agent_runs/issue_<N>/`
- `tests/agent_runs/issue_<N>/`
- `docs/agent_runs/issue_<N>/`

After Gemini exits, deterministic workflow code:

- validates `git status` against the issue sandbox;
- rejects delete/rename/copy operations;
- rejects production `.pkl` and protected runtime paths;
- installs zero-cost test dependencies without exposing `GEMINI_API_KEY`;
- syntax-checks generated Python;
- runs issue-specific tests;
- revalidates the final working tree;
- verifies production artifact SHA256 values are unchanged;
- runs `git diff --check`;
- stages only validated issue-sandbox paths;
- creates a unique research branch and PR;
- never merges or promotes production automatically.

## Existing Issue #428

After the secret and enable variable are configured, editing/reopening Issue #428 will
re-run the V2 workflow. Because its hypothesis already passes the intake gate, the V3
Gemini job can then execute automatically.

## Failure behavior

If Gemini modifies an out-of-sandbox path, a test fails, a production hash changes, or
the credential is missing, the workflow stops before commit/push/PR creation.

Free-tier quota exhaustion is also a normal failure mode: no fallback to a paid API is
configured.
