"""Six-signal retrospective corner-market screen.

Research-only. Uses already-opened immutable 2026/27 corner-market cohorts plus
historical Football-Data rows for source/feature reconstruction. It does not collect
new prospective matches, does not call paid odds providers, and does not modify
production models.

Signals:
1. opening Over/Under price pressure -> later corner-centre direction;
2. opening price pressure -> actual corner-line step mechanics;
3. historical 1X2/O-U/AH match-shape model -> opening corner-centre gap -> direction;
4. historical referee corner bias -> direction;
5. last-10 corner-environment volatility -> incremental material-repricing risk;
6. existing-source capability for manager/coach/lineup/availability regime changes.
"""
from __future__ import annotations

import argparse
import io
import json
import math
import zipfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import requests
from scipy.stats import pearsonr, skew, spearmanr
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import brier_score_loss, log_loss, mean_absolute_error, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from corner_market_state_repricing_v1 import (
    devig_over_probability,
    implied_poisson_centre,
)
from cross_league_direct_markets_transport import _official_or_pinned_mirror_get
from v2b_travel_venue_identity_feasibility_v1 import _matches_target

EXPERIMENT_ID = "CORNER_SIX_SIGNAL_SCREEN_V1"
COHORT_ORDER = ("V1_55", "REP50", "V1_46", "V2B_43")
LEAGUES = ("EPL", "LA_LIGA", "SERIE_A")
COMP = {"EPL": "E0", "LA_LIGA": "SP1", "SERIE_A": "I1"}
HIST_CODES = {
    "2019-2020": "1920",
    "2020-2021": "2021",
    "2021-2022": "2122",
    "2022-2023": "2223",
    "2023-2024": "2324",
    "2024-2025": "2425",
    "2025-2026": "2526",
}
CURRENT_CODE = "2627"
MATERIAL_MOVE_THRESHOLD = 0.362835012901983
REFEREE_SHRINKAGE_K = 20.0
VOLATILITY_WINDOW = 10
LOGISTIC_C = 0.1
EPS = 1e-12

EXPECTED_ARTIFACTS = {
    "pilot": {
        "id": "10503575942",
        "sha256": "ed012ae16dc3835900e7696d572088056724990866485078fed250283b379fe0",
    },
    "backfill": {
        "id": "10506736726",
        "sha256": "b5d426ee99bb04d7b5eeae59f494cf0ba6b16aa15fe93fd28ec13e3fcdc3a441",
    },
    "rep50": {
        "id": "10551727936",
        "sha256": "ca3c0f96338cf213e1dc76dbf47e88d01f7ad551f18e83ef2c185d4bc9eb6ba3",
    },
    "v1_46": {
        "id": "10557706131",
        "sha256": "5ff43199cdf1bb73e6b87649c3e68aa57bac628c68888a06a809c5df473b8d1f",
    },
    "v2b_raw": {
        "id": "10899611444",
        "sha256": "c2f5313efad4afb8663d9980f5ea004f52fe02827a83b5c99a8b775c35498a57",
    },
    "v2b_lock": {
        "id": "10899325930",
        "sha256": "ad6bba499cc12abf5ca10732d88e0403565e2582e6c6c8a642ca7bb81248726f",
    },
    "v2b_eval": {
        "id": "10899842049",
        "sha256": "7d4ecad191518cc551567ad1513b5f6c53121d56154a6de86b51b99d54f078ff",
    },
}

MARKET_FEATURES = (
    "p_home",
    "p_draw",
    "p_away",
    "p_over25",
    "ah_line",
    "p_ah_home",
)


def _find_member(zf: zipfile.ZipFile, suffix: str) -> str:
    matches = [name for name in zf.namelist() if name.endswith(suffix)]
    if len(matches) != 1:
        raise RuntimeError(f"expected one member ending {suffix!r}, found {len(matches)}")
    return matches[0]


def _read_json_member(zf: zipfile.ZipFile, suffix: str) -> Any:
    return json.loads(zf.read(_find_member(zf, suffix)))


