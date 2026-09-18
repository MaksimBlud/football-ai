"""Fresh free-holdout replication of corner-market repricing magnitude and direction.

Research only. Uses immutable V1 artifacts for training and previously unused
fixture IDs from the provider Free window for holdout evaluation. No match
outcomes or football-state inputs are used.
"""
from __future__ import annotations

import argparse
import email.utils
import json
import math
import os
import time
from dataclasses import dataclass
from datetime import timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import requests
from scipy.stats import binomtest
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

import corner_market_state_repricing_v1 as v1
from five_dollar_corners_source_pilot_v1 import normalize_corner_odds

EXPERIMENT_ID = "CORNER_REPRICING_DIRECTION_REPLICATION_V1"
BASE_URL = "https://api.5dollarfootballapi.com"
KEY_ENV = "FIVE_DOLLAR_FOOTBALL_API_KEY"
LEAGUES = {
    "EPL": "4160026622",
    "LA_LIGA": "4212821298",
    "SERIE_A": "3405541143",
    "BUNDESLIGA": "686337048",
    "LIGUE_1": "3614399544",
}
FIXTURES_PER_LEAGUE = 10
LIST_PER_PAGE = 50
MAX_PROVIDER_REQUESTS = 60
REQUEST_INTERVAL_SECONDS = 3.1
MAX_RATE_LIMIT_RETRIES = 2
RESET_SAFETY_SECONDS = 2.0
MAX_RESET_WAIT_SECONDS = 3700.0
MOVEMENT_QUANTILE = 0.75
LOGISTIC_C = 0.1
MIN_TOTAL_ROWS = 30
MIN_ROWS_PER_LEAGUE = 4
MIN_LEAGUES_WITH_MIN_ROWS = 4
MIN_HIGH_RISK_NONZERO = 8
DIRECTION_MIN_POSITIVE_SHARE = 0.70
DIRECTION_MAX_PVALUE = 0.10


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _require_key(key: str | None = None) -> str:
    value = (key or os.getenv(KEY_ENV, "")).strip()
    if not value:
        raise RuntimeError(f"{KEY_ENV} is required")
    return value


def _header_wait_seconds(headers: Any, *, now_epoch: float | None = None) -> float | None:
    now_epoch = time.time() if now_epoch is None else now_epoch
    retry_after = str(headers.get("Retry-After") or "").strip()
    if retry_after:
        try:
            value = float(retry_after)
            if value >= 0:
                return min(value + RESET_SAFETY_SECONDS, MAX_RESET_WAIT_SECONDS)
        except ValueError:
            try:
                parsed = email.utils.parsedate_to_datetime(retry_after)
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=timezone.utc)
                return min(
                    max(0.0, parsed.timestamp() - now_epoch) + RESET_SAFETY_SECONDS,
                    MAX_RESET_WAIT_SECONDS,
                )
            except Exception:
                pass

    reset = str(
        headers.get("X-RateLimit-Reset")
        or headers.get("X-Ratelimit-Reset")
        or ""
    ).strip()
    if reset:
        try:
            return min(
                max(0.0, float(reset) - now_epoch) + RESET_SAFETY_SECONDS,
                MAX_RESET_WAIT_SECONDS,
            )
        except ValueError:
            pass
    return None


@dataclass
class ProviderClient:
    key: str
    request_count: int = 0
    last_request_at: float | None = None

    def get(self, path: str, *, params: dict[str, Any]) -> dict[str, Any]:
        retries = 0
        while True:
            if self.request_count >= MAX_PROVIDER_REQUESTS:
                raise RuntimeError("provider request budget exceeded")
            now = time.monotonic()
            if self.last_request_at is not None:
                remaining = REQUEST_INTERVAL_SECONDS - (now - self.last_request_at)
                if remaining > 0:
                    time.sleep(remaining)
            response = requests.get(
                BASE_URL + path,
                headers={"Authorization": f"Bearer {self.key}", "Accept": "application/json"},
                params=params,
                timeout=45,
            )
            self.last_request_at = time.monotonic()
            self.request_count += 1
            if response.status_code == 429:
                if retries >= MAX_RATE_LIMIT_RETRIES:
                    raise RuntimeError("provider rate limit remained active after bounded retries")
                wait_seconds = _header_wait_seconds(response.headers)
                if wait_seconds is None:
                    raise RuntimeError("provider 429 without usable reset header")
                retries += 1
                time.sleep(wait_seconds)
                continue
            response.raise_for_status()
            payload = response.json()
            if payload.get("success") != 1:
                raise RuntimeError(f"provider API failure: {payload.get('error')}")
            return payload


