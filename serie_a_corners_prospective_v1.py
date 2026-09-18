"""Prospective Serie A replication of the corner-state diagnostic.

Research-only collector/evaluator. The confirmatory metrics remain sealed until the
first 30 eligible new Serie A fixtures have finished.
"""
from __future__ import annotations

import argparse
import email.utils
import json
import math
import os
import re
import time
import unicodedata
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import requests

import free_corners_signal_screen_v1 as frozen

EXPERIMENT_ID = "SERIE_A_CORNERS_PROSPECTIVE_V1"
BASE_URL = "https://api.5dollarfootballapi.com"
KEY_ENV = "FIVE_DOLLAR_FOOTBALL_API_KEY"
LEAGUE = "SERIE_A"
LEAGUE_ID = "3405541143"
COMPETITION_CODE = "I1"
CURRENT_SEASON = "2026-27"
PROSPECTIVE_START_UTC = pd.Timestamp("2026-09-19T00:00:00Z")
TARGET_ELIGIBLE_ROWS = 30
CAPTURE_HORIZON_DAYS = 14
MIN_PREMATCH_LEAD_HOURS = 6
MAX_PROVIDER_REQUESTS = 20
REQUEST_INTERVAL_SECONDS = 3.1
MAX_RATE_LIMIT_RETRIES = 2
MAX_RESET_WAIT_SECONDS = 3700.0
RESET_SAFETY_SECONDS = 2.0
BLEND_WEIGHT_FOOTBALL = frozen.BLEND_WEIGHT_FOOTBALL
BOOTSTRAP_RESAMPLES = frozen.BOOTSTRAP_RESAMPLES
BOOTSTRAP_SEED = 20260918
MIN_PRIOR_MATCHES = frozen.MIN_PRIOR_MATCHES
TRAIN_SEASONS = frozen.TRAIN_SEASONS


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _read_json(path: Path | None, default: Any) -> Any:
    if path is None or not path.exists():
        return default
    return json.loads(path.read_text())


def _number(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _norm_key(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch)).lower()
    return re.sub(r"[^a-z0-9]+", "", text)


def _iso_utc(value: datetime | pd.Timestamp) -> str:
    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    else:
        ts = ts.tz_convert("UTC")
    return ts.isoformat().replace("+00:00", "Z")


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
                    parsed = parsed.replace(tzinfo=UTC)
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
                headers={
                    "Authorization": f"Bearer {self.key}",
                    "Accept": "application/json",
                },
                params=params,
                timeout=45,
            )
            self.last_request_at = time.monotonic()
            self.request_count += 1
            if response.status_code == 429:
                if retries >= MAX_RATE_LIMIT_RETRIES:
                    raise RuntimeError(
                        "provider rate limit remained active after bounded retries"
                    )
                wait_seconds = _header_wait_seconds(response.headers)
                if wait_seconds is None:
                    raise RuntimeError(
                        "provider returned HTTP 429 without a usable reset header"
                    )
                retries += 1
                time.sleep(wait_seconds)
                continue
            response.raise_for_status()
            payload = response.json()
            if payload.get("success") != 1:
                raise RuntimeError(f"provider API failure: {payload.get('error')}")
            return payload


def _require_key() -> str:
    key = os.getenv(KEY_ENV, "").strip()
    if not key:
        raise RuntimeError(f"{KEY_ENV} is required")
    return key


def _fixture_identity(raw: dict[str, Any]) -> dict[str, Any] | None:
    fixture_id = str(raw.get("id") or "").strip()
    league = raw.get("league") or {}
    teams = raw.get("teams") or {}
    home = (teams.get("home") or {}).get("name") if isinstance(teams, dict) else None
    away = (teams.get("away") or {}).get("name") if isinstance(teams, dict) else None
    kickoff = str(raw.get("kickoff_utc") or "").strip()
    if (
        not fixture_id.isdigit()
        or str((league or {}).get("id") or "") != LEAGUE_ID
        or not home
        or not away
        or not kickoff
    ):
        return None
    try:
        kickoff_ts = pd.Timestamp(kickoff)
        if kickoff_ts.tzinfo is None:
            kickoff_ts = kickoff_ts.tz_localize("UTC")
        else:
            kickoff_ts = kickoff_ts.tz_convert("UTC")
    except Exception:
        return None
    return {
        "fixture_id": fixture_id,
        "league": LEAGUE,
        "league_id": LEAGUE_ID,
        "kickoff_utc": _iso_utc(kickoff_ts),
        "home_team": str(home),
        "away_team": str(away),
    }