def _flatten_selected(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        raise RuntimeError("selected fixture payload must be an object")
    rows: list[dict[str, Any]] = []
    for league, values in payload.items():
        if not isinstance(values, list):
            continue
        for raw in values:
            if not isinstance(raw, dict):
                continue
            row = dict(raw)
            row.setdefault("league", league)
            rows.append(row)
    return rows


def _raw_corner_row(payload: dict[str, Any]) -> dict[str, Any]:
    data = payload.get("data")
    if not isinstance(data, dict):
        raise RuntimeError("corner payload missing data")
    books = data.get("bookmakers")
    if not isinstance(books, list):
        raise RuntimeError("corner payload missing bookmakers")
    candidates = [
        row for row in books
        if isinstance(row, dict)
        and (
            str(row.get("slug") or "").lower() == "bet365"
            or "365" in str(row.get("name") or "").lower()
        )
    ]
    if len(candidates) != 1:
        raise RuntimeError("expected exactly one Bet365 row")
    market = ((candidates[0].get("odds") or {}).get("corner_line"))
    if not isinstance(market, dict):
        raise RuntimeError("missing corner_line")
    opening = market.get("opening")
    closing = market.get("closing")
    if not isinstance(opening, dict) or not isinstance(closing, dict):
        raise RuntimeError("missing opening/closing corner state")
    values = {
        "fixture_id": str(data.get("fixture_id")),
        "opening_line": float(opening["line"]),
        "opening_over": float(opening["over"]),
        "opening_under": float(opening["under"]),
        "closing_line": float(closing["line"]),
        "closing_over": float(closing["over"]),
        "closing_under": float(closing["under"]),
    }
    return values


def _metadata_row(raw: dict[str, Any], league: str | None = None) -> dict[str, Any]:
    return {
        "fixture_id": str(raw.get("fixture_id")),
        "league": str(raw.get("league") or league or ""),
        "kickoff_utc": str(raw.get("kickoff_utc") or ""),
        "home_team": str(
            raw.get("home_team")
            or raw.get("provider_home_team")
            or raw.get("HomeTeam")
            or ""
        ),
        "away_team": str(
            raw.get("away_team")
            or raw.get("provider_away_team")
            or raw.get("AwayTeam")
            or ""
        ),
    }


def _load_raw_cohort(
    *,
    zip_path: Path,
    cohort: str,
) -> list[dict[str, Any]]:
    with zipfile.ZipFile(zip_path) as zf:
        selected = _flatten_selected(_read_json_member(zf, "selected_fixtures.json"))
        metadata = {
            str(row["fixture_id"]): _metadata_row(row)
            for row in selected
            if row.get("fixture_id") is not None
        }
        rows: list[dict[str, Any]] = []
        for name in zf.namelist():
            if "/raw/odds/" not in f"/{name}" or not name.endswith(".json"):
                continue
            raw = _raw_corner_row(json.loads(zf.read(name)))
            meta = metadata.get(raw["fixture_id"])
            if meta is None:
                raise RuntimeError(f"{cohort}: no metadata for {raw['fixture_id']}")
            rows.append({**meta, **raw, "cohort": cohort})
    return rows


def _load_v2b(raw_zip: Path, lock_zip: Path) -> list[dict[str, Any]]:
    with zipfile.ZipFile(lock_zip) as zf:
        lock = _read_json_member(zf, "cohort_lock.json")
        metadata_rows = _read_json_member(zf, "future_fixture_metadata.json")
    if not isinstance(lock, dict) or not isinstance(metadata_rows, list):
        raise RuntimeError("invalid V2B lock")
    selected_ids = {
        str(fid)
        for block in lock.get("selected_blocks") or []
        for fid in block.get("fixture_ids") or []
    }
    if len(selected_ids) != 43:
        raise RuntimeError("unexpected V2B selected fixture count")
    metadata = {
        str(row["fixture_id"]): _metadata_row(row)
        for row in metadata_rows
        if isinstance(row, dict) and str(row.get("fixture_id")) in selected_ids
    }
    if len(metadata) != 43:
        raise RuntimeError("V2B metadata coverage mismatch")

    rows: list[dict[str, Any]] = []
    with zipfile.ZipFile(raw_zip) as zf:
        for name in zf.namelist():
            if not name.startswith("raw/odds/") or not name.endswith(".json"):
                continue
            raw = _raw_corner_row(json.loads(zf.read(name)))
            meta = metadata.get(raw["fixture_id"])
            if meta is None:
                raise RuntimeError(f"V2B no metadata for {raw['fixture_id']}")
            rows.append({**meta, **raw, "cohort": "V2B_43"})
    if len(rows) != 43:
        raise RuntimeError(f"expected 43 V2B raw rows, got {len(rows)}")
    return rows


def load_corner_rows(
    pilot_zip: Path,
    backfill_zip: Path,
    rep50_zip: Path,
    v1_zip: Path,
    v2b_raw_zip: Path,
    v2b_lock_zip: Path,
) -> pd.DataFrame:
    rows = []
    rows.extend(_load_raw_cohort(zip_path=pilot_zip, cohort="V1_55"))
    rows.extend(_load_raw_cohort(zip_path=backfill_zip, cohort="V1_55"))
    rows.extend(_load_raw_cohort(zip_path=rep50_zip, cohort="REP50"))
    rows.extend(_load_raw_cohort(zip_path=v1_zip, cohort="V1_46"))
    rows.extend(_load_v2b(v2b_raw_zip, v2b_lock_zip))
    frame = pd.DataFrame(rows)
    if len(frame) != 194 or frame["fixture_id"].nunique() != 194:
        raise RuntimeError(
            f"expected 194 unique corner rows, got rows={len(frame)} unique={frame['fixture_id'].nunique()}"
        )
    expected = {"V1_55": 55, "REP50": 50, "V1_46": 46, "V2B_43": 43}
    actual = frame.groupby("cohort").size().to_dict()
    if actual != expected:
        raise RuntimeError(f"corner cohort counts changed: {actual}")

    frame["opening_p_over"] = [
        devig_over_probability(o, u)
        for o, u in zip(frame["opening_over"], frame["opening_under"])
    ]
    frame["opening_price_pressure"] = frame["opening_p_over"] - 0.5
    frame["opening_lambda"] = [
        implied_poisson_centre(line, over, under)
        for line, over, under in zip(
            frame["opening_line"], frame["opening_over"], frame["opening_under"]
        )
    ]
    frame["closing_lambda"] = [
        implied_poisson_centre(line, over, under)
        for line, over, under in zip(
            frame["closing_line"], frame["closing_over"], frame["closing_under"]
        )
    ]
    frame["centre_delta"] = frame["closing_lambda"] - frame["opening_lambda"]
    frame["movement_magnitude"] = frame["centre_delta"].abs()
    frame["line_delta"] = frame["closing_line"] - frame["opening_line"]
    frame["material_move"] = (
        frame["movement_magnitude"] >= MATERIAL_MOVE_THRESHOLD
    ).astype(int)
    frame["match_date"] = pd.to_datetime(
        frame["kickoff_utc"], utc=True, errors="raise"
    ).dt.tz_convert(None).dt.normalize()
    return frame.sort_values(["cohort", "league", "match_date", "fixture_id"]).reset_index(drop=True)


def _safe_corr(x: pd.Series, y: pd.Series, method: str) -> float | None:
    local = pd.DataFrame({"x": x, "y": y}).dropna()
    if len(local) < 3 or local["x"].nunique() < 2 or local["y"].nunique() < 2:
        return None
    if method == "pearson":
        value = pearsonr(local["x"].astype(float), local["y"].astype(float)).statistic
    else:
        value = spearmanr(local["x"].astype(float), local["y"].astype(float)).statistic
    return float(value) if np.isfinite(value) else None


def _direction_metrics(
    frame: pd.DataFrame,
    *,
    score_col: str,
    target_col: str,
) -> dict[str, Any]:
    local = frame[[score_col, target_col]].dropna().copy()
    local = local[(local[score_col] != 0) & (local[target_col] != 0)]
    if local.empty:
        return {
            "rows": 0,
            "actual_up": 0,
            "actual_down": 0,
            "accuracy": None,
            "majority_direction_accuracy": None,
            "excess_vs_majority": None,
            "recall_up": None,
            "recall_down": None,
            "balanced_accuracy": None,
            "pearson": None,
            "spearman": None,
        }
    actual = np.sign(local[target_col].astype(float).to_numpy())
    pred = np.sign(local[score_col].astype(float).to_numpy())
    up = actual > 0
    down = actual < 0
    accuracy = float((actual == pred).mean())
    recall_up = float((pred[up] > 0).mean()) if up.any() else None
    recall_down = float((pred[down] < 0).mean()) if down.any() else None
    balanced = (
        float((recall_up + recall_down) / 2.0)
        if recall_up is not None and recall_down is not None
        else None
    )
    majority = float(max(int(up.sum()), int(down.sum())) / len(local))
    return {
        "rows": int(len(local)),
        "actual_up": int(up.sum()),
        "actual_down": int(down.sum()),
        "accuracy": accuracy,
        "majority_direction_accuracy": majority,
        "excess_vs_majority": accuracy - majority,
        "recall_up": recall_up,
        "recall_down": recall_down,
        "balanced_accuracy": balanced,
        "pearson": _safe_corr(local[score_col], local[target_col], "pearson"),
        "spearman": _safe_corr(local[score_col], local[target_col], "spearman"),
    }


def signal_1_opening_price_pressure(corner: pd.DataFrame) -> dict[str, Any]:
    pooled = _direction_metrics(
        corner,
        score_col="opening_price_pressure",
        target_col="centre_delta",
    )
    by_cohort = {
        cohort: _direction_metrics(
            group,
            score_col="opening_price_pressure",
            target_col="centre_delta",
        )
        for cohort, group in corner.groupby("cohort")
    }
    positive_spearman = sum(
        1
        for result in by_cohort.values()
        if result["spearman"] is not None and result["spearman"] > 0
    )
    supported = bool(
        pooled["balanced_accuracy"] is not None
        and pooled["balanced_accuracy"] >= 0.55
        and pooled["spearman"] is not None
        and pooled["spearman"] > 0
        and positive_spearman >= 3
    )
    return {
        "signal_id": "OPENING_PRICE_PRESSURE_DIRECTION_V1",
        "definition": "devigged opening Over probability minus 0.50",
        "rows_total": int(len(corner)),
        "pooled": pooled,
        "by_cohort": by_cohort,
        "positive_spearman_cohorts": int(positive_spearman),
        "support_gate": {
            "pooled_balanced_accuracy_min": 0.55,
            "pooled_spearman_positive": True,
            "positive_spearman_cohorts_min": 3,
        },
        "supported": supported,
        "verdict": (
            "PROMISING_OPENING_PRICE_PRESSURE_DIRECTION_SIGNAL"
            if supported
            else "NO_PORTABLE_OPENING_PRICE_PRESSURE_DIRECTION_SIGNAL"
        ),
    }


def _line_move_auc(group: pd.DataFrame) -> dict[str, Any]:
    target = (group["line_delta"].astype(float) != 0).astype(int)
    score = group["opening_price_pressure"].abs().astype(float)
    auc = None
    if target.nunique() == 2:
        auc = float(roc_auc_score(target, score))
    return {
        "rows": int(len(group)),
        "line_moves": int(target.sum()),
        "auc_abs_pressure_for_any_line_move": auc,
        "mean_abs_pressure_line_move": (
            float(score[target == 1].mean()) if int(target.sum()) else None
        ),
        "mean_abs_pressure_no_line_move": (
            float(score[target == 0].mean()) if int((target == 0).sum()) else None
        ),
    }


def signal_2_line_transition(corner: pd.DataFrame) -> dict[str, Any]:
    pooled_direction = _direction_metrics(
        corner,
        score_col="opening_price_pressure",
        target_col="line_delta",
    )
    pooled_move = _line_move_auc(corner)
    by_cohort = {}
    auc_positive = 0
    direction_positive = 0
    for cohort, group in corner.groupby("cohort"):
        direction = _direction_metrics(
            group,
            score_col="opening_price_pressure",
            target_col="line_delta",
        )
        move = _line_move_auc(group)
        by_cohort[cohort] = {"direction": direction, "move_hazard": move}
        if (
            move["auc_abs_pressure_for_any_line_move"] is not None
            and move["auc_abs_pressure_for_any_line_move"] > 0.5
        ):
            auc_positive += 1
        if (
            direction["balanced_accuracy"] is not None
            and direction["balanced_accuracy"] > 0.5
        ):
            direction_positive += 1

    supported = bool(
        pooled_move["auc_abs_pressure_for_any_line_move"] is not None
        and pooled_move["auc_abs_pressure_for_any_line_move"] >= 0.55
        and pooled_direction["balanced_accuracy"] is not None
        and pooled_direction["balanced_accuracy"] >= 0.55
        and auc_positive >= 3
        and direction_positive >= 3
    )
    return {
        "signal_id": "OPENING_PRESSURE_LINE_TRANSITION_V1",
        "definition": "opening price-pressure magnitude for move hazard; sign for line-step direction",
        "pooled_direction": pooled_direction,
        "pooled_move_hazard": pooled_move,
        "by_cohort": by_cohort,
        "cohorts_auc_above_half": int(auc_positive),
        "cohorts_balanced_accuracy_above_half": int(direction_positive),
        "supported": supported,
        "verdict": (
            "PROMISING_LINE_TRANSITION_MECHANICS_SIGNAL"
            if supported
            else "NO_LINE_TRANSITION_MECHANICS_SIGNAL"
        ),
    }


def _get_csv(url: str, *, historical: bool) -> pd.DataFrame:
    if historical:
        response = _official_or_pinned_mirror_get(url, timeout=60)
    else:
        last_error: Exception | None = None
        response = None
        for _ in range(3):
            try:
                response = requests.get(
                    url,
                    timeout=60,
                    headers={"User-Agent": "football-ai-six-signal-screen/1.0"},
                )
                response.raise_for_status()
                break
            except Exception as exc:
                last_error = exc
                response = None
        if response is None:
            raise RuntimeError(f"current Football-Data source failed: {last_error}")
    return pd.read_csv(io.BytesIO(response.content))


def download_football_data() -> dict[str, pd.DataFrame]:
    result: dict[str, pd.DataFrame] = {}
    for league in LEAGUES:
        frames = []
        comp = COMP[league]
        for season, code in HIST_CODES.items():
            url = f"https://www.football-data.co.uk/mmz4281/{code}/{comp}.csv"
            frame = _get_csv(url, historical=True)
            frame["season"] = season
            frames.append(frame)
        current_url = (
            f"https://www.football-data.co.uk/mmz4281/{CURRENT_CODE}/{comp}.csv"
        )
        current = _get_csv(current_url, historical=False)
        current["season"] = "2026-2027"
        frames.append(current)
        combined = pd.concat(frames, ignore_index=True)
        combined["match_date"] = pd.to_datetime(
            combined.get("Date"), dayfirst=True, errors="coerce"
        ).dt.normalize()
        result[league] = combined.sort_values(
            ["match_date", "HomeTeam", "AwayTeam"], kind="stable"
        ).reset_index(drop=True)
    return result


def _three_way_probs(row: pd.Series) -> tuple[float, float, float] | None:
    values = []
    for col in ("B365H", "B365D", "B365A"):
        try:
            value = float(row.get(col))
        except (TypeError, ValueError):
            return None
        if not math.isfinite(value) or value <= 1.0:
            return None
        values.append(1.0 / value)
    total = sum(values)
    return tuple(value / total for value in values)


def _binary_prob(row: pd.Series, over_col: str, under_col: str) -> float | None:
    try:
        over = float(row.get(over_col))
        under = float(row.get(under_col))
    except (TypeError, ValueError):
        return None
    if not (math.isfinite(over) and math.isfinite(under)):
        return None
    if over <= 1.0 or under <= 1.0:
        return None
    oi, ui = 1.0 / over, 1.0 / under
    return oi / (oi + ui)


def _first_finite(row: pd.Series, columns: tuple[str, ...]) -> float | None:
    for column in columns:
        try:
            value = float(row.get(column))
        except (TypeError, ValueError):
            continue
        if math.isfinite(value):
            return value
    return None


def _market_feature_row(row: pd.Series) -> dict[str, float] | None:
    one_x_two = _three_way_probs(row)
    over25 = _binary_prob(row, "B365>2.5", "B365<2.5")
    if one_x_two is None or over25 is None:
        return None
    ah_line = _first_finite(row, ("AHh", "B365AH"))
    ah_home = _binary_prob(row, "B365AHH", "B365AHA")
    return {
        "p_home": float(one_x_two[0]),
        "p_draw": float(one_x_two[1]),
        "p_away": float(one_x_two[2]),
        "p_over25": float(over25),
        "ah_line": float(ah_line) if ah_line is not None else np.nan,
        "p_ah_home": float(ah_home) if ah_home is not None else np.nan,
    }


def _historical_market_training_rows(
    raw: pd.DataFrame,
    *,
    allowed_seasons: set[str],
) -> pd.DataFrame:
    rows = []
    for _, row in raw.iterrows():
        season = str(row.get("season"))
        if season not in allowed_seasons:
            continue
        features = _market_feature_row(row)
        if features is None:
            continue
        try:
            hc = float(row.get("HC"))
            ac = float(row.get("AC"))
        except (TypeError, ValueError):
            continue
        if not (math.isfinite(hc) and math.isfinite(ac) and hc >= 0 and ac >= 0):
            continue
        rows.append(
            {
                "season": season,
                "match_date": row.get("match_date"),
                "total_corners": hc + ac,
                **features,
            }
        )
    return pd.DataFrame(rows)


def _ridge_model() -> Pipeline:
    return Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
            ("ridge", Ridge(alpha=1.0)),
        ]
    )


