"""Product-facing market contract for Football AI.

The product has two independent concepts:

* main forecast: the eligible selection with the highest model probability;
* value signal: a separate price comparison based on raw EV.

A value signal must never replace the model forecast. Positive raw EV is only a
mathematical comparison with bookmaker price, not evidence of profitability.
"""

from __future__ import annotations

import hashlib
import math
from typing import Any, Mapping


MARKET_READINESS = {
    "1x2": {
        "status": "comparison_ready",
        "eligible_for_main_forecast": True,
        "eligible_for_value": True,
        "label": "Исход матча",
        "note": (
            "Главный прогноз определяется вероятностью модели. Bookmaker price "
            "и raw EV отображаются отдельно как дополнительный value-сигнал."
        ),
    },
    "total_goals": {
        "status": "model_only",
        "eligible_for_main_forecast": True,
        "eligible_for_value": False,
        "label": "Тотал голов",
        "note": (
            "Вероятность и fair odds доступны для модельного прогноза, но "
            "сопоставленная цена БК для линии тотала пока не подключена."
        ),
    },
    "handicap": {
        "status": "research_only",
        "eligible_for_main_forecast": False,
        "eligible_for_value": False,
        "label": "Фора",
        "note": (
            "Рынок остаётся research-only до отдельного проверенного расчёта "
            "вероятностей и корректной обработки push/half-win/half-loss."
        ),
    },
    "corners_total": {
        "status": "research_only",
        "eligible_for_main_forecast": False,
        "eligible_for_value": False,
        "label": "Тотал угловых",
        "note": (
            "Нужна отдельная модель распределения угловых и её prospective "
            "валидация. CORNERS10 для 1X2 не заменяет такую проверку."
        ),
    },
}


def _number(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
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
        "raw_expected_value": raw_expected_value(probability_value, odds_value),
    }


def _highest_probability(
    selections: list[dict[str, Any]],
) -> dict[str, Any] | None:
    available = [s for s in selections if s["probability"] is not None]
    if not available:
        return None
    return max(available, key=lambda s: s["probability"])


def _best_priced_selection(
    selections: list[dict[str, Any]],
) -> dict[str, Any] | None:
    priced = [s for s in selections if s["raw_expected_value"] is not None]
    if not priced:
        return None
    return max(priced, key=lambda s: s["raw_expected_value"])


def _readiness(market: str) -> dict[str, Any]:
    return dict(MARKET_READINESS[market])


def fixture_key(row: Mapping[str, Any]) -> tuple[str, str, str, str]:
    """Return the legacy product fixture identity including kickoff fields."""
    return (
        str(row.get("home_team_model") or row.get("home_team") or "").strip(),
        str(row.get("away_team_model") or row.get("away_team") or "").strip(),
        str(row.get("match_date") or "").strip(),
        str(row.get("match_time") or "").strip(),
    )


def product_match_id(row: Mapping[str, Any]) -> str:
    """Return a stable URL-safe identity that survives list reordering.

    Provider ``event_id`` is preferred. A deterministic fixture hash is used only
    when the upstream provider id is unavailable.
    """
    event_id = str(row.get("event_id") or "").strip()
    if event_id:
        return f"event_{event_id}"

    kickoff = str(row.get("commence_time_utc") or "").strip()
    if not kickoff:
        kickoff = f"{row.get('match_date') or ''}T{row.get('match_time') or ''}"
    parts = (
        str(row.get("league") or "").strip(),
        str(row.get("home_team_model") or row.get("home_team") or "").strip(),
        str(row.get("away_team_model") or row.get("away_team") or "").strip(),
        kickoff,
    )
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]
    return f"fixture_{digest}"


def _build_main_forecast(
    market_selections: list[tuple[str, str, dict[str, Any] | None]],
) -> dict[str, Any]:
    eligible = []
    for market, market_label, selection in market_selections:
        if selection is None:
            continue
        if not MARKET_READINESS[market]["eligible_for_main_forecast"]:
            continue
        if selection.get("probability") is None:
            continue
        eligible.append((market, market_label, selection))

    if not eligible:
        return {
            "status": "unavailable",
            "market": None,
            "market_label": None,
            "selection": None,
            "reason": "Нет доступного проверенного модельного прогноза.",
        }

    market, market_label, selection = max(
        eligible,
        key=lambda item: item[2]["probability"],
    )
    return {
        "status": "model_forecast",
        "market": market,
        "market_label": market_label,
        "selection": dict(selection),
        "reason": (
            "Выбран исход с максимальной вероятностью модели среди рынков, "
            "допущенных к модельному прогнозу. Value/EV на выбор не влияет."
        ),
    }


