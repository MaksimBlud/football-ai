# Prospective Availability Signal Lab — Protocol

Status: **OPEN — RESEARCH-ONLY / DATA-COLLECTION FIRST**

## Research question

Does genuinely point-in-time player availability information add stable predictive value for pre-match 1X2 outcomes after bookmaker market probabilities are already known?

This is a new independent research block. It does not reopen or tune the closed Historical Football Signal Lab.

## Initial scope

The initial research leagues are EPL, La Liga, and Serie A. The primary source is API-Football `/injuries`, queried against provider fixture IDs only after the relevant league-season reports `coverage.injuries=true`.

API-Football documents `/injuries` as a pre-match availability endpoint that can return injury and suspension records for a fixture. Because the endpoint does not provide a guaranteed public-publication timestamp for every observation, the collector's own observation time is authoritative whenever a provider publication timestamp is unavailable.

No historical `start_date` / `end_date` injury spell is sufficient to establish information-time availability.

## Canonical fixture identity

Availability observations must attach to the existing canonical fixture identity:

`(league, home_team, away_team, commence_time_utc)`

Provider fixture IDs are retained as source identifiers but do not replace repository fixture identity.

## Information-time contract

Every normalized observation must retain at minimum:

- provider and provider fixture/team/player identifiers;
- canonical league, home team, away team, and UTC kickoff;
- observed team/player name, availability type, and reason;
- `observed_at_utc`;
- `first_seen_timestamp_utc`;
- `source_timestamp_utc` and `source_timestamp_kind`;
- a SHA256 fingerprint of the raw source payload.

`source_timestamp_kind` is either `provider_published` when a reliable provider publication timestamp is actually present, or `collector_observed` otherwise.

**Prediction eligibility is governed by `first_seen_timestamp_utc <= prediction_cutoff_utc`.** Retrospective event dates, return dates, injury start dates, current roster flags, or post-kickoff updates must never move an observation backward across the cutoff.

## Snapshot and mutation rules

Collection is append-oriented. A later provider response may change a player's status or reason, but must not rewrite the historical fact that an earlier version was first observed at a particular time. Raw-response fingerprints must allow repeated identical polls to be recognized without inventing a new information state.

Postponed fixtures must retain their provider fixture identity and be reconciled to the repository fixture identity using the current canonical kickoff. Any kickoff change must remain auditable; collectors must not silently attach old observations to a different fixture.

## Pre-registered evaluation

No predictive evaluation begins until a prospective dataset exists with sufficient coverage. The primary paired comparison is:

`MARKET_MODEL` vs `MARKET_AVAILABILITY`

Both variants must use exactly the same eligible fixtures and the same market rows. The availability variant may use only observations first seen by the frozen prediction cutoff. Primary scoring metrics are multiclass Brier score and log loss, with accuracy reported as secondary context.

Results must be reported aggregate and by league/time block. Promotion evidence requires stable improvement rather than a single favorable aggregate or one league. ROI or betting claims, if later studied, require a separately pre-registered decision rule and OOS evaluation.

Feature design and prediction cutoffs must be frozen before outcome-based comparison. Repeatedly changing injury weights, windows, key-player thresholds, or cutoffs after observing results is not valid promotion evidence.

## Player importance

Historical player participation may be used to define player importance only when it is itself computed from matches completed before the prediction cutoff. Existing prior-365-day minutes concepts are research candidates, not automatically accepted features.

Availability timing and player importance are separate contracts: a point-in-time importance estimate does not repair an availability record whose information time is unknown.

## Safety boundaries

This block must not:

- modify or promote production `.pkl` artifacts;
- add availability features to production inference;
- change calibrators, production thresholds, or live prediction decisions;
- use closing odds observed after the prediction cutoff as model features;
- backfill historical injury spells and label them strict point-in-time;
- mutate existing market observations or prediction ledgers.

A future research-only persistence table and scheduled collector may be added after this protocol and source contract pass review. Supabase activation is a separate step.

## Phase gates

Phase 1 is complete when the source/timestamp contract, protocol, and focused tests are merged without production changes.

Phase 2 may bootstrap provider league/fixture coverage, verify unresolved provider identifiers live, implement normalized append-only collection, and add persistence tests.

Phase 3 is prospective accumulation. No outcome-driven feature tuning should occur during this period.

Phase 4 is the frozen paired market-incremental evaluation described above.

No production promotion is implied by any phase of this lab.