def _join_current_row(
    fixture: pd.Series,
    current: pd.DataFrame,
) -> pd.Series | None:
    date_value = pd.Timestamp(fixture["match_date"]).normalize()
    candidates = current[current["match_date"] == date_value]
    exact = []
    for _, row in candidates.iterrows():
        if _matches_target(str(fixture["home_team"]), row.get("HomeTeam")) and _matches_target(
            str(fixture["away_team"]), row.get("AwayTeam")
        ):
            exact.append(row)
    if len(exact) == 1:
        return exact[0]
    if len(exact) > 1:
        raise RuntimeError(
            f"ambiguous current Football-Data identity: {fixture['home_team']} vs {fixture['away_team']}"
        )
    return None


def _direction_by_cohort(
    frame: pd.DataFrame,
    score_col: str,
) -> dict[str, Any]:
    return {
        cohort: _direction_metrics(
            group,
            score_col=score_col,
            target_col="centre_delta",
        )
        for cohort, group in frame.groupby("cohort")
    }


def signal_3_cross_market_shape(
    corner: pd.DataFrame,
    football_data: dict[str, pd.DataFrame],
) -> tuple[dict[str, Any], pd.DataFrame]:
    validation = {}
    models = {}
    training_counts = {}
    for league in LEAGUES:
        raw = football_data[league]
        train = _historical_market_training_rows(
            raw,
            allowed_seasons=set(HIST_CODES) - {"2025-2026"},
        )
        valid = _historical_market_training_rows(
            raw,
            allowed_seasons={"2025-2026"},
        )
        if len(train) < 200 or len(valid) < 50:
            validation[league] = {
                "status": "INSUFFICIENT_HISTORICAL_MARKET_ROWS",
                "train_rows": int(len(train)),
                "validation_rows": int(len(valid)),
            }
            continue
        model = _ridge_model()
        model.fit(train[list(MARKET_FEATURES)], train["total_corners"])
        pred = model.predict(valid[list(MARKET_FEATURES)])
        baseline = np.full(len(valid), float(train["total_corners"].mean()))
        mae_model = float(mean_absolute_error(valid["total_corners"], pred))
        mae_baseline = float(mean_absolute_error(valid["total_corners"], baseline))
        validation[league] = {
            "status": "OK",
            "train_rows": int(len(train)),
            "validation_rows": int(len(valid)),
            "mae_match_shape_model": mae_model,
            "mae_league_mean_baseline": mae_baseline,
            "delta_mae": mae_model - mae_baseline,
            "mae_win": bool(mae_model < mae_baseline),
        }

        full = _historical_market_training_rows(
            raw,
            allowed_seasons=set(HIST_CODES),
        )
        full_model = _ridge_model()
        full_model.fit(full[list(MARKET_FEATURES)], full["total_corners"])
        models[league] = full_model
        training_counts[league] = int(len(full))

    valid_leagues = [
        league
        for league, result in validation.items()
        if result.get("status") == "OK"
    ]
    historical_wins = sum(
        int(validation[league]["mae_win"]) for league in valid_leagues
    )
    historical_model_supported = bool(
        len(valid_leagues) == 3 and historical_wins >= 2
    )

    rows = []
    target_corner = corner[corner["league"].isin(LEAGUES)].copy()
    for _, fixture in target_corner.iterrows():
        raw = football_data[str(fixture["league"])]
        current = raw[raw["season"].astype(str) == "2026-2027"]
        source_row = _join_current_row(fixture, current)
        if source_row is None:
            continue
        features = _market_feature_row(source_row)
        if features is None or str(fixture["league"]) not in models:
            continue
        feature_frame = pd.DataFrame([features], columns=MARKET_FEATURES)
        predicted = float(models[str(fixture["league"])].predict(feature_frame)[0])
        rows.append(
            {
                **fixture.to_dict(),
                "match_shape_expected_corners": predicted,
                "match_shape_gap": predicted - float(fixture["opening_lambda"]),
            }
        )
    joined = pd.DataFrame(rows)
    pooled = (
        _direction_metrics(joined, score_col="match_shape_gap", target_col="centre_delta")
        if not joined.empty
        else {}
    )
    by_cohort = _direction_by_cohort(joined, "match_shape_gap") if not joined.empty else {}
    positive_cohorts = sum(
        1
        for result in by_cohort.values()
        if result["spearman"] is not None and result["spearman"] > 0
    )
    direction_supported = bool(
        pooled
        and pooled.get("balanced_accuracy") is not None
        and pooled["balanced_accuracy"] >= 0.55
        and pooled.get("spearman") is not None
        and pooled["spearman"] > 0
        and positive_cohorts >= 3
    )
    supported = bool(historical_model_supported and direction_supported)
    return {
        "signal_id": "CROSS_MARKET_MATCH_SHAPE_CORNER_GAP_V1",
        "historical_validation": validation,
        "historical_mae_win_leagues": int(historical_wins),
        "historical_model_supported": historical_model_supported,
        "full_training_rows": training_counts,
        "current_corner_rows_available": int(len(joined)),
        "pooled_direction": pooled,
        "by_cohort": by_cohort,
        "positive_spearman_cohorts": int(positive_cohorts),
        "supported": supported,
        "verdict": (
            "PROMISING_CROSS_MARKET_CORNER_DIRECTION_SIGNAL"
            if supported
            else (
                "MATCH_SHAPE_MODEL_NOT_VALIDATED"
                if not historical_model_supported
                else "NO_CROSS_MARKET_CORNER_DIRECTION_SIGNAL"
            )
        ),
    }, joined