def _fixture_from_raw(raw: dict[str, Any], league: str) -> dict[str, Any] | None:
    if str(raw.get("status") or "").lower() != "finished":
        return None
    fixture_id = str(raw.get("id") or "").strip()
    kickoff = str(raw.get("kickoff_utc") or "").strip()
    teams = raw.get("teams") or {}
    home = (teams.get("home") or {}).get("name") if isinstance(teams, dict) else None
    away = (teams.get("away") or {}).get("name") if isinstance(teams, dict) else None
    if not fixture_id.isdigit() or not kickoff or not home or not away:
        return None
    return {
        "fixture_id": fixture_id,
        "league": league,
        "league_id": LEAGUES[league],
        "kickoff_utc": kickoff,
        "home_team": str(home),
        "away_team": str(away),
    }


def select_unseen_fixtures(
    payload: dict[str, Any],
    league: str,
    excluded_ids: set[str],
) -> list[dict[str, Any]]:
    if payload.get("success") != 1 or not isinstance(payload.get("data"), list):
        raise ValueError(f"{league}: invalid fixture-list payload")
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in payload["data"]:
        if not isinstance(raw, dict):
            continue
        row = _fixture_from_raw(raw, league)
        if row is None:
            continue
        fixture_id = row["fixture_id"]
        if fixture_id in excluded_ids or fixture_id in seen:
            continue
        seen.add(fixture_id)
        rows.append(row)
    rows.sort(key=lambda r: (-pd.Timestamp(r["kickoff_utc"]).timestamp(), int(r["fixture_id"])))
    return rows[:FIXTURES_PER_LEAGUE]


def _normalize_holdout_row(row: dict[str, Any]) -> dict[str, Any] | None:
    try:
        opening_line = float(row["opening_line"])
        closing_line = float(row["closing_line"])
        v1._line_kind(opening_line)
        v1._line_kind(closing_line)
        opening_over = float(row["opening_over"])
        opening_under = float(row["opening_under"])
        closing_over = float(row["closing_over"])
        closing_under = float(row["closing_under"])
        opening_lambda = v1.implied_poisson_centre(
            opening_line, opening_over, opening_under
        )
        closing_lambda = v1.implied_poisson_centre(
            closing_line, closing_over, closing_under
        )
    except (KeyError, TypeError, ValueError):
        return None
    centre_delta = closing_lambda - opening_lambda
    return {
        "fixture_id": str(row["fixture_id"]),
        "league": str(row["league"]),
        "kickoff_utc": row.get("kickoff_utc"),
        "home_team": row.get("home_team"),
        "away_team": row.get("away_team"),
        "opening_line": opening_line,
        "opening_lambda": float(opening_lambda),
        "closing_lambda": float(closing_lambda),
        "centre_delta": float(centre_delta),
        "movement_magnitude": float(abs(centre_delta)),
    }


def fit_frozen_v1_predictor(v1_frame: pd.DataFrame) -> tuple[Pipeline, float, float]:
    threshold = float(
        np.quantile(v1_frame["movement_magnitude"].to_numpy(float), MOVEMENT_QUANTILE)
    )
    y = (v1_frame["movement_magnitude"] >= threshold).astype(int).to_numpy()
    model = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
            ("logit", LogisticRegression(C=LOGISTIC_C, max_iter=2000)),
        ]
    )
    model.fit(v1_frame[["opening_lambda"]], y)
    return model, threshold, float(y.mean())


