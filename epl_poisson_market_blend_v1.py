"""Research-only as-of-date independent-Poisson / Dixon-Coles 1X2 replay.

The 2019/20 season selects a bounded Poisson blend with contemporaneous but
UNTIMESTAMPED historic odds. 2020/21–2021/22 is a later historical sensitivity
period, NOT a pristine new OOS period (prior studies have already used it).
No model promotion, provider calls, betting, write queries, or future-period
research outcomes. Market-only fallback is NOT an AI model.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import date
from itertools import product
import json
import math
from typing import Any, Iterable, Mapping

SCHEMA = "epl-poisson-market-blend-research.v1"
HISTORY_BEGIN = "2016-08-01"
HISTORY_END_EXCLUSIVE = "2022-08-01"
PRICE_BEGIN = "2019-08-01"
VALIDATION_END = "2020-08-01"
PRIOR_STRENGTH = 150
PRIOR_HOME_GOALS = 1.5
PRIOR_AWAY_GOALS = 1.1
SMOOTHING = (5, 12, 25)
DC_RHO = (-0.08, 0.0, 0.08)
MARKET_WEIGHTS = (0.1, 0.25, 0.4, 0.6)
MAX_GOALS = 10
MIN_GOAL_RATE = 0.15
MAX_GOAL_RATE = 4.5
CANDIDATE_COUNT = len(SMOOTHING) * len(DC_RHO) * len(MARKET_WEIGHTS)
REQUIRED_COLUMNS = (
    "id", "match_date", "home_team", "away_team", "home_goals", "away_goals",
    "result", "home_odds", "draw_odds", "away_odds",
)


def _finite(value: Any) -> float:
    if value is None or isinstance(value, bool):
        raise ValueError("missing or invalid numeric field")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("non-finite numeric field")
    return number


def no_vig_prices(odds: Iterable[Any]) -> tuple[float, float, float]:
    values = tuple(_finite(x) for x in odds)
    if len(values) != 3 or any(v <= 1 for v in values):
        raise ValueError("three valid decimal bookmaker odds required")
    inv = [1.0 / v for v in values]
    total = sum(inv)
    return tuple(v / total for v in inv)


def poisson_score_probabilities(home_rate: float, away_rate: float,
                                rho: float) -> tuple[float, float, float]:
    """Low-score Dixon–Coles tau correction, then normalize finite score grid."""
    lh, la = _finite(home_rate), _finite(away_rate)
    if not (MIN_GOAL_RATE <= lh <= MAX_GOAL_RATE and
            MIN_GOAL_RATE <= la <= MAX_GOAL_RATE and rho in DC_RHO):
        raise ValueError("goal rates or DC rho outside frozen contract")
    ph, pa = [math.exp(-lh)], [math.exp(-la)]
    for goals in range(1, MAX_GOALS + 1):
        ph.append(ph[-1] * lh / goals)
        pa.append(pa[-1] * la / goals)
    acc = [0.0, 0.0, 0.0]
    for h, a in product(range(MAX_GOALS + 1), repeat=2):
        tau = 1.0
        if h == 0 and a == 0:
            tau = 1 - lh * la * rho
        elif h == 0 and a == 1:
            tau = 1 + lh * rho
        elif h == 1 and a == 0:
            tau = 1 + la * rho
        elif h == 1 and a == 1:
            tau = 1 - rho
        contribution = ph[h] * pa[a] * tau
        if contribution < 0:
            raise ValueError("invalid low-score adjustment")
        acc[0 if h > a else 1 if h == a else 2] += contribution
    total = sum(acc)
    return tuple(v / total for v in acc)


def _side() -> dict[str, float]:
    return {"n": 0, "f": 0.0, "c": 0.0}


def _team():
    return {"h": _side(), "a": _side()}


def historical_priced_examples(matches: Iterable[Mapping[str, Any]]):
    """No same-day outcomes enter ANY same-day pre-match team rate."""
    rows = sorted((dict(m) for m in matches),
                  key=lambda m: (str(m["match_date"]), int(m["id"])))
    team_stats = defaultdict(_team)
    seen_ids: set[int] = set()
    home_goals = away_goals = 0.0
    total_games = 0
    output = []

    position = 0
    while position < len(rows):
        end = position + 1
        day = str(rows[position]["match_date"])
        while end < len(rows) and str(rows[end]["match_date"]) == day:
            end += 1
        if not HISTORY_BEGIN <= day < HISTORY_END_EXCLUSIVE:
            raise ValueError("research end-date boundary violated")
        base_home = max(.5, (home_goals + PRIOR_STRENGTH * PRIOR_HOME_GOALS) /
                        (total_games + PRIOR_STRENGTH))
        base_away = max(.5, (away_goals + PRIOR_STRENGTH * PRIOR_AWAY_GOALS) /
                        (total_games + PRIOR_STRENGTH))

        # Freeze all feature states until the day's entire fixture batch is scored.
        for match in rows[position:end]:
            mid = int(match["id"])
            if mid in seen_ids:
                raise ValueError("duplicate historical match")
            seen_ids.add(mid)
            home, away = str(match["home_team"]).strip(), str(match["away_team"]).strip()
            if not home or not away or home == away:
                raise ValueError("invalid historical team pairing")
            if match["result"] not in ("H", "D", "A"):
                raise ValueError("invalid historical outcome")
            if day < PRICE_BEGIN:
                continue
            market = no_vig_prices(match.get(k) for k in
                                   ("home_odds", "draw_odds", "away_odds"))
            estimates = {}
            hs, as_ = team_stats[home]["h"], team_stats[away]["a"]
            for smooth in SMOOTHING:
                h_attack = (hs["f"] + smooth * base_home) / (hs["n"] + smooth)
                a_defend = (as_["c"] + smooth * base_home) / (as_["n"] + smooth)
                a_attack = (as_["f"] + smooth * base_away) / (as_["n"] + smooth)
                h_defend = (hs["c"] + smooth * base_away) / (hs["n"] + smooth)
                lam_h = max(MIN_GOAL_RATE, min(MAX_GOAL_RATE,
                                                  h_attack * a_defend / base_home))
                lam_a = max(MIN_GOAL_RATE, min(MAX_GOAL_RATE,
                                                  a_attack * h_defend / base_away))
                for rho in DC_RHO:
                    estimates[(smooth, rho)] = poisson_score_probabilities(lam_h, lam_a, rho)
            output.append({
                "date": day,
                "y": "HDA".index(match["result"]),
                "market": market,
                "estimates": estimates,
            })

        # For each date: only AFTER predicting all fixtures do outcomes enter history.
        for match in rows[position:end]:
            gh, ga = _finite(match["home_goals"]), _finite(match["away_goals"])
            if min(gh, ga) < 0 or gh != int(gh) or ga != int(ga):
                raise ValueError("invalid historical goal counts")
            home, away = str(match["home_team"]).strip(), str(match["away_team"]).strip()
            hs, as_ = team_stats[home]["h"], team_stats[away]["a"]
            hs["n"] += 1
            hs["f"] += gh
            hs["c"] += ga
            as_["n"] += 1
            as_["f"] += ga
            as_["c"] += gh
            home_goals += gh
            away_goals += ga
            total_games += 1
        position = end
    return output


def score(rows, smooth=None, rho=None, weight=None):
    records = list(rows)
    if not records:
        raise ValueError("cannot score empty fixture population")
    total_brier = total_ll = correct = 0.0
    for match in records:
        prob = match["market"]
        if smooth is not None:
            if smooth not in SMOOTHING or rho not in DC_RHO or weight not in MARKET_WEIGHTS:
                raise ValueError("unregistered model parameters")
            model = match["estimates"][(smooth, rho)]
            prob = tuple((1 - weight) * p + weight * m for p, m in zip(prob, model))
        actual = match["y"]
        total_brier += sum((p - float(j == actual)) ** 2 for j, p in enumerate(prob))
        total_ll -= math.log(prob[actual])
        correct += int(max(range(3), key=lambda j: prob[j]) == actual)
    n = len(records)
    return {"n": n, "brier": total_brier / n,
            "log_loss": total_ll / n, "accuracy": correct / n}


def choose_on_validation(rows):
    baseline = score(rows)
    candidates = []
    for smooth, rho, weight in product(SMOOTHING, DC_RHO, MARKET_WEIGHTS):
        metrics = score(rows, smooth, rho, weight)
        if metrics["brier"] < baseline["brier"] and metrics["log_loss"] < baseline["log_loss"]:
            candidates.append((metrics["log_loss"], metrics["brier"],
                               smooth, rho, weight))
    # Frozen rank: loss, Brier, strength, rho and market blend.
    candidates.sort()
    return (candidates[0][2:] if candidates else None), baseline


def evaluate(rows):
    examples = historical_priced_examples(rows)
    validation = [e for e in examples if e["date"] < VALIDATION_END]
    forward = [e for e in examples if e["date"] >= VALIDATION_END]
    if len(validation) != 380 or len(forward) != 760:
        raise ValueError("expected exactly 380/760 complete dated priced EPL fixtures")
    chosen, market_val = choose_on_validation(validation)
    market_forward = score(forward)
    candidate_val = score(validation, *chosen) if chosen else None
    candidate_forward = score(forward, *chosen) if chosen else None
    success = bool(candidate_forward and
                   candidate_forward["brier"] <= market_forward["brier"] and
                   candidate_forward["log_loss"] <= market_forward["log_loss"])
    return {
        "schema_version": SCHEMA,
        "research_status": ("HISTORICAL_SUPPORT_NOT_PROSPECTIVE" if success else
                            "FAILED_FORWARD_HISTORICAL_EVAL" if chosen else
                            "NO_VALIDATION_IMPROVEMENT"),
        "cohort": {"prior_unpriced_start": HISTORY_BEGIN,
                   "priced_from": PRICE_BEGIN, "end_exclusive": HISTORY_END_EXCLUSIVE,
                   "validation_end": VALIDATION_END,
                   "validation_n": len(validation), "forward_n": len(forward)},
        "candidate_grid_size": CANDIDATE_COUNT,
        "frozen_selection": (
            {"smooth_games": chosen[0], "rho": chosen[1],
             "poisson_blend_weight": chosen[2]} if chosen else None),
        "validation_market": market_val, "validation_candidate": candidate_val,
        "forward_market": market_forward, "forward_candidate": candidate_forward,
        "market_fallback": market_forward if not success else None,
        "market_fallback_is_ai": False,
        "historic_odds_timestamp_qualified": False,
        "is_pristine_untouched_evaluation": False,
        "read_frozen_prospective_outcomes": False,
        "production_promotion": False, "production_model_changed": False,
        "provider_calls": 0, "bets": 0, "roi": None,
    }


def read_historical_epl(client):
    rows = []
    page = 0
    size = 500
    while True:
        request = (client.table("matches")
                   .select(",".join(REQUIRED_COLUMNS))
                   .eq("league", "EPL")
                   .gte("match_date", HISTORY_BEGIN)
                   .lt("match_date", HISTORY_END_EXCLUSIVE)
                   .order("match_date").order("id")
                   .range(page * size, (page + 1) * size - 1))
        batch = request.execute().data or []
        rows.extend(batch)
        if len(batch) < size:
            break
        page += 1
        if page > 20:
            raise ValueError("historical EPL dataset outside bounded read")
    return rows


def main():
    parser = argparse.ArgumentParser(description="Read-only EPL Poisson market blend audit")
    parser.add_argument("--read-only-historical-supabase", required=True,
                        action="store_true")
    parser.parse_args()
    from database import supabase
    print(json.dumps(evaluate(read_historical_epl(supabase)),
                     ensure_ascii=False, indent=2, sort_keys=True))
    print("PASS: historical research only, no promotion")


if __name__ == "__main__":
    main()