def _referee_bias_table(
    frame: pd.DataFrame,
    *,
    seasons: set[str],
) -> tuple[float, dict[str, float], dict[str, int]]:
    local = frame[frame["season"].astype(str).isin(seasons)].copy()
    local["HC"] = pd.to_numeric(local.get("HC"), errors="coerce")
    local["AC"] = pd.to_numeric(local.get("AC"), errors="coerce")
    local = local.dropna(subset=["HC", "AC"])
    local["total_corners"] = local["HC"] + local["AC"]
    local["Referee"] = local.get("Referee", pd.Series(index=local.index, dtype=object)).fillna("").astype(str).str.strip()
    league_mean = float(local["total_corners"].mean())
    biases: dict[str, float] = {}
    counts: dict[str, int] = {}
    for referee, group in local[local["Referee"] != ""].groupby("Referee"):
        n = int(len(group))
        raw_bias = float(group["total_corners"].mean() - league_mean)
        biases[str(referee)] = float((n / (n + REFEREE_SHRINKAGE_K)) * raw_bias)
        counts[str(referee)] = n
    return league_mean, biases, counts


def signal_4_referee(
    corner: pd.DataFrame,
    football_data: dict[str, pd.DataFrame],
) -> tuple[dict[str, Any], pd.DataFrame]:
    validation = {}
    current_biases = {}
    for league in LEAGUES:
        raw = football_data[league]
        if "Referee" not in raw.columns:
            validation[league] = {"status": "REFEREE_COLUMN_ABSENT"}
            continue
        mean_ref, bias_ref, counts_ref = _referee_bias_table(
            raw,
            seasons=set(HIST_CODES) - {"2025-2026"},
        )
        valid = raw[raw["season"].astype(str) == "2025-2026"].copy()
        valid["HC"] = pd.to_numeric(valid.get("HC"), errors="coerce")
        valid["AC"] = pd.to_numeric(valid.get("AC"), errors="coerce")
        valid = valid.dropna(subset=["HC", "AC"])
        valid["total_corners"] = valid["HC"] + valid["AC"]
        refs = valid["Referee"].fillna("").astype(str).str.strip()
        pred = np.asarray(
            [mean_ref + bias_ref.get(ref, 0.0) for ref in refs],
            dtype=float,
        )
        baseline = np.full(len(valid), mean_ref)
        mae_model = float(mean_absolute_error(valid["total_corners"], pred))
        mae_base = float(mean_absolute_error(valid["total_corners"], baseline))
        validation[league] = {
            "status": "OK",
            "validation_rows": int(len(valid)),
            "reference_referees": int(len(bias_ref)),
            "known_referee_validation_rows": int(sum(ref in bias_ref for ref in refs)),
            "mae_referee_model": mae_model,
            "mae_league_mean_baseline": mae_base,
            "delta_mae": mae_model - mae_base,
            "mae_win": bool(mae_model < mae_base),
        }
        full_mean, full_bias, full_counts = _referee_bias_table(
            raw,
            seasons=set(HIST_CODES),
        )
        current_biases[league] = (full_mean, full_bias, full_counts)

    historical_wins = sum(
        int(result.get("mae_win", False))
        for result in validation.values()
        if result.get("status") == "OK"
    )
    historical_supported = bool(
        sum(result.get("status") == "OK" for result in validation.values()) == 3
        and historical_wins >= 2
    )

    rows = []
    target_corner = corner[corner["league"].isin(LEAGUES)].copy()
    for _, fixture in target_corner.iterrows():
        league = str(fixture["league"])
        if league not in current_biases:
            continue
        current = football_data[league]
        current = current[current["season"].astype(str) == "2026-2027"]
        source_row = _join_current_row(fixture, current)
        if source_row is None:
            continue
        referee = str(source_row.get("Referee") or "").strip()
        mean_value, bias_map, count_map = current_biases[league]
        rows.append(
            {
                **fixture.to_dict(),
                "referee": referee,
                "referee_prior_matches": int(count_map.get(referee, 0)),
                "referee_corner_bias": float(bias_map.get(referee, 0.0)),
                "referee_known": bool(referee and referee in bias_map),
            }
        )
    joined = pd.DataFrame(rows)
    pooled = (
        _direction_metrics(
            joined,
            score_col="referee_corner_bias",
            target_col="centre_delta",
        )
        if not joined.empty
        else {}
    )
    by_cohort = _direction_by_cohort(joined, "referee_corner_bias") if not joined.empty else {}
    positive_cohorts = sum(
        1
        for result in by_cohort.values()
        if result["spearman"] is not None and result["spearman"] > 0
    )
    direction_supported = bool(
        pooled
        and pooled.get("balanced_accuracy") is not None
        and pooled["balanced_accuracy"] >= 0.55
        and pooled.get("spearman") is not None
        and pooled["spearman"] > 0
        and positive_cohorts >= 3
    )
    supported = bool(historical_supported and direction_supported)
    return {
        "signal_id": "REFEREE_CORNER_BIAS_DIRECTION_V1",
        "shrinkage_pseudo_count": REFEREE_SHRINKAGE_K,
        "historical_validation": validation,
        "historical_mae_win_leagues": int(historical_wins),
        "historical_referee_signal_supported": historical_supported,
        "current_corner_rows_available": int(len(joined)),
        "current_known_referee_rows": (
            int(joined["referee_known"].sum()) if not joined.empty else 0
        ),
        "pooled_direction": pooled,
        "by_cohort": by_cohort,
        "positive_spearman_cohorts": int(positive_cohorts),
        "supported": supported,
        "verdict": (
            "PROMISING_REFEREE_DIRECTION_SIGNAL"
            if supported
            else (
                "NO_PORTABLE_REFEREE_CORNER_SIGNAL"
                if not historical_supported
                else "REFEREE_SIGNAL_ABSORBED_OR_NOT_DIRECTIONAL"
            )
        ),
    }, joined


