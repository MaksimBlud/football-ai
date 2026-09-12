# Product Production-Readiness Framework v1

Version: `product-production-readiness.v1`

## Purpose

This framework answers one governance question:

> Is a concrete `league × market` scope ready to be treated as an operational
> Football AI product market, and if not, what exactly is still missing?

It is deliberately separate from model training, research evaluation, Product
Decision ranking, betting and model promotion.

## Status vocabulary

Every observed league/market scope has one of five states:

- `RESEARCH_ONLY` — there is no approved production probability/price/settlement
  contract yet. Good-looking outcomes cannot bypass this state.
- `PROVISIONAL` — a product/model contract exists, but one or more objective
  production-readiness gates are still open.
- `REVIEWABLE` — all objective gates required for a new scope are satisfied. An
  explicit approval is still required.
- `OPERATIONAL` — the scope is explicitly recorded as an approved operational
  product scope and its current technical/live gates are healthy.
- `BLOCKED` — a previously approved operational scope has regressed on a critical
  technical/live gate and therefore fails closed.

`REVIEWABLE` never auto-promotes to `OPERATIONAL`.

## Objective gates

The framework evaluates, as applicable:

1. production model-probability contract;
2. current live model-probability availability;
3. complete stable `product_match_id` coverage;
4. bookmaker-price contract;
5. current live bookmaker-price availability;
6. deterministic settlement contract;
7. immutable lifecycle contract;
8. empirical reliability evidence for a new scope.

Coverage ratios are also reported. v1 deliberately does **not** invent a market-
level pass threshold such as 80% or 90%. Zero availability of a required live
function is a blocker; partial coverage is surfaced as `coverage_warnings` and
must be improved operationally without pretending an arbitrary percentage is a
scientific gate.

A new operational scope must satisfy all applicable objective gates and then
receive a separate explicit approval.

## Existing EPL / 1X2 baseline

`EPL × 1X2` is registered as the pre-existing operational product baseline.
This preserves the already-live product contract that existed before this
framework.

This exception means only that existing delivery may remain operational while
its new Product Reliability sample accumulates. It does **not** mean:

- reliability PASS;
- model promotion;
- automatic approval for another league;
- automatic promotion of another model artifact;
- betting readiness.

Model promotion remains its own explicit/manual process. If EPL/1X2 loses a
critical live function entirely — for example model probabilities or bookmaker
prices disappear for the whole exposed window — or stable identity regresses,
the framework returns `BLOCKED`.

## Reliability relationship

For any **new** league/market scope, empirical reliability must be attached and
`evidence_gate.reviewable=true` before the scope can reach `REVIEWABLE`.

The Reliability v1 meaning remains unchanged:

`REVIEWABLE != reliable != PASS != promotion`

The production-readiness framework consumes that evidence-readiness state; it
does not reinterpret `INCONCLUSIVE` as PASS.

## Market policy in v1

### 1X2

- model probability contract: yes;
- bookmaker price contract: yes;
- settlement contract: yes;
- lifecycle contract: yes;
- new scope requires empirical reliability review;
- EPL/1X2 is the only recorded pre-existing operational scope in v1.

### Goal total

- model probability contract: yes;
- bookmaker price contract: not yet production-ready;
- settlement contract: not yet product-ready;
- lifecycle contract: not yet product-ready;
- therefore remains `PROVISIONAL` even if model probabilities are present.

### Handicap

`RESEARCH_ONLY` until a validated probability model, priced line contract and
push/half-win/half-loss settlement semantics exist.

### Corner total

`RESEARCH_ONLY`. CORNERS10 as a football signal for 1X2 is not a production
corner-total model or a bookmaker corner-line proof.

## Outcome / no-peek safety

`build_production_readiness_view()` uses only the current product-market view and
optional externally supplied reliability summaries.

It does not query research outcome tables and does not open any frozen research
gate. This is important while `ALL_LEAGUES_MARKET_ONLY_V1_1` remains in
`collect, don't peek / SAMPLE_CLOSED` mode.

## Automatic effects explicitly forbidden

Production Readiness v1 never automatically:

- changes `MARKET_READINESS`;
- changes Product Decision `decision_tier`;
- changes forecast ranking;
- promotes a model;
- promotes a market;
- creates a betting recommendation;
- changes stake or portfolio exposure.

Those are separate contracts/decisions.

## Product API

The main `product-market-view.v1` response now includes:

- `production_readiness_version`;
- `production_readiness`.

The deployment-safe FastAPI app also exposes:

`GET /production-readiness-view`

The endpoint is read-only and derives readiness from the same durable public
product feed. It does not require lifecycle/service-role access and therefore
does not expose private outcome evidence.
