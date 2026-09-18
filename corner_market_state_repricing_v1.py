"""Market-only corner repricing-risk screen, analogous to the 1X2 market-state work.

No match outcomes or football-state features are used. Opening and closing
Bet365 corner total markets are reconstructed to a comparable Poisson-implied
market centre. A fixed leave-one-league-out classifier asks whether opening
market geometry predicts top-quartile subsequent repricing magnitude.
"""

from __future__ import annotations

import argparse
import io
import json
import math
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import brentq
from scipy.stats import poisson
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    log_loss,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

EXPERIMENT_ID = "CORNER_MARKET_STATE_REPRICING_V1"
MOVEMENT_QUANTILE = 0.75
LOGISTIC_C = 0.1
MIN_TOTAL_ROWS = 40
MIN_ROWS_PER_LEAGUE = 6
LEAGUES = ("EPL", "LA_LIGA", "SERIE_A", "BUNDESLIGA", "LIGUE_1")

FEATURES = {
    "FULL_STATE": ["opening_line", "opening_over_prob"],
    "OVER_LEVEL": ["opening_over_prob"],
    "ENTROPY": ["market_entropy"],
    "LINE_LEVEL": ["opening_line"],
    "PRICE_IMBALANCE": ["price_imbalance"],
    "FAIR_CENTRE": ["opening_lambda"],
}


def devig_over_probability(over_price: float, under_price: float) -> float:
    over_price = float(over_price)
    under_price = float(under_price)
    if not (math.isfinite(over_price) and math.isfinite(under_price)):
        raise ValueError("non-finite prices")
    if over_price <= 1.0 or under_price <= 1.0:
        raise ValueError("prices must exceed 1.0")
    over_inv = 1.0 / over_price
    under_inv = 1.0 / under_price
    return over_inv / (over_inv + under_inv)


def _line_kind(line: float) -> str:
    line = float(line)
    frac = line - math.floor(line)
    if abs(frac) < 1e-9:
        return "integer"
    if abs(frac - 0.5) < 1e-9:
        return "half"
    raise ValueError(f"unsupported corner line: {line}")


def implied_poisson_centre(line: float, over_price: float, under_price: float) -> float:
    """Reconstruct one comparable market centre from line and two-way prices."""
    line = float(line)
    p_over = devig_over_probability(over_price, under_price)
    kind = _line_kind(line)

    if kind == "half":
        threshold = math.floor(line) + 1

        def objective(lam: float) -> float:
            return float(poisson.sf(threshold - 1, lam)) - p_over

    else:
        integer_line = int(round(line))

        def objective(lam: float) -> float:
            p_win_over = float(poisson.sf(integer_line, lam))
            p_win_under = float(poisson.cdf(integer_line - 1, lam))
            denom = p_win_over + p_win_under
            if denom <= 0:
                raise ValueError("invalid non-push mass")
            return p_win_over / denom - p_over

    low, high = 1.0, 25.0
    f_low = objective(low)
    f_high = objective(high)
    if f_low == 0:
        return low
    if f_high == 0:
        return high
    if f_low * f_high > 0:
        raise ValueError("market centre outside frozen solve interval")
    return float(brentq(objective, low, high))


def _find_member(zf: zipfile.ZipFile, suffix: str) -> str:
    matches = [name for name in zf.namelist() if name.endswith(suffix)]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one {suffix!r}, found {len(matches)}")
    return matches[0]