def _team_corner_environment_history(
    raw: pd.DataFrame,
    target_team: str,
    target_date: pd.Timestamp,
) -> list[float]:
    local = raw[
        raw["season"].astype(str).isin({"2025-2026", "2026-2027"})
        & (raw["match_date"] < pd.Timestamp(target_date).normalize())
    ].copy()
    rows = []
    for _, row in local.iterrows():
        if not (
            _matches_target(target_team, row.get("HomeTeam"))
            or _matches_target(target_team, row.get("AwayTeam"))
        ):
            continue
        try:
            hc = float(row.get("HC"))
            ac = float(row.get("AC"))
        except (TypeError, ValueError):
            continue
        if math.isfinite(hc) and math.isfinite(ac) and hc >= 0 and ac >= 0:
            rows.append((pd.Timestamp(row["match_date"]), hc + ac))
    rows.sort(key=lambda item: item[0])
    return [value for _, value in rows]


def _add_volatility(
    corner: pd.DataFrame,
    football_data: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    rows = []
    for _, fixture in corner[corner["league"].isin(LEAGUES)].iterrows():
        raw = football_data[str(fixture["league"])]
        home_hist = _team_corner_environment_history(
            raw, str(fixture["home_team"]), pd.Timestamp(fixture["match_date"])
        )
        away_hist = _team_corner_environment_history(
            raw, str(fixture["away_team"]), pd.Timestamp(fixture["match_date"])
        )
        if len(home_hist) < VOLATILITY_WINDOW or len(away_hist) < VOLATILITY_WINDOW:
            continue
        home_values = np.asarray(home_hist[-VOLATILITY_WINDOW:], dtype=float)
        away_values = np.asarray(away_hist[-VOLATILITY_WINDOW:], dtype=float)
        rows.append(
            {
                **fixture.to_dict(),
                "home_corner_env_sd10": float(np.std(home_values, ddof=0)),
                "away_corner_env_sd10": float(np.std(away_values, ddof=0)),
                "joint_corner_env_volatility10": float(
                    (np.std(home_values, ddof=0) + np.std(away_values, ddof=0)) / 2.0
                ),
                "home_corner_env_skew10": float(skew(home_values, bias=False)),
                "away_corner_env_skew10": float(skew(away_values, bias=False)),
            }
        )
    return pd.DataFrame(rows)


def _logistic_model(columns: list[str]) -> Pipeline:
    return Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
            (
                "logistic",
                LogisticRegression(
                    C=LOGISTIC_C,
                    max_iter=2000,
                    random_state=20261004,
                ),
            ),
        ]
    )


