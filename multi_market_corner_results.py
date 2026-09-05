"""Canonical current-season corner outcomes for Multi-Market V2 research.

The source side is intentionally limited to Football-Data CSV contracts that
are already explicit in repository runtime configuration. This module never
constructs an unconfigured league/season source.

Corner rows are not considered canonical until they reconcile one-to-one with
an existing canonical finished result on league/season/date/home/away and exact
full-time goals. Persistence is append-only and dependency-injected.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import math
from typing import Any, Iterable

import pandas as pd

from audit_multi_market_corner_outcomes import SEASON, configured_csv_contract
from league_offline_history import normalize_team, parse_football_data_date


TABLE = "league_corner_results"
SCHEMA_VERSION = "LEAGUE_CORNER_RESULT_V1"
SOURCE = "FOOTBALL_DATA_CSV_HC_AC"
IDENTITY_FIELDS = ("league", "season", "match_date", "home_team", "away_team")


class CornerResultIdentityError(ValueError):
    """A source corner row cannot be reconciled uniquely to canonical results."""


class CornerResultConflictError(RuntimeError):
    """An immutable corner-result key already exists with different content."""


def _nonnegative_int(value: Any, field: str) -> int:
    if value is None or isinstance(value, bool):
        raise ValueError(f"{field} must be a non-negative integer")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be a non-negative integer") from exc
    if not math.isfinite(number) or number < 0 or not number.is_integer():
        raise ValueError(f"{field} must be a non-negative integer")
    return int(number)


def _date_text(value: Any) -> str:
    if hasattr(value, "date"):
        return value.date().isoformat()
    text = str(value or "").strip()
    if len(text) >= 10:
        return text[:10]
    raise CornerResultIdentityError("match_date must be ISO-compatible")


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def source_fingerprint(row: dict) -> str:
    material = {
        field: row[field]
        for field in (
            "league",
            "season",
            "match_date",
            "home_team",
            "away_team",
            "home_goals",
            "away_goals",
            "home_corners",
            "away_corners",
            "source",
        )
    }
    return hashlib.sha256(_canonical_json(material).encode("utf-8")).hexdigest()


def corner_result_key(row: dict, fingerprint: str) -> str:
    identity = "|".join(str(row[field]) for field in IDENTITY_FIELDS)
    return hashlib.sha256(
        f"{identity}|{fingerprint}|{SCHEMA_VERSION}".encode("utf-8")
    ).hexdigest()


def normalize_corner_source_frame(
    config,
    frame: pd.DataFrame,
    *,
    source_url: str,
    fetched_at_utc: str | None = None,
) -> pd.DataFrame:
    """Normalize only finished rows that carry valid HC/AC outcomes."""
    contract = configured_csv_contract(config)
    if contract is None:
        raise ValueError(
            f"{config.identity.identifier}: no configured {SEASON} Football-Data CSV contract"
        )

    required = {"Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR", "HC", "AC"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError("Missing corner source columns: " + ", ".join(sorted(missing)))

    fthg = pd.to_numeric(frame["FTHG"], errors="coerce")
    ftag = pd.to_numeric(frame["FTAG"], errors="coerce")
    hc = pd.to_numeric(frame["HC"], errors="coerce")
    ac = pd.to_numeric(frame["AC"], errors="coerce")
    finished = frame["FTR"].astype(str).isin(["H", "D", "A"]) & fthg.notna() & ftag.notna()

    work = frame.loc[finished].copy()
    if work.empty:
        return pd.DataFrame(
            columns=[
                *IDENTITY_FIELDS,
                "home_goals",
                "away_goals",
                "home_corners",
                "away_corners",
                "source",
                "source_url",
                "source_competition_code",
                "source_season_code",
                "fetched_at_utc",
            ]
        )

    dates = parse_football_data_date(work["Date"])
    rows: list[dict] = []
    for index, source_row in work.iterrows():
        rows.append(
            {
                "league": config.identity.identifier,
                "season": SEASON,
                "match_date": dates.loc[index].date().isoformat(),
                "home_team": normalize_team(source_row["HomeTeam"], config),
                "away_team": normalize_team(source_row["AwayTeam"], config),
                "home_goals": _nonnegative_int(source_row["FTHG"], "home_goals"),
                "away_goals": _nonnegative_int(source_row["FTAG"], "away_goals"),
                "home_corners": _nonnegative_int(source_row["HC"], "home_corners"),
                "away_corners": _nonnegative_int(source_row["AC"], "away_corners"),
                "source": SOURCE,
                "source_url": source_url,
                "source_competition_code": contract["competition_code"],
                "source_season_code": contract["season_code"],
                "fetched_at_utc": fetched_at_utc
                or datetime.now(timezone.utc).isoformat(),
            }
        )

    result = pd.DataFrame(rows).sort_values(
        ["match_date", "home_team", "away_team"], kind="stable"
    ).reset_index(drop=True)
    if result.duplicated(subset=list(IDENTITY_FIELDS)).any():
        raise CornerResultIdentityError("duplicate normalized corner fixture identity")
    return result


def reconcile_with_finished_results(
    corner_rows: pd.DataFrame,
    finished_results: Iterable[dict],
) -> list[dict]:
    """Require exact one-to-one identity and exact full-time goal reconciliation."""
    canonical = [dict(row) for row in finished_results]
    output: list[dict] = []

    for source_row in corner_rows.to_dict(orient="records"):
        identity = tuple(str(source_row[field]) for field in IDENTITY_FIELDS)
        matches = []
        for result in canonical:
            candidate = (
                str(result.get("league") or ""),
                str(result.get("season") or ""),
                _date_text(result.get("match_date")),
                str(result.get("home_team") or ""),
                str(result.get("away_team") or ""),
            )
            if candidate == identity:
                matches.append(result)

        if not matches:
            raise CornerResultIdentityError(f"no canonical finished result for {identity!r}")
        if len(matches) != 1:
            raise CornerResultIdentityError(
                f"ambiguous canonical finished results for {identity!r}: {len(matches)}"
            )

        matched = matches[0]
        canonical_home = _nonnegative_int(matched.get("home_goals"), "canonical home_goals")
        canonical_away = _nonnegative_int(matched.get("away_goals"), "canonical away_goals")
        if canonical_home != source_row["home_goals"] or canonical_away != source_row["away_goals"]:
            raise CornerResultIdentityError(
                f"goal reconciliation mismatch for {identity!r}: "
                f"source={source_row['home_goals']}-{source_row['away_goals']} "
                f"canonical={canonical_home}-{canonical_away}"
            )

        fingerprint = source_fingerprint(source_row)
        payload = {
            "schema_version": SCHEMA_VERSION,
            "research_only": True,
            "identity_reconciled": True,
            "goals_reconciled": True,
            "home_goals": source_row["home_goals"],
            "away_goals": source_row["away_goals"],
            "home_corners": source_row["home_corners"],
            "away_corners": source_row["away_corners"],
            "source_url": source_row["source_url"],
            "source_competition_code": source_row["source_competition_code"],
            "source_season_code": source_row["source_season_code"],
        }
        output.append(
            {
                "corner_result_key": corner_result_key(source_row, fingerprint),
                **{field: source_row[field] for field in IDENTITY_FIELDS},
                "home_goals": source_row["home_goals"],
                "away_goals": source_row["away_goals"],
                "home_corners": source_row["home_corners"],
                "away_corners": source_row["away_corners"],
                "source": SOURCE,
                "source_fingerprint": fingerprint,
                "source_fetched_at_utc": source_row["fetched_at_utc"],
                "payload": payload,
            }
        )
    return output


def settlement_corner_outcome(record: dict) -> dict:
    """Project a canonical corner result into the settlement identity contract."""
    return {
        "league": record["league"],
        "match_date": record["match_date"],
        "home_team": record["home_team"],
        "away_team": record["away_team"],
        "home_corners": record["home_corners"],
        "away_corners": record["away_corners"],
    }


def _response_rows(response: Any) -> list[dict]:
    return list(getattr(response, "data", None) or [])


def persist_corner_results(client, records: Iterable[dict]) -> dict:
    """Insert immutable canonical corner-result revisions idempotently."""
    incoming = [dict(row) for row in records]
    if not incoming:
        return {"inserted": 0, "unchanged": 0, "conflicts": 0}
    keys = [str(row.get("corner_result_key") or "") for row in incoming]
    if any(not key for key in keys):
        raise ValueError("corner_result_key is required")
    if len(keys) != len(set(keys)):
        raise ValueError("duplicate corner_result_key in incoming batch")

    response = client.table(TABLE).select("*").in_("corner_result_key", keys).execute()
    existing = {str(row["corner_result_key"]): dict(row) for row in _response_rows(response)}
    inserted = 0
    unchanged = 0
    for record in incoming:
        key = str(record["corner_result_key"])
        previous = existing.get(key)
        if previous is not None:
            comparable = {field: previous.get(field) for field in record}
            if _canonical_json(comparable) != _canonical_json(record):
                raise CornerResultConflictError(f"immutable corner-result conflict for {key}")
            unchanged += 1
            continue
        client.table(TABLE).insert(record).execute()
        existing[key] = record
        inserted += 1
    return {"inserted": inserted, "unchanged": unchanged, "conflicts": 0}