def _build_value_signal(one_x_two: list[dict[str, Any]]) -> dict[str, Any]:
    if not MARKET_READINESS["1x2"]["eligible_for_value"]:
        return {
            "status": "unavailable",
            "market": None,
            "market_label": None,
            "selection": None,
            "reason": "Value comparison для этого рынка отключён.",
        }

    best = _best_priced_selection(one_x_two)
    if (
        best is None
        or best["raw_expected_value"] is None
        or best["raw_expected_value"] <= 0
    ):
        return {
            "status": "none",
            "market": "1x2",
            "market_label": MARKET_READINESS["1x2"]["label"],
            "selection": None,
            "reason": "Нет положительного raw EV среди доступных 1X2 цен.",
        }

    return {
        "status": "positive_raw_ev",
        "market": "1x2",
        "market_label": MARKET_READINESS["1x2"]["label"],
        "selection": dict(best),
        "reason": (
            "Дополнительный value-сигнал по максимальному положительному raw EV. "
            "Он не меняет главный прогноз модели."
        ),
    }


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

    best_1x2_forecast = _highest_probability(one_x_two)
    best_total_forecast = _highest_probability(totals)
    main_forecast = _build_main_forecast(
        [
            ("1x2", MARKET_READINESS["1x2"]["label"], best_1x2_forecast),
            (
                "total_goals",
                MARKET_READINESS["total_goals"]["label"],
                best_total_forecast,
            ),
        ]
    )
    value_signal = _build_value_signal(one_x_two)

    return {
        "match": {
            "product_match_id": product_match_id(prediction),
            "event_id": prediction.get("event_id"),
            "league": prediction.get("league"),
            "commence_time_utc": prediction.get("commence_time_utc"),
            "match_date": prediction.get("match_date"),
            "match_time": prediction.get("match_time"),
            "home_team": home_team,
            "away_team": away_team,
            "home_team_model": prediction.get("home_team_model"),
            "away_team_model": prediction.get("away_team_model"),
        },
        "main_forecast": main_forecast,
        "value_signal": value_signal,
        # Temporary compatibility alias. Semantics are now forecast-first, never EV-first.
        "main_choice": dict(main_forecast),
        "markets": {
            "1x2": {
                "readiness": _readiness("1x2"),
                "selections": one_x_two,
                "display_selection": best_1x2_forecast,
            },
            "total_goals": {
                "readiness": _readiness("total_goals"),
                "line": 2.5,
                "selections": totals,
                "display_selection": best_total_forecast,
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
            "expected_home_goals": _number(prediction.get("expected_home_goals")),
            "expected_away_goals": _number(prediction.get("expected_away_goals")),
            "expected_total_goals": _number(prediction.get("expected_total_goals")),
            "btts_yes_probability": _number(prediction.get("btts_yes_probability")),
            "btts_no_probability": _number(prediction.get("btts_no_probability")),
            "top_score": prediction.get("top_score"),
            "top_score_probability": _number(prediction.get("top_score_probability")),
        },
    }


def build_product_market_view(
    predictions: list[Mapping[str, Any]],
    odds_by_fixture: Mapping[tuple[str, str, str, str], Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build the versioned response consumed by list and match-detail UIs."""
    odds_by_fixture = odds_by_fixture or {}
    matches = []

    for prediction in predictions:
        odds = odds_by_fixture.get(fixture_key(prediction))
        matches.append(build_product_match(prediction, odds))

    return {
        "schema_version": "product-market-view.v1",
        "fixture_identity": "provider event_id; deterministic fixture hash fallback",
        "selection_policy": {
            "forecast": (
                "Highest model probability among markets eligible for main forecast."
            ),
            "value": (
                "Highest positive raw EV among priced value-eligible selections; "
                "informational only and never overrides forecast."
            ),
            "future": (
                "Use research readiness, calibration and reliability as eligibility "
                "and confidence controls without conflating forecast with value."
            ),
        },
        "market_readiness": {key: dict(value) for key, value in MARKET_READINESS.items()},
        "matches": matches,
    }
