"""EPL market floor v1: deterministic research-only, dated historical replay.

The market baseline removes bookmaker overround. An *optional* multiclass
residual candidate adds prior-only form/goals/shots/venue features. Candidate
selection is exclusively on the 2022/23 validation season. 2023/24 and 2024/25
are held out until the model and selection rule are frozen. If none improves
BOTH multiclass Brier and log loss, retain precisely the no-vig market floor.

This is NOT an autonomous production prediction model. Historical 'matches'
odds do not prove quote timestamp/provenance. Never promote, train or alter a
production .pkl, draw preregistered prospective research outcomes, or place bets.
"""
from __future__ import annotations

import argparse
import json
import math
from datetime import date
from typing import Any, Iterable, Mapping

SCHEMA = "epl-market-floor-research.v1"
HISTORY_START = "2016-08-01"
HISTORY_END_EXCLUSIVE = "2025-08-01"
PRICE_START = "2019-08-01"
TRAIN_END = "2022-08-01"
VALID_END = "2023-08-01"
OUTCOMES = ("H", "D", "A")
DIMENSIONS = (1, 2, 3, 5)
REGULARIZATION = (0.001, 0.01, 0.05, 0.20)
MIX_WEIGHTS = (0.25, 0.5, 0.75, 1.0)
EPOCHS = 750
STEP_SIZE = 0.65
MODEL_BETTING_STATUS = "NO_BET"
PRICE_COLUMNS = ("home_odds", "draw_odds", "away_odds")
REQUIRED_COLUMNS = (
    "id", "match_date", "match_time", "home_team", "away_team",
    "result", "home_goals", "away_goals", "home_shots_target",
    "away_shots_target", *PRICE_COLUMNS,
)


def finite(value: Any, label: str) -> float:
    try:
        if value is None or isinstance(value, bool):
            raise ValueError(label + " missing")
        x = float(value)
    except (ValueError, TypeError, OverflowError) as exc:
        raise ValueError(label + " not finite") from exc
    if not math.isfinite(x):
        raise ValueError(label + " not finite")
    return x


def no_vig_market(odds: Iterable[Any]) -> tuple[float, float, float]:
    raw = tuple(finite(odd, "decimal odds") for odd in odds)
    if len(raw) != 3 or any(odd <= 1.0 for odd in raw):
        raise ValueError("exact three positive 1X2 decimal prices are required")
    implied = tuple(1.0 / o for o in raw)
    total = sum(implied)
    if not (total > 0 and math.isfinite(total)):
        raise ValueError("invalid bookmaker overround")
    return tuple(p / total for p in implied)


def _average(seq: list[dict[str, Any]], key: str) -> float:
    return sum(float(row[key]) for row in seq) / len(seq) if seq else 0.0


