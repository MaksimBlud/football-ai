# V2B CROSS-BOOK RAW FEASIBILITY V1 — Results

Status: **FINAL SOURCE FEASIBILITY / INSUFFICIENT_CROSS_BOOK_DIVERSITY**

## Provenance

Workflow run:

`36582565629`

Authoritative audit artifact:

- ID `11040276332`;
- digest `sha256:e8f83be1ed950b53d32788b921b678971d8cb7bc4d8d4cf38a46104aea8626e2`;
- size 1,311 bytes.

Immutable raw V2B source:

- artifact ID `10899611444`;
- digest `sha256:c2f5313efad4afb8663d9980f5ea004f52fe02827a83b5c99a8b775c35498a57`;
- locked raw responses = 43.

No new provider request was made.

## Bookmaker diversity

Captured raw responses:

**43 / 43**

Bookmaker-count distribution:

- exactly 1 bookmaker = **43 fixtures**;
- >=2 bookmakers = **0 fixtures**;
- no bookmaker = **0 fixtures**.

Unique bookmaker slug:

**bet365**

Bet365 appears in:

**43 / 43 fixtures**

No second bookmaker slug or name appears anywhere in the immutable raw cohort.

## Corner-market structures

Within the single Bet365 entry:

- opening corner structure present = **43 / 43**;
- closing corner structure present = **43 / 43**;
- in-play corner structure present = **43 / 43**.

These are different states from one bookmaker. They are **not** cross-book data.

## Final status

**`INSUFFICIENT_CROSS_BOOK_DIVERSITY`**

`cross_book_direction_feature_feasible = false`

`partial_cross_book_support = false`

The existing V2B raw artifact cannot support a cross-book bookmaker-disagreement,
leader/laggard, sharp-vs-soft, consensus-dispersion, or cross-book direction hypothesis.

## Important distinction

The raw provider schema contains a `bookmakers` array, but the array contains only one
bookmaker for every locked fixture.

Therefore it would be methodologically invalid to:

- treat Bet365 opening vs closing as two bookmakers;
- treat the provider's opening/closing/in-play states as cross-book disagreement;
- manufacture a second book from an aggregate or transformed Bet365 line;
- claim that the existing V2B acquisition contains bookmaker microstructure.

## Relation to historical cross-book research

Historical Football-Data work had multiple bookmaker columns in earlier seasons but
suffered source-coverage and semantic instability in 2025/26.

The timestamped V2B source avoids that timing ambiguity, but the specific raw acquisition
contains only Bet365, so the cross-book hypothesis cannot be reconstructed from the
already-paid artifact.

## Decision

Close the **existing-V2B cross-book microstructure path**.

A genuine future cross-book experiment would require a separate provider/source contract
that returns at least two independently identified bookmaker lines at the same
pre-kickoff timestamp, frozen before any direction evaluation.

Do not spend provider credits on that acquisition unless a later source audit first proves
that multi-book corner lines are actually available.

## Next research implication

The next zero-cost Stage-B source screen should move to a genuinely different football
state dimension:

**full-calendar congestion / recovery / travel**

It must include non-league fixtures where possible:

- domestic cups;
- UEFA competitions;
- league matches;
- rest days;
- short-turnaround counts;
- optionally travel distance if fixture venues are reliably reconstructable.

This should begin as source/time-provenance feasibility only, not a direction test.

## Safety

- research-only;
- NO_BET;
- provider requests = 0;
- Supabase operations = 0;
- production model operations = 0;
- production `.pkl` hashes unchanged;
- centre_delta not read;
- market direction not evaluated.
