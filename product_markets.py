"""Product-facing market contract for Football AI.

This module deliberately contains no data fetching and no model execution. It only
turns already-produced model probabilities plus optional bookmaker prices into a
single, explicit product representation.

Important: a positive raw EV is a mathematical comparison, not evidence of
validated profitability. Market readiness is therefore carried separately from
probability/price calculations and controls eligibility for the current main
choice.
"""

from __future__ import annotations

import math
from typing import Any, Mapping


MARKET_READINESS = {
    "1x2": {
        "status": "comparison_ready",
        "eligible_for_main_choice": True,
        "label": "Исход матча",
        "note": (
            "Вероятности модели можно сравнивать с доступной ценой БК. "
            "Положительный raw EV остаётся расчётным кандидатом, а не "
            "подтверждённой прибыльной ставкой."
        ),
    },
    "total_goals": {
        "status": "model_only",
        "eligible_for_main_choice": False,
        "label": "Тотал голов",
        "note": (
            "Вероятность и fair odds доступны, но текущий продуктовый поток "
            "ещё не содержит сопоставленную цену БК для линии тотала."
        ),
    },
    "handicap": {
        "status": "research_only",
        "eligible_for_main_choice": False,
        "label": "Фора",
        "note": (
            "Рынок остаётся research-only до отдельного проверенного расчёта "
            "вероятностей и корректной обработки push/half-win/half-loss."
        ),
    },
    "corners_total": {
        "status": "research_only",
        "eligible_for_main_choice": False,
        "label": "Тотал угловых",
        "note": (
            "Нужна отдельная модель распределения угловых и её prospective "
            "валидация. CORNERS10 для 1X2 не заменяет такую проверку."
        ),
    },
}


