"""Pure research-only Multi-Market V2 outcome classification.

No network, database, model, or production-artifact I/O occurs here.
The caller supplies a frozen pre-kickoff Multi-Market V1 card and explicit
finished match observations. Missing corner observations remain unsettled.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Any

WIN = "WIN"
LOSS = "LOSS"
PUSH = "PUSH"
HALF_WIN = "HALF_WIN"
HALF_LOSS = "HALF_LOSS"
UNSETTLED_MISSING_OUTCOME = "UNSETTLED_MISSING_OUTCOME"
NOT_OFFERED = "NOT_OFFERED"
INVALID = "INVALID"


@dataclass(frozen=True)
class Settlement:
    status: str
    score: float | None
    observed: float | None = None
    line: float | None = None
    side: str | None = None
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _line_parts(line: float) -> tuple[float, ...]:
    doubled = line * 2.0
    if math.isclose(doubled, round(doubled), abs_tol=1e-9):
        return (line,)
    quadrupled = line * 4.0
    if not math.isclose(quadrupled, round(quadrupled), abs_tol=1e-9):
        raise ValueError("line must use 0.25 increments")
    return (math.floor(doubled) / 2.0, math.ceil(doubled) / 2.0)


def _combined(values: list[float], observed: float, line: float, side: str) -> Settlement:
    score = round(sum(values) / len(values), 10)
    statuses = {1.0: WIN, 0.5: HALF_WIN, 0.0: PUSH, -0.5: HALF_LOSS, -1.0: LOSS}
    status = statuses.get(score)
    if status is None:
        return Settlement(INVALID, None, observed, line, side, "unexpected classification score")
    return Settlement(status, score, observed, line, side)


def settle_total(side: str, observed: Any, line: Any) -> Settlement:
    side = str(side or "").strip().upper()
    if side not in {"OVER", "UNDER"}:
        return Settlement(INVALID, None, side=side or None, reason="side must be OVER or UNDER")
    obs, ln = _number(observed), _number(line)
    if obs is None:
        return Settlement(UNSETTLED_MISSING_OUTCOME, None, side=side, reason="outcome is missing")
    if ln is None:
        return Settlement(INVALID, None, observed=obs, side=side, reason="line is invalid")
    try:
        parts = _line_parts(ln)
    except ValueError as exc:
        return Settlement(INVALID, None, obs, ln, side, str(exc))
    values = []
    for part in parts:
        diff = obs - part
        raw = 0.0 if math.isclose(diff, 0.0, abs_tol=1e-9) else 1.0 if diff > 0 else -1.0
        values.append(raw if side == "OVER" else -raw)
    return _combined(values, obs, ln, side)


def settle_handicap(side: str, home_goals: Any, away_goals: Any, home_handicap: Any) -> Settlement:
    side = str(side or "").strip().upper()
    if side not in {"HOME", "AWAY"}:
        return Settlement(INVALID, None, side=side or None, reason="side must be HOME or AWAY")
    home, away, line = _number(home_goals), _number(away_goals), _number(home_handicap)
    if home is None or away is None:
        return Settlement(UNSETTLED_MISSING_OUTCOME, None, side=side, reason="goal outcome is missing")
    if line is None:
        return Settlement(INVALID, None, side=side, reason="home handicap is invalid")
    try:
        parts = _line_parts(line)
    except ValueError as exc:
        return Settlement(INVALID, None, home - away, line, side, str(exc))
    margin = home - away
    values = []
    for part in parts:
        adjusted = margin + part
        home_score = 0.0 if math.isclose(adjusted, 0.0, abs_tol=1e-9) else 1.0 if adjusted > 0 else -1.0
        values.append(home_score if side == "HOME" else -home_score)
    return _combined(values, margin, line, side)


def settle_1x2(side: str, home_goals: Any, away_goals: Any) -> Settlement:
    side = str(side or "").strip().upper()
    side = {"1": "HOME", "X": "DRAW", "2": "AWAY", "H": "HOME", "D": "DRAW", "A": "AWAY"}.get(side, side)
    if side not in {"HOME", "DRAW", "AWAY"}:
        return Settlement(INVALID, None, side=side or None, reason="side must be HOME, DRAW, or AWAY")
    home, away = _number(home_goals), _number(away_goals)
    if home is None or away is None:
        return Settlement(UNSETTLED_MISSING_OUTCOME, None, side=side, reason="goal outcome is missing")
    actual = "HOME" if home > away else "AWAY" if away > home else "DRAW"
    score = 1.0 if side == actual else -1.0
    return Settlement(WIN if score > 0 else LOSS, score, home - away, None, side)


def _not_offered(side: str) -> dict[str, Any]:
    return Settlement(NOT_OFFERED, None, side=side).to_dict()


def settle_multi_market_card(card: dict, outcome: dict | None) -> dict[str, Any]:
    if not isinstance(card, dict):
        raise ValueError("card must be a mapping")
    if card.get("schema_version") != "MULTI_MARKET_V1" or card.get("research_only") is not True:
        raise ValueError("unsupported or non-research Multi-Market card")
    outcome = outcome if isinstance(outcome, dict) else {}
    hg, ag = outcome.get("home_goals"), outcome.get("away_goals")
    hc, ac = outcome.get("home_corners"), outcome.get("away_corners")
    result: dict[str, Any] = {
        "schema_version": "MULTI_MARKET_SETTLEMENT_V2",
        "research_only": True,
        "handicap": {},
        "total_goals": {},
        "total_corners": {},
        "team_corners": {"home": {}, "away": {}},
    }

    handicap = card.get("handicap")
    if isinstance(handicap, dict) and handicap.get("home_handicap") is not None:
        line = handicap["home_handicap"]
        result["handicap"] = {
            "home": settle_handicap("HOME", hg, ag, line).to_dict(),
            "away": settle_handicap("AWAY", hg, ag, line).to_dict(),
        }
    else:
        result["handicap"] = {"home": _not_offered("HOME"), "away": _not_offered("AWAY")}

    goals = card.get("total_goals")
    if isinstance(goals, dict) and goals.get("point") is not None:
        home, away = _number(hg), _number(ag)
        observed = home + away if home is not None and away is not None else None
        line = goals["point"]
        result["total_goals"] = {
            "over": settle_total("OVER", observed, line).to_dict(),
            "under": settle_total("UNDER", observed, line).to_dict(),
        }
    else:
        result["total_goals"] = {"over": _not_offered("OVER"), "under": _not_offered("UNDER")}

    corners = card.get("total_corners")
    if isinstance(corners, dict) and corners.get("point") is not None:
        home, away = _number(hc), _number(ac)
        observed = home + away if home is not None and away is not None else None
        line = corners["point"]
        result["total_corners"] = {
            "over": settle_total("OVER", observed, line).to_dict(),
            "under": settle_total("UNDER", observed, line).to_dict(),
        }
    else:
        result["total_corners"] = {"over": _not_offered("OVER"), "under": _not_offered("UNDER")}

    team_markets = card.get("team_corners") if isinstance(card.get("team_corners"), dict) else {}
    for key, observed in (("home", hc), ("away", ac)):
        market = team_markets.get(key)
        if isinstance(market, dict) and market.get("point") is not None:
            line = market["point"]
            result["team_corners"][key] = {
                "over": settle_total("OVER", observed, line).to_dict(),
                "under": settle_total("UNDER", observed, line).to_dict(),
            }
        else:
            result["team_corners"][key] = {"over": _not_offered("OVER"), "under": _not_offered("UNDER")}
    return result
