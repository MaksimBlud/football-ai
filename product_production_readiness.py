"""Product Production-Readiness Framework v1.

This module standardizes when a league/market scope is research-only,
provisional, reviewable, operational, or blocked. It is a governance/readiness
layer only: it never changes model probabilities, Product Decision tiers,
research gates, model promotion state, betting decisions, or stakes.

A new scope can become REVIEWABLE automatically when all objective gates are
satisfied, but OPERATIONAL always requires an explicit approved scope. Existing
EPL/1X2 is recorded as the pre-existing operational product baseline; this does
not claim empirical reliability and does not waive reliability evidence for new
scopes.
"""

from __future__ import annotations

from typing import Any, Mapping


PRODUCTION_READINESS_VERSION = "product-production-readiness.v1"

STATUS_RESEARCH_ONLY = "RESEARCH_ONLY"
STATUS_PROVISIONAL = "PROVISIONAL"
STATUS_REVIEWABLE = "REVIEWABLE"
STATUS_OPERATIONAL = "OPERATIONAL"
STATUS_BLOCKED = "BLOCKED"

RELIABILITY_REVIEWABLE = "REVIEWABLE"
RELIABILITY_NOT_ATTACHED = "NOT_ATTACHED"


MARKET_PRODUCTION_POLICY: dict[str, dict[str, Any]] = {
    "1x2": {
        "label": "Исход матча",
        "baseline_stage": STATUS_PROVISIONAL,
        "required_selection_count": 3,
        "model_probability_contract": True,
        "bookmaker_price_contract": True,
        "settlement_contract": True,
        "lifecycle_contract": True,
        "requires_bookmaker_prices_for_operational": True,
        "requires_reliability_review_for_new_scope": True,
        "note": (
            "1X2 имеет полный product contract. Новые league/model scopes всё равно "
            "должны пройти empirical reliability review и explicit approval."
        ),
    },
    "total_goals": {
        "label": "Тотал голов",
        "baseline_stage": STATUS_PROVISIONAL,
        "required_selection_count": 2,
        "model_probability_contract": True,
        "bookmaker_price_contract": False,
        "settlement_contract": False,
        "lifecycle_contract": False,
        "requires_bookmaker_prices_for_operational": True,
        "requires_reliability_review_for_new_scope": True,
        "note": (
            "Model probability contract существует, но production price, settlement "
            "и lifecycle contracts для тотала ещё не закрыты."
        ),
    },
    "handicap": {
        "label": "Фора",
        "baseline_stage": STATUS_RESEARCH_ONLY,
        "required_selection_count": 0,
        "model_probability_contract": False,
        "bookmaker_price_contract": False,
        "settlement_contract": False,
        "lifecycle_contract": False,
        "requires_bookmaker_prices_for_operational": True,
        "requires_reliability_review_for_new_scope": True,
        "note": (
            "Нет утверждённого production probability/settlement contract, включая "
            "push/half-win/half-loss semantics."
        ),
    },
    "corners_total": {
        "label": "Тотал угловых",
        "baseline_stage": STATUS_RESEARCH_ONLY,
        "required_selection_count": 0,
        "model_probability_contract": False,
        "bookmaker_price_contract": False,
        "settlement_contract": False,
        "lifecycle_contract": False,
        "requires_bookmaker_prices_for_operational": True,
        "requires_reliability_review_for_new_scope": True,
        "note": (
            "CORNERS10 как 1X2 signal не является production corner-total model. "
            "Нужны отдельные probability, bookmaker-line и settlement contracts."
        ),
    },
}


# Explicit governance registry. Entries here are not generated from performance.
# EPL/1X2 is the already-existing operational product baseline created before this
# framework. Retaining it does not imply a reliability PASS.
APPROVED_OPERATIONAL_SCOPES: dict[tuple[str, str], dict[str, str]] = {
    ("EPL", "1x2"): {
        "basis": "preexisting_operational_product_baseline",
        "note": (
            "Existing EPL/1X2 operational product contract is retained. Empirical "
            "reliability remains separately reported and is required for new scopes."
        ),
    }
}


def _text(value: Any) -> str:
    return str(value or "").strip()


