"""Product Portfolio / Risk Layer v1 for Football AI.

The layer evaluates structural portfolio risk around product signals and future
bet decisions. It deliberately does not create a bet, choose a stake, allocate a
bankroll, use Kelly sizing, or infer covariance from model probabilities/raw EV.

Core v1 rules:
- forecasts and value signals are not positions;
- only an explicit future ``bet_decision.status == 'bet'`` can create an
  actionable position;
- exact duplicate actionable positions are blocked;
- multiple actionable positions on one fixture are blocked until an explicit
  within-fixture covariance/correlation model is validated;
- conflicting selections in one fixture/market are blocked;
- any unapproved stake/money field is blocked because v1 has no staking policy;
- league/team concentration is descriptive only, never a fabricated money cap.
"""

from __future__ import annotations

import hashlib
from collections import Counter, defaultdict
from typing import Any, Iterable, Mapping


PORTFOLIO_RISK_SCHEMA_VERSION = "product-portfolio-risk.v1"
MAX_ACTIONABLE_RISK_SLOTS_PER_FIXTURE = 1

STATUS_NO_ACTIONABLE_EXPOSURE = "NO_ACTIONABLE_EXPOSURE"
STATUS_BLOCKED = "BLOCKED_STRUCTURAL_RISK"
STATUS_UNSIZED = "UNSIZED_ACTIONABLE_PORTFOLIO"

VIOLATION_DUPLICATE = "EXACT_DUPLICATE_POSITION"
VIOLATION_SAME_FIXTURE = "MULTIPLE_ACTIONABLE_POSITIONS_SAME_FIXTURE"
VIOLATION_CONFLICTING_MARKET = "CONFLICTING_SELECTIONS_SAME_MARKET"
VIOLATION_UNAPPROVED_STAKE = "UNAPPROVED_STAKE_INPUT"
VIOLATION_UNSUPPORTED_BET_STATUS = "UNSUPPORTED_BET_DECISION_STATUS"
VIOLATION_MALFORMED_BET = "MALFORMED_BET_DECISION"

UNAPPROVED_STAKE_KEYS = {
    "stake",
    "stake_units",
    "stake_amount",
    "amount",
    "bankroll_fraction",
    "bankroll_pct",
    "kelly_fraction",
    "risk_units",
}


def _text(value: Any) -> str:
    return str(value or "").strip()


def _number(value: Any) -> float | None:
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed


def _stable_signal_id(parts: Iterable[Any]) -> str:
    raw = "|".join(_text(part) for part in parts)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]
    return f"signal_{digest}"


def _match_meta(item: Mapping[str, Any]) -> dict[str, Any]:
    match = dict(item.get("match") or {})
    product_match_id = _text(match.get("product_match_id"))
    if not product_match_id:
        raise ValueError("product_match_id is required for portfolio risk")
    return {
        "product_match_id": product_match_id,
        "event_id": _text(match.get("event_id")) or None,
        "league": _text(match.get("league")) or None,
        "commence_time_utc": _text(match.get("commence_time_utc")) or None,
        "home_team": _text(match.get("home_team")) or None,
        "away_team": _text(match.get("away_team")) or None,
    }


def _signal_from_selection(
    item: Mapping[str, Any],
    *,
    source_type: str,
    market: Any,
    selection: Mapping[str, Any],
    actionable: bool,
) -> dict[str, Any]:
    meta = _match_meta(item)
    market_text = _text(market)
    code = _text(selection.get("code")) or _text(selection.get("label"))
    if not market_text or not code:
        raise ValueError("portfolio signal requires market and selection identity")
    return {
        **meta,
        "signal_id": _stable_signal_id(
            (meta["product_match_id"], source_type, market_text, code)
        ),
        "source_type": source_type,
        "market": market_text,
        "selection_code": code,
        "selection_label": _text(selection.get("label")) or code,
        "probability": _number(selection.get("probability")),
        "fair_odds": _number(selection.get("fair_odds")),
        "bookmaker_odds": _number(selection.get("bookmaker_odds")),
        "raw_expected_value": _number(selection.get("raw_expected_value")),
        "actionable": bool(actionable),
    }