def select_scheduled(
    payload: dict[str, Any],
    *,
    captured_at: pd.Timestamp,
) -> list[dict[str, Any]]:
    data = payload.get("data")
    if payload.get("success") != 1 or not isinstance(data, list):
        raise RuntimeError("invalid scheduled fixture payload")
    earliest = max(
        PROSPECTIVE_START_UTC,
        captured_at + pd.Timedelta(hours=MIN_PREMATCH_LEAD_HOURS),
    )
    latest = captured_at + pd.Timedelta(days=CAPTURE_HORIZON_DAYS)
    rows: list[dict[str, Any]] = []
    for raw in data:
        if not isinstance(raw, dict) or str(raw.get("status") or "").lower() != "scheduled":
            continue
        row = _fixture_identity(raw)
        if row is None:
            continue
        kickoff = pd.Timestamp(row["kickoff_utc"])
        if earliest <= kickoff <= latest:
            rows.append(row)
    rows.sort(key=lambda row: (row["kickoff_utc"], int(row["fixture_id"])))
    return rows


def opening_corner_row(
    payload: dict[str, Any],
    fixture: dict[str, Any],
    *,
    captured_at: pd.Timestamp,
) -> dict[str, Any] | None:
    kickoff = pd.Timestamp(fixture["kickoff_utc"])
    if captured_at + pd.Timedelta(hours=MIN_PREMATCH_LEAD_HOURS) > kickoff:
        return None
    if kickoff < PROSPECTIVE_START_UTC:
        return None
    data = payload.get("data")
    bookmakers = data.get("bookmakers") if isinstance(data, dict) else None
    if not isinstance(bookmakers, list):
        return None
    for bookmaker in bookmakers:
        if not isinstance(bookmaker, dict):
            continue
        if str(bookmaker.get("slug") or "").lower() != "bet365":
            continue
        odds = bookmaker.get("odds")
        corner = odds.get("corner_line") if isinstance(odds, dict) else None
        opening = corner.get("opening") if isinstance(corner, dict) else None
        if not isinstance(opening, dict):
            return None
        line = _number(opening.get("line"))
        over = _number(opening.get("over"))
        under = _number(opening.get("under"))
        if line is None or over is None or under is None or over <= 1 or under <= 1:
            return None
        if frozen._line_kind(line) is None:
            return None
        return {
            **fixture,
            "bookmaker": "bet365",
            "market": "corner",
            "opening_line": line,
            "opening_over": over,
            "opening_under": under,
            "captured_at_utc": _iso_utc(captured_at),
            "capture_lead_hours": float(
                (kickoff - captured_at).total_seconds() / 3600.0
            ),
            "finished": False,
            "home_corners": None,
            "away_corners": None,
            "total_corners": None,
        }
    return None


def _finished_result(raw: dict[str, Any]) -> dict[str, Any] | None:
    if str(raw.get("status") or "").lower() != "finished":
        return None
    fixture = _fixture_identity(raw)
    if fixture is None:
        return None
    corners = raw.get("corners") or {}
    hc = _number(corners.get("home")) if isinstance(corners, dict) else None
    ac = _number(corners.get("away")) if isinstance(corners, dict) else None
    if hc is None or ac is None:
        return None
    return {
        "fixture_id": fixture["fixture_id"],
        "home_corners": hc,
        "away_corners": ac,
        "total_corners": hc + ac,
    }


def load_ledger(path: Path | None) -> list[dict[str, Any]]:
    if path is None or not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text().splitlines():
        if line.strip():
            rows.append(json.loads(line))
    ids = [str(row.get("fixture_id") or "") for row in rows]
    if len(ids) != len(set(ids)):
        raise RuntimeError("duplicate fixture ids in prospective ledger")
    return rows


