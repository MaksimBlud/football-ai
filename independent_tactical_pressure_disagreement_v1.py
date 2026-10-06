"""Frozen independent tactical-pressure disagreement experiment (#568).

The football-only estimate uses prior-match Understat tactical fields and never
consumes bookmaker information.  Average Football-Data 1X2 odds are used only
as the control.  Reserved validation/test outcomes are read only after the
timestamp/source audit and the outcome-free disagreement support gate pass.
"""
from __future__ import annotations

import math
from io import BytesIO
from typing import Any

import numpy as np
import pandas as pd
import requests
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from cross_league_direct_markets_transport import _official_or_pinned_mirror_get
from v2b_true_xg_replay_feasibility_v1 import (
    LEAGUE_SLUGS,
    fetch_understat_league,
    resolve_team_title,
)
from v2b_understat_tactical_pressure_feasibility_v1 import (
    TACTICAL_FIELDS,
    prepare_tactical_histories,
)


EXPERIMENT_ID = "INDEPENDENT_TACTICAL_PRESSURE_DISAGREEMENT_V1"
FOOTBALL_DATA_BASE = "https://www.football-data.co.uk/mmz4281/{code}/{competition}.csv"
LEAGUES = {
    "EPL": "E0",
    "LA_LIGA": "SP1",
    "SERIE_A": "I1",
    "BUNDESLIGA": "D1",
    "LIGUE_1": "F1",
}
SEASON_CODES = {
    f"{year % 100:02d}{(year + 1) % 100:02d}": year for year in range(2019, 2026)
}
DEVELOPMENT = {year for year in range(2019, 2024)}
VALIDATION = 2024
TEST = 2025
REQUIRED_FOOTBALL_DATA_COLUMNS = {
    "Date",
    "HomeTeam",
    "AwayTeam",
    "FTR",
    "AvgH",
    "AvgD",
    "AvgA",
}
RESULT_TO_INT = {"H": 0, "D": 1, "A": 2}
BOOTSTRAP_DRAWS = 5000
SEED = 20261006
MIN_SPLIT_DISAGREEMENTS = 50
MIN_LEAGUE_DISAGREEMENTS = 8

# Football-Data target title -> Understat title.  Identity normalization and
# the existing provider-lock aliases still apply after this explicit map.
FOOTBALL_DATA_ALIASES = {
    "EPL": {
        "Man City": "Manchester City",
        "Man United": "Manchester United",
        "Newcastle": "Newcastle United",
        "Nott'm Forest": "Nottingham Forest",
        "Wolves": "Wolverhampton Wanderers",
        "Leeds": "Leeds United",
        "Leicester": "Leicester City",
        "West Ham": "West Ham United",
        "Sheffield United": "Sheffield United",
    },
    "LA_LIGA": {
        "Alaves": "Alaves",
        "Ath Bilbao": "Athletic Club",
        "Ath Madrid": "Atletico Madrid",
        "Betis": "Real Betis",
        "Celta": "Celta Vigo",
        "Espanol": "Espanyol",
        "La Coruna": "Deportivo La Coruna",
        "Sociedad": "Real Sociedad",
        "Vallecano": "Rayo Vallecano",
    },
    "SERIE_A": {
        "Inter": "Inter",
        "Milan": "AC Milan",
        "Roma": "Roma",
        "Verona": "Hellas Verona",
        "Parma": "Parma Calcio 1913",
    },
    "BUNDESLIGA": {
        "Bayern Munich": "Bayern Munich",
        "Dortmund": "Borussia Dortmund",
        "Ein Frankfurt": "Eintracht Frankfurt",
        "FC Koln": "FC Cologne",
        "Freiburg": "Freiburg",
        "Hertha": "Hertha Berlin",
        "Hoffenheim": "Hoffenheim",
        "Leverkusen": "Bayer Leverkusen",
        "M'gladbach": "Borussia M.Gladbach",
        "Mainz": "Mainz 05",
        "RB Leipzig": "RasenBallsport Leipzig",
        "Schalke 04": "Schalke 04",
        "Union Berlin": "Union Berlin",
    },
    "LIGUE_1": {
        "Paris SG": "Paris Saint Germain",
        "St Etienne": "Saint-Etienne",
    },
}