def _market_observation(
    matches: list[Mapping[str, Any]],
    *,
    league: str,
    market: str,
) -> dict[str, Any]:
    policy = MARKET_PRODUCTION_POLICY[market]
    league_matches = [
        match
        for match in matches
        if _text((match.get("match") or {}).get("league")) == league
    ]
    fixture_count = len(league_matches)
    required_selection_count = int(policy["required_selection_count"])

    stable_identity_count = 0
    complete_model_probability_count = 0
    complete_bookmaker_price_count = 0

    for match in league_matches:
        metadata = match.get("match") or {}
        if _text(metadata.get("product_match_id")):
            stable_identity_count += 1

        market_payload = (match.get("markets") or {}).get(market) or {}
        selections = list(market_payload.get("selections") or [])

        if required_selection_count > 0 and len(selections) >= required_selection_count:
            required = selections[:required_selection_count]
            if all(selection.get("probability") is not None for selection in required):
                complete_model_probability_count += 1
            if all(selection.get("bookmaker_odds") is not None for selection in required):
                complete_bookmaker_price_count += 1

    return {
        "fixture_count": fixture_count,
        "stable_identity_count": stable_identity_count,
        "complete_model_probability_count": complete_model_probability_count,
        "complete_bookmaker_price_count": complete_bookmaker_price_count,
        "stable_identity_complete": fixture_count > 0 and stable_identity_count == fixture_count,
        "model_probability_complete": (
            fixture_count > 0 and complete_model_probability_count == fixture_count
        ),
        "bookmaker_price_complete": (
            fixture_count > 0 and complete_bookmaker_price_count == fixture_count
        ),
    }


def _reliability_state(
    reliability_by_scope: Mapping[str, Any] | None,
    *,
    league: str,
    market: str,
) -> dict[str, Any]:
    if not reliability_by_scope:
        return {
            "attached": False,
            "state": RELIABILITY_NOT_ATTACHED,
            "reviewable": False,
            "verdict": None,
        }

    league_payload = reliability_by_scope.get(league) or {}
    payload = league_payload.get(market) if isinstance(league_payload, Mapping) else None
    if not isinstance(payload, Mapping):
        return {
            "attached": False,
            "state": RELIABILITY_NOT_ATTACHED,
            "reviewable": False,
            "verdict": None,
        }

    gate = payload.get("evidence_gate") or {}
    verdict = payload.get("reliability_verdict") or {}
    return {
        "attached": True,
        "state": _text(gate.get("state")) or "UNKNOWN",
        "reviewable": gate.get("reviewable") is True,
        "verdict": _text(verdict.get("status")) or None,
        "settled_predictions": payload.get("settled_predictions"),
    }


def _objective_gates(
    policy: Mapping[str, Any],
    observation: Mapping[str, Any],
    reliability: Mapping[str, Any],
    *,
    approved_scope: bool,
) -> dict[str, dict[str, Any]]:
    requires_prices = bool(policy.get("requires_bookmaker_prices_for_operational"))
    requires_reliability = bool(policy.get("requires_reliability_review_for_new_scope"))

    # Existing approved scope may retain operational delivery while empirical
    # reliability accumulates. This exception cannot promote any new scope.
    reliability_satisfied = (
        approved_scope
        or not requires_reliability
        or reliability.get("reviewable") is True
    )

    return {
        "product_contract": {
            "passed": bool(policy.get("model_probability_contract")),
            "reason": "Production model probability contract exists.",
        },
        "live_model_coverage": {
            "passed": observation.get("model_probability_complete") is True,
            "reason": "All currently exposed fixtures have complete model probabilities.",
        },
        "stable_identity": {
            "passed": observation.get("stable_identity_complete") is True,
            "reason": "All currently exposed fixtures have stable product_match_id.",
        },
        "bookmaker_price_contract": {
            "passed": bool(policy.get("bookmaker_price_contract")) or not requires_prices,
            "reason": "Bookmaker-price contract exists when operational comparison requires it.",
        },
        "live_price_coverage": {
            "passed": (
                observation.get("bookmaker_price_complete") is True
                if requires_prices
                else True
            ),
            "reason": "All currently exposed fixtures have complete required bookmaker prices.",
        },
        "settlement_contract": {
            "passed": bool(policy.get("settlement_contract")),
            "reason": "Deterministic product settlement contract exists.",
        },
        "lifecycle_contract": {
            "passed": bool(policy.get("lifecycle_contract")),
            "reason": "Immutable product lifecycle contract exists.",
        },
        "empirical_reliability": {
            "passed": reliability_satisfied,
            "reason": (
                "New scopes require a reviewable empirical reliability slice. Existing "
                "approved operational baseline may retain delivery while evidence accumulates."
            ),
        },
    }


