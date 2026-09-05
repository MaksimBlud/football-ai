"""Canonical market-backed Multi-Market Card V1 normalization.

No model probabilities are invented here. Every displayed probability is derived from
paired bookmaker decimal prices with the overround removed.
"""
from __future__ import annotations

from collections import defaultdict
from statistics import median
from typing import Iterable


def no_vig_pair(price_a: float, price_b: float) -> tuple[float, float]:
    if price_a <= 1.0 or price_b <= 1.0:
        raise ValueError("decimal prices must be > 1")
    ia, ib = 1.0 / float(price_a), 1.0 / float(price_b)
    total = ia + ib
    return ia / total, ib / total


def _median_price(values: Iterable[float]) -> float:
    vals = [float(v) for v in values if v is not None and float(v) > 1.0]
    if not vals:
        raise ValueError("no valid prices")
    return float(median(vals))


def _markets(event: dict, key: str):
    for book in event.get("bookmakers", []):
        for market in book.get("markets", []):
            if market.get("key") == key:
                yield book, market


def _select_balanced(rows: list[dict]) -> dict | None:
    if not rows:
        return None
    return min(rows, key=lambda x: (abs(float(x["prob_a"]) - 0.5), abs(float(x.get("point", 0.0)))))


def _two_way_totals(event: dict, key: str, *, preferred_point: float | None = None) -> dict | None:
    prices: dict[float, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    books: dict[float, set[str]] = defaultdict(set)
    for book, market in _markets(event, key):
        by_point: dict[float, dict[str, float]] = defaultdict(dict)
        for outcome in market.get("outcomes", []):
            point = outcome.get("point")
            name = str(outcome.get("name") or "")
            price = outcome.get("price")
            if point is None or name not in {"Over", "Under"} or price is None:
                continue
            by_point[float(point)][name] = float(price)
        for point, sides in by_point.items():
            if {"Over", "Under"} <= set(sides):
                prices[point]["Over"].append(sides["Over"])
                prices[point]["Under"].append(sides["Under"])
                books[point].add(str(book.get("key") or book.get("title") or "unknown"))
    rows = []
    for point, sides in prices.items():
        try:
            over_price = _median_price(sides["Over"])
            under_price = _median_price(sides["Under"])
            over_prob, under_prob = no_vig_pair(over_price, under_price)
        except ValueError:
            continue
        rows.append({
            "point": point,
            "over_probability": over_prob,
            "under_probability": under_prob,
            "over_price_median": over_price,
            "under_price_median": under_price,
            "bookmakers": len(books[point]),
            "prob_a": over_prob,
        })
    if not rows:
        return None
    if preferred_point is not None:
        exact = [row for row in rows if abs(row["point"] - preferred_point) < 1e-9]
        selected = exact[0] if exact else _select_balanced(rows)
    else:
        selected = _select_balanced(rows)
    selected = dict(selected)
    selected.pop("prob_a", None)
    return selected


def _team_totals(event: dict, key: str, home_team: str, away_team: str) -> dict:
    result = {}
    for team in (home_team, away_team):
        prices: dict[float, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
        books: dict[float, set[str]] = defaultdict(set)
        for book, market in _markets(event, key):
            by_point: dict[float, dict[str, float]] = defaultdict(dict)
            for outcome in market.get("outcomes", []):
                if str(outcome.get("name") or "") != team:
                    continue
                point = outcome.get("point")
                price = outcome.get("price")
                description = str(outcome.get("description") or "")
                if point is None or price is None or description not in {"Over", "Under"}:
                    continue
                by_point[float(point)][description] = float(price)
            for point, sides in by_point.items():
                if {"Over", "Under"} <= set(sides):
                    prices[point]["Over"].append(sides["Over"])
                    prices[point]["Under"].append(sides["Under"])
                    books[point].add(str(book.get("key") or book.get("title") or "unknown"))
        rows = []
        for point, sides in prices.items():
            try:
                op = _median_price(sides["Over"])
                up = _median_price(sides["Under"])
                oprob, uprob = no_vig_pair(op, up)
            except ValueError:
                continue
            rows.append({"point": point, "over_probability": oprob, "under_probability": uprob,
                         "over_price_median": op, "under_price_median": up,
                         "bookmakers": len(books[point]), "prob_a": oprob})
        selected = _select_balanced(rows)
        if selected:
            selected = dict(selected); selected.pop("prob_a", None)
        result["home" if team == home_team else "away"] = selected
    return result


def _spreads(event: dict, key: str, home_team: str, away_team: str) -> dict | None:
    grouped: dict[float, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    books: dict[float, set[str]] = defaultdict(set)
    for book, market in _markets(event, key):
        home_outcomes = [o for o in market.get("outcomes", []) if str(o.get("name")) == home_team]
        away_outcomes = [o for o in market.get("outcomes", []) if str(o.get("name")) == away_team]
        for h in home_outcomes:
            if h.get("point") is None or h.get("price") is None:
                continue
            hp = float(h["point"])
            matching = [a for a in away_outcomes if a.get("point") is not None and abs(float(a["point"]) + hp) < 1e-9]
            if not matching:
                continue
            a = matching[0]
            if a.get("price") is None:
                continue
            grouped[hp]["home"].append(float(h["price"]))
            grouped[hp]["away"].append(float(a["price"]))
            books[hp].add(str(book.get("key") or book.get("title") or "unknown"))
    rows = []
    for hp, sides in grouped.items():
        try:
            hprice = _median_price(sides["home"]); aprice = _median_price(sides["away"])
            hprob, aprob = no_vig_pair(hprice, aprice)
        except ValueError:
            continue
        rows.append({"home_handicap": hp, "away_handicap": -hp, "home_probability": hprob,
                     "away_probability": aprob, "home_price_median": hprice,
                     "away_price_median": aprice, "bookmakers": len(books[hp]),
                     "point": hp, "prob_a": hprob})
    selected = _select_balanced(rows)
    if selected:
        selected = dict(selected); selected.pop("prob_a", None); selected.pop("point", None)
    return selected


def build_multi_market_card(event: dict) -> dict:
    home = str(event.get("home_team") or "")
    away = str(event.get("away_team") or "")
    return {
        "schema_version": "MULTI_MARKET_V1",
        "research_only": True,
        "handicap": _spreads(event, "alternate_spreads", home, away) or _spreads(event, "spreads", home, away),
        "total_goals": _two_way_totals(event, "alternate_totals", preferred_point=2.5) or _two_way_totals(event, "totals", preferred_point=2.5),
        "total_corners": _two_way_totals(event, "alternate_totals_corners"),
        "team_corners": _team_totals(event, "alternate_team_totals_corners", home, away),
    }