def load_pilot_rows(pilot_zip: Path) -> dict[str, dict]:
    rows: dict[str, dict] = {}
    with zipfile.ZipFile(pilot_zip) as zf:
        name = _find_member(zf, "bet365_corner_opening_closing.jsonl")
        for line in zf.read(name).decode("utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            rows[str(row["fixture_id"])] = row
    return rows


def load_screen_rows(screen_zip: Path) -> dict[str, dict]:
    rows: dict[str, dict] = {}
    with zipfile.ZipFile(screen_zip) as zf:
        selected = json.loads(zf.read(_find_member(zf, "selected_fixtures.json")))
        fixture_meta: dict[str, dict] = {}
        for league, league_rows in selected.items():
            for row in league_rows:
                fixture_meta[str(row["fixture_id"])] = {
                    "league": league,
                    "home_team": row.get("provider_home_team") or row.get("HomeTeam"),
                    "away_team": row.get("provider_away_team") or row.get("AwayTeam"),
                    "kickoff_utc": row.get("kickoff_utc"),
                }

        for name in zf.namelist():
            if "/raw/odds/" not in name or not name.endswith(".json"):
                continue
            payload = json.loads(zf.read(name))
            data = payload.get("data") or {}
            fixture_id = str(data.get("fixture_id") or Path(name).stem)
            bookmaker = next(
                (item for item in data.get("bookmakers", []) if item.get("slug") == "bet365"),
                None,
            )
            if not bookmaker:
                continue
            corner_line = ((bookmaker.get("odds") or {}).get("corner_line") or {})
            opening = corner_line.get("opening") or {}
            closing = corner_line.get("closing") or {}
            required = ("line", "over", "under")
            if not all(key in opening for key in required):
                continue
            if not all(key in closing for key in required):
                continue
            meta = fixture_meta.get(fixture_id)
            if not meta:
                continue
            rows[fixture_id] = {
                "fixture_id": fixture_id,
                **meta,
                "bookmaker": "bet365",
                "opening_line": opening["line"],
                "opening_over": opening["over"],
                "opening_under": opening["under"],
                "closing_line": closing["line"],
                "closing_over": closing["over"],
                "closing_under": closing["under"],
                "source": "FREE_CORNERS_SCREEN_RAW",
            }
    return rows


def load_market_rows(pilot_zip: Path, screen_zip: Path) -> pd.DataFrame:
    # The screen raw payload is the later immutable acquisition, so it wins only
    # when it contains a complete Bet365 opening+closing structure.
    union = load_pilot_rows(pilot_zip)
    union.update(load_screen_rows(screen_zip))

    normalized = []
    for fixture_id, row in union.items():
        try:
            opening_line = float(row["opening_line"])
            closing_line = float(row["closing_line"])
            _line_kind(opening_line)
            _line_kind(closing_line)
            opening_over = float(row["opening_over"])
            opening_under = float(row["opening_under"])
            closing_over = float(row["closing_over"])
            closing_under = float(row["closing_under"])
            p_over = devig_over_probability(opening_over, opening_under)
            opening_lambda = implied_poisson_centre(
                opening_line, opening_over, opening_under
            )
            closing_lambda = implied_poisson_centre(
                closing_line, closing_over, closing_under
            )
        except (KeyError, TypeError, ValueError):
            continue

        normalized.append(
            {
                "fixture_id": str(fixture_id),
                "league": str(row["league"]),
                "opening_line": opening_line,
                "opening_over_prob": p_over,
                "market_entropy": -(
                    p_over * math.log(max(p_over, 1e-12))
                    + (1.0 - p_over) * math.log(max(1.0 - p_over, 1e-12))
                ),
                "price_imbalance": abs(p_over - 0.5),
                "opening_lambda": opening_lambda,
                "closing_lambda": closing_lambda,
                "centre_delta": closing_lambda - opening_lambda,
                "movement_magnitude": abs(closing_lambda - opening_lambda),
            }
        )

    frame = pd.DataFrame(normalized)
    if frame.empty:
        return frame
    return frame.sort_values(["league", "fixture_id"], kind="stable").reset_index(drop=True)


def _metrics(y: np.ndarray, p: np.ndarray) -> dict:
    y = np.asarray(y, dtype=int)
    p = np.clip(np.asarray(p, dtype=float), 1e-12, 1 - 1e-12)
    result = {
        "n": int(len(y)),
        "positives": int(y.sum()),
        "prevalence": float(y.mean()) if len(y) else None,
        "brier": float(brier_score_loss(y, p)),
        "log_loss": float(log_loss(y, p, labels=[0, 1])),
    }
    if len(np.unique(y)) == 2:
        result["roc_auc"] = float(roc_auc_score(y, p))
        result["average_precision"] = float(average_precision_score(y, p))
    else:
        result["roc_auc"] = None
        result["average_precision"] = None
    return result


def _fit(train: pd.DataFrame, y: np.ndarray, columns: list[str]) -> Pipeline:
    model = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
            ("logit", LogisticRegression(C=LOGISTIC_C, max_iter=2000)),
        ]
    )
    model.fit(train[columns], y)
    return model


