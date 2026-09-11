from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ALLOWED_LEAGUES = {"SERIE_A", "LA_LIGA"}
PROTOCOL = "NON_EPL_MARKET_ONLY_V1"
TARGET_N = 100
FORBIDDEN_FIELDS = {
    "result",
    "outcome",
    "settled",
    "settlement",
    "home_score",
    "away_score",
    "score",
    "ft_home_goals",
    "ft_away_goals",
    "winner",
}
AI_FIELDS = {
    "ai_home_probability",
    "ai_draw_probability",
    "ai_away_probability",
    "model_probability_home",
    "model_probability_draw",
    "model_probability_away",
    "model_version",
    "model_artifact",
}


@dataclass(frozen=True)
class CaptureResult:
    status: str
    league: str
    protocol: str
    observation_number: int | None
    target_n: int
    canonical_key: str
    inserted: bool
    unchanged: bool


def _parse_utc(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("timestamp must be timezone-aware")
    return dt.astimezone(timezone.utc)


def _norm_team(value: str) -> str:
    return " ".join(value.strip().lower().split())


def _canonical_key(row: dict[str, Any]) -> str:
    return "|".join(
        [
            row["league"],
            _norm_team(str(row["home_team"])),
            _norm_team(str(row["away_team"])),
            _parse_utc(str(row["commence_time_utc"])).isoformat(),
            PROTOCOL,
        ]
    )


def _validate_market(row: dict[str, Any]) -> None:
    for field in ("home_odds", "draw_odds", "away_odds"):
        if field not in row:
            raise ValueError(f"missing required market field: {field}")
        value = float(row[field])
        if not math.isfinite(value) or value <= 1.0:
            raise ValueError(f"invalid decimal odds in {field}")


def _validate_no_forbidden_fields(row: dict[str, Any]) -> None:
    present = sorted(field for field in FORBIDDEN_FIELDS if field in row and row[field] not in (None, ""))
    if present:
        raise ValueError(f"capture row contains forbidden outcome fields: {present}")


def _validate_no_ai_fields(row: dict[str, Any]) -> None:
    present = sorted(field for field in AI_FIELDS if field in row and row[field] not in (None, ""))
    if present:
        raise ValueError(
            "AI fields are forbidden by NON_EPL_MARKET_ONLY_V1 until a separate league-specific "
            f"frozen eligibility manifest exists: {present}"
        )


def validate_capture(row: dict[str, Any]) -> dict[str, Any]:
    league = str(row.get("league", "")).strip().upper()
    if league not in ALLOWED_LEAGUES:
        raise ValueError(f"unsupported league: {league!r}")
    normalized = dict(row)
    normalized["league"] = league
    for field in ("home_team", "away_team", "commence_time_utc", "captured_at_utc"):
        if not str(normalized.get(field, "")).strip():
            raise ValueError(f"missing required field: {field}")
    kickoff = _parse_utc(str(normalized["commence_time_utc"]))
    captured = _parse_utc(str(normalized["captured_at_utc"]))
    if captured >= kickoff:
        raise ValueError("prospective capture must happen strictly before kickoff")
    _validate_market(normalized)
    _validate_no_forbidden_fields(normalized)
    _validate_no_ai_fields(normalized)
    normalized["protocol"] = PROTOCOL
    normalized["target_n"] = TARGET_N
    normalized["canonical_key"] = _canonical_key(normalized)
    return normalized


def _load_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _stable_projection(row: dict[str, Any]) -> dict[str, str]:
    return {
        "league": str(row["league"]),
        "protocol": PROTOCOL,
        "target_n": str(TARGET_N),
        "canonical_key": str(row["canonical_key"]),
        "home_team": str(row["home_team"]).strip(),
        "away_team": str(row["away_team"]).strip(),
        "commence_time_utc": _parse_utc(str(row["commence_time_utc"])).isoformat(),
        "captured_at_utc": _parse_utc(str(row["captured_at_utc"])).isoformat(),
        "home_odds": str(float(row["home_odds"])),
        "draw_odds": str(float(row["draw_odds"])),
        "away_odds": str(float(row["away_odds"])),
    }


def capture_market_only(row: dict[str, Any], ledger_path: Path) -> CaptureResult:
    normalized = validate_capture(row)
    current = _load_rows(ledger_path)
    projection = _stable_projection(normalized)
    same_key = [r for r in current if r.get("canonical_key") == projection["canonical_key"]]
    if same_key:
        if len(same_key) != 1:
            raise ValueError("ledger contains duplicate canonical keys")
        existing = same_key[0]
        comparable = {k: existing.get(k, "") for k in projection}
        if comparable != projection:
            raise ValueError("conflicting rewrite for an existing prospective observation")
        try:
            observation_number = int(existing["observation_number"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("existing prospective row has invalid observation_number") from exc
        return CaptureResult(
            status="UNCHANGED",
            league=projection["league"],
            protocol=PROTOCOL,
            observation_number=observation_number,
            target_n=TARGET_N,
            canonical_key=projection["canonical_key"],
            inserted=False,
            unchanged=True,
        )

    league_rows = [
        r for r in current if r.get("league") == projection["league"] and r.get("protocol") == PROTOCOL
    ]
    if len(league_rows) >= TARGET_N:
        raise ValueError(f"prospective target already reached for {projection['league']}: {TARGET_N}/{TARGET_N}")

    existing_numbers: list[int] = []
    for existing in league_rows:
        try:
            existing_numbers.append(int(existing["observation_number"]))
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("existing prospective row has invalid observation_number") from exc
    if sorted(existing_numbers) != list(range(1, len(existing_numbers) + 1)):
        raise ValueError("ledger observation numbers are not contiguous; refusing to append")

    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "league",
        "protocol",
        "target_n",
        "observation_number",
        "canonical_key",
        "home_team",
        "away_team",
        "commence_time_utc",
        "captured_at_utc",
        "home_odds",
        "draw_odds",
        "away_odds",
    ]
    observation_number = len(league_rows) + 1
    new_row = dict(projection)
    new_row["observation_number"] = str(observation_number)
    write_header = not ledger_path.exists()
    with ledger_path.open("a", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        if write_header:
            writer.writeheader()
        writer.writerow(new_row)
    return CaptureResult(
        status="INSERTED",
        league=projection["league"],
        protocol=PROTOCOL,
        observation_number=observation_number,
        target_n=TARGET_N,
        canonical_key=projection["canonical_key"],
        inserted=True,
        unchanged=False,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Fail-closed Serie A / La Liga MARKET_ONLY prospective capture")
    parser.add_argument("--input-json", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, default=Path("experiments/non_epl_market_only_v1.csv"))
    args = parser.parse_args()
    row = json.loads(args.input_json.read_text(encoding="utf-8"))
    result = capture_market_only(row, args.ledger)
    print(json.dumps(result.__dict__, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
