"""Research-only bookmaker-source/consensus reconstruction benchmark.

The existing historical market baseline prefers B365 whenever available, so it is
not a bookmaker consensus. This experiment keeps de-vigging fixed to proportional
normalization and isolates the source question: B365 vs Pinnacle/PS vs Football-Data
average odds. Selection uses 2024-2025 only and 2025-2026 remains untouched OOT.

Source coverage is reported before common-cohort filtering. Common-source scores are
only comparable on fixtures where all three source triplets exist and must not be
generalized to the full season when that common cohort is incomplete.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from bookmaker_reconstruction_devig_v1 import calibration_ece, proportional
from historical_football_signal_lab import RESULT_TO_INT
from historical_football_signal_runner import BASE, LEAGUES
from market_anchor_1x2_v1 import score_probabilities

EXPERIMENT_ID = "BOOKMAKER_RECONSTRUCTION_CONSENSUS_V1"
VALIDATION_SEASON = "2024-2025"
TEST_SEASON = "2025-2026"
BASELINE_SOURCE = "B365"
SOURCES = {
    "B365": ("B365H", "B365D", "B365A"),
    "PS": ("PSH", "PSD", "PSA"),
    "AVG": ("AvgH", "AvgD", "AvgA"),
}
BOOTSTRAP_REPS = 10_000
BOOTSTRAP_SEED = 20260915
EPS = 1e-12


def _decimal_triplet(row: pd.Series, columns: tuple[str, str, str]) -> tuple[float, float, float] | None:
    if not all(column in row.index for column in columns):
        return None
    odds = pd.to_numeric(pd.Series([row[column] for column in columns]), errors="coerce").to_numpy(float)
    if not np.isfinite(odds).all() or (odds <= 1.0).any():
        return None
    return float(odds[0]), float(odds[1]), float(odds[2])


def raw_source_frame(raw: pd.DataFrame, league: str, season: str) -> pd.DataFrame:
    rows = []
    for _, row in raw.iterrows():
        result = row.get("FTR")
        if result not in RESULT_TO_INT:
            continue
        record: dict[str, object] = {
            "league": league,
            "season": season,
            "match_date": pd.to_datetime(row.get("Date"), dayfirst=True, errors="coerce"),
            "result": result,
        }
        for source, columns in SOURCES.items():
            odds = _decimal_triplet(row, columns)
            for outcome, value in zip(("home", "draw", "away"), odds or (np.nan, np.nan, np.nan)):
                record[f"{source}_{outcome}_odds"] = value
        rows.append(record)
    return pd.DataFrame(rows)


def load_history(raw_dir: Path) -> pd.DataFrame:
    frames = []
    allowed = {VALIDATION_SEASON, TEST_SEASON}
    for league, config in LEAGUES.items():
        league_dir = raw_dir / league.lower()
        league_dir.mkdir(parents=True, exist_ok=True)
        for code, season in config.historical_source.season_codes.items():
            if season not in allowed:
                continue
            url = BASE.format(code=code, comp=config.historical_source.competition_code)
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            path = league_dir / f"{league.lower()}_{code}.csv"
            path.write_bytes(response.content)
            frames.append(raw_source_frame(pd.read_csv(path), league, season))
    if not frames:
        raise RuntimeError("no consensus benchmark history loaded")
    return pd.concat(frames, ignore_index=True)


def source_columns(source: str) -> list[str]:
    if source not in SOURCES:
        raise ValueError(f"unknown source: {source}")
    return [f"{source}_{outcome}_odds" for outcome in ("home", "draw", "away")]


def source_available(frame: pd.DataFrame, source: str) -> pd.Series:
    values = frame[source_columns(source)].to_numpy(float)
    mask = np.isfinite(values).all(axis=1) & (values > 1.0).all(axis=1)
    return pd.Series(mask, index=frame.index, dtype=bool)


def common_source_mask(frame: pd.DataFrame) -> pd.Series:
    mask = pd.Series(True, index=frame.index, dtype=bool)
    for source in SOURCES:
        mask &= source_available(frame, source)
    return mask


def common_source_frame(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.loc[common_source_mask(frame)].copy()


def _coverage_row(frame: pd.DataFrame) -> dict[str, object]:
    total = int(len(frame))
    counts = {source: int(source_available(frame, source).sum()) for source in SOURCES}
    common = int(common_source_mask(frame).sum())
    return {
        "total_matches": total,
        "source_available": counts,
        "source_fraction": {
            source: (float(count / total) if total else 0.0)
            for source, count in counts.items()
        },
        "common_all_sources": common,
        "common_all_sources_fraction": float(common / total) if total else 0.0,
    }


def coverage_report(frame: pd.DataFrame) -> dict[str, object]:
    finished = frame[frame["result"].isin(RESULT_TO_INT)].copy()
    pooled_by_season = {
        season: _coverage_row(group)
        for season, group in finished.groupby("season", sort=True)
    }
    league_season = []
    for (league, season), group in finished.groupby(["league", "season"], sort=True):
        league_season.append({"league": str(league), "season": str(season), **_coverage_row(group)})

    test = finished[finished["season"] == TEST_SEASON].copy()
    test_monthly = []
    dated = test.dropna(subset=["match_date"]).copy()
    if not dated.empty:
        dated["month"] = dated["match_date"].dt.to_period("M").astype(str)
        for (league, month), group in dated.groupby(["league", "month"], sort=True):
            test_monthly.append({"league": str(league), "month": str(month), **_coverage_row(group)})

    return {
        "pooled_by_season": pooled_by_season,
        "league_season": league_season,
        "test_monthly": test_monthly,
    }


def fair_probabilities(frame: pd.DataFrame, source: str) -> np.ndarray:
    odds = frame[source_columns(source)].to_numpy(float)
    if not np.isfinite(odds).all() or (odds <= 1.0).any():
        raise ValueError("source odds must be finite decimal odds > 1")
    return proportional(1.0 / odds)


def _score(frame: pd.DataFrame, source: str) -> dict[str, float]:
    y = frame["result"].map(RESULT_TO_INT).to_numpy(dtype=int)
    p = fair_probabilities(frame, source)
    result = score_probabilities(y, p)
    result["calibration_ece"] = calibration_ece(y, p)
    return result


def _scores(frame: pd.DataFrame) -> dict[str, dict[str, float]]:
    return {source: _score(frame, source) for source in SOURCES}


def _select(scores: dict[str, dict[str, float]]) -> str:
    return min(SOURCES, key=lambda source: (scores[source]["log_loss"], scores[source]["brier"], source))


def source_overround(frame: pd.DataFrame, source: str) -> dict[str, float]:
    odds = frame[source_columns(source)].to_numpy(float)
    overround = (1.0 / odds).sum(axis=1) - 1.0
    return {
        "mean": float(overround.mean()),
        "median": float(np.median(overround)),
        "min": float(overround.min()),
        "max": float(overround.max()),
    }


def source_dispersion(frame: pd.DataFrame) -> np.ndarray:
    stack = np.stack([fair_probabilities(frame, source) for source in SOURCES], axis=1)
    return np.std(stack, axis=1).mean(axis=1)


def dispersion_summary(values: np.ndarray) -> dict[str, float]:
    values = np.asarray(values, dtype=float)
    return {
        "mean": float(values.mean()),
        "median": float(np.median(values)),
        "p75": float(np.quantile(values, 0.75)),
        "p90": float(np.quantile(values, 0.90)),
        "max": float(values.max()),
    }


def paired_loss_deltas(frame: pd.DataFrame, candidate: str) -> dict[str, np.ndarray]:
    y = frame["result"].map(RESULT_TO_INT).to_numpy(dtype=int)
    baseline = fair_probabilities(frame, BASELINE_SOURCE)
    contender = fair_probabilities(frame, candidate)
    onehot = np.eye(3)[y]
    base_brier = np.sum((baseline - onehot) ** 2, axis=1)
    candidate_brier = np.sum((contender - onehot) ** 2, axis=1)
    rows = np.arange(len(y))
    base_log = -np.log(np.clip(baseline[rows, y], EPS, 1.0))
    candidate_log = -np.log(np.clip(contender[rows, y], EPS, 1.0))
    return {"brier": candidate_brier - base_brier, "log_loss": candidate_log - base_log}


def paired_bootstrap(deltas: np.ndarray, *, reps: int = BOOTSTRAP_REPS, seed: int = BOOTSTRAP_SEED) -> dict[str, float | int]:
    values = np.asarray(deltas, dtype=float)
    if values.ndim != 1 or len(values) == 0 or not np.isfinite(values).all():
        raise ValueError("bootstrap deltas must be finite non-empty 1D values")
    rng = np.random.default_rng(seed)
    means = np.empty(reps, dtype=float)
    n = len(values)
    for i in range(reps):
        means[i] = float(values[rng.integers(0, n, size=n)].mean())
    low, high = np.quantile(means, [0.025, 0.975])
    return {
        "n": int(n),
        "reps": int(reps),
        "seed": int(seed),
        "observed_delta": float(values.mean()),
        "bootstrap_ci95_low": float(low),
        "bootstrap_ci95_high": float(high),
        "bootstrap_probability_better_than_b365": float(np.mean(means < 0.0)),
    }


def _bootstrap(frame: pd.DataFrame, candidate: str, seed_offset: int = 0) -> dict[str, dict[str, float | int]]:
    return {
        metric: paired_bootstrap(values, seed=BOOTSTRAP_SEED + seed_offset + i)
        for i, (metric, values) in enumerate(paired_loss_deltas(frame, candidate).items())
    }


def _dispersion_segments(validation: pd.DataFrame, test: pd.DataFrame, candidate: str) -> dict:
    validation_dispersion = source_dispersion(validation)
    thresholds = np.quantile(validation_dispersion, [0.25, 0.50, 0.75])
    test_dispersion = source_dispersion(test)
    labels = np.digitize(test_dispersion, thresholds, right=True)
    rows = []
    for bucket in range(4):
        mask = labels == bucket
        segment = test.loc[mask]
        if segment.empty:
            continue
        baseline = _score(segment, BASELINE_SOURCE)
        contender = _score(segment, candidate)
        rows.append({
            "quartile": bucket + 1,
            "matches": int(len(segment)),
            "dispersion_min": float(test_dispersion[mask].min()),
            "dispersion_max": float(test_dispersion[mask].max()),
            "delta_brier": float(contender["brier"] - baseline["brier"]),
            "delta_log_loss": float(contender["log_loss"] - baseline["log_loss"]),
        })
    return {
        "validation_quartile_thresholds": [float(x) for x in thresholds],
        "test_segments": rows,
    }


def evaluate_frame(frame: pd.DataFrame) -> dict:
    finished = frame[frame["result"].isin(RESULT_TO_INT)].copy()
    coverage = coverage_report(finished)
    clean = common_source_frame(finished)
    validation = clean[clean["season"] == VALIDATION_SEASON].copy()
    test = clean[clean["season"] == TEST_SEASON].copy()
    full_validation = finished[finished["season"] == VALIDATION_SEASON]
    full_test = finished[finished["season"] == TEST_SEASON]
    if validation.empty or test.empty:
        raise RuntimeError("missing common-source validation/OOT rows")

    validation_scores = _scores(validation)
    selected = _select(validation_scores)
    test_scores = _scores(test)
    baseline = test_scores[BASELINE_SOURCE]
    selected_test = test_scores[selected]
    validation_fraction = float(len(validation) / len(full_validation)) if len(full_validation) else 0.0
    test_fraction = float(len(test) / len(full_test)) if len(full_test) else 0.0

    league_reports = []
    for league, group in clean.groupby("league"):
        league_validation = group[group["season"] == VALIDATION_SEASON]
        league_test = group[group["season"] == TEST_SEASON]
        if league_validation.empty or league_test.empty:
            raise RuntimeError(f"{league}: missing common-source validation/OOT rows")
        league_reports.append({
            "league": league,
            "validation_n": int(len(league_validation)),
            "test_n": int(len(league_test)),
            "validation": _scores(league_validation),
            "untouched_test": _scores(league_test),
            "validation_dispersion": dispersion_summary(source_dispersion(league_validation)),
            "test_dispersion": dispersion_summary(source_dispersion(league_test)),
            "test_overround": {source: source_overround(league_test, source) for source in SOURCES},
        })

    return {
        "experiment_id": EXPERIMENT_ID,
        "evidence_class": "HISTORICAL_TEMPORAL_OOT_WITH_COVERAGE_DIAGNOSTIC",
        "research_only": True,
        "production_promotion": False,
        "betting_enabled": False,
        "result": "NO_BET",
        "opened_2026_27_outcomes_used": False,
        "devig_method_fixed": "PROPORTIONAL",
        "baseline_source": BASELINE_SOURCE,
        "candidate_sources": list(SOURCES),
        "source_selection_metric": "2024-2025 pooled LogLoss, then Brier; 2025-2026 untouched",
        "validation_season": VALIDATION_SEASON,
        "untouched_test_season": TEST_SEASON,
        "full_validation_n": int(len(full_validation)),
        "full_test_n": int(len(full_test)),
        "common_source_validation_n": int(len(validation)),
        "common_source_test_n": int(len(test)),
        "common_source_validation_fraction": validation_fraction,
        "common_source_test_fraction": test_fraction,
        "common_source_test_is_full_cohort": bool(len(test) == len(full_test)),
        "coverage": coverage,
        "coverage_interpretation": (
            "common-source performance is a same-fixture diagnostic only; when common_source_test_is_full_cohort is false, "
            "candidate-source OOT results must not be generalized to the full 2025-2026 market cohort"
        ),
        "pooled_selected_on_validation": selected,
        "pooled_validation": validation_scores,
        "pooled_untouched_test": test_scores,
        "pooled_selected_test_delta_vs_b365": {
            "brier": float(selected_test["brier"] - baseline["brier"]),
            "log_loss": float(selected_test["log_loss"] - baseline["log_loss"]),
            "calibration_ece": float(selected_test["calibration_ece"] - baseline["calibration_ece"]),
        },
        "pooled_selected_test_bootstrap": _bootstrap(test, selected),
        "validation_dispersion": dispersion_summary(source_dispersion(validation)),
        "test_dispersion": dispersion_summary(source_dispersion(test)),
        "dispersion_segments": _dispersion_segments(validation, test, selected),
        "pooled_test_overround": {source: source_overround(test, source) for source in SOURCES},
        "league_reports": league_reports,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-dir", type=Path, default=Path("artifacts/bookmaker_reconstruction_consensus_v1/work"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/bookmaker_reconstruction_consensus_v1/report.json"))
    args = parser.parse_args()
    report = evaluate_frame(load_history(args.work_dir))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
