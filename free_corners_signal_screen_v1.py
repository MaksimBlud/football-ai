"""Free-window CORNERS10 total screen against Bet365 opening corner prices.

Research only. Historical football model is trained on free Football-Data rows through
2025-26; 2026-27 current-season fixtures and Bet365 corner prices come from the
5DollarFootballAPI Free plan. No paid access, betting, or production model changes.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import time
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import requests
from scipy.stats import poisson
from sklearn.impute import SimpleImputer
from sklearn.linear_model import PoissonRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from historical_football_signal_lab import build_point_in_time_features

EXPERIMENT_ID = "FREE_CORNERS_SIGNAL_SCREEN_V1"
BASE_URL = "https://api.5dollarfootballapi.com"
KEY_ENV = "FIVE_DOLLAR_FOOTBALL_API_KEY"
FOOTBALL_DATA_BASE = "https://www.football-data.co.uk/mmz4281/{code}/{comp}.csv"
LEAGUES = {
    "EPL": {"provider_id": "4160026622", "competition_code": "E0"},
    "LA_LIGA": {"provider_id": "4212821298", "competition_code": "SP1"},
    "SERIE_A": {"provider_id": "3405541143", "competition_code": "I1"},
    "BUNDESLIGA": {"provider_id": "686337048", "competition_code": "D1"},
    "LIGUE_1": {"provider_id": "3614399544", "competition_code": "F1"},
}
TRAIN_SEASONS = (
    ("1617", "2016-17"), ("1718", "2017-18"), ("1819", "2018-19"),
    ("1920", "2019-20"), ("2021", "2020-21"), ("2122", "2021-22"),
    ("2223", "2022-23"), ("2324", "2023-24"), ("2425", "2024-25"),
    ("2526", "2025-26"),
)
CURRENT_SEASON = "2026-27"
FIXTURES_PER_LEAGUE = 11
LIST_PER_PAGE = 50
MAX_PROVIDER_REQUESTS = 60
REQUEST_INTERVAL_SECONDS = 3.1
MIN_PRIOR_MATCHES = 10
MIN_POOLED_ROWS = 40
MIN_LEAGUE_ROWS = 5
MIN_LEAGUES_WITH_ROWS = 4
BLEND_WEIGHT_FOOTBALL = 0.25
BOOTSTRAP_RESAMPLES = 10_000
BOOTSTRAP_SEED = 20260917
FEATURES = [
    "home_corners_for_10", "home_corners_against_10",
    "away_corners_for_10", "away_corners_against_10",
    "home_corners_for_venue5", "home_corners_against_venue5",
    "away_corners_for_venue5", "away_corners_against_venue5",
]

_ALIAS_GROUPS = [
    ("manunited", "manchesterunited", "manutd"), ("mancity", "manchestercity"),
    ("newcastle", "newcastleunited"), ("nottmforest", "nottinghamforest", "nottingham"),
    ("tottenham", "tottenhamhotspur"), ("brighton", "brightonandhovealbion", "brightonhovealbion"),
    ("wolves", "wolverhamptonwanderers", "wolverhampton"), ("westham", "westhamunited"),
    ("leeds", "leedsunited"), ("athleticbilbao", "athbilbao"),
    ("atleticomadrid", "athmadrid", "atleticomadridcf"), ("realbetis", "betis"),
    ("realsociedad", "sociedad"), ("deportivoalaves", "cdalaves", "alaves"),
    ("deportivoacoruna", "deporlacoruna", "lacoruna"),
    ("inter", "intermilan", "internazionale", "internazionalemilano"), ("milan", "acmilan"),
    ("roma", "asroma"), ("verona", "hellasverona"), ("napoli", "sscnapoli"),
    ("atalanta", "atalantabc"), ("bologna", "bolognafc"), ("juventus", "juventusfc"),
    ("lecce", "uslecce"), ("como", "como1907"), ("parma", "parmacalcio1913"),
    ("bayernmunich", "bayernmunchen", "fcbayernmunich"), ("dortmund", "borussiadortmund"),
    ("mgladbach", "borussiamonchengladbach", "monchengladbach"),
    ("einfrankfurt", "eintrachtfrankfurt"), ("leverkusen", "bayerleverkusen"),
    ("freiburg", "scfreiburg"), ("augsburg", "fcaugsburg"),
    ("mainz", "fsvmainz05", "mainz05"), ("wolfsburg", "vflwolfsburg"),
    ("stpauli", "fcstpauli"), ("parissg", "parissaintgermain", "psg"),
    ("marseille", "olympiquemarseille"), ("lyon", "olympiquelyonnais"),
    ("monaco", "asmonaco"), ("lille", "lilleosc"), ("nice", "ogcnice"),
    ("strasbourg", "rcstrasbourg"), ("rennes", "staderennais"),
    ("lens", "rclens"), ("toulouse", "toulousefc"),
]
ALIASES: dict[str, str] = {}
for group in _ALIAS_GROUPS:
    canonical = group[0]
    for key in group:
        ALIASES[key] = canonical


def _norm_key(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch)).lower()
    return re.sub(r"[^a-z0-9]+", "", text)


def canonical_team(value: Any) -> str:
    key = _norm_key(value)
    return ALIASES.get(key, key)


def _number(value: Any) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


@dataclass
class ProviderClient:
    key: str
    request_count: int = 0
    last_request_at: float | None = None

    def get(self, path: str, *, params: dict[str, Any]) -> dict[str, Any]:
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
        response.raise_for_status()
        payload = response.json()
        if payload.get("success") != 1:
            raise RuntimeError(f"provider API failure: {payload.get('error')}")
        return payload


def _require_key(key: str | None = None) -> str:
    value = (key or os.getenv(KEY_ENV, "")).strip()
    if not value:
        raise RuntimeError(f"{KEY_ENV} is required")
    return value


def _fixture_row(raw: dict[str, Any], league: str) -> dict[str, Any] | None:
    if str(raw.get("status") or "").lower() != "finished":
        return None
    fixture_id = str(raw.get("id") or "").strip()
    kickoff = str(raw.get("kickoff_utc") or "").strip()
    teams = raw.get("teams") or {}
    goals = raw.get("goals") or {}
    corners = raw.get("corners") or {}
    cards = raw.get("cards") or {}
    home = (teams.get("home") or {}).get("name") if isinstance(teams, dict) else None
    away = (teams.get("away") or {}).get("name") if isinstance(teams, dict) else None
    hg = _number(goals.get("home")) if isinstance(goals, dict) else None
    ag = _number(goals.get("away")) if isinstance(goals, dict) else None
    hc = _number(corners.get("home")) if isinstance(corners, dict) else None
    ac = _number(corners.get("away")) if isinstance(corners, dict) else None
    if not fixture_id.isdigit() or not kickoff or not home or not away or hg is None or ag is None or hc is None or ac is None:
        return None
    ftr = "H" if hg > ag else ("A" if hg < ag else "D")
    home_cards = cards.get("home") if isinstance(cards, dict) else {}
    away_cards = cards.get("away") if isinstance(cards, dict) else {}
    return {
        "fixture_id": fixture_id, "league": league, "kickoff_utc": kickoff,
        "Date": pd.to_datetime(kickoff, utc=True).strftime("%d/%m/%Y"),
        "HomeTeam": canonical_team(home), "AwayTeam": canonical_team(away),
        "provider_home_team": str(home), "provider_away_team": str(away),
        "FTHG": hg, "FTAG": ag, "FTR": ftr, "HC": hc, "AC": ac,
        "HY": _number((home_cards or {}).get("yellow")), "AY": _number((away_cards or {}).get("yellow")),
        "HR": _number((home_cards or {}).get("red")), "AR": _number((away_cards or {}).get("red")),
        "season": CURRENT_SEASON,
    }


def acquire_current_fixtures(client: ProviderClient, output_dir: Path) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]]]:
    selected: dict[str, list[dict[str, Any]]] = {}
    all_current: list[dict[str, Any]] = []
    for league, cfg in LEAGUES.items():
        payload = client.get(
            f"/v1/leagues/{cfg['provider_id']}/fixtures",
            params={"status": "finished", "order": "desc", "page": 1, "per_page": LIST_PER_PAGE},
        )
        _write_json(output_dir / "raw" / "fixtures" / f"{league}.json", payload)
        rows = []
        seen: set[str] = set()
        for raw in payload.get("data", []):
            if not isinstance(raw, dict):
                continue
            row = _fixture_row(raw, league)
            if row is None:
                continue
            kickoff = pd.to_datetime(row["kickoff_utc"], utc=True)
            if not (pd.Timestamp("2026-07-01", tz="UTC") <= kickoff < pd.Timestamp("2027-07-01", tz="UTC")):
                continue
            if row["fixture_id"] in seen:
                continue
            seen.add(row["fixture_id"])
            rows.append(row)
        rows.sort(key=lambda r: (r["kickoff_utc"], int(r["fixture_id"])), reverse=True)
        selected[league] = rows[:FIXTURES_PER_LEAGUE]
        all_current.extend(rows)
    _write_json(output_dir / "selected_fixtures.json", selected)
    return selected, all_current


def load_market_cache(path: Path | None) -> dict[str, dict[str, Any]]:
    if path is None or not path.exists():
        return {}
    out: dict[str, dict[str, Any]] = {}
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        fixture_id = str(row.get("fixture_id") or "")
        if fixture_id.isdigit():
            out[fixture_id] = row
    return out


def _opening_from_odds_payload(payload: dict[str, Any], fixture: dict[str, Any]) -> dict[str, Any] | None:
    data = payload.get("data")
    if not isinstance(data, dict) or not isinstance(data.get("bookmakers"), list):
        return None
    for bookmaker in data["bookmakers"]:
        if not isinstance(bookmaker, dict) or str(bookmaker.get("slug") or "").lower() != "bet365":
            continue
        odds = bookmaker.get("odds")
        corner_line = odds.get("corner_line") if isinstance(odds, dict) else None
        opening = corner_line.get("opening") if isinstance(corner_line, dict) else None
        if not isinstance(opening, dict):
            return None
        line = _number(opening.get("line")); over = _number(opening.get("over")); under = _number(opening.get("under"))
        if line is None or over is None or under is None or over <= 1.0 or under <= 1.0:
            return None
        return {
            "fixture_id": fixture["fixture_id"], "league": fixture["league"],
            "kickoff_utc": fixture["kickoff_utc"], "home_team": fixture["provider_home_team"],
            "away_team": fixture["provider_away_team"], "opening_line": line,
            "opening_over": over, "opening_under": under, "source": "5DOLLARFOOTBALLAPI",
        }
    return None


def acquire_opening_markets(client: ProviderClient, selected: dict[str, list[dict[str, Any]]], output_dir: Path, cache: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for league in LEAGUES:
        for fixture in selected.get(league, []):
            fixture_id = fixture["fixture_id"]
            cached = cache.get(fixture_id)
            if cached is not None:
                line = _number(cached.get("opening_line")); over = _number(cached.get("opening_over")); under = _number(cached.get("opening_under"))
                if line is not None and over is not None and under is not None and over > 1 and under > 1:
                    rows.append({
                        "fixture_id": fixture_id, "league": league, "kickoff_utc": fixture["kickoff_utc"],
                        "home_team": fixture["provider_home_team"], "away_team": fixture["provider_away_team"],
                        "opening_line": line, "opening_over": over, "opening_under": under,
                        "source": "5DOLLARFOOTBALLAPI_CACHE",
                    })
                    continue
            payload = client.get(f"/v1/fixtures/{fixture_id}/odds", params={"market": "corner"})
            _write_json(output_dir / "raw" / "odds" / f"{fixture_id}.json", payload)
            row = _opening_from_odds_payload(payload, fixture)
            if row is not None:
                rows.append(row)
    normalized = output_dir / "normalized" / "opening_corner_markets.jsonl"
    normalized.parent.mkdir(parents=True, exist_ok=True)
    with normalized.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    return rows


def _download_history(output_dir: Path) -> dict[str, pd.DataFrame]:
    result: dict[str, pd.DataFrame] = {}
    for league, cfg in LEAGUES.items():
        frames = []
        for code, season in TRAIN_SEASONS:
            response = requests.get(FOOTBALL_DATA_BASE.format(code=code, comp=cfg["competition_code"]), timeout=60)
            response.raise_for_status()
            path = output_dir / "football_data" / league / f"{code}.csv"
            path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(response.content)
            frame = pd.read_csv(path); frame["season"] = season
            frame["HomeTeam"] = frame["HomeTeam"].map(canonical_team); frame["AwayTeam"] = frame["AwayTeam"].map(canonical_team)
            frames.append(frame)
        result[league] = pd.concat(frames, ignore_index=True)
    return result


def _load_history_dir(history_dir: Path) -> dict[str, pd.DataFrame]:
    result: dict[str, pd.DataFrame] = {}
    required = {"Date", "HomeTeam", "AwayTeam", "HC", "AC"}
    for league in LEAGUES:
        frames = []
        for code, season in TRAIN_SEASONS:
            path = history_dir / league / f"{code}.csv"
            if not path.exists():
                raise FileNotFoundError(path)
            frame = pd.read_csv(path)
            missing = required - set(frame.columns)
            if missing:
                raise RuntimeError(f"{league} {season}: missing historical columns {sorted(missing)}")
            frame = frame.copy()
            frame["season"] = season
            frame["HomeTeam"] = frame["HomeTeam"].map(canonical_team)
            frame["AwayTeam"] = frame["AwayTeam"].map(canonical_team)
            if pd.to_numeric(frame["HC"], errors="coerce").notna().sum() == 0 or pd.to_numeric(frame["AC"], errors="coerce").notna().sum() == 0:
                raise RuntimeError(f"{league} {season}: no usable corner counts")
            frames.append(frame)
        result[league] = pd.concat(frames, ignore_index=True)
    return result


def _load_replay_inputs(replay_dir: Path) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]], list[dict[str, Any]]]:
    selected_path = replay_dir / "selected_fixtures.json"
    market_path = replay_dir / "normalized" / "opening_corner_markets.jsonl"
    if not selected_path.exists() or not market_path.exists():
        raise RuntimeError("offline replay artifact is incomplete")
    selected = json.loads(selected_path.read_text())
    current_rows: list[dict[str, Any]] = []
    for league in LEAGUES:
        fixture_path = replay_dir / "raw" / "fixtures" / f"{league}.json"
        if not fixture_path.exists():
            raise RuntimeError(f"offline replay missing fixture payload for {league}")
        payload = json.loads(fixture_path.read_text())
        for raw in payload.get("data", []):
            if not isinstance(raw, dict):
                continue
            row = _fixture_row(raw, league)
            if row is None:
                continue
            kickoff = pd.to_datetime(row["kickoff_utc"], utc=True)
            if pd.Timestamp("2026-07-01", tz="UTC") <= kickoff < pd.Timestamp("2027-07-01", tz="UTC"):
                current_rows.append(row)
    markets = list(load_market_cache(market_path).values())
    if any(len(selected.get(league, [])) != FIXTURES_PER_LEAGUE for league in LEAGUES):
        raise RuntimeError("offline replay does not contain the frozen 11-per-league sample")
    selected_ids = {str(row["fixture_id"]) for rows in selected.values() for row in rows}
    market_ids = {str(row["fixture_id"]) for row in markets}
    if selected_ids != market_ids:
        raise RuntimeError("offline replay market rows do not exactly match frozen fixture ids")
    return selected, current_rows, markets


def _build_features(history: pd.DataFrame, current_rows: list[dict[str, Any]], league: str) -> pd.DataFrame:
    hist = history.copy()
    current = pd.DataFrame([r for r in current_rows if r["league"] == league])
    current_base = current[["Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR", "HC", "AC", "HY", "AY", "HR", "AR", "season", "fixture_id", "kickoff_utc"]].copy()
    hist["fixture_id"] = None; hist["kickoff_utc"] = None
    cols = sorted(set(hist.columns) | set(current_base.columns))
    combined = pd.concat([hist.reindex(columns=cols), current_base.reindex(columns=cols)], ignore_index=True)
    features = build_point_in_time_features(combined, league, "MULTI_SEASON")
    keys = combined[["Date", "HomeTeam", "AwayTeam", "season", "HC", "AC", "fixture_id", "kickoff_utc"]].copy()
    keys["match_date"] = pd.to_datetime(keys["Date"], dayfirst=True, errors="coerce")
    keys = keys.rename(columns={"HomeTeam": "home_team", "AwayTeam": "away_team"})
    keys["total_corners"] = pd.to_numeric(keys["HC"], errors="coerce") + pd.to_numeric(keys["AC"], errors="coerce")
    keys = keys[["match_date", "home_team", "away_team", "season", "total_corners", "fixture_id", "kickoff_utc"]]
    merged = features.drop(columns=["season"]).merge(keys, on=["match_date", "home_team", "away_team"], how="left", validate="one_to_one")
    if merged["season"].isna().any():
        raise RuntimeError(f"{league}: failed to restore season labels")
    return merged


def _fit_models(feature_frames: dict[str, pd.DataFrame]) -> dict[str, Pipeline]:
    models: dict[str, Pipeline] = {}
    for league, frame in feature_frames.items():
        train = frame[(frame["season"] != CURRENT_SEASON) & (frame["home_prior_matches"] >= MIN_PRIOR_MATCHES) & (frame["away_prior_matches"] >= MIN_PRIOR_MATCHES) & frame["total_corners"].notna()].copy()
        if len(train) < 500:
            raise RuntimeError(f"{league}: insufficient historical training rows: {len(train)}")
        model = Pipeline([("imputer", SimpleImputer(strategy="median")), ("scale", StandardScaler()), ("model", PoissonRegressor(alpha=0.1, max_iter=2000))])
        model.fit(train[FEATURES], train["total_corners"].astype(float)); models[league] = model
    return models


def _line_kind(line: float) -> str | None:
    frac = round(line - math.floor(line), 6)
    if abs(frac) < 1e-6: return "integer"
    if abs(frac - 0.5) < 1e-6: return "half"
    return None


def _market_probability(over: float, under: float) -> float:
    qo, qu = 1.0 / over, 1.0 / under
    return qo / (qo + qu)


def _football_probability(mu: float, line: float) -> float:
    kind = _line_kind(line)
    if kind == "half":
        return float(poisson.sf(math.floor(line), mu))
    if kind == "integer":
        k = int(round(line)); p_over = float(poisson.sf(k, mu)); p_under = float(poisson.cdf(k - 1, mu)); denom = p_over + p_under
        return p_over / denom if denom > 0 else 0.5
    raise ValueError("unsupported line")


def _clip_prob(value: float) -> float:
    return float(np.clip(value, 1e-6, 1 - 1e-6))


def _scores(y: np.ndarray, p: np.ndarray) -> dict[str, float]:
    p = np.clip(p.astype(float), 1e-6, 1 - 1e-6); y = y.astype(float)
    return {"brier": float(np.mean((p - y) ** 2)), "log_loss": float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))}


def _bootstrap_alignment(terms: np.ndarray) -> tuple[float, float]:
    if len(terms) == 0: return math.nan, math.nan
    rng = np.random.default_rng(BOOTSTRAP_SEED); idx = rng.integers(0, len(terms), size=(BOOTSTRAP_RESAMPLES, len(terms))); means = terms[idx].mean(axis=1)
    return float(np.quantile(means, 0.05)), float(np.quantile(means, 0.95))


def evaluate(selected: dict[str, list[dict[str, Any]]], markets: list[dict[str, Any]], feature_frames: dict[str, pd.DataFrame], models: dict[str, Pipeline]) -> tuple[pd.DataFrame, dict[str, Any]]:
    market_by_id = {row["fixture_id"]: row for row in markets}; detail: list[dict[str, Any]] = []; exclusions: dict[str, str] = {}
    for league in LEAGUES:
        current = feature_frames[league][feature_frames[league]["season"] == CURRENT_SEASON].copy()
        by_fixture = {str(row.fixture_id): row for row in current.itertuples(index=False) if row.fixture_id is not None and str(row.fixture_id) != "nan"}
        for fixture in selected.get(league, []):
            fixture_id = fixture["fixture_id"]; market = market_by_id.get(fixture_id)
            if market is None: exclusions[fixture_id] = "missing_opening_market"; continue
            feature_row = by_fixture.get(fixture_id)
            if feature_row is None: exclusions[fixture_id] = "missing_current_feature_row"; continue
            if float(feature_row.home_prior_matches) < MIN_PRIOR_MATCHES or float(feature_row.away_prior_matches) < MIN_PRIOR_MATCHES:
                exclusions[fixture_id] = "insufficient_prior_topflight_history"; continue
            line = float(market["opening_line"]); kind = _line_kind(line)
            if kind is None: exclusions[fixture_id] = "quarter_or_unsupported_line"; continue
            total = float(feature_row.total_corners)
            if kind == "integer" and abs(total - line) < 1e-9: exclusions[fixture_id] = "integer_line_push"; continue
            y = 1.0 if total > line else 0.0
            X = pd.DataFrame([{feature: getattr(feature_row, feature) for feature in FEATURES}]); mu = float(models[league].predict(X)[0])
            p_market = _clip_prob(_market_probability(float(market["opening_over"]), float(market["opening_under"])))
            p_football = _clip_prob(_football_probability(mu, line)); p_blend = _clip_prob((1 - BLEND_WEIGHT_FOOTBALL) * p_market + BLEND_WEIGHT_FOOTBALL * p_football)
            term = (y - p_market) * (p_football - p_market)
            detail.append({"fixture_id": fixture_id, "league": league, "kickoff_utc": fixture["kickoff_utc"], "home_team": fixture["provider_home_team"], "away_team": fixture["provider_away_team"], "total_corners": total, "opening_line": line, "opening_over": float(market["opening_over"]), "opening_under": float(market["opening_under"]), "y_over": y, "poisson_mean": mu, "p_market": p_market, "p_football": p_football, "p_blend25": p_blend, "alignment_term": term})
    df = pd.DataFrame(detail)
    if df.empty: return df, {"pooled": {"eligible_rows": 0, "verdict": "SAMPLE_TOO_SMALL"}, "per_league": {}, "exclusions": exclusions}
    y = df.y_over.to_numpy(float); market_scores = _scores(y, df.p_market.to_numpy(float)); football_scores = _scores(y, df.p_football.to_numpy(float)); blend_scores = _scores(y, df.p_blend25.to_numpy(float))
    alignment = float(df.alignment_term.mean()); ci_low, ci_high = _bootstrap_alignment(df.alignment_term.to_numpy(float))
    per_league: dict[str, Any] = {}; positive_leagues = 0; leagues_with_rows = 0
    for league in LEAGUES:
        g = df[df.league == league]
        if len(g):
            leagues_with_rows += int(len(g) >= MIN_LEAGUE_ROWS); league_alignment = float(g.alignment_term.mean()); positive_leagues += int(league_alignment > 0)
            per_league[league] = {"eligible_rows": int(len(g)), "residual_alignment": league_alignment, "market": _scores(g.y_over.to_numpy(float), g.p_market.to_numpy(float)), "football": _scores(g.y_over.to_numpy(float), g.p_football.to_numpy(float)), "blend25": _scores(g.y_over.to_numpy(float), g.p_blend25.to_numpy(float))}
        else: per_league[league] = {"eligible_rows": 0, "residual_alignment": None}
    sample_gate = len(df) >= MIN_POOLED_ROWS and leagues_with_rows >= MIN_LEAGUES_WITH_ROWS
    core_signal = blend_scores["brier"] < market_scores["brier"] and blend_scores["log_loss"] < market_scores["log_loss"] and alignment > 0 and positive_leagues >= 3
    verdict = "SAMPLE_TOO_SMALL" if not sample_gate else ("STRONG_SIGNAL_SCREEN" if core_signal and ci_low > 0 else ("INDICATIVE_SIGNAL_SCREEN" if core_signal else "NO_CLEAR_SIGNAL_SCREEN"))
    pooled = {"eligible_rows": int(len(df)), "sample_gate_pass": bool(sample_gate), "leagues_with_at_least_5_rows": int(leagues_with_rows), "positive_alignment_leagues": int(positive_leagues), "market": market_scores, "football": football_scores, "blend25": blend_scores, "delta_blend25_brier_vs_market": float(blend_scores["brier"] - market_scores["brier"]), "delta_blend25_log_loss_vs_market": float(blend_scores["log_loss"] - market_scores["log_loss"]), "residual_alignment": alignment, "residual_alignment_bootstrap_90": [ci_low, ci_high], "verdict": verdict}
    return df, {"pooled": pooled, "per_league": per_league, "exclusions": exclusions}


def run_screen(output_dir: Path, cache_path: Path | None = None, key: str | None = None) -> dict[str, Any]:
    client = ProviderClient(key=_require_key(key)); selected, current_rows = acquire_current_fixtures(client, output_dir)
    if any(len(selected.get(league, [])) < FIXTURES_PER_LEAGUE for league in LEAGUES): raise RuntimeError("insufficient current-season finished fixtures for frozen 11-per-league sample")
    cache = load_market_cache(cache_path); markets = acquire_opening_markets(client, selected, output_dir, cache)
    history = _download_history(output_dir / "raw"); feature_frames = {league: _build_features(history[league], current_rows, league) for league in LEAGUES}; models = _fit_models(feature_frames)
    detail, result = evaluate(selected, markets, feature_frames, models); detail.to_csv(output_dir / "evaluation_rows.csv", index=False)
    report = {"experiment_id": EXPERIMENT_ID, "research_only": True, "betting_enabled": False, "paid_subscription_used": False, "provider_requests": client.request_count, "provider_request_budget": MAX_PROVIDER_REQUESTS, "selected_fixtures": sum(len(v) for v in selected.values()), "market_rows": len(markets), "cache_rows_available": len(cache), **result}
    _write_json(output_dir / "report.json", report); return report


def run_offline_replay(output_dir: Path, replay_dir: Path, history_dir: Path) -> dict[str, Any]:
    selected, current_rows, markets = _load_replay_inputs(replay_dir)
    history = _load_history_dir(history_dir)
    feature_frames = {league: _build_features(history[league], current_rows, league) for league in LEAGUES}
    models = _fit_models(feature_frames)
    detail, result = evaluate(selected, markets, feature_frames, models)
    output_dir.mkdir(parents=True, exist_ok=True)
    detail.to_csv(output_dir / "evaluation_rows.csv", index=False)
    report = {
        "experiment_id": EXPERIMENT_ID,
        "research_only": True,
        "betting_enabled": False,
        "paid_subscription_used": False,
        "provider_requests": 0,
        "provider_request_budget": MAX_PROVIDER_REQUESTS,
        "selected_fixtures": sum(len(v) for v in selected.values()),
        "market_rows": len(markets),
        "cache_rows_available": len(markets),
        "offline_replay": True,
        **result,
    }
    _write_json(output_dir / "report.json", report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/free_corners_signal_screen_v1"))
    parser.add_argument("--cached-market-jsonl", type=Path)
    parser.add_argument("--offline-replay-dir", type=Path)
    parser.add_argument("--history-dir", type=Path)
    args = parser.parse_args()
    if args.offline_replay_dir is not None or args.history_dir is not None:
        if args.offline_replay_dir is None or args.history_dir is None:
            parser.error("--offline-replay-dir and --history-dir must be supplied together")
        report = run_offline_replay(args.output_dir, args.offline_replay_dir, args.history_dir)
    else:
        report = run_screen(args.output_dir, args.cached_market_jsonl)
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__": main()