def _blocking_gate_names(gates: Mapping[str, Mapping[str, Any]]) -> list[str]:
    return [name for name, payload in gates.items() if payload.get("passed") is not True]


def evaluate_scope_readiness(
    *,
    league: str,
    market: str,
    observation: Mapping[str, Any],
    reliability: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Evaluate one league/market scope without changing any production state."""
    if market not in MARKET_PRODUCTION_POLICY:
        raise ValueError(f"unsupported product market: {market}")

    league = _text(league)
    if not league:
        raise ValueError("league is required")

    policy = MARKET_PRODUCTION_POLICY[market]
    approval = APPROVED_OPERATIONAL_SCOPES.get((league, market))
    approved_scope = approval is not None
    reliability_payload = dict(reliability or {})
    gates = _objective_gates(
        policy,
        observation,
        reliability_payload,
        approved_scope=approved_scope,
    )
    blockers = _blocking_gate_names(gates)
    baseline_stage = policy["baseline_stage"]

    if baseline_stage == STATUS_RESEARCH_ONLY:
        status = STATUS_RESEARCH_ONLY
        reason = (
            "Market remains research-only by product policy; missing production "
            "probability/price/settlement contracts cannot be bypassed by raw results."
        )
    elif approved_scope:
        # An existing approved operational scope fails closed if a technical/live
        # gate other than empirical reliability regresses.
        critical_blockers = [name for name in blockers if name != "empirical_reliability"]
        if critical_blockers:
            status = STATUS_BLOCKED
            reason = (
                "Previously approved operational scope has a critical product gate "
                "failure and is blocked until the regression is fixed."
            )
        else:
            status = STATUS_OPERATIONAL
            reason = (
                "Existing explicitly recorded operational scope passes current "
                "technical/live gates. Empirical reliability remains a separate claim."
            )
    elif not blockers:
        status = STATUS_REVIEWABLE
        reason = (
            "All objective production-readiness gates are satisfied. Explicit approval "
            "is still required; REVIEWABLE never auto-promotes to OPERATIONAL."
        )
    else:
        status = STATUS_PROVISIONAL
        reason = "Product contract exists, but one or more production-readiness gates remain open."

    return {
        "framework_version": PRODUCTION_READINESS_VERSION,
        "league": league,
        "market": market,
        "market_label": policy["label"],
        "status": status,
        "reason": reason,
        "approved_operational_scope": approved_scope,
        "approval": dict(approval) if approval else None,
        "policy": dict(policy),
        "observation": dict(observation),
        "reliability": reliability_payload,
        "gates": {name: dict(payload) for name, payload in gates.items()},
        "open_gates": blockers,
        "automatic_effects": {
            "changes_market_readiness": False,
            "changes_decision_tier": False,
            "changes_forecast_ranking": False,
            "promotes_model": False,
            "promotes_market": False,
            "creates_bet_recommendation": False,
        },
    }


def build_production_readiness_view(
    product_market_view: Mapping[str, Any],
    *,
    reliability_by_scope: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build readiness for every market in every league present in product view."""
    matches = list(product_market_view.get("matches") or [])
    leagues = sorted(
        {
            _text((match.get("match") or {}).get("league"))
            for match in matches
            if _text((match.get("match") or {}).get("league"))
        }
    )

    scopes = []
    for league in leagues:
        for market in MARKET_PRODUCTION_POLICY:
            observation = _market_observation(matches, league=league, market=market)
            reliability = _reliability_state(
                reliability_by_scope,
                league=league,
                market=market,
            )
            scopes.append(
                evaluate_scope_readiness(
                    league=league,
                    market=market,
                    observation=observation,
                    reliability=reliability,
                )
            )

    counts: dict[str, int] = {
        STATUS_RESEARCH_ONLY: 0,
        STATUS_PROVISIONAL: 0,
        STATUS_REVIEWABLE: 0,
        STATUS_OPERATIONAL: 0,
        STATUS_BLOCKED: 0,
    }
    for scope in scopes:
        counts[scope["status"]] += 1

    return {
        "schema_version": PRODUCTION_READINESS_VERSION,
        "source_product_schema_version": product_market_view.get("schema_version"),
        "policy": {
            "new_scope_operational_requires_explicit_approval": True,
            "reviewable_auto_promotes_to_operational": False,
            "reliability_pass_is_not_model_promotion": True,
            "existing_operational_baseline_can_be_blocked_by_technical_regression": True,
            "reads_research_outcomes": False,
        },
        "status_counts": counts,
        "scopes": scopes,
    }
