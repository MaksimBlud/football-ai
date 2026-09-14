"""Outcome-blind point-in-time replay of the frozen production 1X2 model.

This protocol exists only to rescue the 2026-09-11 non-EPL MARKET_ONLY cohort.
It is retrospective reconstruction, never prospective evidence.  The code does
not query settlement/result tables.  Current-season Football-Data rows are
admitted only when their fixture time was safely before the saved market
snapshot; later rows are not inspected for result/stat fields.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from dataclasses import dataclass
from pathlib import Path
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

import joblib
import numpy as np
import pandas as pd

from la_liga_canonical_names import normalize_team as normalize_la_liga_team
from research_model_features import (
    FEATURES,
    HOME_ADVANTAGE,
    INITIAL_ELO,
    LAST_MATCHES,
    average,
    calculate_current_state,
)
from serie_a_runtime_config import SERIE_A_ALIASES

EXPERIMENT_ID = "POINT_IN_TIME_CROSS_LEAGUE_REPLAY_V1"
EVIDENCE_CLASS = "RETROSPECTIVE_POINT_IN_TIME_REPLAY"
SOURCE_CODE_COMMIT = "3ecb981080f724ec6f10c0c762f75bd535307ed3"
MODEL_PATH = Path("football_model_xgboost_elo.pkl")
FROZEN_MODEL_SHA256 = "1e516fe91420fdc2d6479e9fb92b005c4a0c75c7f0f217493dd6b27fd64d99a5"
MODEL_GIT_BLOB_SHA = "f8d9b2cd92ff5e8e550bb8c0de358f1d795d3327"
FEATURE_FORMULA_GIT_BLOB_SHA = "3068d08c1e28523ca71f3218e8db3a1fef4b0c05"

CAPTURE_START_UTC = pd.Timestamp("2026-09-11T00:00:00Z")
CAPTURE_END_UTC = pd.Timestamp("2026-09-12T00:00:00Z")
KICKOFF_END_UTC = pd.Timestamp("2026-09-15T00:00:00Z")
CURRENT_SEASON = "2026-2027"
CURRENT_SEASON_CODE = "2627"
CURRENT_HISTORY_CUTOFF_DATE = pd.Timestamp("2026-09-11")
RESULT_AVAILABILITY_BUFFER = pd.Timedelta(hours=4)
PROB_TOL = 1e-6
BASE_URL = "https://www.football-data.co.uk/mmz4281/{season_code}/{competition}.csv"
SEASON_CODES = (
    "1617", "1718", "1819", "1920", "2021",
    "2122", "2223", "2324", "2425", "2526", "2627",
)

EXPECTED_COUNTS = {
    "BUNDESLIGA": 9,
    "EREDIVISIE": 9,
    "LA_LIGA": 10,
    "LIGUE_1": 9,
    "SERIE_A": 10,
}

SOURCE_ALIASES = {
    "BUNDESLIGA": {
        "Dortmund": "Borussia Dortmund",
        "Leverkusen": "Bayer Leverkusen",
        "Ein Frankfurt": "Eintracht Frankfurt",
        "Freiburg": "SC Freiburg",
        "M'gladbach": "Borussia Monchengladbach",
        "Hoffenheim": "TSG Hoffenheim",
        "FC Koln": "1. FC Köln",
        "Hamburg": "Hamburger SV",
        "Paderborn": "SC Paderborn",
        "Schalke 04": "FC Schalke 04",
        "Mainz": "FSV Mainz 05",
        "Stuttgart": "VfB Stuttgart",
    },
    "EREDIVISIE": {
        "Cambuur": "SC Cambuur",
        "Den Haag": "ADO Den Haag",
        "Twente": "FC Twente Enschede",
        "Utrecht": "FC Utrecht",
        "Zwolle": "FC Zwolle",
        "Nijmegen": "NEC Nijmegen",
        "For Sittard": "Fortuna Sittard",
        "Telstar": "SC Telstar",
        "PSV": "PSV Eindhoven",
    },
    "LA_LIGA": {},
    "LIGUE_1": {
        "Monaco": "AS Monaco",
        "Lens": "RC Lens",
        "Paris SG": "Paris Saint Germain",
        "Le Mans": "Le Mans FC",
    },
    "SERIE_A": {
        **SERIE_A_ALIASES,
        "Atalanta": "Atalanta BC",
    },
}

@dataclass(frozen=True)
class LeagueSpec:
    competition: str
    timezone: str

LEAGUE_SPECS = {
    "BUNDESLIGA": LeagueSpec("D1", "Europe/Berlin"),
    "EREDIVISIE": LeagueSpec("N1", "Europe/Amsterdam"),
    "LA_LIGA": LeagueSpec("SP1", "Europe/Madrid"),
    "LIGUE_1": LeagueSpec("F1", "Europe/Paris"),
    "SERIE_A": LeagueSpec("I1", "Europe/Rome"),
}

LEDGER_COLUMNS = (
    "prediction_key,league,event_id,home_team,away_team,kickoff_utc,"
    "prediction_time_utc,snapshot_time_utc,market_home_prob,market_draw_prob,"
    "market_away_prob,prediction_mode"
)
ODDS_COLUMNS = (
    "league,event_id,snapshot_time_utc,commence_time_utc,home_team,away_team,"
    "home_odds,draw_odds,away_odds"
)
HISTORY_COLUMNS = [
    "match_date", "match_time", "home_team", "away_team",
    "home_goals", "away_goals", "result",
    "home_shots", "away_shots", "home_shots_target", "away_shots_target",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json_sha256(records: list[dict]) -> str:
    payload = "\n".join(
        json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)
        for record in records
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def fetch_all(table: str, columns: str) -> pd.DataFrame:
    from database import supabase

    rows: list[dict] = []
    page_size = 1000
    start = 0
    while True:
        response = (
            supabase.table(table)
            .select(columns)
            .range(start, start + page_size - 1)
            .execute()
        )
        batch = response.data or []
        rows.extend(batch)
        if len(batch) < page_size:
            break
        start += page_size
    return pd.DataFrame(rows)


def normalized_market_probabilities(home_odds: float, draw_odds: float, away_odds: float) -> np.ndarray:
    odds = np.asarray([home_odds, draw_odds, away_odds], dtype=float)
    if not np.isfinite(odds).all() or (odds <= 1.0).any():
        raise ValueError("Invalid raw 1X2 odds")
    inv = 1.0 / odds
    return inv / inv.sum()


def build_frozen_cohort(ledger: pd.DataFrame, odds: pd.DataFrame) -> pd.DataFrame:
    required_ledger = set(LEDGER_COLUMNS.split(","))
    required_odds = set(ODDS_COLUMNS.split(","))
    missing = required_ledger - set(ledger.columns)
    if missing:
        raise ValueError(f"ledger missing columns: {sorted(missing)}")
    missing = required_odds - set(odds.columns)
    if missing:
        raise ValueError(f"odds snapshots missing columns: {sorted(missing)}")

    work = ledger.copy()
    for column in ("kickoff_utc", "prediction_time_utc", "snapshot_time_utc"):
        work[column] = pd.to_datetime(work[column], utc=True, errors="coerce")
    if work[["kickoff_utc", "prediction_time_utc", "snapshot_time_utc"]].isna().any(axis=None):
        raise ValueError("ledger contains invalid timestamps")

    work = work.loc[
        work["league"].astype(str).isin(EXPECTED_COUNTS)
        & work["prediction_mode"].astype(str).eq("MARKET_ONLY")
        & work["prediction_time_utc"].ge(CAPTURE_START_UTC)
        & work["prediction_time_utc"].lt(CAPTURE_END_UTC)
        & work["kickoff_utc"].ge(work["prediction_time_utc"])
        & work["kickoff_utc"].lt(KICKOFF_END_UTC)
        & work["snapshot_time_utc"].lt(work["kickoff_utc"])
    ].copy()

    identity = work.groupby(["league", "event_id"]).agg(
        home_count=("home_team", "nunique"),
        away_count=("away_team", "nunique"),
        kickoff_count=("kickoff_utc", "nunique"),
    )
    if (identity > 1).any(axis=None):
        raise RuntimeError("ambiguous event identity in replay cohort")

    work = (
        work.sort_values(["league", "event_id", "prediction_time_utc", "prediction_key"])
        .groupby(["league", "event_id"], as_index=False, sort=False)
        .head(1)
        .copy()
    )

    counts = work.groupby("league")["event_id"].nunique().to_dict()
    if counts != EXPECTED_COUNTS:
        raise RuntimeError(f"frozen cohort count mismatch: expected={EXPECTED_COUNTS}, actual={counts}")

    raw = odds.copy()
    for column in ("snapshot_time_utc", "commence_time_utc"):
        raw[column] = pd.to_datetime(raw[column], utc=True, errors="coerce")
    keys = ["league", "event_id", "snapshot_time_utc"]
    if raw.duplicated(keys).any():
        raise RuntimeError("ambiguous exact raw odds snapshot identity")

    merged = work.merge(
        raw[list(required_odds)],
        on=keys,
        how="left",
        suffixes=("", "_raw"),
        validate="one_to_one",
    )
    if merged[["home_odds", "draw_odds", "away_odds"]].isna().any(axis=None):
        raise RuntimeError("missing exact raw odds for replay cohort")

    if not merged["commence_time_utc"].eq(merged["kickoff_utc"]).all():
        raise RuntimeError("raw odds kickoff mismatch")
    if not merged["home_team_raw"].astype(str).eq(merged["home_team"].astype(str)).all():
        raise RuntimeError("raw odds home-team mismatch")
    if not merged["away_team_raw"].astype(str).eq(merged["away_team"].astype(str)).all():
        raise RuntimeError("raw odds away-team mismatch")

    for row in merged.itertuples(index=False):
        market = normalized_market_probabilities(row.home_odds, row.draw_odds, row.away_odds)
        ledger_probs = np.asarray(
            [row.market_home_prob, row.market_draw_prob, row.market_away_prob],
            dtype=float,
        )
        if not np.allclose(market, ledger_probs, atol=PROB_TOL, rtol=0):
            raise RuntimeError(f"market probability mismatch for {row.league}/{row.event_id}")

    return merged.sort_values(["league", "kickoff_utc", "event_id"]).reset_index(drop=True)


def normalize_source_team(league: str, value: str) -> str:
    name = str(value).strip()
    if league == "LA_LIGA":
        return normalize_la_liga_team(name)
    return SOURCE_ALIASES[league].get(name, name)


def _parse_source_date(value: str) -> pd.Timestamp:
    parsed = pd.to_datetime(str(value).strip(), dayfirst=True, errors="coerce")
    if pd.isna(parsed):
        raise ValueError(f"unparseable Football-Data date: {value!r}")
    return pd.Timestamp(parsed).normalize()


def _source_row_to_history(league: str, row: dict[str, str]) -> dict:
    required = ("HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR")
    if any(str(row.get(column, "")).strip() == "" for column in required):
        raise ValueError(f"incomplete finished row for {league}")
    result = str(row["FTR"]).strip()
    if result not in {"H", "D", "A"}:
        raise ValueError(f"unexpected result code for {league}: {result!r}")

    def number(column: str) -> float:
        value = str(row.get(column, "")).strip()
        if value == "":
            return 0.0
        parsed = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
        return 0.0 if pd.isna(parsed) else float(parsed)

    return {
        "match_date": _parse_source_date(row["Date"]),
        "match_time": str(row.get("Time", "") or "").strip() or None,
        "home_team": normalize_source_team(league, row["HomeTeam"]),
        "away_team": normalize_source_team(league, row["AwayTeam"]),
        "home_goals": number("FTHG"),
        "away_goals": number("FTAG"),
        "result": result,
        "home_shots": number("HS"),
        "away_shots": number("AS"),
        "home_shots_target": number("HST"),
        "away_shots_target": number("AST"),
    }


def parse_football_data_csv_outcome_blind(
    league: str,
    content: bytes,
    *,
    current_season: bool,
) -> pd.DataFrame:
    """Parse history without touching post-cutoff outcome/stat fields.

    The current public CSV may now contain matches played after the replay
    decision point.  We inspect only Date/Time/team identity first and skip
    any row dated 2026-09-11 or later before reading FTHG/FTAG/FTR/shot fields.
    """
    text = content.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    rows: list[dict] = []
    for row in reader:
        date = _parse_source_date(row.get("Date", ""))
        if current_season and date >= CURRENT_HISTORY_CUTOFF_DATE:
            continue
        rows.append(_source_row_to_history(league, row))
    return pd.DataFrame(rows, columns=HISTORY_COLUMNS)


def download_bytes(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0 football-ai-replay"})
    with urlopen(request, timeout=60) as response:
        payload = response.read()
    if len(payload) < 500:
        raise RuntimeError(f"suspiciously small Football-Data response: {url}")
    return payload


def load_league_history(league: str) -> pd.DataFrame:
    spec = LEAGUE_SPECS[league]
    frames: list[pd.DataFrame] = []
    for season_code in SEASON_CODES:
        url = BASE_URL.format(season_code=season_code, competition=spec.competition)
        payload = download_bytes(url)
        frame = parse_football_data_csv_outcome_blind(
            league,
            payload,
            current_season=(season_code == CURRENT_SEASON_CODE),
        )
        if frame.empty:
            raise RuntimeError(f"empty history source: {league} {season_code}")
        frame["season_code"] = season_code
        frames.append(frame)
    history = pd.concat(frames, ignore_index=True)
    history = history.sort_values(
        ["match_date", "match_time", "home_team", "away_team"],
        kind="stable",
        na_position="first",
    ).reset_index(drop=True)
    if history["match_date"].max() >= CURRENT_HISTORY_CUTOFF_DATE:
        raise RuntimeError(f"post-cutoff history leaked into {league}")
    return history


def history_as_of_snapshot(history: pd.DataFrame, snapshot_utc: pd.Timestamp, timezone: str) -> pd.DataFrame:
    cutoff = pd.Timestamp(snapshot_utc)
    cutoff = cutoff.tz_localize("UTC") if cutoff.tzinfo is None else cutoff.tz_convert("UTC")
    local_tz = ZoneInfo(timezone)
    work = history.copy()
    work["match_date"] = pd.to_datetime(work["match_date"], errors="raise")
    has_time = work["match_time"].notna() & work["match_time"].astype(str).str.strip().ne("")

    availability = pd.Series(pd.NaT, index=work.index, dtype="datetime64[ns, UTC]")
    if has_time.any():
        local_naive = pd.to_datetime(
            work.loc[has_time, "match_date"].dt.strftime("%Y-%m-%d")
            + " "
            + work.loc[has_time, "match_time"].astype(str),
            errors="coerce",
        )
        if local_naive.isna().any():
            raise ValueError("invalid Football-Data match_time")
        availability.loc[has_time] = (
            local_naive.dt.tz_localize(local_tz, ambiguous="raise", nonexistent="raise")
            .dt.tz_convert("UTC")
            + RESULT_AVAILABILITY_BUFFER
        )

    cutoff_local_date = cutoff.tz_convert(local_tz).date()
    known_safe = has_time & availability.le(cutoff)
    missing_safe_before = pd.Timestamp(cutoff_local_date) - pd.Timedelta(days=2)
    missing_safe = (~has_time) & work["match_date"].lt(missing_safe_before)
    safe = work.loc[known_safe | missing_safe, HISTORY_COLUMNS].copy()
    return safe.sort_values(["match_date", "match_time"], na_position="first").reset_index(drop=True)


def build_feature_frame_allow_cold_start(
    history: pd.DataFrame,
    *,
    home_team: str,
    away_team: str,
    home_odds: float,
    draw_odds: float,
    away_odds: float,
) -> tuple[pd.DataFrame, bool, bool]:
    odds = np.asarray([home_odds, draw_odds, away_odds], dtype=float)
    if not np.isfinite(odds).all() or (odds <= 1.0).any():
        raise ValueError("invalid 1X2 odds")

    team_history, home_venue_history, away_venue_history, ratings = calculate_current_state(history)
    known = set(team_history)
    home_history = team_history.get(home_team, [])[-LAST_MATCHES:]
    away_history = team_history.get(away_team, [])[-LAST_MATCHES:]
    home_points = sum(match["points"] for match in home_history)
    away_points = sum(match["points"] for match in away_history)
    home_elo = ratings.get(home_team, INITIAL_ELO)
    away_elo = ratings.get(away_team, INITIAL_ELO)
    home_venue = home_venue_history.get(home_team, [])
    away_venue = away_venue_history.get(away_team, [])

    values = {
        "home_odds": float(home_odds),
        "draw_odds": float(draw_odds),
        "away_odds": float(away_odds),
        "home_last5_points": home_points,
        "away_last5_points": away_points,
        "form_difference": home_points - away_points,
        "home_goals_scored_last5": average([m["goals_scored"] for m in home_history]),
        "home_goals_conceded_last5": average([m["goals_conceded"] for m in home_history]),
        "away_goals_scored_last5": average([m["goals_scored"] for m in away_history]),
        "away_goals_conceded_last5": average([m["goals_conceded"] for m in away_history]),
        "home_shots_last5": average([m["shots"] for m in home_history]),
        "away_shots_last5": average([m["shots"] for m in away_history]),
        "home_shots_target_last5": average([m["shots_target"] for m in home_history]),
        "away_shots_target_last5": average([m["shots_target"] for m in away_history]),
        "home_elo": home_elo,
        "away_elo": away_elo,
        "elo_difference": home_elo + HOME_ADVANTAGE - away_elo,
        "home_venue_win_rate": average([m["win"] for m in home_venue]),
        "away_venue_win_rate": average([m["win"] for m in away_venue]),
        "home_venue_goals_scored": average([m["goals_scored"] for m in home_venue]),
        "away_venue_goals_scored": average([m["goals_scored"] for m in away_venue]),
    }
    return (
        pd.DataFrame([values], columns=FEATURES),
        home_team in known,
        away_team in known,
    )


def history_sha256(history: pd.DataFrame) -> str:
    rows = []
    for row in history[HISTORY_COLUMNS].itertuples(index=False):
        rows.append(
            {
                "match_date": pd.Timestamp(row.match_date).strftime("%Y-%m-%d"),
                "match_time": None if row.match_time is None else str(row.match_time),
                "home_team": str(row.home_team),
                "away_team": str(row.away_team),
                "home_goals": float(row.home_goals),
                "away_goals": float(row.away_goals),
                "result": str(row.result),
                "home_shots": float(row.home_shots),
                "away_shots": float(row.away_shots),
                "home_shots_target": float(row.home_shots_target),
                "away_shots_target": float(row.away_shots_target),
            }
        )
    return canonical_json_sha256(rows)


def feature_sha256(features: pd.DataFrame) -> str:
    record = {column: float(features.iloc[0][column]) for column in FEATURES}
    return canonical_json_sha256([record])


def cohort_inventory_sha256(cohort: pd.DataFrame) -> str:
    records = []
    for row in cohort.itertuples(index=False):
        records.append(
            {
                "league": str(row.league),
                "event_id": str(row.event_id),
                "home_team": str(row.home_team),
                "away_team": str(row.away_team),
                "kickoff_utc": pd.Timestamp(row.kickoff_utc).isoformat(),
                "prediction_time_utc": pd.Timestamp(row.prediction_time_utc).isoformat(),
                "snapshot_time_utc": pd.Timestamp(row.snapshot_time_utc).isoformat(),
                "home_odds": float(row.home_odds),
                "draw_odds": float(row.draw_odds),
                "away_odds": float(row.away_odds),
                "market_home_prob": float(row.market_home_prob),
                "market_draw_prob": float(row.market_draw_prob),
                "market_away_prob": float(row.market_away_prob),
            }
        )
    return canonical_json_sha256(records)


def run_replay() -> tuple[pd.DataFrame, dict]:
    model_digest = sha256_file(MODEL_PATH)
    if model_digest != FROZEN_MODEL_SHA256:
        raise RuntimeError(
            f"production model SHA mismatch: expected={FROZEN_MODEL_SHA256}, actual={model_digest}"
        )
    model = joblib.load(MODEL_PATH)
    if list(map(str, model.feature_names_in_)) != FEATURES:
        raise RuntimeError("production model feature schema mismatch")

    ledger = fetch_all("league_prediction_ledger", LEDGER_COLUMNS)
    odds = fetch_all("odds_snapshots", ODDS_COLUMNS)
    cohort = build_frozen_cohort(ledger, odds)
    inventory_sha = cohort_inventory_sha256(cohort)

    histories = {league: load_league_history(league) for league in EXPECTED_COUNTS}

    output_rows: list[dict] = []
    for row in cohort.itertuples(index=False):
        league = str(row.league)
        snapshot = pd.Timestamp(row.snapshot_time_utc)
        safe_history = history_as_of_snapshot(
            histories[league],
            snapshot,
            LEAGUE_SPECS[league].timezone,
        )
        if safe_history.empty:
            raise RuntimeError(f"empty safe history for {league}/{row.event_id}")
        features, home_known, away_known = build_feature_frame_allow_cold_start(
            safe_history,
            home_team=str(row.home_team),
            away_team=str(row.away_team),
            home_odds=float(row.home_odds),
            draw_odds=float(row.draw_odds),
            away_odds=float(row.away_odds),
        )
        probs = np.asarray(model.predict_proba(features)[0], dtype=float)
        probs = probs / probs.sum()
        if probs.shape != (3,) or not np.isfinite(probs).all() or (probs < 0).any():
            raise RuntimeError(f"invalid model probabilities for {league}/{row.event_id}")

        out = {
            "experiment_id": EXPERIMENT_ID,
            "evidence_class": EVIDENCE_CLASS,
            "prospective": False,
            "outcome_fields_read": False,
            "league": league,
            "event_id": str(row.event_id),
            "home_team": str(row.home_team),
            "away_team": str(row.away_team),
            "kickoff_utc": pd.Timestamp(row.kickoff_utc).isoformat(),
            "market_snapshot_time_utc": snapshot.isoformat(),
            "home_odds": float(row.home_odds),
            "draw_odds": float(row.draw_odds),
            "away_odds": float(row.away_odds),
            "market_home_prob": float(row.market_home_prob),
            "market_draw_prob": float(row.market_draw_prob),
            "market_away_prob": float(row.market_away_prob),
            "model_home_prob": float(probs[0]),
            "model_draw_prob": float(probs[1]),
            "model_away_prob": float(probs[2]),
            "home_history_known": bool(home_known),
            "away_history_known": bool(away_known),
            "history_rows": int(len(safe_history)),
            "history_max_match_date": pd.Timestamp(safe_history["match_date"].max()).strftime("%Y-%m-%d"),
            "history_sha256": history_sha256(safe_history),
            "feature_sha256": feature_sha256(features),
            "model_artifact_sha256": model_digest,
            "source_code_commit": SOURCE_CODE_COMMIT,
            "model_git_blob_sha": MODEL_GIT_BLOB_SHA,
            "feature_formula_git_blob_sha": FEATURE_FORMULA_GIT_BLOB_SHA,
            "cohort_inventory_sha256": inventory_sha,
        }
        for column in FEATURES:
            out[f"feature_{column}"] = float(features.iloc[0][column])
        output_rows.append(out)

    output = pd.DataFrame(output_rows).sort_values(
        ["league", "kickoff_utc", "event_id"], kind="stable"
    ).reset_index(drop=True)
    counts = output.groupby("league")["event_id"].nunique().to_dict()
    if counts != EXPECTED_COUNTS or len(output) != sum(EXPECTED_COUNTS.values()):
        raise RuntimeError("replay output coverage mismatch")

    manifest = {
        "experiment_id": EXPERIMENT_ID,
        "evidence_class": EVIDENCE_CLASS,
        "prospective": False,
        "outcome_fields_read": False,
        "model_artifact_sha256": model_digest,
        "source_code_commit": SOURCE_CODE_COMMIT,
        "model_git_blob_sha": MODEL_GIT_BLOB_SHA,
        "feature_formula_git_blob_sha": FEATURE_FORMULA_GIT_BLOB_SHA,
        "cohort_inventory_sha256": inventory_sha,
        "league_counts": counts,
        "total_events": int(len(output)),
        "history_source": "football-data.co.uk CSV; seasons 2016-2017 through 2026-2027",
        "current_season_admission_rule": "rows dated before 2026-09-11; exact per-event availability then filtered to saved market snapshot with +4h result buffer",
        "bet_decision": "NO_BET",
        "evaluation_status": "FROZEN_REPLAY_OUTPUTS_NOT_YET_JOINED_TO_OUTCOMES",
    }
    return output, manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="artifacts/point_in_time_cross_league_replay_v1.csv")
    parser.add_argument("--manifest", default="artifacts/point_in_time_cross_league_replay_v1_manifest.json")
    args = parser.parse_args()

    output, manifest = run_replay()
    output_path = Path(args.output)
    manifest_path = Path(args.manifest)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(output_path, index=False)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