def save_ledger(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = sorted(rows, key=lambda r: (r["kickoff_utc"], int(r["fixture_id"])))
    with path.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def merge_results(
    ledger: list[dict[str, Any]],
    results: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for original in ledger:
        row = dict(original)
        result = results.get(str(row["fixture_id"]))
        if result is not None:
            row["finished"] = True
            row["home_corners"] = result["home_corners"]
            row["away_corners"] = result["away_corners"]
            row["total_corners"] = result["total_corners"]
        out.append(row)
    return out


def _current_fixture_row(raw: dict[str, Any]) -> dict[str, Any] | None:
    return frozen._fixture_row(raw, LEAGUE)


def _fetch_fixture_list(
    client: ProviderClient,
    *,
    status: str,
    start_time: int,
    end_time: int,
    order: str,
) -> dict[str, Any]:
    return client.get(
        f"/v1/leagues/{LEAGUE_ID}/fixtures",
        params={
            "status": status,
            "start_time": start_time,
            "end_time": end_time,
            "order": order,
            "page": 1,
            "per_page": 100,
        },
    )


def collect(
    *,
    output_dir: Path,
    ledger_in: Path | None = None,
    state_in: Path | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    state = _read_json(state_in, {"sealed": False})
    ledger = load_ledger(ledger_in)
    if state.get("sealed") is True:
        save_ledger(output_dir / "ledger.jsonl", ledger)
        _write_json(output_dir / "state.json", state)
        report = {
            "experiment_id": EXPERIMENT_ID,
            "status": "SEALED",
            "provider_requests": 0,
            "provider_request_budget": MAX_PROVIDER_REQUESTS,
            "captured_market_rows": len(ledger),
            "finished_market_rows": sum(bool(r.get("finished")) for r in ledger),
            "paid_subscription_used": False,
            "research_only": True,
            "betting_enabled": False,
        }
        _write_json(output_dir / "report.json", report)
        return report

    key = _require_key()
    client = ProviderClient(key)
    captured_at = pd.Timestamp(now or datetime.now(UTC))
    if captured_at.tzinfo is None:
        captured_at = captured_at.tz_localize("UTC")
    else:
        captured_at = captured_at.tz_convert("UTC")

    scheduled_start = int(
        max(
            PROSPECTIVE_START_UTC,
            captured_at + pd.Timedelta(hours=MIN_PREMATCH_LEAD_HOURS),
        ).timestamp()
    )
    scheduled_end = int(
        (captured_at + pd.Timedelta(days=CAPTURE_HORIZON_DAYS)).timestamp()
    )
    scheduled_payload = _fetch_fixture_list(
        client,
        status="scheduled",
        start_time=scheduled_start,
        end_time=scheduled_end,
        order="asc",
    )
    _write_json(output_dir / "raw" / "scheduled_fixtures.json", scheduled_payload)
    scheduled = select_scheduled(scheduled_payload, captured_at=captured_at)

    by_id = {str(row["fixture_id"]): dict(row) for row in ledger}
    capture_errors: dict[str, str] = {}
    for fixture in scheduled:
        fixture_id = fixture["fixture_id"]
        if fixture_id in by_id:
            continue
        # Reserve one request for the finished fixture list.
        if client.request_count >= MAX_PROVIDER_REQUESTS - 1:
            break
        try:
            payload = client.get(
                f"/v1/fixtures/{fixture_id}/odds",
                params={"market": "corner"},
            )
            _write_json(output_dir / "raw" / "odds" / f"{fixture_id}.json", payload)
            row = opening_corner_row(
                payload,
                fixture,
                captured_at=captured_at,
            )
            if row is not None:
                by_id[fixture_id] = row
            else:
                capture_errors[fixture_id] = "no_valid_bet365_opening_corner_market"
        except Exception as exc:
            capture_errors[fixture_id] = f"{type(exc).__name__}: {exc}"

    season_start = int(pd.Timestamp("2026-07-01T00:00:00Z").timestamp())
    finished_end = int((captured_at + pd.Timedelta(hours=1)).timestamp())
    finished_payload = _fetch_fixture_list(
        client,
        status="finished",
        start_time=season_start,
        end_time=finished_end,
        order="asc",
    )
    _write_json(output_dir / "raw" / "finished_fixtures.json", finished_payload)
    results: dict[str, dict[str, Any]] = {}
    for raw in finished_payload.get("data", []):
        if isinstance(raw, dict):
            result = _finished_result(raw)
            if result is not None:
                results[result["fixture_id"]] = result

    merged = merge_results(list(by_id.values()), results)
    save_ledger(output_dir / "ledger.jsonl", merged)
    state = {
        "sealed": False,
        "prospective_start_utc": _iso_utc(PROSPECTIVE_START_UTC),
        "updated_at_utc": _iso_utc(captured_at),
    }
    _write_json(output_dir / "state.json", state)

    report = {
        "experiment_id": EXPERIMENT_ID,
        "status": "COLLECTING",
        "research_only": True,
        "betting_enabled": False,
        "paid_subscription_used": False,
        "provider_requests": client.request_count,
        "provider_request_budget": MAX_PROVIDER_REQUESTS,
        "captured_market_rows": len(merged),
        "finished_market_rows": sum(bool(r.get("finished")) for r in merged),
        "capture_errors": capture_errors,
        "confirmatory_metrics_opened": False,
    }
    _write_json(output_dir / "report.json", report)
    return report


def load_serie_a_history(history_dir: Path) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    required = {"Date", "HomeTeam", "AwayTeam", "HC", "AC"}
    for code, season in TRAIN_SEASONS:
        path = history_dir / LEAGUE / f"{code}.csv"
        if not path.exists():
            raise FileNotFoundError(path)
        frame = pd.read_csv(path)
        missing = required - set(frame.columns)
        if missing:
            raise RuntimeError(f"{season}: missing historical columns {sorted(missing)}")
        frame = frame.copy()
        frame["season"] = season
        frame["HomeTeam"] = frame["HomeTeam"].map(frozen.canonical_team)
        frame["AwayTeam"] = frame["AwayTeam"].map(frozen.canonical_team)
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)


def _eligible_cohort(
    ledger: list[dict[str, Any]],
    feature_frame: pd.DataFrame,
) -> tuple[list[tuple[dict[str, Any], Any]], dict[str, str]]:
    current = feature_frame[feature_frame["season"] == CURRENT_SEASON].copy()
    by_fixture = {
        str(row.fixture_id): row
        for row in current.itertuples(index=False)
        if row.fixture_id is not None and str(row.fixture_id) != "nan"
    }
    eligible: list[tuple[dict[str, Any], Any]] = []
    exclusions: dict[str, str] = {}
    for market in sorted(
        (row for row in ledger if bool(row.get("finished"))),
        key=lambda row: (row["kickoff_utc"], int(row["fixture_id"])),
    ):
        fixture_id = str(market["fixture_id"])
        kickoff = pd.Timestamp(market["kickoff_utc"])
        captured = pd.Timestamp(market["captured_at_utc"])
        if kickoff < PROSPECTIVE_START_UTC:
            exclusions[fixture_id] = "before_prospective_start"
            continue
        if captured + pd.Timedelta(hours=MIN_PREMATCH_LEAD_HOURS) > kickoff:
            exclusions[fixture_id] = "capture_too_close_to_kickoff"
            continue
        feature_row = by_fixture.get(fixture_id)
        if feature_row is None:
            exclusions[fixture_id] = "missing_current_feature_row"
            continue
        if (
            float(feature_row.home_prior_matches) < MIN_PRIOR_MATCHES
            or float(feature_row.away_prior_matches) < MIN_PRIOR_MATCHES
        ):
            exclusions[fixture_id] = "insufficient_prior_topflight_history"
            continue
        line = float(market["opening_line"])
        kind = frozen._line_kind(line)
        if kind is None:
            exclusions[fixture_id] = "quarter_or_unsupported_line"
            continue
        total = float(market["total_corners"])
        if kind == "integer" and abs(total - line) < 1e-9:
            exclusions[fixture_id] = "integer_line_push"
            continue
        eligible.append((market, feature_row))
    return eligible, exclusions


def _decide_verdict(
    *,
    market_brier: float,
    blend_brier: float,
    market_logloss: float,
    blend_logloss: float,
    alignment: float,
    ci_low: float,
) -> str:
    improves = blend_brier < market_brier and blend_logloss < market_logloss
    if improves and alignment > 0 and ci_low > 0:
        return "REPLICATED_SIGNAL_SCREEN"
    if improves and alignment > 0:
        return "INDICATIVE_NOT_CONFIRMED"
    return "NOT_REPLICATED"


def evaluate(
    *,
    output_dir: Path,
    ledger_path: Path,
    history_dir: Path,
    current_fixtures_json: Path,
) -> dict[str, Any]:
    ledger = load_ledger(ledger_path)
    payload = json.loads(current_fixtures_json.read_text())
    current_rows = [
        row
        for raw in payload.get("data", [])
        if isinstance(raw, dict)
        for row in [_current_fixture_row(raw)]
        if row is not None
    ]
    history = load_serie_a_history(history_dir)
    feature_frame = frozen._build_features(history, current_rows, LEAGUE)
    eligible, exclusions = _eligible_cohort(ledger, feature_frame)

    if len(eligible) < TARGET_ELIGIBLE_ROWS:
        report = {
            "experiment_id": EXPERIMENT_ID,
            "status": "COLLECTING",
            "eligible_finished_rows": len(eligible),
            "target_eligible_rows": TARGET_ELIGIBLE_ROWS,
            "exclusions": exclusions,
            "confirmatory_metrics_opened": False,
            "research_only": True,
            "betting_enabled": False,
            "paid_subscription_used": False,
        }
        _write_json(output_dir / "evaluation_report.json", report)
        return report

    cohort = eligible[:TARGET_ELIGIBLE_ROWS]
    model = frozen._fit_models({LEAGUE: feature_frame})[LEAGUE]
    detail: list[dict[str, Any]] = []
    for market, feature_row in cohort:
        line = float(market["opening_line"])
        total = float(market["total_corners"])
        y = 1.0 if total > line else 0.0
        X = pd.DataFrame(
            [{feature: getattr(feature_row, feature) for feature in frozen.FEATURES}]
        )
        mu = float(model.predict(X)[0])
        p_market = frozen._clip_prob(
            frozen._market_probability(
                float(market["opening_over"]),
                float(market["opening_under"]),
            )
        )
        p_football = frozen._clip_prob(frozen._football_probability(mu, line))
        p_blend = frozen._clip_prob(
            (1 - BLEND_WEIGHT_FOOTBALL) * p_market
            + BLEND_WEIGHT_FOOTBALL * p_football
        )
        alignment_term = (y - p_market) * (p_football - p_market)
        detail.append(
            {
                "fixture_id": str(market["fixture_id"]),
                "kickoff_utc": market["kickoff_utc"],
                "home_team": market["home_team"],
                "away_team": market["away_team"],
                "opening_line": line,
                "total_corners": total,
                "y_over": y,
                "poisson_mean": mu,
                "p_market": p_market,
                "p_football": p_football,
                "p_blend25": p_blend,
                "alignment_term": alignment_term,
            }
        )

    frame = pd.DataFrame(detail)
    y = frame["y_over"].to_numpy(float)
    market_scores = frozen._scores(y, frame["p_market"].to_numpy(float))
    football_scores = frozen._scores(y, frame["p_football"].to_numpy(float))
    blend_scores = frozen._scores(y, frame["p_blend25"].to_numpy(float))
    alignment = float(frame["alignment_term"].mean())

    rng = np.random.default_rng(BOOTSTRAP_SEED)
    terms = frame["alignment_term"].to_numpy(float)
    indices = rng.integers(
        0,
        len(terms),
        size=(BOOTSTRAP_RESAMPLES, len(terms)),
    )
    means = terms[indices].mean(axis=1)
    ci_low = float(np.quantile(means, 0.05))
    ci_high = float(np.quantile(means, 0.95))

    verdict = _decide_verdict(
        market_brier=market_scores["brier"],
        blend_brier=blend_scores["brier"],
        market_logloss=market_scores["log_loss"],
        blend_logloss=blend_scores["log_loss"],
        alignment=alignment,
        ci_low=ci_low,
    )
    frame.to_csv(output_dir / "evaluation_rows.csv", index=False)
    report = {
        "experiment_id": EXPERIMENT_ID,
        "status": verdict,
        "eligible_finished_rows": len(eligible),
        "confirmatory_rows": TARGET_ELIGIBLE_ROWS,
        "cohort_fixture_ids": frame["fixture_id"].tolist(),
        "market": market_scores,
        "football_diagnostic": football_scores,
        "blend25": blend_scores,
        "blend_delta_vs_market": {
            "brier": blend_scores["brier"] - market_scores["brier"],
            "log_loss": blend_scores["log_loss"] - market_scores["log_loss"],
        },
        "residual_alignment": alignment,
        "residual_alignment_bootstrap90": [ci_low, ci_high],
        "exclusions": exclusions,
        "confirmatory_metrics_opened": True,
        "research_only": True,
        "betting_enabled": False,
        "paid_subscription_used": False,
    }
    _write_json(output_dir / "evaluation_report.json", report)
    _write_json(
        output_dir / "state.json",
        {
            "sealed": True,
            "sealed_verdict": verdict,
            "sealed_at_utc": _iso_utc(datetime.now(UTC)),
            "confirmatory_fixture_ids": frame["fixture_id"].tolist(),
        },
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/serie_a_corners_prospective_v1"),
    )
    parser.add_argument("--ledger-in", type=Path)
    parser.add_argument("--state-in", type=Path)
    parser.add_argument("--evaluate", action="store_true")
    parser.add_argument("--history-dir", type=Path)
    parser.add_argument("--current-fixtures-json", type=Path)
    args = parser.parse_args()

    if args.evaluate:
        if args.ledger_in is None or args.history_dir is None or args.current_fixtures_json is None:
            raise SystemExit(
                "--evaluate requires --ledger-in, --history-dir and --current-fixtures-json"
            )
        report = evaluate(
            output_dir=args.output_dir,
            ledger_path=args.ledger_in,
            history_dir=args.history_dir,
            current_fixtures_json=args.current_fixtures_json,
        )
    else:
        report = collect(
            output_dir=args.output_dir,
            ledger_in=args.ledger_in,
            state_in=args.state_in,
        )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
