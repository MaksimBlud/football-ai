"""Market-anchored Over/Under 2.5 residual candidate, research only.

The standard (non-closing) Football-Data O/U 2.5 market is the mandatory prior.
Fixed football-only goal/corner state may add a bounded logit residual, but the
active candidate fails closed to the exact de-vigged market unless untouched
2025-2026 temporal OOT improves both Brier and LogLoss.

No production model artifact, Supabase row, paid provider, bet, or stake is read,
written, trained, promoted, or activated by this module.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from scipy.optimize import minimize
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

from historical_football_signal_lab import build_point_in_time_features
from historical_football_signal_runner import BASE, LEAGUES

EXPERIMENT_ID = "MARKET_ANCHOR_OU25_V1"
TRAIN_SEASONS = tuple(f"{y}-{y+1}" for y in range(2016, 2024))
VALIDATION_SEASON = "2024-2025"
TEST_SEASON = "2025-2026"
LATEST_ALLOWED_DATE = pd.Timestamp("2026-06-30")
LAMBDA_GRID = (0.0, 0.10, 0.25, 0.50, 0.75, 1.0)
L2_PENALTY = 1.0
MIN_MARKET_COVERAGE = 0.90
EPS = 1e-12

# Deliberately excludes every closing ("C") field. Consensus standard prices are
# preferred across eras; the provider renamed BbAv to Avg from 2019/20.
MARKET_ODDS_PAIRS = (
    ("Avg>2.5", "Avg<2.5", "AVG_STANDARD"),
    ("BbAv>2.5", "BbAv<2.5", "BBAV_STANDARD"),
    ("B365>2.5", "B365<2.5", "B365_STANDARD"),
    ("P>2.5", "P<2.5", "PINNACLE_STANDARD"),
)

GOALS10 = (
    "home_goals_for_10",
    "home_goals_against_10",
    "away_goals_for_10",
    "away_goals_against_10",
    "home_goals_for_venue5",
    "home_goals_against_venue5",
    "away_goals_for_venue5",
    "away_goals_against_venue5",
)
CORNERS10 = (
    "home_corners_for_10",
    "home_corners_against_10",
    "away_corners_for_10",
    "away_corners_against_10",
    "home_corners_for_venue5",
    "home_corners_against_venue5",
    "away_corners_for_venue5",
    "away_corners_against_venue5",
)
FEATURE_VARIANTS = {
    "GOALS10": GOALS10,
    "GOALS_CORNERS10": GOALS10 + CORNERS10,
}


def _valid_probability(p: np.ndarray) -> np.ndarray:
    p = np.asarray(p, dtype=float)
    if p.ndim != 1 or len(p) == 0:
        raise ValueError("probabilities must be a non-empty vector")
    if not np.isfinite(p).all() or (p <= 0).any() or (p >= 1).any():
        raise ValueError("probabilities must be finite and strictly inside (0, 1)")
    return p


def devig_ou25_odds(over_odds: np.ndarray, under_odds: np.ndarray) -> np.ndarray:
    over = np.asarray(over_odds, dtype=float)
    under = np.asarray(under_odds, dtype=float)
    if over.shape != under.shape or over.ndim != 1 or len(over) == 0:
        raise ValueError("over/under odds must be same-length non-empty vectors")
    if not np.isfinite(over).all() or not np.isfinite(under).all():
        raise ValueError("odds must be finite")
    if (over <= 1.0).any() or (under <= 1.0).any():
        raise ValueError("decimal odds must be > 1")
    inv_over = 1.0 / over
    inv_under = 1.0 / under
    return _valid_probability(inv_over / (inv_over + inv_under))


def _extract_ou25_odds(row: pd.Series) -> tuple[float, float, str | None]:
    for over_col, under_col, source in MARKET_ODDS_PAIRS:
        if over_col not in row.index or under_col not in row.index:
            continue
        over = pd.to_numeric(pd.Series([row[over_col]]), errors="coerce").iloc[0]
        under = pd.to_numeric(pd.Series([row[under_col]]), errors="coerce").iloc[0]
        if pd.notna(over) and pd.notna(under) and float(over) > 1.0 and float(under) > 1.0:
            return float(over), float(under), source
    return np.nan, np.nan, None


def _sigmoid(z: np.ndarray) -> np.ndarray:
    z = np.clip(np.asarray(z, dtype=float), -40.0, 40.0)
    return 1.0 / (1.0 + np.exp(-z))


def market_anchored_probability(market_over: np.ndarray, residual_logit: np.ndarray, lam: float) -> np.ndarray:
    market = _valid_probability(market_over)
    residual = np.asarray(residual_logit, dtype=float)
    if residual.shape != market.shape or not np.isfinite(residual).all():
        raise ValueError("residual logits must be finite and match market shape")
    if lam < 0.0 or lam > 1.0:
        raise ValueError("lambda must be in [0, 1]")
    if lam == 0.0:
        return market.copy()
    base_logit = np.log(np.clip(market, EPS, 1 - EPS) / np.clip(1 - market, EPS, 1.0))
    return _valid_probability(_sigmoid(base_logit + lam * residual))


def score_probabilities(y: np.ndarray, p: np.ndarray) -> dict[str, float]:
    y = np.asarray(y, dtype=int)
    p = _valid_probability(p)
    if y.shape != p.shape or not np.isin(y, [0, 1]).all():
        raise ValueError("binary outcomes must be 0/1 and match probabilities")
    actual = np.where(y == 1, p, 1.0 - p)
    return {
        "brier": float(np.mean((p - y) ** 2)),
        "log_loss": float(-np.mean(np.log(np.clip(actual, EPS, 1.0)))),
        "accuracy": float(((p >= 0.5).astype(int) == y).mean()),
        "over_rate": float(y.mean()),
        "mean_p_over": float(p.mean()),
    }


def dual_metric_improvement(candidate: dict[str, float], market: dict[str, float]) -> bool:
    return candidate["brier"] < market["brier"] and candidate["log_loss"] < market["log_loss"]


@dataclass
class ResidualModel:
    imputer: SimpleImputer
    scaler: StandardScaler
    weights: np.ndarray

    def residual_logit(self, X: pd.DataFrame) -> np.ndarray:
        x = self.scaler.transform(self.imputer.transform(X))
        x = np.column_stack([np.ones(len(x)), x])
        residual = x @ self.weights
        if not np.isfinite(residual).all():
            raise ValueError("non-finite residual logits")
        return residual


def fit_residual_model(
    X: pd.DataFrame,
    y: np.ndarray,
    market_over: np.ndarray,
    l2_penalty: float = L2_PENALTY,
) -> ResidualModel:
    market = _valid_probability(market_over)
    y = np.asarray(y, dtype=int)
    if y.shape != market.shape or not np.isin(y, [0, 1]).all():
        raise ValueError("binary outcomes must be 0/1 and match market")
    imputer = SimpleImputer(strategy="median")
    scaler = StandardScaler()
    x = scaler.fit_transform(imputer.fit_transform(X))
    x = np.column_stack([np.ones(len(x)), x])
    base = np.log(np.clip(market, EPS, 1 - EPS) / np.clip(1 - market, EPS, 1.0))
    d = x.shape[1]

    def objective(w: np.ndarray):
        p = _sigmoid(base + x @ w)
        nll = -float(
            np.mean(
                y * np.log(np.clip(p, EPS, 1.0))
                + (1 - y) * np.log(np.clip(1 - p, EPS, 1.0))
            )
        )
        penalty = 0.5 * l2_penalty * float(np.sum(w[1:] ** 2)) / max(1, d - 1)
        grad = x.T @ (p - y) / len(y)
        if d > 1:
            grad[1:] += (l2_penalty / max(1, d - 1)) * w[1:]
        return nll + penalty, grad

    result = minimize(
        objective,
        np.zeros(d),
        method="L-BFGS-B",
        jac=True,
        options={"maxiter": 500, "ftol": 1e-12},
    )
    if not result.success or not np.isfinite(result.x).all():
        raise RuntimeError(f"residual optimization failed: {result.message}")
    return ResidualModel(imputer, scaler, result.x)


def _raw_market_rows(raw: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in raw.iterrows():
        over_odds, under_odds, source = _extract_ou25_odds(row)
        if np.isfinite(over_odds) and np.isfinite(under_odds):
            market_over = float(devig_ou25_odds(np.array([over_odds]), np.array([under_odds]))[0])
        else:
            market_over = np.nan
        home_goals = pd.to_numeric(pd.Series([row.get("FTHG")]), errors="coerce").iloc[0]
        away_goals = pd.to_numeric(pd.Series([row.get("FTAG")]), errors="coerce").iloc[0]
        total_goals = float(home_goals + away_goals) if pd.notna(home_goals) and pd.notna(away_goals) else np.nan
        rows.append(
            {
                "match_date": pd.to_datetime(row.get("Date"), dayfirst=True, errors="coerce"),
                "home_team": row.get("HomeTeam"),
                "away_team": row.get("AwayTeam"),
                "season": row.get("_season"),
                "total_goals": total_goals,
                "over_25": float(total_goals >= 3.0) if np.isfinite(total_goals) else np.nan,
                "market_over_odds": over_odds,
                "market_under_odds": under_odds,
                "market_over_prob": market_over,
                "market_source": source,
            }
        )
    return pd.DataFrame(rows)


def download_ou25(config, league: str, raw_dir: Path) -> pd.DataFrame:
    raw_frames = []
    raw_dir.mkdir(parents=True, exist_ok=True)
    for code, season in config.historical_source.season_codes.items():
        url = BASE.format(code=code, comp=config.historical_source.competition_code)
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        path = raw_dir / f"{league.lower()}_{code}.csv"
        path.write_bytes(response.content)
        season_raw = pd.read_csv(path)
        season_raw["_season"] = season
        raw_frames.append(season_raw)
        print(f"{league} {season}: raw={len(season_raw)}")

    raw = pd.concat(raw_frames, ignore_index=True)
    features = build_point_in_time_features(raw, league, "MULTI_SEASON")
    targets = _raw_market_rows(raw).drop_duplicates(
        subset=["match_date", "home_team", "away_team", "season"], keep="last"
    )
    features = features.drop(columns=["season"]).merge(
        targets,
        on=["match_date", "home_team", "away_team"],
        how="left",
        validate="one_to_one",
    )
    if features["season"].isna().any():
        raise RuntimeError(f"{league}: failed to restore season labels")
    return features


def _allowed_frame(frame: pd.DataFrame) -> pd.DataFrame:
    allowed = set(TRAIN_SEASONS) | {VALIDATION_SEASON, TEST_SEASON}
    out = frame.copy()
    out = out[out["season"].isin(allowed)]
    out = out[out["match_date"] <= LATEST_ALLOWED_DATE]
    out = out[out["over_25"].isin([0.0, 1.0])]
    return out.sort_values(["match_date", "league"], kind="stable").reset_index(drop=True)


def source_coverage(frame: pd.DataFrame) -> list[dict]:
    rows = []
    allowed = _allowed_frame(frame)
    for (league, season), group in allowed.groupby(["league", "season"], sort=True):
        available = group["market_over_prob"].notna()
        counts = group.loc[available, "market_source"].value_counts().sort_index()
        rows.append(
            {
                "league": league,
                "season": season,
                "rows": int(len(group)),
                "market_rows": int(available.sum()),
                "coverage": float(available.mean()) if len(group) else 0.0,
                "source_counts": {str(k): int(v) for k, v in counts.items()},
            }
        )
    return rows


def _prepare(frame: pd.DataFrame) -> pd.DataFrame:
    out = _allowed_frame(frame)
    out = out.dropna(subset=["market_over_prob"])
    out["over_25"] = out["over_25"].astype(int)
    return out.reset_index(drop=True)


def _choose_on_validation(train: pd.DataFrame, val: pd.DataFrame):
    y_train = train["over_25"].to_numpy(int)
    y_val = val["over_25"].to_numpy(int)
    market_train = _valid_probability(train["market_over_prob"].to_numpy(float))
    market_val = _valid_probability(val["market_over_prob"].to_numpy(float))
    market_score = score_probabilities(y_val, market_val)
    choices = []
    fitted: dict[str, ResidualModel] = {}
    for variant, columns in FEATURE_VARIANTS.items():
        model = fit_residual_model(train[list(columns)], y_train, market_train)
        fitted[variant] = model
        residual = model.residual_logit(val[list(columns)])
        for lam in LAMBDA_GRID:
            score = score_probabilities(
                y_val,
                market_anchored_probability(market_val, residual, lam),
            )
            choices.append({"feature_variant": variant, "lambda": float(lam), **score})
    admissible = [c for c in choices if c["lambda"] > 0 and dual_metric_improvement(c, market_score)]
    if not admissible:
        return {"feature_variant": "MARKET", "lambda": 0.0, **market_score}, choices, None
    selected = min(
        admissible,
        key=lambda c: (c["log_loss"], c["brier"], c["lambda"], c["feature_variant"]),
    )
    return selected, choices, fitted[selected["feature_variant"]]


def evaluate_frame(frame: pd.DataFrame) -> dict:
    coverage = source_coverage(frame)
    insufficient = [
        row for row in coverage if row["coverage"] < MIN_MARKET_COVERAGE
    ]
    if insufficient:
        raise RuntimeError(f"O/U 2.5 market coverage below {MIN_MARKET_COVERAGE:.0%}: {insufficient}")

    prepared = _prepare(frame)
    league_reports = []
    pooled_y, pooled_market, pooled_candidate = [], [], []
    for league, group in prepared.groupby("league", sort=True):
        train = group[group["season"].isin(TRAIN_SEASONS)].copy()
        val = group[group["season"] == VALIDATION_SEASON].copy()
        test = group[group["season"] == TEST_SEASON].copy()
        if min(len(train), len(val), len(test)) == 0:
            raise RuntimeError(f"{league}: incomplete train/validation/test seasons")

        selected, choices, model = _choose_on_validation(train, val)
        y_test = test["over_25"].to_numpy(int)
        market_test = _valid_probability(test["market_over_prob"].to_numpy(float))
        if selected["lambda"] == 0.0:
            candidate = market_test.copy()
        else:
            columns = list(FEATURE_VARIANTS[selected["feature_variant"]])
            candidate = market_anchored_probability(
                market_test,
                model.residual_logit(test[columns]),
                float(selected["lambda"]),
            )

        market_score = score_probabilities(y_test, market_test)
        candidate_score = score_probabilities(y_test, candidate)
        y_val = val["over_25"].to_numpy(int)
        market_val = _valid_probability(val["market_over_prob"].to_numpy(float))
        league_reports.append(
            {
                "league": league,
                "train_n": int(len(train)),
                "validation_n": int(len(val)),
                "test_n": int(len(test)),
                "selected_feature_variant": selected["feature_variant"],
                "selected_lambda": float(selected["lambda"]),
                "validation_market": score_probabilities(y_val, market_val),
                "validation_selected": {
                    key: selected[key]
                    for key in ("brier", "log_loss", "accuracy", "over_rate", "mean_p_over")
                },
                "test_market": market_score,
                "test_residual_candidate": candidate_score,
                "test_delta_brier": candidate_score["brier"] - market_score["brier"],
                "test_delta_log_loss": candidate_score["log_loss"] - market_score["log_loss"],
                "validation_candidates_evaluated": int(len(choices)),
            }
        )
        pooled_y.append(y_test)
        pooled_market.append(market_test)
        pooled_candidate.append(candidate)

    y = np.concatenate(pooled_y)
    market = np.concatenate(pooled_market)
    candidate = np.concatenate(pooled_candidate)
    market_score = score_probabilities(y, market)
    residual_score = score_probabilities(y, candidate)
    accepted = dual_metric_improvement(residual_score, market_score)
    active = candidate if accepted else market
    active_score = score_probabilities(y, active)
    return {
        "experiment_id": EXPERIMENT_ID,
        "evidence_class": "HISTORICAL_TEMPORAL_OOT",
        "research_only": True,
        "production_promotion": False,
        "market": "OVER_UNDER_2_5",
        "market_price_family": "STANDARD_NON_CLOSING",
        "market_odds_priority": [source for _, _, source in MARKET_ODDS_PAIRS],
        "min_market_coverage": MIN_MARKET_COVERAGE,
        "source_coverage": coverage,
        "train_seasons": list(TRAIN_SEASONS),
        "validation_season": VALIDATION_SEASON,
        "untouched_test_season": TEST_SEASON,
        "opened_2026_09_outcomes_used": False,
        "feature_variants": list(FEATURE_VARIANTS),
        "lambda_grid": list(LAMBDA_GRID),
        "l2_penalty": L2_PENALTY,
        "test_n": int(len(y)),
        "market_test": market_score,
        "residual_candidate_test": residual_score,
        "residual_delta_brier": residual_score["brier"] - market_score["brier"],
        "residual_delta_log_loss": residual_score["log_loss"] - market_score["log_loss"],
        "residual_accepted": bool(accepted),
        "active_mode": "RESIDUAL" if accepted else "MARKET_FALLBACK",
        "active_test": active_score,
        "active_delta_brier": active_score["brier"] - market_score["brier"],
        "active_delta_log_loss": active_score["log_loss"] - market_score["log_loss"],
        "acceptance_rule": "residual pooled OOT Brier < market AND residual pooled OOT LogLoss < market; otherwise exact market fallback",
        "roi_threshold_search_performed": False,
        "league_reports": league_reports,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=Path("artifacts/market_anchor_ou25_v1/work"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/market_anchor_ou25_v1/report.json"),
    )
    args = parser.parse_args()
    frames = [
        download_ou25(config, league, args.work_dir / league.lower())
        for league, config in LEAGUES.items()
    ]
    report = evaluate_frame(pd.concat(frames, ignore_index=True))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    print("RESEARCH ONLY: no production promotion, Supabase writes, paid calls, bets, or stakes.")


if __name__ == "__main__":
    main()
