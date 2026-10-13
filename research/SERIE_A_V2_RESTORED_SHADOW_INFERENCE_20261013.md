# Serie A MARKET_ANCHOR V2 — restored original model, executable shadow

Date: 2026-10-13. **RESEARCH-ONLY / no automatic activation / no betting.**

The original 2026-09 frozen weights, not a newly tuned model, were recovered
in [PR #644](https://github.com/MaksimBlud/football-ai/pull/644) and
saved at `research/models/market_anchor_v2_serie_a_frozen_candidate.json`.
Immutable candidate artifact SHA256:
`a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`.

This change adds `serie_a_v2_frozen_shadow_preview.py`, a **working
inference bridge** to the established `market_anchor_1x2_v2_shadow.py`
calculator, using the actual 3,799-row fitted weight matrix, feature
median imputer and standard scaler. It accepts:
- existing read-only `odds_snapshots` rows for **future** Serie A events;
- an **external** exact 19-feature as-of history manifest for those same
  fixtures (including event ID, teams, kickoff, and history cutoff).

It rejects fixture identity mismatches, extra/fewer features, prices not
strictly above 1, unqualified clock times, duplicate data, quoted prices at
or after kickoff, and feature cutoffs later than the quote. Any quote older
than **24 hours** at query time is marked stale, never priced for this
diagnostic. No empty, guessed or season-inferred features are used. The
original frozen median-imputation path handles explicitly missing fields
only in otherwise complete manifest schemas.

If qualified inputs exist, it returns three separate probabilistic
triples: **no-vig bookmaker market**; **active lambda=0 identical market
fallback**; and **nonzero frozen V2 residual shadow**. These are never
presented as settled results or publication-ready AI forecasts.

To run with existing project server credentials and a separately verified
as-of feature manifest:

```bash
python serie_a_v2_frozen_shadow_preview.py --saved-supabase-quotes \
  --features-json /path/to/your/independently-verified-19-feature-input.json
```

The feature manifest is a JSON array of records with `event_id`,
`home_team`, `away_team`, `commence_time_utc`,
`feature_history_cutoff_utc` and `features` (mapping containing
exactly the 19 frozen original keys). Use only features derived from
records existing before the named cutoff; no later game results.

**Critical distinction:** merely supplying a JSON feature manifest does
not make its provenance trustworthy. The preview explicitly sets
`eligible_for_frozen_prospective_cohort=false` and
`eligible_for_product_publication=false` even if input time checks pass.
A proper immutable future V2 capture still requires an independently
attested feature source and genuine pre-kickoff incumbent/model/market
timestamps under the September frozen V2 protocol. It must not
retroactively count this diagnostic as prospective evidence.

## Current real data blocker

Read-only Supabase query at 2026-10-13:

- `odds_snapshots` for Serie A: **605** historical observations;
- **zero** rows with `commence_time_utc > now()`;
- latest Serie A `snapshot_time_utc` **2026-09-11 15:48:24.896863 UTC**.

Thus **zero eligible fixtures** can be scored right now. This is a real
input-data absence, not a problem with recovering V2, and cannot be
patched by fabricating quotes. Existing The Odds API limits and its paid
call explicit-authorization gate remain in effect. No provider requests
were made for this PR.

## Safeguards

- Exact SHA256 validated through the frozen V2 artifact checksum method;
  original scales, weights and feature order are used.
- `active_lambda=0` until the old stability gate is passed.
- No writes to Supabase, no `.pkl` files, no production site or Vercel
  changes, no alternative market source, no new experiment settlement.
- Does not import prospective outcomes. Only reads the existing quotes
  table when explicitly run with `--saved-supabase-quotes`.
- Synthetic regression tests execute actual model weights, verify
  meaningful shadow/residual differentiation and reject false input,
  old quotes or feature leak attempts.
- Output is ephemeral JSON, never registered as frozen prospective
  evidence, never labeled betting advice.
