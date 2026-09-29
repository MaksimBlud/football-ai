"""MARKET_DEVIG_METHODS_V1 — research-only historical de-vig comparison.

Compares the current multiplicative 1X2 margin removal with additive, power,
and Shin transformations on Football AI's stored Football-Data average odds.

No training, no live activation, no Supabase writes, no Odds API calls, and no
production artifact changes.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd


EXPERIMENT_ID = "MARKET_DEVIG_METHODS_V1"
OUTPUT_DIR = Path("artifacts/market_devig_methods_v1")
OUTPUT_PATH = OUTPUT_DIR / "report.json"

SEASONS = [
    "2019/2020",
    "2020/2021",
    "2021/2022",
    "2022/2023",
    "2023/2024",
    "2024/2025",
    "2025/2026",
]
DISCOVERY_SEASONS = SEASONS[:5]
VALIDATION_SEASON = "2024/2025"
TEST_SEASON = "2025/2026"

METHODS = ("MULTIPLICATIVE", "ADDITIVE", "POWER", "SHIN")
ALTERNATIVES = ("ADDITIVE", "POWER", "SHIN")
EPS = 1e-12
SOLVER_TOL = 1e-12
MAX_ITERATIONS = 1000
BOOTSTRAP_SAMPLES = 10000
BOOTSTRAP_SEED = 20260929


def load_market_history() -> pd.DataFrame:
    """Read the frozen historical market sample from live Supabase."""
    from database import supabase

    rows: list[dict] = []
    page_size = 1000
    start = 0

    while True:
        response = (
            supabase
            .table("matches")
            .select(
                "id,season,league,match_date,home_team,away_team,"
                "home_goals,away_goals,result,home_odds,draw_odds,away_odds"
            )
            .in_("season", SEASONS)
            .eq("league", "EPL")
            .order("match_date")
            .order("id")
            .range(start, start + page_size - 1)
            .execute()
        )
        batch = response.data or []
        if not batch:
            break
        rows.extend(batch)
        if len(batch) < page_size:
            break
        start += page_size

    frame = pd.DataFrame(rows)
    if frame.empty:
        raise RuntimeError("No historical EPL market rows returned.")

    observed = sorted(frame["season"].astype(str).unique())
    if observed != SEASONS:
        raise RuntimeError(
            f"Season contract mismatch: observed={observed}, expected={SEASONS}"
        )

    counts = frame.groupby("season").size().to_dict()
    expected = {season: 380 for season in SEASONS}
    if counts != expected:
        raise RuntimeError(f"Season row-count contract changed: {counts}")

    odds_columns = ["home_odds", "draw_odds", "away_odds"]
    for column in odds_columns:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    valid_odds = frame[odds_columns].gt(1.0).all(axis=1)
    valid_outcomes = frame["result"].astype(str).isin(["H", "D", "A"])
    if not valid_odds.all():
        bad = frame.loc[~valid_odds, ["season", *odds_columns]]
        raise RuntimeError(
            f"Frozen sample contains invalid average odds rows: {len(bad)}"
        )
    if not valid_outcomes.all():
        raise RuntimeError("Frozen sample contains invalid outcomes.")

    if len(frame) != 2660:
        raise RuntimeError(f"Expected 2660 rows, got {len(frame)}")

    return frame.sort_values(["match_date", "id"], kind="stable").reset_index(drop=True)


def _validate_odds(odds: np.ndarray) -> tuple[np.ndarray, float]:
    values = np.asarray(odds, dtype=float)
    if values.shape != (3,):
        raise ValueError("1X2 odds must contain exactly three outcomes")
    if not np.isfinite(values).all() or (values <= 1.0).any():
        raise ValueError("Decimal odds must be finite and > 1")
    q = 1.0 / values
    booksum = float(q.sum())
    if not math.isfinite(booksum) or booksum <= 1.0:
        raise ValueError("V1 requires a positive bookmaker overround")
    return q, booksum


def _validate_probabilities(probabilities: np.ndarray) -> np.ndarray:
    p = np.asarray(probabilities, dtype=float)
    if p.shape != (3,):
        raise ValueError("probabilities must contain three outcomes")
    if not np.isfinite(p).all() or (p <= 0.0).any() or (p >= 1.0).any():
        raise ValueError("probabilities must be finite and strictly inside (0, 1)")
    if not math.isclose(float(p.sum()), 1.0, rel_tol=0.0, abs_tol=1e-10):
        raise ValueError(f"probabilities do not sum to one: {p.sum()}")
    return p


def multiplicative_probabilities(odds: np.ndarray) -> tuple[np.ndarray, dict]:
    q, booksum = _validate_odds(odds)
    return _validate_probabilities(q / booksum), {
        "overround": booksum - 1.0,
    }


def additive_probabilities(odds: np.ndarray) -> tuple[np.ndarray, dict]:
    q, booksum = _validate_odds(odds)
    p = q - ((booksum - 1.0) / 3.0)
    return _validate_probabilities(p), {
        "overround": booksum - 1.0,
    }


def power_probabilities(odds: np.ndarray) -> tuple[np.ndarray, dict]:
    q, booksum = _validate_odds(odds)

    def objective(k: float) -> float:
        return float(np.power(q, k).sum() - 1.0)

    low = 1.0
    high = 2.0
    while objective(high) > 0.0 and high < 64.0:
        high *= 2.0
    if objective(high) > 0.0:
        raise RuntimeError("Power solver failed to bracket root")

    iterations = 0
    while iterations < MAX_ITERATIONS:
        mid = (low + high) / 2.0
        value = objective(mid)
        if abs(value) <= SOLVER_TOL or (high - low) <= SOLVER_TOL:
            k = mid
            break
        if value > 0.0:
            low = mid
        else:
            high = mid
        iterations += 1
    else:
        raise RuntimeError("Power solver did not converge")

    p = np.power(q, k)
    p = p / p.sum()
    return _validate_probabilities(p), {
        "overround": booksum - 1.0,
        "k": float(k),
        "iterations": int(iterations + 1),
    }


def shin_probabilities(odds: np.ndarray) -> tuple[np.ndarray, dict]:
    q, booksum = _validate_odds(odds)
    n = len(q)
    z = 0.0
    delta = math.inf
    iterations = 0

    while delta > SOLVER_TOL and iterations < MAX_ITERATIONS:
        previous = z
        z = (
            sum(
                math.sqrt(
                    z**2
                    + 4.0 * (1.0 - z) * float(io) ** 2 / booksum
                )
                for io in q
            )
            - 2.0
        ) / (n - 2.0)
        delta = abs(z - previous)
        iterations += 1

    if delta > SOLVER_TOL:
        raise RuntimeError("Shin solver did not converge")
    if not (0.0 <= z < 1.0):
        raise RuntimeError(f"Shin z outside [0,1): {z}")

    p = np.asarray(
        [
            (
                math.sqrt(
                    z**2
                    + 4.0 * (1.0 - z) * float(io) ** 2 / booksum
                )
                - z
            )
            / (2.0 * (1.0 - z))
            for io in q
        ],
        dtype=float,
    )
    # The fixed-point solver is precise but normalize only within numerical
    # tolerance so scoring always consumes an exact simplex.
    p = p / p.sum()
    return _validate_probabilities(p), {
        "overround": booksum - 1.0,
        "z": float(z),
        "iterations": int(iterations),
        "delta": float(delta),
    }


TRANSFORMS = {
    "MULTIPLICATIVE": multiplicative_probabilities,
    "ADDITIVE": additive_probabilities,
    "POWER": power_probabilities,
    "SHIN": shin_probabilities,
}


def apply_method(frame: pd.DataFrame, method: str) -> tuple[np.ndarray, pd.DataFrame]:
    transform = TRANSFORMS[method]
    probabilities = np.empty((len(frame), 3), dtype=float)
    details: list[dict] = []

    for row_index, row in enumerate(frame.itertuples(index=False)):
        odds = np.asarray(
            [row.home_odds, row.draw_odds, row.away_odds],
            dtype=float,
        )
        p, meta = transform(odds)
        probabilities[row_index] = p
        details.append(meta)

    return probabilities, pd.DataFrame(details)


def actual_indices(frame: pd.DataFrame) -> np.ndarray:
    mapping = {"H": 0, "D": 1, "A": 2}
    return frame["result"].map(mapping).to_numpy(dtype=int)


def per_match_losses(frame: pd.DataFrame, probabilities: np.ndarray) -> pd.DataFrame:
    y = actual_indices(frame)
    onehot = np.eye(3)[y]
    actual_p = np.clip(probabilities[np.arange(len(y)), y], EPS, 1.0)
    return pd.DataFrame(
        {
            "logloss": -np.log(actual_p),
            "brier": np.sum((probabilities - onehot) ** 2, axis=1),
        },
        index=frame.index,
    )


def calibration_diagnostics(frame: pd.DataFrame, probabilities: np.ndarray) -> dict:
    y = actual_indices(frame)
    raw_q = 1.0 / frame[
        ["home_odds", "draw_odds", "away_odds"]
    ].to_numpy(dtype=float)
    favorite = raw_q.argmax(axis=1)
    longshot = raw_q.argmin(axis=1)
    rows = np.arange(len(frame))

    favorite_p = probabilities[rows, favorite]
    favorite_y = (y == favorite).astype(float)
    draw_p = probabilities[:, 1]
    draw_y = (y == 1).astype(float)
    longshot_p = probabilities[rows, longshot]
    longshot_y = (y == longshot).astype(float)

    return {
        "favorite_mean_probability": float(favorite_p.mean()),
        "favorite_observed_rate": float(favorite_y.mean()),
        "favorite_calibration_gap_observed_minus_predicted": float(
            favorite_y.mean() - favorite_p.mean()
        ),
        "draw_mean_probability": float(draw_p.mean()),
        "draw_observed_rate": float(draw_y.mean()),
        "draw_calibration_gap_observed_minus_predicted": float(
            draw_y.mean() - draw_p.mean()
        ),
        "longshot_mean_probability": float(longshot_p.mean()),
        "longshot_observed_rate": float(longshot_y.mean()),
        "longshot_calibration_gap_observed_minus_predicted": float(
            longshot_y.mean() - longshot_p.mean()
        ),
    }


def score_method(frame: pd.DataFrame, method: str) -> tuple[dict, pd.DataFrame]:
    p, details = apply_method(frame, method)
    losses = per_match_losses(frame, p)
    diagnostics = calibration_diagnostics(frame, p)

    parameter_summary: dict[str, float | int | None] = {
        "mean_overround": float(details["overround"].mean()),
    }
    if method == "POWER":
        parameter_summary.update(
            {
                "mean_k": float(details["k"].mean()),
                "min_k": float(details["k"].min()),
                "max_k": float(details["k"].max()),
                "max_iterations": int(details["iterations"].max()),
            }
        )
    elif method == "SHIN":
        parameter_summary.update(
            {
                "mean_z": float(details["z"].mean()),
                "min_z": float(details["z"].min()),
                "max_z": float(details["z"].max()),
                "max_iterations": int(details["iterations"].max()),
                "max_delta": float(details["delta"].max()),
            }
        )

    return {
        "matches": int(len(frame)),
        "logloss": float(losses["logloss"].mean()),
        "brier": float(losses["brier"].mean()),
        "accuracy": float(
            (p.argmax(axis=1) == actual_indices(frame)).mean()
        ),
        "calibration": diagnostics,
        "parameters": parameter_summary,
    }, losses


def evaluate_all_methods(frame: pd.DataFrame) -> tuple[dict, dict]:
    reports: dict[str, dict] = {}
    losses: dict[str, pd.DataFrame] = {}

    for method in METHODS:
        overall, method_losses = score_method(frame, method)
        by_season = {}
        for season in SEASONS:
            mask = frame["season"].eq(season).to_numpy()
            season_frame = frame.loc[mask].reset_index(drop=True)
            season_report, _ = score_method(season_frame, method)
            by_season[season] = season_report
        reports[method] = {
            "overall": overall,
            "by_season": by_season,
        }
        losses[method] = method_losses.reset_index(drop=True)

    return reports, losses


def _window_metrics(reports: dict, method: str, seasons: list[str]) -> dict:
    rows = [reports[method]["by_season"][season] for season in seasons]
    weights = np.asarray([row["matches"] for row in rows], dtype=float)
    return {
        "matches": int(weights.sum()),
        "logloss": float(
            np.average([row["logloss"] for row in rows], weights=weights)
        ),
        "brier": float(
            np.average([row["brier"] for row in rows], weights=weights)
        ),
    }


def select_discovery_method(reports: dict) -> tuple[str, dict]:
    baseline = _window_metrics(
        reports,
        "MULTIPLICATIVE",
        DISCOVERY_SEASONS,
    )
    candidates = {}

    for method in ALTERNATIVES:
        metrics = _window_metrics(reports, method, DISCOVERY_SEASONS)
        joint_wins = 0
        season_deltas = {}

        for season in DISCOVERY_SEASONS:
            base = reports["MULTIPLICATIVE"]["by_season"][season]
            candidate = reports[method]["by_season"][season]
            delta_ll = candidate["logloss"] - base["logloss"]
            delta_brier = candidate["brier"] - base["brier"]
            if delta_ll < 0.0 and delta_brier < 0.0:
                joint_wins += 1
            season_deltas[season] = {
                "logloss": float(delta_ll),
                "brier": float(delta_brier),
            }

        eligible = bool(
            metrics["logloss"] < baseline["logloss"]
            and metrics["brier"] < baseline["brier"]
            and joint_wins >= 3
        )
        candidates[method] = {
            **metrics,
            "delta_logloss_vs_multiplicative": float(
                metrics["logloss"] - baseline["logloss"]
            ),
            "delta_brier_vs_multiplicative": float(
                metrics["brier"] - baseline["brier"]
            ),
            "joint_season_wins": int(joint_wins),
            "eligible": eligible,
            "season_deltas": season_deltas,
        }

    eligible_methods = [
        method for method in ALTERNATIVES
        if candidates[method]["eligible"]
    ]

    if not eligible_methods:
        selected = "MULTIPLICATIVE"
    else:
        selected = min(
            eligible_methods,
            key=lambda method: (
                candidates[method]["logloss"],
                candidates[method]["brier"],
                method,
            ),
        )

    return selected, {
        "baseline": baseline,
        "alternatives": candidates,
    }


def bootstrap_delta(
    candidate_losses: pd.DataFrame,
    baseline_losses: pd.DataFrame,
    key: str,
) -> dict:
    delta = (
        candidate_losses[key].to_numpy(dtype=float)
        - baseline_losses[key].to_numpy(dtype=float)
    )
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    n = len(delta)
    means = np.empty(BOOTSTRAP_SAMPLES, dtype=float)

    for index in range(BOOTSTRAP_SAMPLES):
        sample = rng.integers(0, n, size=n)
        means[index] = float(delta[sample].mean())

    return {
        "mean_delta_candidate_minus_baseline": float(delta.mean()),
        "ci95_low": float(np.quantile(means, 0.025)),
        "ci95_high": float(np.quantile(means, 0.975)),
        "bootstrap_probability_candidate_better": float((means < 0.0).mean()),
        "samples": BOOTSTRAP_SAMPLES,
        "seed": BOOTSTRAP_SEED,
    }


def evaluate(frame: pd.DataFrame) -> dict:
    reports, losses = evaluate_all_methods(frame)
    selected, discovery = select_discovery_method(reports)

    base_val = reports["MULTIPLICATIVE"]["by_season"][VALIDATION_SEASON]
    candidate_val = reports[selected]["by_season"][VALIDATION_SEASON]
    validation_pass = bool(
        selected != "MULTIPLICATIVE"
        and candidate_val["logloss"] < base_val["logloss"]
        and candidate_val["brier"] < base_val["brier"]
    )

    base_test = reports["MULTIPLICATIVE"]["by_season"][TEST_SEASON]
    candidate_test = reports[selected]["by_season"][TEST_SEASON]
    test_pass = bool(
        selected != "MULTIPLICATIVE"
        and candidate_test["logloss"] < base_test["logloss"]
        and candidate_test["brier"] < base_test["brier"]
    )

    bootstrap = {
        key: bootstrap_delta(
            losses[selected],
            losses["MULTIPLICATIVE"],
            key,
        )
        for key in ("logloss", "brier")
    }

    alternative_bootstrap = {
        method: {
            key: bootstrap_delta(
                losses[method],
                losses["MULTIPLICATIVE"],
                key,
            )
            for key in ("logloss", "brier")
        }
        for method in ALTERNATIVES
    }

    overall_deltas = {
        method: {
            "logloss": float(
                reports[method]["overall"]["logloss"]
                - reports["MULTIPLICATIVE"]["overall"]["logloss"]
            ),
            "brier": float(
                reports[method]["overall"]["brier"]
                - reports["MULTIPLICATIVE"]["overall"]["brier"]
            ),
        }
        for method in ALTERNATIVES
    }

    robust_support = bool(
        selected != "MULTIPLICATIVE"
        and validation_pass
        and test_pass
        and bootstrap["logloss"]["ci95_high"] < 0.0
        and bootstrap["brier"]["ci95_high"] < 0.0
    )

    return {
        "discovery_seasons": DISCOVERY_SEASONS,
        "validation_season": VALIDATION_SEASON,
        "test_season": TEST_SEASON,
        "selected_on_discovery": selected,
        "discovery": discovery,
        "validation": {
            "baseline": {
                "logloss": base_val["logloss"],
                "brier": base_val["brier"],
            },
            "candidate": {
                "logloss": candidate_val["logloss"],
                "brier": candidate_val["brier"],
            },
            "delta_candidate_minus_baseline": {
                "logloss": candidate_val["logloss"] - base_val["logloss"],
                "brier": candidate_val["brier"] - base_val["brier"],
            },
            "passed": validation_pass,
        },
        "test": {
            "baseline": {
                "logloss": base_test["logloss"],
                "brier": base_test["brier"],
            },
            "candidate": {
                "logloss": candidate_test["logloss"],
                "brier": candidate_test["brier"],
            },
            "delta_candidate_minus_baseline": {
                "logloss": candidate_test["logloss"] - base_test["logloss"],
                "brier": candidate_test["brier"] - base_test["brier"],
            },
            "passed": test_pass,
        },
        "paired_bootstrap_all_2660": bootstrap,
        "alternative_bootstrap_all_2660": alternative_bootstrap,
        "overall_deltas_vs_multiplicative": overall_deltas,
        "all_methods": reports,
        "robust_support": robust_support,
        "interpretation": (
            "ROBUST_DEVIG_SUPPORT"
            if robust_support
            else "KEEP_MULTIPLICATIVE"
        ),
        "active_method": selected if robust_support else "MULTIPLICATIVE",
    }


def main() -> int:
    frame = load_market_history()
    result = evaluate(frame)

    report = {
        "experiment_id": EXPERIMENT_ID,
        "evidence_class": "HISTORICAL_TEMPORAL_HOLDOUT",
        "research_only": True,
        "production_promotion": False,
        "supabase_writes": False,
        "odds_api_calls": False,
        "candidate_artifact_saved": False,
        "source": "live Supabase public.matches; Football-Data AvgH/AvgD/AvgA",
        "source_rows": int(len(frame)),
        "seasons": SEASONS,
        "methods": list(METHODS),
        "baseline_method": "MULTIPLICATIVE",
        "result": result,
        "package_versions": {
            "pandas": pd.__version__,
            "numpy": np.__version__,
        },
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(json.dumps(report, indent=2, ensure_ascii=False))
    print("Research only; no production state changed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
