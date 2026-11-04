# Football-Data source rights audit — 2026-11-04

## Decision

The original `MARKET_ANCHOR_1X2_V2` workflow must not make further Football-Data CSV requests or perform V2 feature inference from those files until the project's intended AI use and automated archival are explicitly authorized.

This is a conservative fail-closed decision. It does not alter the frozen V2 candidate, 19-feature order, weights, scaler, imputer, candidate SHA, protocol, `active_lambda=0`, `shadow_lambda=1`, or the 30-primary-completed-event evaluation gate.

## Provider policy evidence

The provider's current Fair Data Usage Policy says its free CSV/Excel data is intended for private individuals' personal betting and/or academic interest/research, permits only light automated downloading (up to twice per week), and says requests concerning commercial, AI-use, and model-training purposes should assume no data-use permission is granted.

Official policy page: https://football-data.co.uk/contact.php

A frequency limit is not a licence. The project's existing V2 use includes AI feature inference, and the checked-in project state has no explicit provider authorization for that use. The fact that the model is frozen and no retraining occurs does not itself establish an inference right.

## Required evidence before re-enabling

A later reviewed policy update must provide all of the following:

- documented authorization reference from the provider or a clearly applicable alternative-source licence;
- explicit permission for AI feature inference;
- explicit permission for automated source archiving;
- coverage of the ten historical-season CSVs and the current-season lagged-feature CSV;
- permitted retention and research-use scope.

Until then, the policy file remains `rights_status=NOT_GRANTED`, and live source/forward workflows require the owner-controlled GitHub repository variable `MARKET_ANCHOR_V2_SOURCE_RIGHTS_STATUS=GRANTED` as an additional gate. Both the checked-in rights policy and repository variable must permit execution. The variable alone cannot override the policy file.

## Operational boundaries

- Existing cron expressions are unchanged.
- Push events are offline-only for these live V2 entry points.
- The gate is checked before Supabase reads, GitHub artifact discovery, public CSV requests, or feature inference.
- No Supabase writes/DDL, paid provider requests, production `.pkl` changes, target-outcome reads, refit, promotion, or betting are permitted.
- Offline unit/regression tests remain runnable without rights or external data.