def signal_5_volatility(
    corner: pd.DataFrame,
    football_data: dict[str, pd.DataFrame],
) -> tuple[dict[str, Any], pd.DataFrame]:
    joined = _add_volatility(corner, football_data)
    if joined.empty:
        return {
            "signal_id": "CORNER_ENV_VOLATILITY_INCREMENTAL_REPRICING_V1",
            "verdict": "VOLATILITY_SOURCE_GAP",
            "supported": False,
            "eligible_rows": 0,
        }, joined

    fold_rows = []
    pooled_predictions = []
    for heldout in COHORT_ORDER:
        test = joined[joined["cohort"] == heldout].copy()
        train = joined[joined["cohort"] != heldout].copy()
        if test.empty or train.empty or train["material_move"].nunique() < 2:
            continue
        baseline_cols = ["opening_lambda"]
        candidate_cols = ["opening_lambda", "joint_corner_env_volatility10"]
        base_model = _logistic_model(baseline_cols)
        cand_model = _logistic_model(candidate_cols)
        base_model.fit(train[baseline_cols], train["material_move"])
        cand_model.fit(train[candidate_cols], train["material_move"])
        p_base = base_model.predict_proba(test[baseline_cols])[:, 1]
        p_cand = cand_model.predict_proba(test[candidate_cols])[:, 1]
        y = test["material_move"].astype(int).to_numpy()
        brier_base = float(brier_score_loss(y, p_base))
        brier_cand = float(brier_score_loss(y, p_cand))
        log_base = float(log_loss(y, p_base, labels=[0, 1]))
        log_cand = float(log_loss(y, p_cand, labels=[0, 1]))
        fold_rows.append(
            {
                "heldout_cohort": heldout,
                "rows": int(len(test)),
                "positives": int(y.sum()),
                "baseline_brier": brier_base,
                "candidate_brier": brier_cand,
                "delta_brier": brier_cand - brier_base,
                "baseline_log_loss": log_base,
                "candidate_log_loss": log_cand,
                "delta_log_loss": log_cand - log_base,
                "brier_win": bool(brier_cand < brier_base),
                "log_loss_win": bool(log_cand < log_base),
            }
        )
        pooled_predictions.extend(
            {
                "fixture_id": str(fid),
                "cohort": heldout,
                "y": int(yy),
                "p_base": float(pb),
                "p_candidate": float(pc),
            }
            for fid, yy, pb, pc in zip(
                test["fixture_id"], y, p_base, p_cand
            )
        )

    pred = pd.DataFrame(pooled_predictions)
    if pred.empty:
        pooled = {}
    else:
        pooled = {
            "rows": int(len(pred)),
            "positives": int(pred["y"].sum()),
            "baseline_brier": float(brier_score_loss(pred["y"], pred["p_base"])),
            "candidate_brier": float(
                brier_score_loss(pred["y"], pred["p_candidate"])
            ),
            "delta_brier": float(
                brier_score_loss(pred["y"], pred["p_candidate"])
                - brier_score_loss(pred["y"], pred["p_base"])
            ),
            "baseline_log_loss": float(
                log_loss(pred["y"], pred["p_base"], labels=[0, 1])
            ),
            "candidate_log_loss": float(
                log_loss(pred["y"], pred["p_candidate"], labels=[0, 1])
            ),
            "delta_log_loss": float(
                log_loss(pred["y"], pred["p_candidate"], labels=[0, 1])
                - log_loss(pred["y"], pred["p_base"], labels=[0, 1])
            ),
        }

    brier_wins = sum(int(row["brier_win"]) for row in fold_rows)
    log_wins = sum(int(row["log_loss_win"]) for row in fold_rows)
    supported = bool(
        len(fold_rows) == 4
        and pooled
        and pooled["delta_brier"] < 0
        and pooled["delta_log_loss"] < 0
        and brier_wins >= 3
        and log_wins >= 3
    )
    return {
        "signal_id": "CORNER_ENV_VOLATILITY_INCREMENTAL_REPRICING_V1",
        "window": VOLATILITY_WINDOW,
        "material_move_threshold": MATERIAL_MOVE_THRESHOLD,
        "eligible_rows": int(len(joined)),
        "cohort_rows": joined.groupby("cohort").size().to_dict(),
        "continuous_diagnostic": {
            "pearson_volatility_vs_magnitude": _safe_corr(
                joined["joint_corner_env_volatility10"],
                joined["movement_magnitude"],
                "pearson",
            ),
            "spearman_volatility_vs_magnitude": _safe_corr(
                joined["joint_corner_env_volatility10"],
                joined["movement_magnitude"],
                "spearman",
            ),
        },
        "folds": fold_rows,
        "pooled": pooled,
        "brier_win_cohorts": int(brier_wins),
        "log_loss_win_cohorts": int(log_wins),
        "supported": supported,
        "verdict": (
            "PROMISING_INCREMENTAL_VOLATILITY_REPRICING_SIGNAL"
            if supported
            else "NO_INCREMENTAL_VOLATILITY_REPRICING_SIGNAL"
        ),
    }, joined