def historical_examples(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Only as-of-match prior five and prior ten team performances may enter X."""
    matches = sorted(
        (dict(r) for r in rows),
        key=lambda x: (x["match_date"], x.get("match_time") or "00:00", int(x["id"])),
    )
    team_history: dict[str, list[dict[str, Any]]] = {}
    seen: set[int] = set()
    examples: list[dict[str, Any]] = []

    for match in matches:
        match_id = int(match["id"])
        if match_id in seen:
            raise ValueError("duplicate EPL historical match id")
        seen.add(match_id)
        match_date = str(match["match_date"])
        if not (HISTORY_START <= match_date < HISTORY_END_EXCLUSIVE):
            raise ValueError("history contains a protected newer result")
        if match["result"] not in OUTCOMES:
            raise ValueError("invalid historical 1X2 result")
        home = str(match["home_team"]).strip()
        away = str(match["away_team"]).strip()
        if not home or not away or home == away:
            raise ValueError("invalid historical teams")
        hp = team_history.get(home, [])[-5:]
        ap = team_history.get(away, [])[-5:]
        hvenue = team_history.get(home, [])[-10:]
        avenue = team_history.get(away, [])[-10:]
        hw = [x for x in hvenue if x["side"] == "H"]
        aw = [x for x in avenue if x["side"] == "A"]
        features = [
            1.0,
            (_average(hp, "points") - _average(ap, "points")) / 3.0,
            (_average(hp, "goal_diff") - _average(ap, "goal_diff")) / 3.0,
            (_average(hp, "shots_target") - _average(ap, "shots_target")) / 8.0,
            _average(hw, "win") - _average(aw, "win"),
        ]
        if PRICE_START <= match_date:
            odds = [match.get(key) for key in PRICE_COLUMNS]
            # In the full replay the market comparison population is complete.
            if any(value is None for value in odds):
                raise ValueError("missing market odds in priced replay period")
            probability = no_vig_market(odds)
            examples.append({
                "date": match_date,
                "y": OUTCOMES.index(match["result"]),
                "f": tuple(features),
                "p": probability,
            })

        # Update history only *after* emitting pre-match features.
        hscore = finite(match["home_goals"], "home goals")
        ascore = finite(match["away_goals"], "away goals")
        hsot = finite(match["home_shots_target"], "home shots target")
        asot = finite(match["away_shots_target"], "away shots target")
        if min(hscore, ascore, hsot, asot) < 0:
            raise ValueError("negative historical result or shots")
        result = match["result"]
        team_history.setdefault(home, []).append({
            "side": "H", "points": 3 if result == "H" else 1 if result == "D" else 0,
            "goal_diff": hscore - ascore, "shots_target": hsot,
            "win": float(result == "H"),
        })
        team_history.setdefault(away, []).append({
            "side": "A", "points": 3 if result == "A" else 1 if result == "D" else 0,
            "goal_diff": ascore - hscore, "shots_target": asot,
            "win": float(result == "A"),
        })
    return examples


def _softmax(logits: Iterable[float]) -> tuple[float, float, float]:
    z = tuple(logits)
    maximum = max(z)
    terms = tuple(math.exp(v - maximum) for v in z)
    total = sum(terms)
    return tuple(t / total for t in terms)


def fit_market_residual(
    rows: list[dict[str, Any]], dimension: int, l2: float, *,
    epochs: int = EPOCHS,
) -> tuple[tuple[float, ...], ...]:
    if dimension not in DIMENSIONS or l2 not in REGULARIZATION:
        raise ValueError("model family/hyperparameters must be preregistered")
    if not rows:
        raise ValueError("empty training set")
    weights = [[0.0] * dimension for _ in range(3)]
    for _ in range(epochs):
        gradient = [[0.0] * dimension for _ in range(3)]
        for row in rows:
            f, prior, y = row["f"], row["p"], row["y"]
            probabilities = _softmax(
                math.log(prior[j]) + sum(weights[j][k] * f[k] for k in range(dimension))
                for j in range(3)
            )
            for j in range(3):
                error = probabilities[j] - float(j == y)
                for k in range(dimension):
                    gradient[j][k] += error * f[k]
        for j in range(3):
            for k in range(dimension):
                weights[j][k] -= STEP_SIZE * (
                    gradient[j][k] / len(rows) + l2 * weights[j][k]
                )
    return tuple(tuple(row) for row in weights)


def candidate_probabilities(
    row: Mapping[str, Any], weights: tuple[tuple[float, ...], ...], alpha: float,
) -> tuple[float, float, float]:
    if alpha not in MIX_WEIGHTS:
        raise ValueError("unregistered blend strength")
    prior, features = row["p"], row["f"]
    fitted = _softmax(
        math.log(prior[j]) + sum(w * features[k] for k, w in enumerate(weights[j]))
        for j in range(3)
    )
    return tuple((1.0 - alpha) * prior[j] + alpha * fitted[j] for j in range(3))


def metrics(
    rows: Iterable[Mapping[str, Any]],
    weights: tuple[tuple[float, ...], ...] | None = None,
    alpha: float = 0.0,
) -> dict[str, float | int | None]:
    examples = list(rows)
    if not examples:
        return {"n": 0, "brier": None, "log_loss": None, "accuracy": None}
    loss_brier = loss_log = hits = 0
    for row in examples:
        probabilities = candidate_probabilities(row, weights, alpha) if weights else row["p"]
        y = int(row["y"])
        loss_brier += sum((p - float(y == i)) ** 2 for i, p in enumerate(probabilities))
        loss_log -= math.log(probabilities[y])
        hits += int(max(range(3), key=lambda i: probabilities[i]) == y)
    n = len(examples)
    return {"n": n, "brier": loss_brier / n, "log_loss": loss_log / n, "accuracy": hits / n}


def split_examples(rows: list[dict[str, Any]]):
    train = [x for x in rows if x["date"] < TRAIN_END]
    validation = [x for x in rows if TRAIN_END <= x["date"] < VALID_END]
    heldout = [x for x in rows if VALID_END <= x["date"] < HISTORY_END_EXCLUSIVE]
    if len(rows) != len(train) + len(validation) + len(heldout):
        raise ValueError("historical splits do not cover priced examples")
    if len(train) < 100 or len(validation) < 100 or len(heldout) < 100:
        raise ValueError("insufficient time-separated match sample")
    return train, validation, heldout


def evaluate_historical_market_floor(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    examples = historical_examples(rows)
    train, validation, heldout = split_examples(examples)
    validation_market = metrics(validation)
    # The initial held-out 2023/24–2024/25 outcomes are never used for selection.
    eligible: list[tuple[float, float, int, float, float, tuple[tuple[float, ...], ...]]] = []
    count_candidates = 0
    for dimension in DIMENSIONS:
        for regularization in REGULARIZATION:
            coefficients = fit_market_residual(train, dimension, regularization)
            for alpha in MIX_WEIGHTS:
                count_candidates += 1
                candidate = metrics(validation, coefficients, alpha)
                if (candidate["brier"] < validation_market["brier"] and
                    candidate["log_loss"] < validation_market["log_loss"]):
                    eligible.append((
                        candidate["log_loss"], candidate["brier"],
                        dimension, regularization, alpha, coefficients,
                    ))
    eligible.sort(key=lambda item: (item[0], item[1], item[2], item[3], item[4]))
    selected = eligible[0] if eligible else None

    holdout_market = metrics(heldout)
    holdout_candidate = (
        metrics(heldout, selected[5], selected[4]) if selected else holdout_market.copy()
    )
    passes_holdout = (
        holdout_candidate["brier"] <= holdout_market["brier"]
        and holdout_candidate["log_loss"] <= holdout_market["log_loss"]
    )
    # No post-hoc model choice based on the held-out outcomes.
    return {
        "schema_version": SCHEMA,
        "evaluation": "RESEARCH_ONLY",
        "split_boundaries": {
            "train_before": TRAIN_END, "validation_before": VALID_END,
            "heldout_before": HISTORY_END_EXCLUSIVE,
        },
        "samples": {
            "training": len(train), "validation": len(validation), "heldout": len(heldout),
        },
        "market_validation": validation_market,
        "market_heldout": holdout_market,
        "candidates_considered_on_validation": count_candidates,
        "candidate_accepted_on_validation": selected is not None,
        "selected_candidate": (
            {"dimension": selected[2], "regularization": selected[3],
             "market_blend_alpha": selected[4]} if selected else None
        ),
        "selected_or_floor_heldout": holdout_candidate,
        "not_worse_than_market_on_heldout": passes_holdout,
        "conclusion": (
            "MARKET_FLOOR_ONLY_NO_AI_UPLIFT" if selected is None else
            "RESEARCH_CANDIDATE_PASSED_HOLDOUT" if passes_holdout else
            "RESEARCH_CANDIDATE_FAILED_HELDOUT"
        ),
        "historical_odds_timestamp_qualified": False,
        "bookmaker_margin_removed": True,
        "training_restricted_to_historical_data": True,
        "market_only_is_not_ai_model": True,
        "no_bet": True, "roi": None, "clv": None,
        "automatic_promotion": False, "production_artifact_written": False,
        "provider_calls": 0,
    }


def load_historical_matches(client: Any) -> list[dict[str, Any]]:
    """Read only years before the frozen prospective research window. No writes."""
    limit = 500
    offset = 0
    values: list[dict[str, Any]] = []
    while True:
        query = (
            client.table("matches").select(",".join(REQUIRED_COLUMNS))
            .eq("league", "EPL")
            .gte("match_date", HISTORY_START)
            .lt("match_date", HISTORY_END_EXCLUSIVE)
            .order("match_date").order("id")
            .range(offset, offset + limit - 1)
        )
        batch = query.execute().data or []
        values.extend(batch)
        if len(batch) < limit:
            break
        offset += limit
        if offset > 10000:
            raise ValueError("history unexpectedly large; fail closed")
    return values


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--read-only-historical-supabase", action="store_true", required=True)
    parser.parse_args()
    from database import supabase
    report = evaluate_historical_market_floor(load_historical_matches(supabase))
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    print("PASS: EPL MARKET FLOOR RESEARCH ONLY; NO MODEL PROMOTION OR ODDS API CALL")


if __name__ == "__main__":
    main()
