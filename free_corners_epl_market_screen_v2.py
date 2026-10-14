"""Free-only EPL corner-market OOT screen using pinned pre-2026/27 corner state.

Research only. No betting, no paid provider plan, no production model mutation.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import time
from collections import Counter
from pathlib import Path
from typing import Any

import requests
from scipy.stats import poisson

EXPERIMENT_ID = "FREE_CORNERS_EPL_MARKET_SCREEN_V2"
KEY_ENV = "FIVE_DOLLAR_FOOTBALL_API_KEY"
BASE_URL = "https://api.5dollarfootballapi.com"
SOURCE_ARTIFACT_ID = 10506736726
EXPECTED_FINISHED_FIXTURES = 40
MAX_PROVIDER_REQUESTS = 45
REQUEST_INTERVAL_SECONDS = 3.2
MAX_429_RETRIES = 2
RESET_SAFETY_SECONDS = 2.0
MIN_NON_PUSH_ROWS = 25
BLEND_FOOTBALL_WEIGHT = 0.25

TEAM_ALIASES = {
    "Man Utd": "Man United",
    "Nottm Forest": "Nott'm Forest",
}


def canonical_team(name: str) -> str:
    value = str(name).strip()
    return TEAM_ALIASES.get(value, value)


def _number(value: Any) -> float | None:
    try:
        x = float(value)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _header_wait_seconds(headers: dict[str, Any]) -> float | None:
    retry_after = headers.get("Retry-After") or headers.get("retry-after")
    if retry_after is not None:
        try:
            return max(0.0, float(retry_after)) + RESET_SAFETY_SECONDS
        except (TypeError, ValueError):
            pass
    reset = headers.get("X-RateLimit-Reset") or headers.get("x-ratelimit-reset")
    if reset is not None:
        try:
            return max(0.0, float(reset) - time.time()) + RESET_SAFETY_SECONDS
        except (TypeError, ValueError):
            pass
    return None


class ProviderClient:
    def __init__(self, key: str):
        self.key = key
        self.request_count = 0
        self.last_request_at: float | None = None

    def get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        retries = 0
        while True:
            if self.request_count >= MAX_PROVIDER_REQUESTS:
                raise RuntimeError("provider request budget exceeded")
            now = time.monotonic()
            if self.last_request_at is not None:
                wait = REQUEST_INTERVAL_SECONDS - (now - self.last_request_at)
                if wait > 0:
                    time.sleep(wait)
            response = requests.get(
                BASE_URL + path,
                headers={"Authorization": f"Bearer {self.key}", "Accept": "application/json"},
                params=params,
                timeout=45,
            )
            self.request_count += 1
            self.last_request_at = time.monotonic()
            if response.status_code == 429:
                if retries >= MAX_429_RETRIES:
                    raise RuntimeError("provider rate limit persisted after bounded retries")
                wait = _header_wait_seconds(dict(response.headers))
                if wait is None:
                    raise RuntimeError("provider returned 429 without usable reset header")
                retries += 1
                time.sleep(wait)
                continue
            response.raise_for_status()
            payload = response.json()
            if payload.get("success") != 1:
                raise RuntimeError(f"provider API failure: {payload.get('error')}")
            return payload


def load_seed(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text())
    if payload.get("experiment_id") != EXPERIMENT_ID:
        raise ValueError("seed experiment id mismatch")
    if payload.get("last_training_date") != "2026-05-24":
        raise ValueError("unexpected training cutoff")
    if int(payload.get("historical_rows_with_corners", 0)) != 3800:
        raise ValueError("unexpected historical coverage")
    if int(payload.get("eligible_training_rows", 0)) != 3564:
        raise ValueError("unexpected eligible training coverage")
    return payload


def load_finished_fixtures(source_dir: Path) -> list[dict[str, Any]]:
    payload = json.loads((source_dir / "raw" / "fixtures" / "EPL.json").read_text())
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in payload.get("data", []):
        if not isinstance(raw, dict) or str(raw.get("status", "")).lower() != "finished":
            continue
        fid = str(raw.get("id", "")).strip()
        kickoff = str(raw.get("kickoff_utc", "")).strip()
        teams = raw.get("teams") or {}
        corners = raw.get("corners") or {}
        home = (teams.get("home") or {}).get("name") if isinstance(teams, dict) else None
        away = (teams.get("away") or {}).get("name") if isinstance(teams, dict) else None
        hc = _number(corners.get("home")) if isinstance(corners, dict) else None
        ac = _number(corners.get("away")) if isinstance(corners, dict) else None
        if not fid.isdigit() or not kickoff or not home or not away or hc is None or ac is None:
            continue
        if not ("2026-07-01" <= kickoff[:10] < "2027-07-01"):
            continue
        if fid in seen:
            raise ValueError(f"duplicate fixture id {fid}")
        seen.add(fid)
        rows.append({
            "fixture_id": fid,
            "kickoff_utc": kickoff,
            "home_team": str(home),
            "away_team": str(away),
            "home_corners": int(hc),
            "away_corners": int(ac),
            "actual_total": int(hc + ac),
        })
    rows.sort(key=lambda r: (r["kickoff_utc"], int(r["fixture_id"])))
    if len(rows) != EXPECTED_FINISHED_FIXTURES:
        raise ValueError(f"expected {EXPECTED_FINISHED_FIXTURES} frozen EPL fixtures, got {len(rows)}")
    return rows


def load_cached_markets(source_dir: Path) -> dict[str, dict[str, Any]]:
    path = source_dir / "normalized" / "opening_corner_markets.jsonl"
    out: dict[str, dict[str, Any]] = {}
    if not path.exists():
        return out
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("league") != "EPL":
            continue
        fid = str(row.get("fixture_id", ""))
        line_v = _number(row.get("opening_line"))
        over = _number(row.get("opening_over"))
        under = _number(row.get("opening_under"))
        if fid.isdigit() and line_v is not None and over is not None and under is not None and over > 1 and under > 1:
            out[fid] = {
                "fixture_id": fid,
                "opening_line": line_v,
                "opening_over": over,
                "opening_under": under,
                "source": "FROZEN_ARTIFACT_CACHE",
            }
    return out


def parse_opening_market(payload: dict[str, Any], fixture_id: str) -> dict[str, Any] | None:
    data = payload.get("data")
    if not isinstance(data, dict):
        return None
    for bookmaker in data.get("bookmakers", []):
        if not isinstance(bookmaker, dict) or str(bookmaker.get("slug", "")).lower() != "bet365":
            continue
        odds = bookmaker.get("odds")
        corner_line = odds.get("corner_line") if isinstance(odds, dict) else None
        opening = corner_line.get("opening") if isinstance(corner_line, dict) else None
        if not isinstance(opening, dict):
            return None
        line_v = _number(opening.get("line"))
        over = _number(opening.get("over"))
        under = _number(opening.get("under"))
        if line_v is None or over is None or under is None or over <= 1 or under <= 1:
            return None
        return {
            "fixture_id": fixture_id,
            "opening_line": line_v,
            "opening_over": over,
            "opening_under": under,
            "source": "LIVE_FREE_API",
        }
    return None


def acquire_markets(
    client: ProviderClient,
    fixtures: list[dict[str, Any]],
    cache: dict[str, dict[str, Any]],
    output_dir: Path,
) -> dict[str, dict[str, Any]]:
    markets = dict(cache)
    raw_dir = output_dir / "raw_odds"
    raw_dir.mkdir(parents=True, exist_ok=True)
    for fixture in fixtures:
        fid = fixture["fixture_id"]
        if fid in markets:
            continue
        payload = client.get(f"/v1/fixtures/{fid}/odds", {"market": "corner"})
        _write_json(raw_dir / f"{fid}.json", payload)
        row = parse_opening_market(payload, fid)
        if row is not None:
            markets[fid] = row
    normalized = output_dir / "opening_markets.jsonl"
    with normalized.open("w") as handle:
        for fixture in fixtures:
            row = markets.get(fixture["fixture_id"])
            if row is not None:
                handle.write(json.dumps(row, sort_keys=True) + "\n")
    return markets


def devig(over: float, under: float) -> float:
    io = 1.0 / over
    iu = 1.0 / under
    return io / (io + iu)


def football_over_probability(mu: float, line_v: float) -> float:
    if mu <= 0 or not math.isfinite(mu):
        raise ValueError("invalid calibrated mean")
    nearest = round(line_v * 2) / 2
    if abs(line_v - nearest) > 1e-9:
        raise ValueError("quarter/unsupported line")
    frac = line_v - math.floor(line_v)
    if abs(frac - 0.5) < 1e-9:
        k = math.floor(line_v)
        return float(poisson.sf(k, mu))
    if abs(frac) < 1e-9:
        k = int(round(line_v))
        p_gt = float(poisson.sf(k, mu))
        p_lt = float(poisson.cdf(k - 1, mu))
        denom = p_gt + p_lt
        if denom <= 0:
            raise ValueError("invalid non-push probability mass")
        return p_gt / denom
    raise ValueError("quarter/unsupported line")


def brier(rows: list[dict[str, Any]], key: str) -> float:
    return sum((r[key] - r["y"]) ** 2 for r in rows) / len(rows)


def logloss(rows: list[dict[str, Any]], key: str) -> float:
    eps = 1e-12
    total = 0.0
    for r in rows:
        p = min(1 - eps, max(eps, r[key]))
        y = r["y"]
        total += -(y * math.log(p) + (1 - y) * math.log(1 - p))
    return total / len(rows)


def evaluate(
    fixtures: list[dict[str, Any]],
    markets: dict[str, dict[str, Any]],
    seed: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    calibration = seed["calibration"]
    slope = float(calibration["slope"])
    intercept = float(calibration["intercept"])
    state: dict[str, list[list[float]]] = {
        team: [[float(x[0]), float(x[1])] for x in info["last10"]]
        for team, info in seed["teams"].items()
    }
    rows: list[dict[str, Any]] = []
    exclusions: Counter[str] = Counter()
    pushes = 0

    for fixture in fixtures:
        home = canonical_team(fixture["home_team"])
        away = canonical_team(fixture["away_team"])
        home_hist = state.setdefault(home, [])
        away_hist = state.setdefault(away, [])
        market = markets.get(fixture["fixture_id"])

        reason: str | None = None
        if len(home_hist) < 10 or len(away_hist) < 10:
            reason = "INSUFFICIENT_PRIOR_EPL_HISTORY"
        elif market is None:
            reason = "NO_VALID_BET365_OPENING"
        else:
            line_v = float(market["opening_line"])
            twice = line_v * 2
            if abs(twice - round(twice)) > 1e-9:
                reason = "UNSUPPORTED_QUARTER_LINE"

        if reason is None:
            home10 = home_hist[-10:]
            away10 = away_hist[-10:]
            h_cf = sum(x[0] for x in home10) / 10.0
            h_ca = sum(x[1] for x in home10) / 10.0
            a_cf = sum(x[0] for x in away10) / 10.0
            a_ca = sum(x[1] for x in away10) / 10.0
            raw_expected = (h_cf + a_ca) / 2.0 + (a_cf + h_ca) / 2.0
            mu = intercept + slope * raw_expected
            p_market = devig(float(market["opening_over"]), float(market["opening_under"]))
            p_football = football_over_probability(mu, float(market["opening_line"]))
            p_blend = (1.0 - BLEND_FOOTBALL_WEIGHT) * p_market + BLEND_FOOTBALL_WEIGHT * p_football
            actual = int(fixture["actual_total"])
            line_v = float(market["opening_line"])
            integer_line = abs(line_v - round(line_v)) < 1e-9
            is_push = integer_line and actual == int(round(line_v))
            row = {
                **fixture,
                "canonical_home_team": home,
                "canonical_away_team": away,
                "opening_line": line_v,
                "opening_over": float(market["opening_over"]),
                "opening_under": float(market["opening_under"]),
                "raw_expected_total": raw_expected,
                "calibrated_total": mu,
                "p_market": p_market,
                "p_football": p_football,
                "p_blend25": p_blend,
                "push": is_push,
            }
            if is_push:
                pushes += 1
            else:
                row["y"] = 1 if actual > line_v else 0
            rows.append(row)
        else:
            exclusions[reason] += 1

        hc = float(fixture["home_corners"])
        ac = float(fixture["away_corners"])
        home_hist.append([hc, ac])
        away_hist.append([ac, hc])
        if len(home_hist) > 10:
            del home_hist[:-10]
        if len(away_hist) > 10:
            del away_hist[:-10]

    scored = [r for r in rows if not r["push"]]
    report: dict[str, Any] = {
        "experiment_id": EXPERIMENT_ID,
        "research_only": True,
        "betting_enabled": False,
        "paid_subscription_used": False,
        "fixture_count": len(fixtures),
        "eligible_market_rows_including_pushes": len(rows),
        "non_push_rows": len(scored),
        "pushes": pushes,
        "exclusions": dict(sorted(exclusions.items())),
        "blend_football_weight": BLEND_FOOTBALL_WEIGHT,
        "min_non_push_rows": MIN_NON_PUSH_ROWS,
    }
    if len(scored) < MIN_NON_PUSH_ROWS:
        report["verdict"] = "SAMPLE_TOO_SMALL"
        return rows, report

    report.update({
        "market_brier": brier(scored, "p_market"),
        "football_brier": brier(scored, "p_football"),
        "blend25_brier": brier(scored, "p_blend25"),
        "market_logloss": logloss(scored, "p_market"),
        "football_logloss": logloss(scored, "p_football"),
        "blend25_logloss": logloss(scored, "p_blend25"),
        "residual_alignment": sum(
            (r["y"] - r["p_market"]) * (r["p_football"] - r["p_market"]) for r in scored
        ) / len(scored),
        "mean_abs_probability_disagreement": sum(
            abs(r["p_football"] - r["p_market"]) for r in scored
        ) / len(scored),
        "directional_alignment_rate": sum(
            int((r["p_football"] > r["p_market"]) == (r["y"] == 1)) for r in scored
        ) / len(scored),
    })
    report["delta_brier_blend_minus_market"] = report["blend25_brier"] - report["market_brier"]
    report["delta_logloss_blend_minus_market"] = report["blend25_logloss"] - report["market_logloss"]
    report["verdict"] = (
        "INDICATIVE_INCREMENTAL_SIGNAL"
        if report["blend25_brier"] < report["market_brier"]
        and report["blend25_logloss"] < report["market_logloss"]
        and report["residual_alignment"] > 0
        else "NO_CLEAR_INCREMENTAL_SIGNAL"
    )
    return rows, report


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("")
        return
    fields = sorted({k for row in rows for k in row.keys()})
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def run(seed_path: Path, source_dir: Path, output_dir: Path, key: str) -> dict[str, Any]:
    seed = load_seed(seed_path)
    fixtures = load_finished_fixtures(source_dir)
    cache = load_cached_markets(source_dir)
    client = ProviderClient(key)
    markets = acquire_markets(client, fixtures, cache, output_dir)
    rows, report = evaluate(fixtures, markets, seed)
    report["cached_markets_before_live"] = len(cache)
    report["markets_after_live"] = len(markets)
    report["provider_requests"] = client.request_count
    report["provider_request_budget"] = MAX_PROVIDER_REQUESTS
    report["source_artifact_id"] = SOURCE_ARTIFACT_ID
    write_rows(output_dir / "evaluation_rows.csv", rows)
    _write_json(output_dir / "report.json", report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--seed-json",
        type=Path,
        default=Path("research/reference/FREE_CORNERS_EPL_MARKET_SCREEN_V2_SEED.json"),
    )
    parser.add_argument("--source-artifact-dir", type=Path, required=True)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/free_corners_epl_market_screen_v2"),
    )
    args = parser.parse_args()
    key = os.getenv(KEY_ENV, "").strip()
    if not key:
        raise SystemExit(f"{KEY_ENV} is required")
    print(json.dumps(run(args.seed_json, args.source_artifact_dir, args.output_dir, key), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