def signal_6_regime_change_capability(
    football_data: dict[str, pd.DataFrame],
) -> dict[str, Any]:
    keywords = ("manager", "coach", "lineup", "startingxi", "injur", "suspend")
    per_league = {}
    any_explicit = False
    for league, frame in football_data.items():
        columns = [str(column) for column in frame.columns]
        matching = [
            column
            for column in columns
            if any(token in column.lower().replace("_", "") for token in keywords)
        ]
        any_explicit = any_explicit or bool(matching)
        per_league[league] = {
            "columns": int(len(columns)),
            "matching_manager_coach_lineup_availability_columns": matching,
            "referee_column_present": "Referee" in frame.columns,
        }
    supported = False
    return {
        "signal_id": "COACH_LINEUP_AVAILABILITY_REGIME_CHANGE_V1",
        "existing_football_data_schema": per_league,
        "explicit_regime_change_schema_detected": bool(any_explicit),
        "existing_project_constraints": {
            "historical_lineup_strength_capability": "DATA_GAP unless explicit lineup/strength fields exist",
            "prospective_availability_lab": "IMPLEMENTED_BUT_EXTERNALLY_GATED",
            "retrospective_injury_reconstruction_permitted": False,
        },
        "supported": supported,
        "verdict": (
            "EXISTING_POINT_IN_TIME_SOURCE_AVAILABLE"
            if any_explicit
            else "EXISTING_SOURCE_DATA_GAP_FOR_REGIME_CHANGE_SIGNAL"
        ),
    }


