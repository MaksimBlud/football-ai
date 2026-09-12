from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, Mapping


LEAGUES = (
    "EPL",
    "LA_LIGA",
    "SERIE_A",
    "BUNDESLIGA",
    "LIGUE_1",
    "EREDIVISIE",
    "TURKEY_SUPER_LIG",
    "PRIMEIRA_LIGA",
)
V1_1_FREEZE_UTC = datetime(2026, 9, 12, 2, 4, 34, tzinfo=timezone.utc)
MIN_UNIQUE_EVENTS_PER_LEAGUE = 100
MIN_KICKOFF_MONTHS_PER_LEAGUE = 4
OUTCOME_DELAY_HOURS = 24
SEED_MANIFEST = Path(__file__).parent / "research" / "ALL_LEAGUES_MARKET_ONLY_V1_1_MANIFEST.json"


class EvaluationGateInputError(ValueError):
    pass


def _utc(value: object, field: str) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise EvaluationGateInputError(f"Invalid {field}: {value!r}") from exc
    else:
        raise EvaluationGateInputError(f"Missing/invalid {field}: {value!r}")
    if parsed.tzinfo is None:
        raise EvaluationGateInputError(f"{field} must be timezone-aware")
    return parsed.astimezone(timezone.utc)


def load_seed_keys(path: Path = SEED_MANIFEST) -> frozenset[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    keys: list[str] = []
    for league in LEAGUES:
        entry = payload["leagues"][league]
        keys.extend(entry["prediction_keys"])
    if len(keys) != 127 or len(set(keys)) != 127:
        raise EvaluationGateInputError("Seed manifest must contain exactly 127 unique prediction keys")
    return frozenset(keys)


def _validate_probabilities(row: Mapping[str, object]) -> None:
    values = []
    for field in ("market_home_prob", "market_draw_prob", "market_away_prob"):
        try:
            value = float(row[field])
        except (KeyError, TypeError, ValueError) as exc:
            raise EvaluationGateInputError(f"Missing/invalid {field}") from exc
        if not math.isfinite(value) or value < 0.0 or value > 1.0:
            raise EvaluationGateInputError(f"Invalid {field}: {value!r}")
        values.append(value)
    if abs(sum(values) - 1.0) > 1e-6:
        raise EvaluationGateInputError("Market probabilities must sum to 1")


def _validated_row(row: Mapping[str, object]) -> dict[str, object]:
    league = str(row.get("league", ""))
    event_id = str(row.get("event_id", ""))
    prediction_key = str(row.get("prediction_key", ""))
    if league not in LEAGUES:
        raise EvaluationGateInputError(f"Unexpected league: {league!r}")
    if not event_id or not prediction_key.startswith(f"{league}:"):
        raise EvaluationGateInputError("Missing event_id or malformed prediction_key")
    if row.get("prediction_mode") != "MARKET_ONLY":
        raise EvaluationGateInputError("Only MARKET_ONLY rows are admissible")
    if row.get("structural_applied") is not False:
        raise EvaluationGateInputError("structural_applied must be false")

    kickoff = _utc(row.get("kickoff_utc"), "kickoff_utc")
    prediction_time = _utc(row.get("prediction_time_utc"), "prediction_time_utc")
    snapshot_time = _utc(row.get("snapshot_time_utc"), "snapshot_time_utc")
    created_at = _utc(row.get("created_at_utc"), "created_at_utc")
    if prediction_time >= kickoff or snapshot_time >= kickoff or created_at >= kickoff:
        raise EvaluationGateInputError("Prediction, snapshot and durable creation must all be strictly pre-kickoff")
    _validate_probabilities(row)

    return {
        "league": league,
        "event_id": event_id,
        "prediction_key": prediction_key,
        "kickoff_utc": kickoff,
        "prediction_time_utc": prediction_time,
        "snapshot_time_utc": snapshot_time,
        "created_at_utc": created_at,
    }


def select_event_rows(
    rows: Iterable[Mapping[str, object]],
    *,
    seed_keys: frozenset[str] | None = None,
) -> list[dict[str, object]]:
    seed_keys = load_seed_keys() if seed_keys is None else seed_keys
    grouped: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for raw in rows:
        row = _validated_row(raw)
        grouped[(str(row["league"]), str(row["event_id"]))].append(row)

    selected: list[dict[str, object]] = []
    for group in grouped.values():
        seed = [row for row in group if row["prediction_key"] in seed_keys]
        if seed:
            distinct = {str(row["prediction_key"]) for row in seed}
            if len(distinct) != 1:
                raise EvaluationGateInputError("Multiple frozen seed keys map to one event")
            chosen = min(
                seed,
                key=lambda row: (
                    row["created_at_utc"],
                    row["prediction_time_utc"],
                    row["snapshot_time_utc"],
                    row["prediction_key"],
                ),
            )
            selected.append(chosen)
            continue

        future = [
            row
            for row in group
            if row["created_at_utc"] > V1_1_FREEZE_UTC
        ]
        if not future:
            continue
        selected.append(
            min(
                future,
                key=lambda row: (
                    row["created_at_utc"],
                    row["prediction_time_utc"],
                    row["snapshot_time_utc"],
                    row["prediction_key"],
                ),
            )
        )
    return selected


def _maturity_prefix(rows: list[dict[str, object]]) -> list[dict[str, object]] | None:
    ordered = sorted(
        rows,
        key=lambda row: (row["kickoff_utc"], row["event_id"], row["prediction_key"]),
    )
    months: set[str] = set()
    for index, row in enumerate(ordered, start=1):
        kickoff = row["kickoff_utc"]
        assert isinstance(kickoff, datetime)
        months.add(kickoff.strftime("%Y-%m"))
        if index >= MIN_UNIQUE_EVENTS_PER_LEAGUE and len(months) >= MIN_KICKOFF_MONTHS_PER_LEAGUE:
            return ordered[:index]
    return None


def evaluate_gate(
    rows: Iterable[Mapping[str, object]],
    *,
    now_utc: datetime,
    seed_keys: frozenset[str] | None = None,
    stricter_gate_clear: bool = False,
) -> dict[str, object]:
    now = _utc(now_utc, "now_utc")
    selected = select_event_rows(rows, seed_keys=seed_keys)
    by_league: dict[str, list[dict[str, object]]] = {league: [] for league in LEAGUES}
    for row in selected:
        by_league[str(row["league"])].append(row)

    per_league: dict[str, dict[str, object]] = {}
    prefixes: list[list[dict[str, object]]] = []
    for league in LEAGUES:
        rows_for_league = by_league[league]
        months = {
            row["kickoff_utc"].strftime("%Y-%m")
            for row in rows_for_league
            if isinstance(row["kickoff_utc"], datetime)
        }
        prefix = _maturity_prefix(rows_for_league)
        per_league[league] = {
            "selected_events": len(rows_for_league),
            "kickoff_calendar_months": len(months),
            "sample_ready": prefix is not None,
            "primary_prefix_events": len(prefix) if prefix is not None else None,
            "primary_prefix_last_kickoff_utc": (
                prefix[-1]["kickoff_utc"].isoformat().replace("+00:00", "Z")
                if prefix is not None
                else None
            ),
        }
        if prefix is not None:
            prefixes.append(prefix)

    if len(prefixes) != len(LEAGUES):
        return {
            "status": "SAMPLE_CLOSED",
            "outcome_read_allowed": False,
            "per_league": per_league,
            "outcome_read_not_before_utc": None,
        }

    latest_kickoff = max(
        row["kickoff_utc"]
        for prefix in prefixes
        for row in prefix
        if isinstance(row["kickoff_utc"], datetime)
    )
    not_before = latest_kickoff + timedelta(hours=OUTCOME_DELAY_HOURS)
    if now < not_before:
        status = "TIME_CLOSED"
        allowed = False
    elif not stricter_gate_clear:
        status = "STRICTER_GATE_CLOSED"
        allowed = False
    else:
        status = "OUTCOME_READ_ALLOWED"
        allowed = True

    return {
        "status": status,
        "outcome_read_allowed": allowed,
        "per_league": per_league,
        "latest_primary_prefix_kickoff_utc": latest_kickoff.isoformat().replace("+00:00", "Z"),
        "outcome_read_not_before_utc": not_before.isoformat().replace("+00:00", "Z"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Outcome-blind ALL_LEAGUES_MARKET_ONLY_V1_1 evaluation gate")
    parser.add_argument("metadata_json", type=Path, help="JSON array of canonical ledger metadata rows; no outcomes")
    parser.add_argument("--now-utc", required=True, help="Current UTC timestamp")
    parser.add_argument(
        "--stricter-gates-clear",
        action="store_true",
        help="Assert that all applicable stricter frozen league-specific outcome gates are independently clear",
    )
    args = parser.parse_args()
    rows = json.loads(args.metadata_json.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise EvaluationGateInputError("metadata_json must contain a JSON array")
    result = evaluate_gate(
        rows,
        now_utc=_utc(args.now_utc, "now_utc"),
        stricter_gate_clear=args.stricter_gates_clear,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