def _number(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(parsed):
        return None
    return parsed


def fair_odds(probability: Any) -> float | None:
    """Return model fair decimal odds for a simple no-push outcome."""
    probability_value = _number(probability)
    if probability_value is None or not 0 < probability_value <= 1:
        return None
    return 1.0 / probability_value


def raw_expected_value(probability: Any, bookmaker_odds: Any) -> float | None:
    """Return p * odds - 1 for a simple no-push outcome."""
    probability_value = _number(probability)
    odds_value = _number(bookmaker_odds)
    if (
        probability_value is None
        or odds_value is None
        or not 0 <= probability_value <= 1
        or odds_value <= 1
    ):
        return None
    return probability_value * odds_value - 1.0


def _selection(
    *,
    code: str,
    label: str,
    probability: Any,
    bookmaker_odds: Any = None,
) -> dict[str, Any]:
    probability_value = _number(probability)
    odds_value = _number(bookmaker_odds)
    return {
        "code": code,
        "label": label,
        "probability": probability_value,
        "fair_odds": fair_odds(probability_value),
        "bookmaker_odds": odds_value,
        "raw_expected_value": raw_expected_value(
            probability_value,
            odds_value,
        ),
    }


def _highest_probability(
    selections: list[dict[str, Any]],
) -> dict[str, Any] | None:
    available = [
        selection
        for selection in selections
        if selection["probability"] is not None
    ]
    if not available:
        return None
    return max(
        available,
        key=lambda selection: selection["probability"],
    )


def _best_priced_selection(
    selections: list[dict[str, Any]],
) -> dict[str, Any] | None:
    priced = [
        selection
        for selection in selections
        if selection["raw_expected_value"] is not None
    ]
    if not priced:
        return None
    return max(
        priced,
        key=lambda selection: selection["raw_expected_value"],
    )


def _readiness(market: str) -> dict[str, Any]:
    return dict(MARKET_READINESS[market])


def build_product_match(
    prediction: Mapping[str, Any],
    odds: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build one product row/card from model output and optional market prices."""
    odds = odds or {}

    home_team = str(prediction.get("home_team") or "").strip()
    away_team = str(prediction.get("away_team") or "").strip()

    one_x_two = [
        _selection(
            code="HOME",
            label=f"Победа {home_team}" if home_team else "П1",
            probability=prediction.get("home_probability"),
            bookmaker_odds=odds.get("home_odds"),
        ),
        _selection(
            code="DRAW",
            label="Ничья",
            probability=prediction.get("draw_probability"),
            bookmaker_odds=odds.get("draw_odds"),
        ),
        _selection(
            code="AWAY",
            label=f"Победа {away_team}" if away_team else "П2",
            probability=prediction.get("away_probability"),
            bookmaker_odds=odds.get("away_odds"),
        ),
    ]

    totals = [
        _selection(
            code="OVER_2_5",
            label="ТБ 2.5",
            probability=prediction.get("over_2_5_probability"),
        ),
        _selection(
            code="UNDER_2_5",
            label="ТМ 2.5",
            probability=prediction.get("under_2_5_probability"),
        ),
    ]

    best_1x2 = _best_priced_selection(one_x_two)
    current_main_choice = None
    if (
        best_1x2 is not None
        and best_1x2["raw_expected_value"] is not None
        and best_1x2["raw_expected_value"] > 0
        and MARKET_READINESS["1x2"]["eligible_for_main_choice"]
    ):
        current_main_choice = {
            "market": "1x2",
            "market_label": MARKET_READINESS["1x2"]["label"],
            "selection": dict(best_1x2),
            "status": "provisional_candidate",
            "reason": (
                "Максимальный положительный raw EV среди текущих "
                "comparison-ready рынков. Надёжность ещё не выражена "
                "отдельным количественным весом."
            ),
        }

    if current_main_choice is None:
        main_choice = {
            "status": "no_bet",
            "market": None,
            "market_label": None,
            "selection": None,
            "reason": (
                "Нет положительного raw EV среди рынков, которые сейчас "
                "допущены к продуктовому сравнению, либо отсутствует цена БК."
            ),
        }
    else:
        main_choice = current_main_choice

    return {
        "match": {
            "match_date": prediction.get("match_date"),
            "match_time": prediction.get("match_time"),
            "home_team": home_team,
            "away_team": away_team,
            "home_team_model": prediction.get("home_team_model"),
            "away_team_model": prediction.get("away_team_model"),
        },
        "main_choice": main_choice,
        "markets": {
            "1x2": {
                "readiness": _readiness("1x2"),
                "selections": one_x_two,
                "display_selection": (
                    dict(best_1x2)
                    if best_1x2 is not None
                    else _highest_probability(one_x_two)
                ),
            },
            "total_goals": {
                "readiness": _readiness("total_goals"),
                "line": 2.5,
                "selections": totals,
                "display_selection": _highest_probability(totals),
            },
            "handicap": {
                "readiness": _readiness("handicap"),
                "selections": [],
                "display_selection": None,
            },
            "corners_total": {
                "readiness": _readiness("corners_total"),
                "selections": [],
                "display_selection": None,
            },
        },
        "model_context": {
            "prediction": prediction.get("prediction"),
            "prediction_strength": prediction.get("prediction_strength"),
            "model_agreement": prediction.get("model_agreement"),
            "expected_home_goals": _number(
                prediction.get("expected_home_goals")
            ),
            "expected_away_goals": _number(
                prediction.get("expected_away_goals")
            ),
            "expected_total_goals": _number(
                prediction.get("expected_total_goals")
            ),
            "btts_yes_probability": _number(
                prediction.get("btts_yes_probability")
            ),
            "btts_no_probability": _number(
                prediction.get("btts_no_probability")
            ),
            "top_score": prediction.get("top_score"),
            "top_score_probability": _number(
                prediction.get("top_score_probability")
            ),
        },
    }


def build_product_market_view(
    predictions: list[Mapping[str, Any]],
    odds_by_pair: Mapping[tuple[str, str], Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build the versioned response consumed by list and match-detail UIs."""
    odds_by_pair = odds_by_pair or {}
    matches = []

    for prediction in predictions:
        pair = (
            str(
                prediction.get("home_team_model")
                or prediction.get("home_team")
                or ""
            ).strip(),
            str(
                prediction.get("away_team_model")
                or prediction.get("away_team")
                or ""
            ).strip(),
        )
        odds = odds_by_pair.get(pair)
        matches.append(build_product_match(prediction, odds))

    return {
        "schema_version": "product-market-view.v1",
        "selection_policy": {
            "current": (
                "Highest positive raw EV among comparison-ready markets only."
            ),
            "future": (
                "Replace raw-EV ordering with evidence/reliability-aware "
                "ranking once each market has passed its research gate."
            ),
        },
        "market_readiness": {
            key: dict(value)
            for key, value in MARKET_READINESS.items()
        },
        "matches": matches,
    }