def evaluate(
    *,
    pilot_zip: Path,
    backfill_zip: Path,
    rep50_zip: Path,
    v1_zip: Path,
    v2b_raw_zip: Path,
    v2b_lock_zip: Path,
) -> tuple[dict[str, Any], dict[str, pd.DataFrame]]:
    corner = load_corner_rows(
        pilot_zip,
        backfill_zip,
        rep50_zip,
        v1_zip,
        v2b_raw_zip,
        v2b_lock_zip,
    )
    football_data = download_football_data()

    signal1 = signal_1_opening_price_pressure(corner)
    signal2 = signal_2_line_transition(corner)
    signal3, shape_rows = signal_3_cross_market_shape(corner, football_data)
    signal4, referee_rows = signal_4_referee(corner, football_data)
    signal5, volatility_rows = signal_5_volatility(corner, football_data)
    signal6 = signal_6_regime_change_capability(football_data)

    verdicts = {
        "1_opening_price_pressure": signal1["verdict"],
        "2_line_transition_mechanics": signal2["verdict"],
        "3_cross_market_match_shape": signal3["verdict"],
        "4_referee": signal4["verdict"],
        "5_volatility": signal5["verdict"],
        "6_regime_change": signal6["verdict"],
    }
    promising = [
        key
        for key, signal in (
            ("1_opening_price_pressure", signal1),
            ("2_line_transition_mechanics", signal2),
            ("3_cross_market_match_shape", signal3),
            ("4_referee", signal4),
            ("5_volatility", signal5),
            ("6_regime_change", signal6),
        )
        if bool(signal.get("supported"))
    ]

    report = {
        "experiment_id": EXPERIMENT_ID,
        "evidence_class": "RETROSPECTIVE_MULTI_COHORT_HYPOTHESIS_SCREEN",
        "research_only": True,
        "no_new_prospective_matches_collected": True,
        "corner_cohorts": corner.groupby("cohort").size().to_dict(),
        "corner_rows_total": int(len(corner)),
        "corner_rows_unique": int(corner["fixture_id"].nunique()),
        "football_data_leagues": list(LEAGUES),
        "football_data_historical_seasons": list(HIST_CODES),
        "football_data_current_season": "2026-2027",
        "signals": {
            "1_opening_price_pressure": signal1,
            "2_line_transition_mechanics": signal2,
            "3_cross_market_match_shape": signal3,
            "4_referee": signal4,
            "5_volatility": signal5,
            "6_regime_change": signal6,
        },
        "verdicts": verdicts,
        "promising_signals": promising,
        "opened_sample_caveat": (
            "The 2026/27 corner movement cohorts were already opened in prior research. "
            "Signals 1-5 are retrospective hypothesis screens, not independent confirmation."
        ),
        "paid_odds_api_requests": 0,
        "supabase_writes": 0,
        "production_model_operations": 0,
        "betting_enabled": False,
        "production_promotion": False,
        "result": "NO_BET",
    }
    return report, {
        "corner_rows": corner,
        "cross_market_shape_rows": shape_rows,
        "referee_rows": referee_rows,
        "volatility_rows": volatility_rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pilot-zip", type=Path, required=True)
    parser.add_argument("--backfill-zip", type=Path, required=True)
    parser.add_argument("--rep50-zip", type=Path, required=True)
    parser.add_argument("--v1-zip", type=Path, required=True)
    parser.add_argument("--v2b-raw-zip", type=Path, required=True)
    parser.add_argument("--v2b-lock-zip", type=Path, required=True)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/corner_six_signal_screen_v1"),
    )
    args = parser.parse_args()

    report, frames = evaluate(
        pilot_zip=args.pilot_zip,
        backfill_zip=args.backfill_zip,
        rep50_zip=args.rep50_zip,
        v1_zip=args.v1_zip,
        v2b_raw_zip=args.v2b_raw_zip,
        v2b_lock_zip=args.v2b_lock_zip,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    for name, frame in frames.items():
        frame.to_csv(args.output_dir / f"{name}.csv", index=False)
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))


if __name__ == "__main__":
    main()
