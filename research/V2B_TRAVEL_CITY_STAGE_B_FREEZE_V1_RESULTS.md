# V2B TRAVEL-CITY STAGE-B FREEZE V1 — Results

Status: **FEATURE COHORT FROZEN / NO DIRECTION TEST**.

## Provenance

First successful feature-freeze workflow run:

`36595044678`

Authoritative frozen feature artifact:

- ID `11046080870`;
- digest `sha256:f9908bca9f20d7726cbd27d7f3a96329a4e0bb9af0b0deda97d336b15b440192`;
- generating head `d0655ac12faedf1fdf5c993d642e861ed01c6341`.

Immutable travel-city source:

- artifact ID `11044402420`;
- digest `sha256:24eaa543e51f1d19ec34d5b348fa091b91d31e7eca2ceeac270338dbaab3ab04`;
- source status `FULL_43_TRAVEL_CITY_PROXY_FEASIBLE`;
- 43 fixtures / 86 team-sides / 86 finite travel distances.

No market-direction artifact was read.

## Frozen mapping

Mapping ID:

`JOINT_TRAVEL_CITY_COHORT_MEDIAN_SIGN_V1`

Feature:

`joint_travel_city_km = home_travel_city_km + away_travel_city_km`

Feature-only cohort median:

**600.464688 km**

Score:

`stage_b_score = 600.4646884282998 - joint_travel_city_km`

Call:

- score > 0 -> **UP**;
- score < 0 -> **DOWN**;
- score == 0 -> **NO_CALL**.

Frozen qualitative orientation:

- lower joint travel burden -> UP;
- higher joint travel burden -> DOWN.

This was fixed before any `centre_delta` or observed market direction was opened.

## Frozen calls

Across all 43 fixtures:

- UP = **21**;
- DOWN = **21**;
- NO_CALL = **1**.

Joint travel range:

- minimum = **50.273427 km**;
- maximum = **4601.796009 km**.

Fixture identity hash:

`sha256:a73b44ee30f216e77425f1e014391c89deacd8e02493008368aa8c74f52d4f3e`

Frozen feature hash:

`sha256:a16154b7fac0c8b12868569fd5a5b96d48813fb8a5192480dc4dd77f3638eb18`

## Calls by league

EPL:

- UP = 8;
- DOWN = 1;
- NO_CALL = 0.

La Liga:

- UP = 3;
- DOWN = 6;
- NO_CALL = 0.

Serie A:

- UP = 4;
- DOWN = 4;
- NO_CALL = 1.

Bundesliga:

- UP = 4;
- DOWN = 4;
- NO_CALL = 0.

Ligue 1:

- UP = 2;
- DOWN = 6;
- NO_CALL = 0.

This league heterogeneity is retained exactly. No league-specific threshold is permitted
after direction is opened.

## Closed degrees of freedom

After this freeze, do not:

- move the 600.464688 km median threshold;
- reverse the sign;
- replace joint travel with away-only travel;
- switch to max(home, away) travel;
- add rest days or travel/rest interaction;
- add competition weights;
- use league-specific medians;
- drop leagues;
- reassign the one NO_CALL row;
- combine with FAIR_CENTRE before evaluating this primary mapping.

## Next permitted block

A separate evaluator may join this exact immutable feature artifact to the already-opened
43-row V2B market-direction artifact.

Required diagnostics:

1. preserve all 43 rows;
2. preserve exact 21 UP / 21 DOWN / 1 NO_CALL calls;
3. report ZERO observed movement separately;
4. evaluate only frozen UP/DOWN rows with non-zero movement for concordance;
5. compare with constant-UP / constant-DOWN baseline on the same comparable subset;
6. report UP recall, DOWN recall and balanced accuracy;
7. report by-league diagnostics without excluding any league;
8. report Pearson/Spearman stage_b_score vs centre_delta;
9. report mean centre_delta for frozen UP and DOWN groups.

Opened-sample classification remains:

`PROMISING_DIRECTION_HYPOTHESIS` only if:

- pooled concordance > 0.60;
- at least 3 leagues have >=2 comparable rows and concordance >0.50;
- mean centre_delta for UP calls >0;
- mean centre_delta for DOWN calls <0.

Otherwise:

`WEAK_OR_INCONSISTENT_DIRECTION_HYPOTHESIS`.

## Safety

- research-only;
- NO_BET;
- market rows read = false;
- V2B odds read = false;
- FAIR_CENTRE read = false;
- centre_delta read = false;
- direction test performed = false;
- target outcome used = false;
- rest feature used = false;
- travel/rest interaction used = false;
- Odds API requests = 0;
- Supabase operations = 0;
- production model operations = 0;
- production `.pkl` unchanged.
