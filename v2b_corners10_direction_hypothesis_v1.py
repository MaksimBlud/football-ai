"""Opened-sample CORNERS10 vs market-direction hypothesis audit for V2B.

Research-only hypothesis generation. Uses the frozen 31-fixture feasibility
subset, public Football-Data prior corner history, and the already-opened V2B
evaluation rows. No Odds API/provider odds transport.
"""
from __future__ import annotations

import argparse
import json
from io import StringIO
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import requests

import v2b_corners10_replay_feasibility as feasibility

EXPERIMENT_ID = "V2B_CORNERS10_DIRECTION_HYPOTHESIS_V1"
EXPECTED_LOCKED = 43
EXPECTED_FEASIBLE = 31
EPS = 1e-12


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path}: expected JSON object")
    return payload


def _validate_feasibility(report: dict[str, Any]) -> pd.DataFrame:
    if report.get("experiment_id") != feasibility.EXPERIMENT_ID:
        raise RuntimeError("unexpected feasibility experiment")
    if report.get("status") != "PARTIAL_REPLAY_FEASIBLE":
        raise RuntimeError("expected frozen PARTIAL_REPLAY_FEASIBLE source")
    if report.get("locked_fixture_count") != EXPECTED_LOCKED:
        raise RuntimeError("unexpected locked fixture count")
    if report.get("matched_fixture_count") != EXPECTED_LOCKED:
        raise RuntimeError("source identity coverage is no longer complete")
    if report.get("corners10_feasible_fixture_count") != EXPECTED_FEASIBLE:
        raise RuntimeError("unexpected frozen CORNERS10 feasible count")
    if report.get("direction_test_performed") is not False:
        raise RuntimeError("feasibility artifact must not contain direction test")
    if report.get("v2b_odds_read") is not False:
        raise RuntimeError("feasibility artifact unexpectedly read V2B odds")

    rows = report.get("rows")
    if not isinstance(rows, list) or len(rows) != EXPECTED_LOCKED:
        raise RuntimeError("unexpected feasibility row payload")
    frame = pd.DataFrame(rows)
    required = {
        "fixture_id",
        "league",
        "kickoff_date",
        "canonical_home_team",
        "canonical_away_team",
        "source_identity_status",
        "both_teams_have_corners10",
    }
    missing = required - set(frame.columns)
    if missing:
        raise RuntimeError(f"feasibility rows missing columns {sorted(missing)}")
    if frame["fixture_id"].astype(str).duplicated().any():
        raise RuntimeError("duplicate feasibility fixture IDs")
    if not (frame["source_identity_status"] == "MATCHED").all():
        raise RuntimeError("frozen feasibility contains unmatched fixture")
    eligible = frame[frame["both_teams_have_corners10"].astype(bool)].copy()
    if len(eligible) != EXPECTED_FEASIBLE:
        raise RuntimeError("eligible subset does not equal frozen 31 fixtures")
    eligible["fixture_id"] = eligible["fixture_id"].astype(str)
    return eligible.reset_index(drop=True)


def _validate_market(frame: pd.DataFrame) -> pd.DataFrame:
    required = {"fixture_id", "league", "opening_lambda", "centre_delta"}
    missing = required - set(frame.columns)
    if missing:
        raise RuntimeError(f"market rows missing columns {sorted(missing)}")
    out = frame.copy()
    out["fixture_id"] = out["fixture_id"].astype(str)
    if out["fixture_id"].duplicated().any():
        raise RuntimeError("duplicate market fixture IDs")
    for column in ("opening_lambda", "centre_delta"):
        out[column] = pd.to_numeric(out[column], errors="coerce")
    if not np.isfinite(out[["opening_lambda", "centre_delta"]].to_numpy(float)).all():
        raise RuntimeError("non-finite market values")
    return out


def _team_last10(
    history: pd.DataFrame,
    *,
    team_key: str,
    target_date: pd.Timestamp,
) -> tuple[float, float, int]:
    prior = history[history["match_date"] < target_date]
    team_rows = prior[
        (prior["home_key"] == team_key) | (prior["away_key"] == team_key)
    ].sort_values(["match_date", "home_key", "away_key"], kind="stable")
    recent = team_rows.tail(10)
    if len(recent) < 10:
        return float("nan"), float("nan"), int(len(recent))

    corners_for: list[float] = []
    corners_against: list[float] = []
    for row in recent.itertuples(index=False):
        if row.home_key == team_key:
            corners_for.append(float(row.HC))
            corners_against.append(float(row.AC))
        else:
            corners_for.append(float(row.AC))
            corners_against.append(float(row.HC))
    return (
        float(np.mean(corners_for)),
        float(np.mean(corners_against)),
        len(recent),
    )


