# Original V2 public-source download budget

Audit date: 2026-11-02 UTC

## Provider policy evidence

The official Football-Data.co.uk contact page, updated 2026-10-30, says its free CSV/Excel data is intended for private individuals for personal betting and/or academic research, via manual download or at most light automated download (twice per week maximum). It says the data is not intended for commercial or data-training projects using heavy repeated automated download.

Official references:
- https://www.football-data.co.uk/contact.php
- https://www.football-data.co.uk/italym.php (Serie A data page; last updated 2026-10-29 at this audit)

This is a use-rights constraint, not merely a technical rate limit. The frequency guard below does not grant commercial, redistribution, or model-training rights. If the project use is commercial or otherwise outside the stated scope, a separately licensed source or explicit permission is required.

## Observed workflow demand on main

The existing schedules remain unchanged:
- Current-Form Source Capture: 05:50 UTC daily.
- Free Real-Quote Diagnostic: 06:13 UTC daily.

The 2026-11-01 run evidence recorded 11 public CSV downloads in Source Capture and 10 public CSV requests in Free Diagnostic. Both workflows were independently scheduled daily. This is materially more frequent than the provider's stated twice-weekly ceiling.

## Proposed guard

This PR adds a shared GitHub Actions artifact ledger across those two existing workflows:
- A reservation marker is uploaded before either workflow can start a public CSV download.
- Both workflows use one concurrency group and one marker artifact name.
- A new attempt is permitted only after at least 85 hours from the previous marker. Two such intervals exceed 168 hours, so three attempts cannot fit in any rolling seven-day window.
- The budget reader uses only GitHub Actions artifact/run metadata. It makes no Football-Data, Supabase, odds-provider, or outcome request.
- If GitHub metadata is missing, malformed, redirected, or unavailable, the guard fails closed.
- If a reservation is made and the later download fails, the reservation remains. This deliberately prefers fewer downloads over an automatic retry.
- Existing cron expressions are preserved. No other agent schedules or settings are touched.

The 85-hour guard limits automated workflow download sessions, not the number of CSV files fetched in one session. Source Capture currently still fetches 10 frozen historical CSVs plus the current-season CSV. Whether the provider counts each file separately is not defined on its page; a later optimization should reuse already verified frozen historical bytes and fetch only the changing current-season file. This PR does not claim that the remaining per-session file count is approved.

## Forecast consequence

The original current-form forward contract still requires source observation to be no older than 24 hours at each quote. Reusing an older artifact or skipping a refresh does not refresh its observation timestamp. Therefore, on days without a new source capture, the current-form forward path must report stale-source/no-forecast rather than invent freshness. This is an intentional scientific limitation.

No model, feature, weight, candidate SHA, lambda, source/quote age rule, or evaluation gate is changed. No paid API, Supabase write/DDL, production model artifact, target-outcome read, or automatic promotion is introduced.