def _scores(y: np.ndarray, p: np.ndarray) -> dict[str, float]:
    y = np.asarray(y, dtype=int)
    p = np.clip(np.asarray(p, dtype=float), 1e-12, 1 - 1e-12)
    return {
        "brier": float(np.mean((p - y) ** 2)),
        "log_loss": float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))),
    }


def evaluate_fresh(
    v1_frame: pd.DataFrame,
    fresh_frame: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    counts = fresh_frame["league"].value_counts().to_dict() if not fresh_frame.empty else {}
    valid_leagues = sum(counts.get(league, 0) >= MIN_ROWS_PER_LEAGUE for league in LEAGUES)
    sample_ok = len(fresh_frame) >= MIN_TOTAL_ROWS and valid_leagues >= MIN_LEAGUES_WITH_MIN_ROWS

    base = {
        "experiment_id": EXPERIMENT_ID,
        "research_only": True,
        "betting_enabled": False,
        "match_outcome_used": False,
        "football_state_used": False,
        "fresh_eligible_rows": int(len(fresh_frame)),
        "fresh_rows_by_league": {league: int(counts.get(league, 0)) for league in LEAGUES},
        "sample_gate_pass": bool(sample_ok),
    }
    if not sample_ok:
        return fresh_frame, {**base, "verdict": "SAMPLE_TOO_SMALL"}

    model, movement_threshold, baseline_prevalence = fit_frozen_v1_predictor(v1_frame)
    frame = fresh_frame.copy()
    frame["risk_probability"] = model.predict_proba(frame[["opening_lambda"]])[:, 1]
    frame["material_move"] = (
        frame["movement_magnitude"] >= movement_threshold
    ).astype(int)

    y = frame["material_move"].to_numpy(int)
    candidate_p = frame["risk_probability"].to_numpy(float)
    baseline_p = np.full(len(frame), baseline_prevalence, dtype=float)
    candidate = _scores(y, candidate_p)
    baseline = _scores(y, baseline_p)
    magnitude_replicated = (
        candidate["brier"] < baseline["brier"]
        and candidate["log_loss"] < baseline["log_loss"]
    )

    frame["high_risk"] = False
    for league in LEAGUES:
        idx = frame.index[frame["league"] == league].tolist()
        ranked = frame.loc[idx].sort_values(
            ["risk_probability", "fixture_id"],
            ascending=[False, True],
            kind="stable",
        )
        take = int(math.ceil(len(ranked) * 0.25))
        if take:
            frame.loc[ranked.head(take).index, "high_risk"] = True

    nonzero = frame[frame["centre_delta"].abs() > 1e-12].copy()
    high_nonzero = nonzero[nonzero["high_risk"]].copy()
    rest_nonzero = nonzero[~nonzero["high_risk"]].copy()
    positive = int((high_nonzero["centre_delta"] > 0).sum())
    negative = int((high_nonzero["centre_delta"] < 0).sum())
    high_n = positive + negative
    positive_share = float(positive / high_n) if high_n else None
    p_value = (
        float(binomtest(positive, high_n, p=0.5, alternative="greater").pvalue)
        if high_n
        else None
    )
    rest_positive = int((rest_nonzero["centre_delta"] > 0).sum())
    rest_n = int(len(rest_nonzero))
    rest_share = float(rest_positive / rest_n) if rest_n else None
    direction_confirmed = bool(
        high_n >= MIN_HIGH_RISK_NONZERO
        and positive_share is not None
        and positive_share >= DIRECTION_MIN_POSITIVE_SHARE
        and p_value is not None
        and p_value < DIRECTION_MAX_PVALUE
    )

    if magnitude_replicated and direction_confirmed:
        verdict = "REPRICING_AND_DIRECTION_REPLICATED"
    elif magnitude_replicated:
        verdict = "REPRICING_REPLICATED_DIRECTION_NOT_CONFIRMED"
    else:
        verdict = "NO_FRESH_REPLICATION"

    coefficient = float(model.named_steps["logit"].coef_[0][0])
    report = {
        **base,
        "verdict": verdict,
        "frozen_v1_training_rows": int(len(v1_frame)),
        "frozen_v1_movement_threshold": movement_threshold,
        "frozen_v1_baseline_prevalence": baseline_prevalence,
        "frozen_v1_fair_centre_coefficient": coefficient,
        "magnitude": {
            "replicated": bool(magnitude_replicated),
            "candidate": candidate,
            "baseline": baseline,
            "delta_brier": candidate["brier"] - baseline["brier"],
            "delta_log_loss": candidate["log_loss"] - baseline["log_loss"],
        },
        "direction": {
            "confirmed": direction_confirmed,
            "high_risk_nonzero": high_n,
            "positive_moves": positive,
            "negative_moves": negative,
            "positive_share": positive_share,
            "one_sided_binom_pvalue_vs_half": p_value,
            "non_high_risk_nonzero": rest_n,
            "non_high_risk_positive_share": rest_share,
        },
    }
    return frame, report


def acquire_fresh_holdout(
    output_dir: Path,
    *,
    key: str,
    excluded_ids: set[str],
) -> tuple[pd.DataFrame, int, dict[str, list[dict[str, Any]]]]:
    client = ProviderClient(key=key)
    selected: dict[str, list[dict[str, Any]]] = {}
    for league, league_id in LEAGUES.items():
        payload = client.get(
            f"/v1/leagues/{league_id}/fixtures",
            params={"status": "finished", "order": "desc", "page": 1, "per_page": LIST_PER_PAGE},
        )
        _write_json(output_dir / "raw" / "fixtures" / f"{league}.json", payload)
        selected[league] = select_unseen_fixtures(payload, league, excluded_ids)
        if len(selected[league]) != FIXTURES_PER_LEAGUE:
            raise RuntimeError(
                f"{league}: expected {FIXTURES_PER_LEAGUE} unseen fixtures, got {len(selected[league])}"
            )
    _write_json(output_dir / "selected_fixtures.json", selected)

    normalized_rows: list[dict[str, Any]] = []
    for league in LEAGUES:
        for fixture in selected[league]:
            fixture_id = fixture["fixture_id"]
            payload = client.get(
                f"/v1/fixtures/{fixture_id}/odds",
                params={"market": "corner"},
            )
            _write_json(output_dir / "raw" / "odds" / f"{fixture_id}.json", payload)
            row = normalize_corner_odds(payload, fixture)
            if row is None:
                continue
            normalized = _normalize_holdout_row(row)
            if normalized is not None:
                normalized_rows.append(normalized)

    return pd.DataFrame(normalized_rows), client.request_count, selected


def run(
    pilot_zip: Path,
    screen_zip: Path,
    output_dir: Path,
    *,
    key: str | None = None,
) -> dict[str, Any]:
    v1_frame = v1.load_market_rows(pilot_zip, screen_zip)
    if len(v1_frame) != 55:
        raise RuntimeError(f"expected immutable V1 sample of 55 rows, got {len(v1_frame)}")
    excluded_ids = set(v1_frame["fixture_id"].astype(str))
    fresh, request_count, selected = acquire_fresh_holdout(
        output_dir,
        key=_require_key(key),
        excluded_ids=excluded_ids,
    )
    if not fresh.empty and set(fresh["fixture_id"].astype(str)) & excluded_ids:
        raise RuntimeError("fresh holdout overlaps immutable V1 sample")

    eval_rows, report = evaluate_fresh(v1_frame, fresh)
    output_dir.mkdir(parents=True, exist_ok=True)
    eval_rows.to_csv(output_dir / "evaluation_rows.csv", index=False)
    report.update(
        {
            "selected_fixture_count": int(sum(len(v) for v in selected.values())),
            "provider_requests": int(request_count),
            "provider_request_budget": MAX_PROVIDER_REQUESTS,
            "paid_subscription_used": False,
        }
    )
    _write_json(output_dir / "report.json", report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pilot-zip", type=Path, required=True)
    parser.add_argument("--screen-zip", type=Path, required=True)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/corner_repricing_direction_replication_v1"),
    )
    args = parser.parse_args()
    report = run(args.pilot_zip, args.screen_zip, args.output_dir)
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