def build_corners10_rows(
    eligible: pd.DataFrame,
    histories: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for target in eligible.itertuples(index=False):
        league = str(target.league)
        if league not in histories:
            raise RuntimeError(f"missing history for {league}")
        history = histories[league]
        target_date = pd.Timestamp(target.kickoff_date).normalize()
        home_key = feasibility._identity_key(str(target.canonical_home_team))
        away_key = feasibility._identity_key(str(target.canonical_away_team))

        home_for, home_against, home_n = _team_last10(
            history, team_key=home_key, target_date=target_date
        )
        away_for, away_against, away_n = _team_last10(
            history, team_key=away_key, target_date=target_date
        )
        if home_n != 10 or away_n != 10:
            raise RuntimeError(
                f"{target.fixture_id}: frozen feasible fixture no longer has exact last10 state"
            )

        home_expected = 0.5 * (home_for + away_against)
        away_expected = 0.5 * (away_for + home_against)
        total = home_expected + away_expected

        rows.append(
            {
                "fixture_id": str(target.fixture_id),
                "league": league,
                "kickoff_date": str(target.kickoff_date),
                "home_corners_for_10": home_for,
                "home_corners_against_10": home_against,
                "away_corners_for_10": away_for,
                "away_corners_against_10": away_against,
                "home_expected_corners": home_expected,
                "away_expected_corners": away_expected,
                "corners10_total": total,
            }
        )
    out = pd.DataFrame(rows)
    if len(out) != EXPECTED_FEASIBLE or out["fixture_id"].duplicated().any():
        raise RuntimeError("unexpected CORNERS10 replay output")
    return out


def _correlations(frame: pd.DataFrame) -> dict[str, float | None]:
    if len(frame) < 2:
        return {"pearson": None, "spearman": None}
    x = frame["football_gap"].astype(float)
    y = frame["centre_delta"].astype(float)
    pearson = float(x.corr(y, method="pearson"))
    # Rank then Pearson avoids introducing a separate scipy dependency.
    spearman = float(x.rank(method="average").corr(y.rank(method="average"), method="pearson"))
    return {
        "pearson": pearson if np.isfinite(pearson) else None,
        "spearman": spearman if np.isfinite(spearman) else None,
    }


def _league_report(g: pd.DataFrame) -> dict[str, Any]:
    comparable = g[
        (g["football_gap"].abs() > EPS) & (g["centre_delta"].abs() > EPS)
    ]
    concordant = comparable[
        comparable["football_gap"] * comparable["centre_delta"] > 0
    ]
    return {
        "rows": int(len(g)),
        "comparable_rows": int(len(comparable)),
        "concordant_rows": int(len(concordant)),
        "concordance": (
            float(len(concordant) / len(comparable)) if len(comparable) else None
        ),
    }


def evaluate(
    feasibility_report: dict[str, Any],
    market_rows: pd.DataFrame,
    histories: dict[str, pd.DataFrame],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    eligible = _validate_feasibility(feasibility_report)
    market = _validate_market(market_rows)
    corners = build_corners10_rows(eligible, histories)

    merged = corners.merge(
        market[["fixture_id", "league", "opening_lambda", "centre_delta"]],
        on=["fixture_id", "league"],
        how="left",
        validate="one_to_one",
    )
    if len(merged) != EXPECTED_FEASIBLE:
        raise RuntimeError("market join changed frozen eligible subset")
    if merged[["opening_lambda", "centre_delta"]].isna().any().any():
        raise RuntimeError("market rows missing for frozen eligible fixture")

    merged["football_gap"] = merged["corners10_total"] - merged["opening_lambda"]
    merged["movement_magnitude"] = merged["centre_delta"].abs()
    merged["predicted_direction"] = np.where(
        merged["football_gap"] > EPS,
        "UP",
        np.where(merged["football_gap"] < -EPS, "DOWN", "TIE"),
    )
    merged["observed_direction"] = np.where(
        merged["centre_delta"] > EPS,
        "UP",
        np.where(merged["centre_delta"] < -EPS, "DOWN", "ZERO"),
    )
    merged["comparable"] = (
        (merged["football_gap"].abs() > EPS)
        & (merged["centre_delta"].abs() > EPS)
    )
    merged["concordant"] = (
        merged["comparable"]
        & (merged["football_gap"] * merged["centre_delta"] > 0)
    )

    comparable = merged[merged["comparable"]]
    concordant = merged[merged["concordant"]]

    sign_groups: dict[str, Any] = {}
    for name, mask in {
        "positive_gap": merged["football_gap"] > EPS,
        "negative_gap": merged["football_gap"] < -EPS,
        "zero_gap": merged["football_gap"].abs() <= EPS,
    }.items():
        g = merged[mask]
        sign_groups[name] = {
            "rows": int(len(g)),
            "mean_centre_delta": float(g["centre_delta"].mean()) if len(g) else None,
            "median_centre_delta": float(g["centre_delta"].median()) if len(g) else None,
            "mean_movement_magnitude": (
                float(g["movement_magnitude"].mean()) if len(g) else None
            ),
        }

    by_league = {
        league: _league_report(g)
        for league, g in merged.groupby("league", sort=True)
    }
    supporting_leagues = sum(
        1
        for item in by_league.values()
        if item["comparable_rows"] >= 2
        and item["concordance"] is not None
        and item["concordance"] > 0.50
    )

    pooled_concordance = (
        float(len(concordant) / len(comparable)) if len(comparable) else None
    )
    positive_mean = sign_groups["positive_gap"]["mean_centre_delta"]
    negative_mean = sign_groups["negative_gap"]["mean_centre_delta"]
    sign_means_aligned = bool(
        positive_mean is not None
        and negative_mean is not None
        and positive_mean > 0.0
        and negative_mean < 0.0
    )
    promising = bool(
        pooled_concordance is not None
        and pooled_concordance > 0.60
        and supporting_leagues >= 3
        and sign_means_aligned
    )

    report = {
        "experiment_id": EXPERIMENT_ID,
        "research_only": True,
        "opened_sample_hypothesis_generation": True,
        "confirmatory_replication": False,
        "betting_enabled": False,
        "production_promotion_authorized": False,
        "odds_api_requests": 0,
        "frozen_eligible_fixture_count": EXPECTED_FEASIBLE,
        "evaluated_rows": int(len(merged)),
        "comparable_rows": int(len(comparable)),
        "concordant_rows": int(len(concordant)),
        "pooled_concordance": pooled_concordance,
        "zero_observed_movement_rows": int((merged["centre_delta"].abs() <= EPS).sum()),
        "positive_football_gap_rows": int((merged["football_gap"] > EPS).sum()),
        "negative_football_gap_rows": int((merged["football_gap"] < -EPS).sum()),
        "zero_football_gap_rows": int((merged["football_gap"].abs() <= EPS).sum()),
        "continuous_correlations": _correlations(merged),
        "sign_groups": sign_groups,
        "by_league": by_league,
        "supporting_leagues_with_at_least_2_comparable_rows": int(supporting_leagues),
        "sign_group_mean_deltas_aligned": sign_means_aligned,
        "classification": (
            "PROMISING_DIRECTION_HYPOTHESIS"
            if promising
            else "WEAK_OR_INCONSISTENT_DIRECTION_HYPOTHESIS"
        ),
        "interpretation": (
            "Opened-sample hypothesis generation only. Any promising mechanism "
            "requires a new preregistered unseen market cohort."
        ),
    }
    return merged, report


def run_live_source_audit(
    feasibility_report: dict[str, Any],
    market_rows: pd.DataFrame,
    *,
    session: requests.Session | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    owned = session is None
    if session is None:
        session = requests.Session()
        session.headers.update(
            {"User-Agent": "football-ai-v2b-corners10-direction-hypothesis/1.0"}
        )
    histories: dict[str, pd.DataFrame] = {}
    try:
        for league, config in feasibility.CONFIGS.items():
            previous = feasibility._fetch_csv(
                session, feasibility._previous_contract(config)
            )
            current = feasibility._fetch_csv(
                session, feasibility._current_contract(config)
            )
            prev = feasibility._prepare_source_frame(
                previous, league=league, season=feasibility.PREVIOUS_SEASON
            )
            cur = feasibility._prepare_source_frame(
                current, league=league, season=feasibility.CURRENT_SEASON
            )
            histories[league] = pd.concat([prev, cur], ignore_index=True).sort_values(
                ["match_date", "home_key", "away_key"], kind="stable"
            )
    finally:
        if owned:
            session.close()
    return evaluate(feasibility_report, market_rows, histories)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--feasibility-report", type=Path, required=True)
    parser.add_argument("--market-rows", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    rows, report = run_live_source_audit(
        _read_json(args.feasibility_report),
        pd.read_csv(args.market_rows),
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    rows.to_csv(args.output_dir / "hypothesis_rows.csv", index=False)
    _write_json(args.output_dir / "report.json", report)
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
