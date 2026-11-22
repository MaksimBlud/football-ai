# API-Football Free — original V2 statistics-source audit

**Checked:** 2026-11-20 19:53:31 UTC  
**Decision:** HOLD / NO INTEGRATION  
**Scope:** fixture statistics only, as lagged inputs for future original V2 forecasts. No odds endpoint is part of this audit.

## What is technically promising

The official pricing page lists a $0 Free plan with 100 requests/day, and includes a Statistics endpoint among the listed endpoints. It also warns that free plans are limited by available seasons. The official statistics documentation describes one-fixture statistics and lists shots on/off target, total shots, blocked shots, fouls, corners, offsides, possession, yellow/red cards, saves and passing metrics.

At one request per fixture, 380 fixtures would require at least 380 requests (four full 100-request daily quotas), before fixture/coverage calls, retries or other quota use. The free plan's actual Serie A 2026/27 coverage was not verified.

## Provenance limitations

The inspected documentation gives update-frequency guidance, but does not establish a per-stat first-observed/source timestamp or a guaranteed freshness SLA. Recording local receipt time and a SHA-256 archive before a later quote would prove local possession before that quote; it would not prove when the upstream provider first observed each statistic.

## Rights limitations

The official terms say data is obtained from partners, prohibit direct resale, state that no publication license is granted for user applications/websites/products, require users to obtain necessary third-party authorizations, and state that the provider grants no commercial rights on covered competitions. The inspected terms do not establish an upstream rights chain or written permission for the intended internal ML use.

## Frozen V2 decision

**Do not integrate.** A new statistics provider would change the existing V2 source contract. Keep the existing frozen candidate, 19-feature order, weights, scaler/imputer, active_lambda=0, and shadow_lambda=1 unchanged. No account, key, API request, odds request, Supabase write/DDL, model change, or protected-outcome read was performed.

## Official evidence

- Pricing: https://www.api-football.com/pricing/
- Documentation: https://www.api-football.com/documentation-v3
- Terms: https://www.api-football.com/terms
