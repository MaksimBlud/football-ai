# V2 source authenticity: prove the actual GitHub workflow that created the history archive

**Scope:** the restored, unchanged original `MARKET_ANCHOR_1X2_V2`, strict research-only / NO_BET.

The existing free V2 forward recorder (`serie_a_v2_forward_capture.py`) checked the GitHub Actions archive name, source branch `main`, entire ZIP SHA256, every archived historical CSV SHA/date, and archive-created-before-quote. That proves byte integrity against the GitHub artifact metadata, but a main-branch artifact with a *matching title* could be uploaded by a different workflow. It could be wrongly classified as the approved original history collector.

This patch **requires the authoritative parent GitHub workflow run** before attempting archive download or V2 inference:

- GitHub artifacts must specify `workflow_run.id` (positive int), the unchanged 40-character hexadecimal `head_sha`, `head_branch=main`, and the original archive digest and creation time.
- For each selected source artifact, a separate authenticated `GET /repos/MaksimBlud/football-ai/actions/runs/{run_id}` is required. The response must match the original parent ID/SHA, the **exact path** `.github/workflows/serie-a-v2-free-real-quote-diagnostic.yml`, the `main` branch, allowed free source triggers `push|schedule|workflow_dispatch`, and **completed / success**.
- The parent run's `updated_at` (conservative last GitHub run timestamp) must be strictly before the *saved bookmaker quote time*. The run's creation time cannot be after the source ZIP's upload timestamp, and upload cannot postdate parent completion.
- A single selected source archive's parent check is cached in one V2 cycle; validation is repeated against each quote's actual timestamp. No parent attestation means **no V2 preview and no archive download**.
- Completed parent metadata is recorded alongside each candidate's archive hash/model hash for third-party verification. This does **not** promote shadow outputs: still 19 unchanged original features/weights, `active_lambda=0`, `NO_BET`, no prospective cohort admission, no protected 2026/27 outcomes read.

Regression tests cover the accepted synthetic authentic workflow and failures for wrong workflow path, wrong commit, failed/incomplete run, disallowed event, run finishing after quote, missing parent ID, and lack of verification before ZIP download. The existing live quote cohort is not retroactively eligible: its 20 records predate the first valid source ZIP, so no source-run validation is attempted for them.

The code performs **only** authenticated GitHub read requests and existing read-only Supabase 1X2 fetches; no paid Odds API, no new data vendors, no old production model, no Supabase writes, no production .pkl changes, no training or promotion.

**Next gate after merging:** run on main, validate CI and the result log / immutably archived report. A real source-before-quote V2 shadow prediction still requires a **new bookmaker quote after source capture** with fresh explicit provider authorization if the existing budgeted collector is used. Even then, lack of verified 2026/27 current form and frozen prospective comparison means V2's quality is not yet proven.
