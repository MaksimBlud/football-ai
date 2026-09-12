"""Product Decision Framework v1 for Football AI.

This module turns already-built market outputs into a product decision. It does
not train models, alter probabilities, or promote research results.

Core invariants:
- evidence/readiness tier is considered before raw model probability across markets;
- value/raw EV is independent and can never override the forecast;
- alternatives come from other forecast-eligible markets, not mutually exclusive
  outcomes from the same market;
- confidence is a product-readiness state, not a claim of empirical calibration;
- v1 never emits a betting recommendation. Positive raw EV alone is insufficient.
"""

from __future__ import annotations

from typing import Any, Mapping


DECISION_FRAMEWORK_VERSION = "product-decision.v1"
MAX_ALTERNATIVES = 3

CONFIDENCE_LABELS = {
    "operational": "Операционный",
    "provisional": "Предварительный",
    "unavailable": "Недоступен",
}


def _candidate(
    market: str,
    market_payload: Mapping[str, Any],
) -> dict[str, Any] | None:
    readiness = dict(market_payload.get("readiness") or {})
    selection = market_payload.get("display_selection")
    if not readiness.get("eligible_for_main_forecast"):
        return None
    if not selection or selection.get("probability") is None:
        return None

    return {
        "market": market,
        "market_label": readiness.get("label") or market,
        "decision_tier": int(readiness.get("decision_tier") or 0),
        "confidence_level": readiness.get("decision_confidence") or "unavailable",
        "selection": dict(selection),
    }


def _candidate_rank(candidate: Mapping[str, Any]) -> tuple[int, float, str]:
    probability = candidate["selection"].get("probability")
    probability_value = float(probability) if probability is not None else -1.0
    # Deterministic final key keeps behavior stable when tier/probability tie.
    return (
        int(candidate.get("decision_tier") or 0),
        probability_value,
        str(candidate.get("market") or ""),
    )


def _forecast_from_candidate(candidate: Mapping[str, Any] | None) -> dict[str, Any]:
    if candidate is None:
        return {
            "status": "unavailable",
            "market": None,
            "market_label": None,
            "decision_tier": None,
            "selection": None,
            "reason": "Нет рынка, прошедшего product decision gate с доступной вероятностью.",
        }

    return {
        "status": "model_forecast",
        "market": candidate["market"],
        "market_label": candidate["market_label"],
        "decision_tier": candidate["decision_tier"],
        "selection": dict(candidate["selection"]),
        "reason": (
            "Сначала применяется product decision tier рынка, затем максимальная "
            "вероятность модели внутри доступных кандидатов того же уровня. "
            "Value/EV на выбор не влияет."
        ),
    }


def _alternatives(
    ranked_candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    alternatives = []
    for candidate in ranked_candidates[1 : MAX_ALTERNATIVES + 1]:
        alternatives.append(
            {
                "status": "alternative_forecast",
                "market": candidate["market"],
                "market_label": candidate["market_label"],
                "decision_tier": candidate["decision_tier"],
                "confidence_level": candidate["confidence_level"],
                "selection": dict(candidate["selection"]),
                "reason": (
                    "Альтернативный прогноз из другого forecast-eligible рынка. "
                    "Он не является hedge и не заменяет главный прогноз."
                ),
            }
        )
    return alternatives


def _value_signal(markets: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    candidates = []
    for market, payload in markets.items():
        readiness = payload.get("readiness") or {}
        if not readiness.get("eligible_for_value"):
            continue
        for selection in payload.get("selections") or []:
            raw_ev = selection.get("raw_expected_value")
            if raw_ev is None or raw_ev <= 0:
                continue
            candidates.append(
                {
                    "market": market,
                    "market_label": readiness.get("label") or market,
                    "selection": dict(selection),
                }
            )

    if not candidates:
        return {
            "status": "none",
            "market": None,
            "market_label": None,
            "selection": None,
            "reason": (
                "Нет положительного raw EV среди рынков, допущенных к value comparison."
            ),
        }

    best = max(
        candidates,
        key=lambda item: float(item["selection"]["raw_expected_value"]),
    )
    return {
        "status": "positive_raw_ev",
        "market": best["market"],
        "market_label": best["market_label"],
        "selection": dict(best["selection"]),
        "reason": (
            "Дополнительный value-сигнал по максимальному положительному raw EV "
            "среди value-eligible рынков. Он не меняет прогноз и сам по себе не "
            "является доказательством прибыльности."
        ),
    }


def _confidence(main_candidate: Mapping[str, Any] | None) -> dict[str, Any]:
    if main_candidate is None:
        return {
            "status": "unavailable",
            "level": "unavailable",
            "label": CONFIDENCE_LABELS["unavailable"],
            "market": None,
            "model_probability": None,
            "reason": "Нет главного прогнозного кандидата.",
            "is_empirical_calibration_claim": False,
        }

    level = str(main_candidate.get("confidence_level") or "unavailable")
    if level not in CONFIDENCE_LABELS:
        level = "unavailable"
    return {
        "status": "available",
        "level": level,
        "label": CONFIDENCE_LABELS[level],
        "market": main_candidate["market"],
        "model_probability": main_candidate["selection"].get("probability"),
        "reason": (
            "Уровень отражает зрелость product/research gate рынка, а не "
            "статистический confidence interval и не обещание точности."
        ),
        "is_empirical_calibration_claim": False,
    }


def _bet_decision(
    markets: Mapping[str, Mapping[str, Any]],
    main_candidate: Mapping[str, Any] | None,
) -> dict[str, Any]:
    explicitly_eligible = [
        market
        for market, payload in markets.items()
        if (payload.get("readiness") or {}).get("eligible_for_bet_recommendation")
    ]

    if main_candidate is None:
        reason = "Нет главного прогнозного кандидата; ставка не формируется."
    elif not explicitly_eligible:
        reason = (
            "Ни один рынок ещё не прошёл отдельный bet-recommendation gate. "
            "Высокая вероятность или положительный raw EV сами по себе этот gate "
            "не заменяют."
        )
    else:
        # Product Decision Framework v1 deliberately has no staking/recommendation
        # engine. A later version must define and validate that policy explicitly.
        reason = (
            "Даже при наличии bet-eligible рынка Framework v1 не формирует ставку: "
            "нужен отдельный утверждённый recommendation/staking policy."
        )

    return {
        "status": "no_bet",
        "selection": None,
        "reason": reason,
        "framework_version": DECISION_FRAMEWORK_VERSION,
    }


def build_product_decision(
    markets: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Build the complete Product Decision Framework v1 decision payload."""
    candidates = []
    for market, payload in markets.items():
        candidate = _candidate(market, payload)
        if candidate is not None:
            candidates.append(candidate)

    ranked = sorted(candidates, key=_candidate_rank, reverse=True)
    main_candidate = ranked[0] if ranked else None

    return {
        "framework_version": DECISION_FRAMEWORK_VERSION,
        "main_forecast": _forecast_from_candidate(main_candidate),
        "alternatives": _alternatives(ranked),
        "value_signal": _value_signal(markets),
        "confidence": _confidence(main_candidate),
        "bet_decision": _bet_decision(markets, main_candidate),
        "policy": {
            "forecast_order": "decision_tier_then_model_probability",
            "value_is_independent": True,
            "alternatives_are_cross_market": True,
            "confidence_is_empirical_calibration_claim": False,
            "positive_ev_implies_bet": False,
        },
    }