FEATURES = [
    f"{side}_{field}_last5"
    for side in ("home", "away")
    for field in TACTICAL_FIELDS
] + [f"diff_{field}_last5" for field in TACTICAL_FIELDS]


def _number(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return math.nan
    return number if math.isfinite(number) else math.nan


def _market_probabilities(row: pd.Series) -> tuple[float, float, float] | None:
    odds = np.asarray(
        [_number(row.get("AvgH")), _number(row.get("AvgD")), _number(row.get("AvgA"))],
        dtype=float,
    )
    if not np.isfinite(odds).all() or not (odds > 1.0).all():
        return None
    inverse = 1.0 / odds
    probabilities = inverse / inverse.sum()
    return tuple(float(value) for value in probabilities)


def _resolve_football_data_team(
    *, league: str, target_team: str, source_titles: list[str]
) -> str | None:
    mapped = FOOTBALL_DATA_ALIASES.get(league, {}).get(target_team, target_team)
    return resolve_team_title(
        league=league,
        target_team=mapped,
        source_titles=source_titles,
    )


def _same_season_snapshot(
    history: pd.DataFrame,
    *,
    season_start: int,
    target_date: pd.Timestamp,
) -> dict[str, float] | None:
    """Return exactly the prior five same-season rows, excluding target day."""
    dates = pd.to_datetime(history["match_date"], errors="coerce")
    prior = history[
        (history["season_start"] == season_start)
        & (dates.dt.normalize() < pd.Timestamp(target_date).normalize())
    ].sort_values("match_date", kind="stable")
    recent = prior.tail(5)
    if len(recent) != 5:
        return None
    if not np.isfinite(recent[list(TACTICAL_FIELDS)].to_numpy(float)).all():
        return None
    return {field: float(recent[field].mean()) for field in TACTICAL_FIELDS}


def _download_and_audit() -> tuple[
    dict[tuple[str, int], bytes],
    dict[str, list[tuple[int, dict[str, Any]]]],
    dict[str, Any],
    bool,
]:
    """Fetch and audit every frozen source before any FTR value is read."""
    football_payloads: dict[tuple[str, int], bytes] = {}
    football_files: dict[str, Any] = {}
    source_gate = True
    original_get = requests.get
    try:
        requests.get = _official_or_pinned_mirror_get
        for league, competition in LEAGUES.items():
            for code, season_start in SEASON_CODES.items():
                response = requests.get(
                    FOOTBALL_DATA_BASE.format(code=code, competition=competition),
                    timeout=60,
                )
                response.raise_for_status()
                payload = response.content
                header = pd.read_csv(BytesIO(payload), nrows=0)
                missing = sorted(REQUIRED_FOOTBALL_DATA_COLUMNS - set(header.columns))
                football_files[f"{league}:{season_start}"] = {
                    "missing_required_columns": missing,
                    "market_triplet": ["AvgH", "AvgD", "AvgA"],
                }
                source_gate = source_gate and not missing
                football_payloads[(league, season_start)] = payload
    finally:
        requests.get = original_get

    understat_payloads: dict[str, list[tuple[int, dict[str, Any]]]] = {}
    understat_files: dict[str, Any] = {}
    with requests.Session() as session:
        for league in LEAGUES:
            league_payloads: list[tuple[int, dict[str, Any]]] = []
            for season_start in SEASON_CODES.values():
                payload = fetch_understat_league(
                    session,
                    league=league,
                    season=season_start,
                )
                _, titles, capability = prepare_tactical_histories(
                    [(season_start, payload)]
                )
                required_seen = capability["required_fields_seen"]
                ready = bool(titles) and all(required_seen.values())
                understat_files[f"{league}:{season_start}"] = {
                    "team_count": len(titles),
                    "valid_tactical_rows": capability["valid_tactical_rows"],
                    "required_fields_seen": required_seen,
                    "schema_ready": ready,
                }
                source_gate = source_gate and ready
                league_payloads.append((season_start, payload))
            understat_payloads[league] = league_payloads

    audit = {
        "outcome_read_before_audit": False,
        "reserved_outcomes_read_before_support_gate": False,
        "football_data_files": football_files,
        "understat_files": understat_files,
        "required_understat_fields": list(TACTICAL_FIELDS),
        "header_and_schema_gate_passed": source_gate,
        "opened_2026_27_outcomes": False,
    }
    return football_payloads, understat_payloads, audit, source_gate


def build_feature_rows(
    football_payloads: dict[tuple[str, int], bytes],
    understat_payloads: dict[str, list[tuple[int, dict[str, Any]]]],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Build outcome-free target rows from prior same-season Understat history."""
    histories_by_league: dict[str, dict[str, pd.DataFrame]] = {}
    titles_by_league: dict[str, list[str]] = {}
    for league, payloads in understat_payloads.items():
        histories, titles, _ = prepare_tactical_histories(payloads)
        histories_by_league[league] = histories
        titles_by_league[league] = titles

    rows: list[dict[str, Any]] = []
    coverage: dict[str, Any] = {}
    target_columns = REQUIRED_FOOTBALL_DATA_COLUMNS - {"FTR"}
    for (league, season_start), payload in sorted(football_payloads.items()):
        frame = pd.read_csv(BytesIO(payload), usecols=lambda c: c in target_columns)
        frame["_date"] = pd.to_datetime(frame["Date"], dayfirst=True, errors="coerce")
        histories = histories_by_league.get(league, {})
        titles = titles_by_league.get(league, [])
        identity_matched = 0
        eligible = 0
        for source_row, row in frame.iterrows():
            target_date = row["_date"]
            if pd.isna(target_date):
                continue
            home_team = str(row.get("HomeTeam") or "").strip()
            away_team = str(row.get("AwayTeam") or "").strip()
            home_title = _resolve_football_data_team(
                league=league, target_team=home_team, source_titles=titles
            )
            away_title = _resolve_football_data_team(
                league=league, target_team=away_team, source_titles=titles
            )
            if home_title not in histories or away_title not in histories:
                continue
            identity_matched += 1
            home_snapshot = _same_season_snapshot(
                histories[home_title],
                season_start=season_start,
                target_date=pd.Timestamp(target_date),
            )
            away_snapshot = _same_season_snapshot(
                histories[away_title],
                season_start=season_start,
                target_date=pd.Timestamp(target_date),
            )
            market = _market_probabilities(row)
            if home_snapshot is None or away_snapshot is None or market is None:
                continue
            record: dict[str, Any] = {
                "league": league,
                "season_start": season_start,
                "source_row": int(source_row),
                "match_date": pd.Timestamp(target_date),
                "home_team": home_team,
                "away_team": away_team,
                "market_home": market[0],
                "market_draw": market[1],
                "market_away": market[2],
            }
            for field in TACTICAL_FIELDS:
                record[f"home_{field}_last5"] = home_snapshot[field]
                record[f"away_{field}_last5"] = away_snapshot[field]
                record[f"diff_{field}_last5"] = (
                    home_snapshot[field] - away_snapshot[field]
                )
            rows.append(record)
            eligible += 1
        coverage[f"{league}:{season_start}"] = {
            "raw_rows": int(len(frame)),
            "identity_matched_rows": identity_matched,
            "eligible_rows": eligible,
        }
    return pd.DataFrame(rows), coverage


def _attach_outcomes(
    rows: pd.DataFrame,
    football_payloads: dict[tuple[str, int], bytes],
    *,
    allowed_seasons: set[int],
) -> pd.DataFrame:
    """Read outcomes only for the explicitly permitted temporal partitions."""
    parts: list[pd.DataFrame] = []
    for (league, season_start), payload in sorted(football_payloads.items()):
        if season_start not in allowed_seasons:
            continue
        part = rows[
            (rows["league"] == league) & (rows["season_start"] == season_start)
        ].copy()
        if part.empty:
            continue
        outcomes = pd.read_csv(BytesIO(payload), usecols=["FTR"])["FTR"]
        part["outcome"] = [RESULT_TO_INT.get(str(outcomes.iloc[index])) for index in part["source_row"]]
        part = part[part["outcome"].notna()].copy()
        part["outcome"] = part["outcome"].astype(int)
        parts.append(part)
    if not parts:
        return pd.DataFrame(columns=[*rows.columns, "outcome"])
    return pd.concat(parts, ignore_index=True)


def _model() -> Pipeline:
    return Pipeline(
        [
            ("scale", StandardScaler()),
            ("model", LogisticRegression(max_iter=2000, solver="lbfgs")),
        ]
    )


def _mark_disagreements(model: Pipeline, rows: pd.DataFrame) -> pd.DataFrame:
    marked = rows.copy()
    football = model.predict_proba(marked[FEATURES])
    market = marked[["market_home", "market_draw", "market_away"]].to_numpy(float)
    marked["football_home"] = football[:, 0]
    marked["football_draw"] = football[:, 1]
    marked["football_away"] = football[:, 2]
    marked["disagreement"] = football.argmax(axis=1) != market.argmax(axis=1)
    return marked


def _support(marked: pd.DataFrame) -> dict[str, Any]:
    splits: dict[str, Any] = {}
    supported = True
    for name, season_start in (("validation", VALIDATION), ("test", TEST)):
        subset = marked[(marked["season_start"] == season_start) & marked["disagreement"]]
        by_league = {
            league: int((subset["league"] == league).sum()) for league in LEAGUES
        }
        split_ok = len(subset) >= MIN_SPLIT_DISAGREEMENTS and all(
            count >= MIN_LEAGUE_DISAGREEMENTS for count in by_league.values()
        )
        splits[name] = {
            "disagreement_rows": int(len(subset)),
            "eligible_rows": int((marked["season_start"] == season_start).sum()),
            "by_league": by_league,
            "support_gate_passed": split_ok,
        }
        supported = supported and split_ok
    return {
        "minimum_split_disagreements": MIN_SPLIT_DISAGREEMENTS,
        "minimum_per_league_disagreements": MIN_LEAGUE_DISAGREEMENTS,
        "splits": splits,
        "passed": supported,
    }


def _per_match_losses(
    outcome: np.ndarray, probabilities: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    clipped = np.clip(probabilities, 1e-15, 1.0)
    log_loss = -np.log(clipped[np.arange(len(outcome)), outcome])
    one_hot = np.eye(3)[outcome]
    brier = np.sum((probabilities - one_hot) ** 2, axis=1)
    return log_loss, brier


def _evaluate_split(rows: pd.DataFrame) -> tuple[dict[str, Any], pd.DataFrame]:
    evaluated = rows[rows["disagreement"]].copy()
    outcome = evaluated["outcome"].to_numpy(int)
    football = evaluated[["football_home", "football_draw", "football_away"]].to_numpy(float)
    market = evaluated[["market_home", "market_draw", "market_away"]].to_numpy(float)
    football_ll, football_brier = _per_match_losses(outcome, football)
    market_ll, market_brier = _per_match_losses(outcome, market)
    losses = evaluated[["league", "home_team", "away_team"]].copy()
    losses["log_loss_delta"] = football_ll - market_ll
    losses["brier_delta"] = football_brier - market_brier
    summary = {
        "rows": int(len(losses)),
        "football_log_loss": float(football_ll.mean()),
        "market_log_loss": float(market_ll.mean()),
        "football_minus_market_log_loss": float(losses["log_loss_delta"].mean()),
        "football_brier": float(football_brier.mean()),
        "market_brier": float(market_brier.mean()),
        "football_minus_market_brier": float(losses["brier_delta"].mean()),
        "by_league": {
            league: {
                "rows": int(len(part)),
                "football_minus_market_log_loss": float(part["log_loss_delta"].mean()),
                "football_minus_market_brier": float(part["brier_delta"].mean()),
            }
            for league, part in losses.groupby("league")
        },
    }
    return summary, losses


def _bootstrap(losses: pd.DataFrame) -> dict[str, Any]:
    groups = [part["log_loss_delta"].to_numpy(float) for _, part in losses.groupby("league")]
    if not groups or any(len(values) == 0 for values in groups):
        return {"draws": BOOTSTRAP_DRAWS, "ci95_low": None, "ci95_high": None}
    rng = np.random.default_rng(SEED)
    draws = np.empty(BOOTSTRAP_DRAWS)
    for index in range(BOOTSTRAP_DRAWS):
        sample = np.concatenate(
            [values[rng.integers(0, len(values), len(values))] for values in groups]
        )
        draws[index] = float(sample.mean())
    return {
        "draws": BOOTSTRAP_DRAWS,
        "ci95_low": float(np.quantile(draws, 0.025)),
        "ci95_high": float(np.quantile(draws, 0.975)),
    }


def _formal_gate(validation: dict[str, Any], test: dict[str, Any]) -> dict[str, Any]:
    league_deltas = [
        part["football_minus_market_log_loss"]
        for part in test.get("by_league", {}).values()
    ]
    negative_leagues = sum(value < 0 for value in league_deltas)
    gates = {
        "validation_log_loss_improves": validation.get("football_minus_market_log_loss", 0) < 0,
        "validation_brier_improves": validation.get("football_minus_market_brier", 0) < 0,
        "test_log_loss_improves": test.get("football_minus_market_log_loss", 0) < 0,
        "test_brier_improves": test.get("football_minus_market_brier", 0) < 0,
        "test_log_loss_ci95_upper_below_zero": (
            test.get("bootstrap", {}).get("ci95_high") is not None
            and test["bootstrap"]["ci95_high"] < 0
        ),
        "at_least_four_negative_test_leagues": (
            len(league_deltas) == len(LEAGUES) and negative_leagues >= 4
        ),
        "no_test_league_delta_above_0_01": (
            len(league_deltas) == len(LEAGUES)
            and all(value <= 0.01 for value in league_deltas)
        ),
    }
    return {"supported": all(gates.values()), "gates": gates}


def _blocked(audit: dict[str, Any], reason: str, decision: str) -> dict[str, Any]:
    empty = {
        "rows": 0,
        "football_minus_market_log_loss": None,
        "football_minus_market_brier": None,
        "by_league": {},
    }
    return {
        "experiment_id": EXPERIMENT_ID,
        "research_only": True,
        "source_audit": audit,
        "validation": empty,
        "test": {
            **empty,
            "bootstrap": {"draws": BOOTSTRAP_DRAWS, "ci95_low": None, "ci95_high": None},
        },
        "formal_gate": {"supported": False, "reason": reason, "gates": {}},
        "supported": False,
        "decision": decision,
        "interpretation_guard": reason,
        "paid_odds_api_calls": 0,
        "supabase_writes": 0,
        "production_operations": False,
        "production_promotion": False,
        "result": "RESEARCH_ONLY_NO_BET",
    }


def evaluate_payloads(
    football_payloads: dict[tuple[str, int], bytes],
    understat_payloads: dict[str, list[tuple[int, dict[str, Any]]]],
    audit: dict[str, Any],
) -> dict[str, Any]:
    features, coverage = build_feature_rows(football_payloads, understat_payloads)
    audit = {**audit, "coverage": coverage}
    required = DEVELOPMENT | {VALIDATION, TEST}
    if features.empty or not required.issubset(set(features["season_start"])):
        return _blocked(
            audit,
            "Frozen source/matching design has insufficient eligible rows.",
            "BLOCKED_BY_SOURCE_GAP",
        )

    development = _attach_outcomes(
        features, football_payloads, allowed_seasons=DEVELOPMENT
    )
    if development.empty or set(development["outcome"]) != {0, 1, 2}:
        return _blocked(
            audit,
            "Development split lacks all 1X2 classes after frozen matching.",
            "BLOCKED_BY_SOURCE_GAP",
        )
    model = _model()
    model.fit(development[FEATURES], development["outcome"].to_numpy(int))
    marked = _mark_disagreements(
        model, features[features["season_start"].isin({VALIDATION, TEST})]
    )
    support = _support(marked)
    audit["disagreement_support"] = support
    if not support["passed"]:
        return _blocked(
            audit,
            "Frozen disagreement class failed the preregistered outcome-free support gate.",
            "BLOCKED_LOW_DISAGREEMENT_SAMPLE",
        )

    reserved = _attach_outcomes(
        marked,
        football_payloads,
        allowed_seasons={VALIDATION, TEST},
    )
    audit["reserved_outcomes_read_after_support_gate"] = True
    validation, _ = _evaluate_split(reserved[reserved["season_start"] == VALIDATION])
    test, test_losses = _evaluate_split(reserved[reserved["season_start"] == TEST])
    test["bootstrap"] = _bootstrap(test_losses)
    gate = _formal_gate(validation, test)
    supported = bool(gate["supported"])
    return {
        "experiment_id": EXPERIMENT_ID,
        "evidence_class": "INDEPENDENT_FOOTBALL_ESTIMATE_VS_MARKET_DISAGREEMENT",
        "research_only": True,
        "source_audit": audit,
        "temporal_design": {
            "development": [f"{year}-{year + 1}" for year in sorted(DEVELOPMENT)],
            "validation": "2024-2025",
            "untouched_test": "2025-2026",
            "opened_2026_27_outcomes": False,
            "test_model_refit_on_validation": False,
        },
        "feature_contract": {
            "source": "Understat public league team history",
            "fields": list(TACTICAL_FIELDS),
            "window": 5,
            "same_season_only": True,
            "features": FEATURES,
            "uses_bookmaker_inputs": False,
        },
        "control_contract": {
            "source": "Football-Data average bookmaker 1X2",
            "odds_fields": ["AvgH", "AvgD", "AvgA"],
            "devig": "multiplicative",
        },
        "disagreement_contract": "football_argmax != market_argmax",
        "validation": validation,
        "test": test,
        "formal_gate": gate,
        "supported": supported,
        "decision": (
            "SUPPORTED_INDEPENDENT_TACTICAL_DISAGREEMENT_EDGE"
            if supported
            else "NO_STABLE_INDEPENDENT_TACTICAL_DISAGREEMENT_EDGE"
        ),
        "interpretation_guard": (
            "The frozen independent tactical estimate passed every temporal, uncertainty and cross-league disagreement gate; this is research evidence only and does not authorize blending, betting or production."
            if supported
            else "The frozen independent tactical estimate failed at least one preregistered validation, untouched-test, uncertainty or cross-league gate; do not tune the disagreement class on these outcomes."
        ),
        "paid_odds_api_calls": 0,
        "supabase_writes": 0,
        "production_operations": False,
        "production_promotion": False,
        "result": "RESEARCH_ONLY_NO_BET",
    }


def evaluate() -> dict[str, Any]:
    football, understat, audit, source_gate = _download_and_audit()
    if not source_gate:
        return _blocked(
            audit,
            "Required zero-cost Football-Data or Understat source contract is unavailable.",
            "BLOCKED_BY_SOURCE_GAP",
        )
    return evaluate_payloads(football, understat, audit)


if __name__ == "__main__":
    import json

    print(json.dumps(evaluate(), indent=2, ensure_ascii=False))