def evaluate(frame: pd.DataFrame) -> dict:
    counts = frame["league"].value_counts().to_dict() if not frame.empty else {}
    sample_ok = (
        len(frame) >= MIN_TOTAL_ROWS
        and all(counts.get(league, 0) >= MIN_ROWS_PER_LEAGUE for league in LEAGUES)
    )
    base_report = {
        "experiment_id": EXPERIMENT_ID,
        "research_only": True,
        "betting_enabled": False,
        "production_promotion": False,
        "match_outcome_used": False,
        "football_state_used": False,
        "movement_quantile": MOVEMENT_QUANTILE,
        "logistic_c": LOGISTIC_C,
        "eligible_rows": int(len(frame)),
        "rows_by_league": {league: int(counts.get(league, 0)) for league in LEAGUES},
    }
    if not sample_ok:
        return {**base_report, "verdict": "SAMPLE_TOO_SMALL", "folds": []}

    folds = []
    oof: dict[str, list[dict]] = {variant: [] for variant in FEATURES}
    coefficient_signs: dict[str, list[float]] = {variant: [] for variant in FEATURES}

    for held_out in LEAGUES:
        train = frame[frame["league"] != held_out].copy()
        test = frame[frame["league"] == held_out].copy()
        threshold = float(
            np.quantile(train["movement_magnitude"].to_numpy(float), MOVEMENT_QUANTILE)
        )
        y_train = (train["movement_magnitude"] >= threshold).astype(int).to_numpy()
        y_test = (test["movement_magnitude"] >= threshold).astype(int).to_numpy()
        prevalence = float(y_train.mean())
        baseline_p = np.full(len(test), prevalence, dtype=float)
        baseline = _metrics(y_test, baseline_p)
        variants = {}

        for variant, columns in FEATURES.items():
            model = _fit(train, y_train, columns)
            probs = model.predict_proba(test[columns])[:, 1]
            metrics = _metrics(y_test, probs)
            metrics["delta_brier_vs_constant"] = metrics["brier"] - baseline["brier"]
            metrics["delta_log_loss_vs_constant"] = (
                metrics["log_loss"] - baseline["log_loss"]
            )
            metrics["beats_constant_both"] = bool(
                metrics["delta_brier_vs_constant"] < 0
                and metrics["delta_log_loss_vs_constant"] < 0
            )
            variants[variant] = metrics
            coefficient_signs[variant].append(
                float(model.named_steps["logit"].coef_[0][0])
                if len(columns) == 1
                else float("nan")
            )
            for fixture_id, y_value, prob in zip(
                test["fixture_id"], y_test, probs, strict=True
            ):
                oof[variant].append(
                    {
                        "fixture_id": str(fixture_id),
                        "league": held_out,
                        "y": int(y_value),
                        "probability": float(prob),
                        "baseline_probability": prevalence,
                    }
                )

        folds.append(
            {
                "held_out_league": held_out,
                "train_n": int(len(train)),
                "test_n": int(len(test)),
                "movement_threshold": threshold,
                "baseline": baseline,
                "variants": variants,
            }
        )

    summary = {}
    for variant in FEATURES:
        rows = oof[variant]
        y = np.array([row["y"] for row in rows], dtype=int)
        p = np.array([row["probability"] for row in rows], dtype=float)
        bp = np.array([row["baseline_probability"] for row in rows], dtype=float)
        candidate = _metrics(y, p)
        baseline = _metrics(y, bp)
        wins = sum(
            fold["variants"][variant]["beats_constant_both"] for fold in folds
        )
        summary[variant] = {
            "held_out_league_wins": int(wins),
            "pooled_candidate": candidate,
            "pooled_baseline": baseline,
            "pooled_delta_brier": candidate["brier"] - baseline["brier"],
            "pooled_delta_log_loss": candidate["log_loss"] - baseline["log_loss"],
            "pooled_beats_both": bool(
                candidate["brier"] < baseline["brier"]
                and candidate["log_loss"] < baseline["log_loss"]
            ),
            "single_feature_coefficients": coefficient_signs[variant],
        }

    strong = [
        variant
        for variant, row in summary.items()
        if row["pooled_beats_both"] and row["held_out_league_wins"] >= 4
    ]
    indicative = [
        variant
        for variant, row in summary.items()
        if row["pooled_beats_both"] and row["held_out_league_wins"] >= 3
    ]
    if strong:
        verdict = "STRONG_REPRICING_SIGNAL"
        accepted = sorted(
            strong,
            key=lambda v: (
                summary[v]["pooled_delta_log_loss"],
                summary[v]["pooled_delta_brier"],
                v,
            ),
        )[0]
    elif indicative:
        verdict = "INDICATIVE_REPRICING_SIGNAL"
        accepted = sorted(
            indicative,
            key=lambda v: (
                summary[v]["pooled_delta_log_loss"],
                summary[v]["pooled_delta_brier"],
                v,
            ),
        )[0]
    else:
        verdict = "NO_CLEAR_REPRICING_SIGNAL"
        accepted = None

    direction = None
    if accepted:
        accepted_oof = pd.DataFrame(oof[accepted])
        joined = frame[["fixture_id", "centre_delta"]].merge(
            accepted_oof[["fixture_id", "league", "probability"]],
            on="fixture_id",
            how="inner",
            validate="one_to_one",
        )
        selected_rows = []
        for league in LEAGUES:
            league_rows = joined[joined["league"] == league].sort_values(
                "probability", ascending=False, kind="stable"
            )
            take = max(1, math.ceil(len(league_rows) * 0.25))
            selected_rows.append(league_rows.head(take))
        high_risk = pd.concat(selected_rows, ignore_index=True)
        positive = int((high_risk["centre_delta"] > 0).sum())
        negative = int((high_risk["centre_delta"] < 0).sum())
        zero = int((high_risk["centre_delta"].abs() < 1e-12).sum())
        direction = {
            "diagnostic_only": True,
            "high_risk_rows": int(len(high_risk)),
            "positive_moves": positive,
            "negative_moves": negative,
            "zero_moves": zero,
            "positive_share_nonzero": (
                float(positive / (positive + negative)) if positive + negative else None
            ),
            "stable_direction_claim": False,
        }

    return {
        **base_report,
        "verdict": verdict,
        "selected_variant": accepted,
        "folds": folds,
        "variant_summary": summary,
        "direction_diagnostic": direction,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pilot-zip", type=Path, required=True)
    parser.add_argument("--screen-zip", type=Path, required=True)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/corner_market_state_repricing_v1"),
    )
    args = parser.parse_args()

    frame = load_market_rows(args.pilot_zip, args.screen_zip)
    report = evaluate(frame)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.output_dir / "market_rows.csv", index=False)
    (args.output_dir / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
