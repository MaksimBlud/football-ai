# Football AI — ChatGPT brain + GitHub execution, without AI APIs

## Current architecture

GitHub Actions is **not** an AI model. It cannot autonomously invoke the ChatGPT
conversation, even with a scheduled workflow. There is no integration in this
repository that can call the ChatGPT consumer model from GitHub without using a
separately configured model service. We deliberately **do not** use Gemini,
Groq, OpenAI API, paid provider credits, or a local model.

The independently scheduled `.github/workflows/football-ai-engineering-autopilot.yml`
is now an **hourly read-only engineering checkpoint**. It:

- Reads current `main`, live GitHub issue #581 (backend) and #582 (frontend),
  and open pull requests through GitHub's built-in read-only token.
- Reports exact main SHA, task status, and PR links in its GitHub Actions job
  summary. It makes zero model calls and zero code modifications.
- Validates the workflow and safety guard when the workflow itself changes.
- Uses GitHub's own scheduling instead of the ChatGPT task scheduler.
- Does not pretend that green CI means an AI wrote new code.

The **coding/decision-making component** is ChatGPT. It can work in this chat
or during an available ChatGPT scheduled-task invocation using the connected
GitHub tools. Its actual run duration, availability and ability to mutate
GitHub from a scheduled invocation must be established by real SHA/PR/CI proof.
It cannot be awakened by GitHub Actions alone.

## Proven no-API development loop (interactive)

1. Read GitHub fresh `main`, open issues, PRs and required CI.
2. Implement one bounded scope in a dedicated dev branch with the ChatGPT
   GitHub connector. Do not require a separate model API.
3. Add regression tests; open a PR. GitHub Actions performs six project
   validation jobs on PR heads.
4. Confirm required checks **on the exact PR head SHA** and compare to the
   fresh current `main`. Merge only through safe exact-head PR merge.
5. Verify `main` and record the result. Do not automatically deploy Vercel,
   change production .pkl files, write Supabase, or call paid The Odds API.
6. A paused ChatGPT task is **not** proof the GitHub checkpoint failed;
   conversely, a successful checkpoint is **not** proof of autonomous coding.

## Actual verified progress

- PR #603 installed the first scheduled GitHub Actions workflow, but that
  version depended on free-tier Gemini; it was not a working no-API coder.
- PR #598 was subsequently merged with database-side as-of filters, event and
  kickoff identity checks, price sanity checks and regression tests.
- PR #604 was subsequently merged with explicit model/market snapshot
  provenance and clearer unavailable/ambiguous market states on match detail.
- This revision removes external AI dependencies from the independent hourly
  workflow rather than creating hourly missing-key failures.

## Safety and remaining limitation

The checkpoint uses only `contents: read`, `issues: read`, and
`pull-requests: read`. It never creates commits, PRs or issues by itself.
The separate ChatGPT builder automations may perform code/PR work when they
actually run and have GitHub write capability; their known scheduler
self-disabling issue is **not resolved** by this workflow.

The goal of completely autonomous around-the-clock ChatGPT coding without
a model API or an always-on local model remains **unmet**. No configured,
verifiable way for GitHub Actions to awaken this consumer ChatGPT conversation
has been established. Do not claim otherwise.
