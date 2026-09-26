# CORNER_REGIME_ADJUSTED_DIRECTION_V2_METADATA_RESULTS

Status: **WAIT_FOR_COHORT / AUTHORITATIVE METADATA-ONLY CHECK / NO ODDS OPENED**

## Provenance

- V2 planner source of truth: PR #390 / merge `1431cec32bec5c039a4ac396d2ab383fdd77efcf`;
- metadata-only live planner: PR #392 / merge `fa7745519fb7f919b0b064a46670e0b98b1660a6`;
- explicit same-repo metadata trigger hardening: PR #393 / merge `2043de27f4877355f3f5c1c3a510ce8bb6ccfa7d`;
- authoritative metadata workflow run: `35424349695`;
- tested head: `0746a721554b03ae28eca575b489fe4399e55385`;
- immutable metadata artifact: `10578826642`;
- artifact digest: `sha256:d486527409bed8e4a0cc11ed562ac7574e9362f3c9c83808038b90918d9388e4`;
- provider: 5DollarFootballAPI Free surface;
- provider requests: **5 / 10**;
- paid subscription used: **false**;
- odds endpoint used: **false**;
- market prices opened: **false**;
- match outcomes used for research evaluation: **false**;
- football-state/CORNERS10 used: **false**;
- Supabase writes: **none**;
- production `.pkl` hash guard: **PASS**.

## Frozen V2 metadata contract

The future-only cutoff remains:

`2026-09-19T00:00:00Z`

Prior corner samples excluded by immutable fixture ID:

- discovery sample: 55;
- fresh repricing replication: 50;
- V1 regime-adjusted direction sample: 46;
- total excluded fixture IDs: **151**.

The metadata cohort may lock only when all are true:

- all 5 leagues represented;
- at least 2 metadata blocks per league;
- at least 12 metadata blocks pooled;
- at least 80 metadata potential unordered pairs pooled.

A metadata block remains:

`(league, UTC kickoff date)`

Only whole blocks may be included.

The unchanged downstream statistical gate still requires:

- at least 30 eligible odds rows;
- at least 4 leagues with comparable pairs;
- at least 8 contributing regime blocks;
- at least 40 actual comparable pairs;
- concordance >= 0.60;
- one-sided 20,000-permutation p < 0.10.

The metadata lock does not weaken or replace that statistical gate.

## Authoritative live metadata check

Run `35424349695` queried only the allowed fixture-list endpoint.

Observed metadata:

- live fixture metadata rows returned: **197**;
- provider requests: **5** (one page per league was sufficient);
- prior excluded fixture IDs: **151**;
- normalized finished future fixtures at/after cutoff: **0**;
- candidate future regime blocks: **0**;
- candidate future fixtures: **0**;
- metadata potential pairs: **0**.

Therefore the binding planner status is:

**`WAIT_FOR_COHORT`**

No cohort fixture IDs were locked.

## Why the empty future cohort is expected

The authoritative check was executed very shortly after the frozen cutoff `2026-09-19T00:00:00Z`.

The provider's current Free inventory contained finished fixtures only from before that cutoff. The latest returned EPL finished fixture in the captured metadata was on `2026-09-18T19:00:00Z`.

Therefore zero normalized future finished fixtures is an expected temporal state, not a data-processing failure.

## Important trigger note

During PR #393, a literal execution marker in explanatory PR prose caused an accidental metadata-only pre-full-CI trigger.

That run is explicitly non-authoritative and must not be used as a cohort lock.

The trigger matching was hardened before the authoritative execution. The authoritative run `35424349695` was started only after exact-head CI was green, and the execution marker was removed immediately after launch.

No odds endpoint was exposed by this incident.

## Binding interpretation

This metadata check does **not** test the FAIR_CENTRE direction hypothesis.

It only answers whether enough future, already-finished fixture metadata currently exists to freeze the V2 cohort.

Current answer:

> **No. The project must wait for future league-day blocks to finish before any V2 cohort can be locked.**

Because status is `WAIT_FOR_COHORT`:

- no odds acquisition is authorized;
- no opening/closing prices may be read for V2;
- no statistical evaluation may be run;
- no fixture IDs may be selected ad hoc outside the frozen planner;
- no provider-plan upgrade is authorized.

## Next allowed action

A later metadata-only check may re-run the same frozen planner against newer finished fixture inventory.

That check must preserve:

- cutoff;
- five leagues;
- 151 prior exclusions plus any future immutable V2 lock if one later exists;
- whole-block selection;
- 2 blocks/league;
- 12 blocks pooled;
- 80 metadata potential-pair lock;
- no odds access before `COHORT_LOCKED`.

If the planner later returns `COHORT_LOCKED`, the exact selected fixture IDs and block membership must be saved immutably before any separate odds-acquisition PR is created.

## Safety

- research-only;
- `NO_BET`;
- no production promotion;
- no production `.pkl` changes;
- no odds endpoint;
- no market prices;
- no paid provider action;
- no Supabase writes;
- no automatic odds collection.

---

## Authoritative metadata recheck — 2026-09-26

A second metadata-only inventory check was executed after one week of additional finished fixtures.

Execution-harness PR:

- PR #407;
- closed **without merge** after the run;
- exact head: `62420be164e744be2db2a7b08da5921f53476746`.

Authoritative workflow run:

`36218178333`

Immutable artifact:

- artifact ID: `10898320900`;
- digest: `sha256:276812a4c34c4c1fac5ea9c3f45e82c997bbda85a8fc629eb0c930f76577d635`;
- final size: 23,329 bytes.

Safety proof:

- provider requests = **5 / 10**;
- fixture-list metadata only;
- odds endpoint used = false;
- market prices opened = false;
- match outcomes used = false;
- football-state used = false;
- paid subscription used = false;
- production `.pkl` before/after hash diff = clean.

Observed future metadata:

- live fixture metadata rows returned = **231**;
- prior frozen fixture exclusions = **151**;
- normalized finished future fixtures after cutoff = **43**;
- candidate qualifying league-day blocks = **10**;
- candidate fixtures in those blocks = **43**;
- metadata potential pairs = **74**.

Blocks by league:

- EPL = **2**;
- La Liga = **2**;
- Serie A = **2**;
- Bundesliga = **2**;
- Ligue 1 = **2**.

Therefore the per-league block gate is now satisfied for all five leagues.

The remaining frozen pooled gates are not yet satisfied:

- pooled blocks: **10 / 12**;
- metadata potential pairs: **74 / 80**.

Binding planner status remains:

**`WAIT_FOR_COHORT`**

No fixture cohort is locked:

- selected blocks = 0;
- selected fixtures = 0.

### Distance to frozen metadata lock

Relative to the preregistered aggregate thresholds, the current inventory is short by:

- **2 qualifying pooled blocks**;
- **6 metadata potential pairs**.

This is descriptive only. The thresholds must not be lowered, and no ad-hoc block may be selected outside the deterministic planner.

A later metadata-only check may use the same frozen contract after more matches have finished.

Until the planner first returns `COHORT_LOCKED`:

- no V2 odds acquisition;
- no opening/closing market reads;
- no cohort lock manifest;
- no real acquisition-plan instance;
- no V2 direction evaluation.

---

## Immediate metadata recheck — 2026-09-26

A further metadata-only check was executed immediately at user request, without waiting for another full league round.

Execution-harness PR:

- PR #409;
- closed **without merge** after the run;
- exact head: `8ebab42da35d69f11d199975011a2128b7f9c194`.

Authoritative workflow run:

`36218898253`

Immutable artifact:

- artifact ID: `10898297066`;
- digest: `sha256:eb163d097dc2713b8f8f03370eacead91a15d3a38c0757e48b301d82e799446c`;
- final size: 23,329 bytes.

Safety proof:

- provider requests = **5 / 10**;
- fixture-list metadata only;
- odds endpoint used = false;
- market prices opened = false;
- match outcomes used = false;
- football-state used = false;
- paid subscription used = false;
- production `.pkl` before/after hash diff = clean.

Observed future metadata was unchanged from run `36218178333`:

- live fixture metadata rows returned = **231**;
- normalized finished future fixtures after cutoff = **43**;
- candidate qualifying league-day blocks = **10**;
- candidate fixtures in those blocks = **43**;
- metadata potential pairs = **74**;
- blocks by league = EPL 2 / La Liga 2 / Serie A 2 / Bundesliga 2 / Ligue 1 2.

Binding status remains:

**`WAIT_FOR_COHORT`**

The pooled frozen gate still lacks:

- **2 qualifying blocks** versus 12 required;
- **6 metadata potential pairs** versus 80 required.

No cohort is locked and no V2 odds are authorized.

This immediate rerun confirms that provider finished-fixture inventory had not changed between the two 2026-09-26 authoritative checks. Do not repeat metadata calls again until there is a plausible inventory change or a new operational reason.