def build_signal_inventory(matches: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Collect product-visible forecast/value signals without turning them into bets."""
    signals: list[dict[str, Any]] = []
    for raw in matches:
        item = dict(raw)

        main = dict(item.get("main_forecast") or {})
        if main.get("status") == "model_forecast" and main.get("selection"):
            signals.append(
                _signal_from_selection(
                    item,
                    source_type="main_forecast",
                    market=main.get("market"),
                    selection=dict(main["selection"]),
                    actionable=False,
                )
            )

        for alternative in item.get("alternatives") or []:
            alternative = dict(alternative)
            if alternative.get("selection"):
                signals.append(
                    _signal_from_selection(
                        item,
                        source_type="alternative_forecast",
                        market=alternative.get("market"),
                        selection=dict(alternative["selection"]),
                        actionable=False,
                    )
                )

        value = dict(item.get("value_signal") or {})
        if value.get("status") == "positive_raw_ev" and value.get("selection"):
            signals.append(
                _signal_from_selection(
                    item,
                    source_type="value_signal",
                    market=value.get("market"),
                    selection=dict(value["selection"]),
                    actionable=False,
                )
            )
    return signals


def _has_unapproved_stake_fields(
    bet_decision: Mapping[str, Any], selection: Mapping[str, Any]
) -> list[str]:
    present = []
    for container in (bet_decision, selection):
        for key in UNAPPROVED_STAKE_KEYS:
            if key in container and container.get(key) is not None:
                present.append(key)
    return sorted(set(present))


def _extract_actionable_positions(
    matches: Iterable[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    positions: list[dict[str, Any]] = []
    violations: list[dict[str, Any]] = []

    for raw in matches:
        item = dict(raw)
        meta = _match_meta(item)
        bet = dict(item.get("bet_decision") or {})
        status = _text(bet.get("status")) or "no_bet"

        if status == "no_bet":
            continue
        if status != "bet":
            violations.append(
                {
                    "code": VIOLATION_UNSUPPORTED_BET_STATUS,
                    "product_match_id": meta["product_match_id"],
                    "detail": f"unsupported bet_decision status: {status}",
                }
            )
            continue

        selection_raw = bet.get("selection")
        market = _text(bet.get("market"))
        if not isinstance(selection_raw, Mapping) or not market:
            violations.append(
                {
                    "code": VIOLATION_MALFORMED_BET,
                    "product_match_id": meta["product_match_id"],
                    "detail": "bet decision requires explicit market and selection",
                }
            )
            continue

        selection = dict(selection_raw)
        stake_fields = _has_unapproved_stake_fields(bet, selection)
        if stake_fields:
            violations.append(
                {
                    "code": VIOLATION_UNAPPROVED_STAKE,
                    "product_match_id": meta["product_match_id"],
                    "detail": "staking policy is disabled in v1",
                    "fields": stake_fields,
                }
            )

        position = _signal_from_selection(
            item,
            source_type="bet_decision",
            market=market,
            selection=selection,
            actionable=True,
        )
        positions.append(position)

    return positions, violations


def _structural_violations(positions: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []

    exact_groups: dict[tuple[str, str, str], list[Mapping[str, Any]]] = defaultdict(list)
    fixture_groups: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    market_groups: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)

    for position in positions:
        fixture = _text(position.get("product_match_id"))
        market = _text(position.get("market"))
        selection = _text(position.get("selection_code"))
        exact_groups[(fixture, market, selection)].append(position)
        fixture_groups[fixture].append(position)
        market_groups[(fixture, market)].append(position)

    for (fixture, market, selection), group in sorted(exact_groups.items()):
        if len(group) > 1:
            violations.append(
                {
                    "code": VIOLATION_DUPLICATE,
                    "product_match_id": fixture,
                    "market": market,
                    "selection_code": selection,
                    "count": len(group),
                }
            )

    for fixture, group in sorted(fixture_groups.items()):
        unique_positions = {
            (_text(item.get("market")), _text(item.get("selection_code")))
            for item in group
        }
        if len(unique_positions) > MAX_ACTIONABLE_RISK_SLOTS_PER_FIXTURE:
            violations.append(
                {
                    "code": VIOLATION_SAME_FIXTURE,
                    "product_match_id": fixture,
                    "position_count": len(unique_positions),
                    "max_risk_slots": MAX_ACTIONABLE_RISK_SLOTS_PER_FIXTURE,
                    "reason": (
                        "Within-fixture covariance is not validated; multiple positions "
                        "must not be treated as independent exposure."
                    ),
                }
            )

    for (fixture, market), group in sorted(market_groups.items()):
        selections = sorted({_text(item.get("selection_code")) for item in group})
        if len(selections) > 1:
            violations.append(
                {
                    "code": VIOLATION_CONFLICTING_MARKET,
                    "product_match_id": fixture,
                    "market": market,
                    "selection_codes": selections,
                }
            )

    return violations


def _concentration(positions: list[Mapping[str, Any]]) -> dict[str, Any]:
    league_counts: Counter[str] = Counter()
    team_counts: Counter[str] = Counter()
    for position in positions:
        league = _text(position.get("league"))
        if league:
            league_counts[league] += 1
        for key in ("home_team", "away_team"):
            team = _text(position.get(key))
            if team:
                team_counts[team] += 1

    return {
        "basis": "actionable_position_count_not_money",
        "league_position_counts": dict(sorted(league_counts.items())),
        "team_position_counts": dict(sorted(team_counts.items())),
        "league_money_cap_defined": False,
        "team_money_cap_defined": False,
        "interpretation": (
            "Counts identify concentration for review only. Product Portfolio/Risk v1 "
            "has no validated bankroll or monetary exposure thresholds."
        ),
    }


def _fixture_signal_clusters(signals: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for signal in signals:
        groups[_text(signal.get("product_match_id"))].append(signal)

    clusters = []
    for fixture, group in sorted(groups.items()):
        if len(group) < 2:
            continue
        clusters.append(
            {
                "product_match_id": fixture,
                "signal_count": len(group),
                "markets": sorted({_text(item.get("market")) for item in group}),
                "source_types": sorted(
                    {_text(item.get("source_type")) for item in group}
                ),
                "correlation_status": "UNKNOWN_NOT_INDEPENDENT",
                "probability_or_ev_aggregation_allowed": False,
            }
        )
    return clusters


def build_portfolio_risk_view(product_market_view: Mapping[str, Any]) -> dict[str, Any]:
    """Build a structural portfolio-risk report from the product market view."""
    matches = [dict(item) for item in product_market_view.get("matches") or []]
    signals = build_signal_inventory(matches)
    positions, extraction_violations = _extract_actionable_positions(matches)
    violations = extraction_violations + _structural_violations(positions)

    if not positions and not violations:
        status = STATUS_NO_ACTIONABLE_EXPOSURE
    elif violations:
        status = STATUS_BLOCKED
    else:
        status = STATUS_UNSIZED

    unique_slots = sorted({_text(item.get("product_match_id")) for item in positions})
    return {
        "schema_version": PORTFOLIO_RISK_SCHEMA_VERSION,
        "source_schema_version": product_market_view.get("schema_version"),
        "status": status,
        "policy": {
            "forecast_is_position": False,
            "value_signal_is_position": False,
            "actionable_source": "explicit bet_decision.status == bet only",
            "max_actionable_risk_slots_per_fixture": MAX_ACTIONABLE_RISK_SLOTS_PER_FIXTURE,
            "same_fixture_covariance_model_available": False,
            "cross_fixture_covariance_model_available": False,
            "probability_aggregation_across_signals_allowed": False,
            "raw_ev_aggregation_across_signals_allowed": False,
            "stake_sizing_policy_defined": False,
            "bankroll_policy_defined": False,
            "kelly_sizing_enabled": False,
            "league_money_cap_defined": False,
            "team_money_cap_defined": False,
        },
        "signal_inventory": {
            "count": len(signals),
            "main_forecast_count": sum(
                1 for item in signals if item["source_type"] == "main_forecast"
            ),
            "alternative_forecast_count": sum(
                1
                for item in signals
                if item["source_type"] == "alternative_forecast"
            ),
            "value_signal_count": sum(
                1 for item in signals if item["source_type"] == "value_signal"
            ),
            "signals": signals,
            "same_fixture_signal_clusters": _fixture_signal_clusters(signals),
            "note": "Signal inventory is descriptive and is not a betting portfolio.",
        },
        "actionable_portfolio": {
            "position_count": len(positions),
            "risk_slot_count": len(unique_slots),
            "positions": positions,
            "violations": violations,
            "concentration": _concentration(positions),
        },
        "monetary_exposure": {
            "available": False,
            "total_stake": None,
            "bankroll_fraction": None,
            "portfolio_var": None,
            "reason": (
                "No validated staking/bankroll/covariance policy exists. Structural "
                "risk can be audited, but monetary exposure must not be fabricated."
            ),
        },
        "automatic_effects": {
            "creates_bet": False,
            "changes_main_forecast": False,
            "changes_value_signal": False,
            "changes_decision_tier": False,
            "changes_model_probability": False,
            "changes_model_promotion": False,
        },
    }
