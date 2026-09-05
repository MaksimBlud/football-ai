"""Canonical market-backed Multi-Market Card V1 normalization."""
from __future__ import annotations
from collections import defaultdict
from statistics import median


def no_vig_pair(a: float, b: float) -> tuple[float, float]:
    if float(a) <= 1 or float(b) <= 1:
        raise ValueError("decimal prices must be > 1")
    ia, ib = 1 / float(a), 1 / float(b)
    return ia / (ia + ib), ib / (ia + ib)


def _med(values):
    vals = [float(v) for v in values if v is not None and float(v) > 1]
    if not vals:
        raise ValueError("no valid prices")
    return float(median(vals))


def _markets(event, key):
    for book in event.get("bookmakers", []):
        for market in book.get("markets", []):
            if market.get("key") == key:
                yield book, market


def _balanced(rows):
    return min(rows, key=lambda r: (abs(float(r["_p"]) - .5), abs(float(r.get("point", 0))))) if rows else None


def _totals(event, key, preferred=None):
    values, books = defaultdict(lambda: defaultdict(list)), defaultdict(set)
    for book, market in _markets(event, key):
        local = defaultdict(dict)
        for o in market.get("outcomes", []):
            if o.get("point") is None or o.get("price") is None or o.get("name") not in {"Over", "Under"}:
                continue
            local[float(o["point"])][o["name"]] = float(o["price"])
        for point, sides in local.items():
            if {"Over", "Under"} <= set(sides):
                for side in ("Over", "Under"):
                    values[point][side].append(sides[side])
                books[point].add(str(book.get("key") or book.get("title") or "unknown"))
    rows = []
    for point, sides in values.items():
        try:
            op, up = _med(sides["Over"]), _med(sides["Under"]); po, pu = no_vig_pair(op, up)
        except ValueError:
            continue
        rows.append({"point": point, "over_probability": po, "under_probability": pu,
                     "over_price_median": op, "under_price_median": up,
                     "bookmakers": len(books[point]), "_p": po})
    chosen = next((r for r in rows if preferred is not None and abs(r["point"] - preferred) < 1e-9), None) or _balanced(rows)
    if chosen:
        chosen = dict(chosen); chosen.pop("_p", None)
    return chosen


def _team_totals(event, key, home, away):
    # Live provider contract: outcome.name is Over/Under and outcome.description is team.
    out = {}
    for team, label in ((home, "home"), (away, "away")):
        values, books = defaultdict(lambda: defaultdict(list)), defaultdict(set)
        for book, market in _markets(event, key):
            local = defaultdict(dict)
            for o in market.get("outcomes", []):
                side = str(o.get("name") or "")
                description = str(o.get("description") or "")
                if description != team or side not in {"Over", "Under"} or o.get("point") is None or o.get("price") is None:
                    continue
                local[float(o["point"])][side] = float(o["price"])
            for point, sides in local.items():
                if {"Over", "Under"} <= set(sides):
                    for side in ("Over", "Under"):
                        values[point][side].append(sides[side])
                    books[point].add(str(book.get("key") or book.get("title") or "unknown"))
        rows = []
        for point, sides in values.items():
            try:
                op, up = _med(sides["Over"]), _med(sides["Under"]); po, pu = no_vig_pair(op, up)
            except ValueError:
                continue
            rows.append({"point": point, "over_probability": po, "under_probability": pu,
                         "over_price_median": op, "under_price_median": up,
                         "bookmakers": len(books[point]), "_p": po})
        chosen = _balanced(rows)
        if chosen:
            chosen = dict(chosen); chosen.pop("_p", None)
        out[label] = chosen
    return out


def _spreads(event, key, home, away):
    values, books = defaultdict(lambda: defaultdict(list)), defaultdict(set)
    for book, market in _markets(event, key):
        hs = [o for o in market.get("outcomes", []) if str(o.get("name")) == home]
        aws = [o for o in market.get("outcomes", []) if str(o.get("name")) == away]
        for h in hs:
            if h.get("point") is None or h.get("price") is None:
                continue
            hp = float(h["point"])
            matches = [a for a in aws if a.get("point") is not None and abs(float(a["point"]) + hp) < 1e-9 and a.get("price") is not None]
            if matches:
                values[hp]["home"].append(float(h["price"])); values[hp]["away"].append(float(matches[0]["price"]))
                books[hp].add(str(book.get("key") or book.get("title") or "unknown"))
    rows = []
    for hp, sides in values.items():
        try:
            hprice, aprice = _med(sides["home"]), _med(sides["away"]); ph, pa = no_vig_pair(hprice, aprice)
        except ValueError:
            continue
        rows.append({"home_handicap": hp, "away_handicap": -hp, "home_probability": ph, "away_probability": pa,
                     "home_price_median": hprice, "away_price_median": aprice, "bookmakers": len(books[hp]), "point": hp, "_p": ph})
    chosen = _balanced(rows)
    if chosen:
        chosen = dict(chosen); chosen.pop("_p", None); chosen.pop("point", None)
    return chosen


def build_multi_market_card(event: dict) -> dict:
    home, away = str(event.get("home_team") or ""), str(event.get("away_team") or "")
    return {
        "schema_version": "MULTI_MARKET_V1", "research_only": True,
        "handicap": _spreads(event, "alternate_spreads", home, away) or _spreads(event, "spreads", home, away),
        "total_goals": _totals(event, "alternate_totals", 2.5) or _totals(event, "totals", 2.5),
        "total_corners": _totals(event, "alternate_totals_corners"),
        "team_corners": _team_totals(event, "alternate_team_totals_corners", home, away),
    }
