"""Read-only as-of Serie A V2 feature manifest from the EXISTING Football-Data source.

Reuses the exact historical 19-feature definitions; no re-fitting, paid requests
or database writes. Date-only historical fixtures mean the manifest is DIAGNOSTIC,
not independent evidence for admission to frozen prospective V2.
"""
from __future__ import annotations

import argparse
from collections import defaultdict, deque
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import pandas as pd

from historical_football_signal_lab import TeamMatch, _snapshot, FEATURE_SETS
from serie_a_runtime_config import SERIE_A_RUNTIME_CONFIG
from serie_a_v2_frozen_shadow_preview import load_verified_original, parse_utc

STATS = ("HC", "AC", "HY", "AY", "HR", "AR")
REQUIRED = frozenset(("Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR", *STATS))
FROZEN_FEATURE_BUILDER_GIT_BLOB_SHA = "401b3a0893371bfa4a488ec92a4a54af2678c8f7"

PROTECTED_SEASON_START = pd.Timestamp("2026-07-01")


class ProtectedSeasonOutcomeError(ValueError):
    """Raised before any 2026/27 result/stat columns are processed."""


def _require_frozen_inference_scope() -> dict:
    # Keep this guard inside every public feature-building entrypoint. A CLI
    # preflight alone is not an access boundary because build_manifest() is
    # directly importable by other Python callers.
    from market_anchor_v2_source_rights import require_personal_research_inference_scope

    return require_personal_research_inference_scope()


def _assert_no_protected_season_history(history: pd.DataFrame) -> pd.Series:
    """Inspect only date values and reject protected 2026/27 rows before outcomes."""
    if not isinstance(history, pd.DataFrame) or "Date" not in history.columns:
        raise ValueError("historical source requires a Date column")
    dates = pd.to_datetime(history["Date"], dayfirst=True, format="mixed", errors="raise")
    if dates.isna().any():
        raise ValueError("unparseable historical match date")
    if dates.dt.tz is not None:
        raise ValueError("expected date-only historical source")
    if (dates >= PROTECTED_SEASON_START).any():
        raise ProtectedSeasonOutcomeError(
            "protected Serie A 2026/27 outcomes cannot enter original V2 feature construction before the frozen outcome gate"
        )
    return dates

# Only the restored original Serie A V2 feature source. Bookmaker fixture
# labels are not training team IDs: all 10 verified historical I1 seasons call
# this club "Atalanta", whereas the saved 2026 bookmaker fixtures use
# "Atalanta BC". Keep this adapter local to V2; other league/product models
# and the frozen candidate's feature order/weights remain untouched.
V2_HISTORICAL_TEAM_ALIASES = {"Atalanta BC": "Atalanta"}


def _git_blob_sha1(path: Path) -> str:
    payload = path.read_bytes()
    return hashlib.sha1(f"blob {len(payload)}\0".encode("ascii") + payload).hexdigest()


def _verify_original_feature_builder(path: Path | None = None) -> str:
    source = path or Path(__file__).resolve().parent / "historical_football_signal_lab.py"
    actual = _git_blob_sha1(source)
    if actual != FROZEN_FEATURE_BUILDER_GIT_BLOB_SHA:
        raise ValueError(
            "original V2 feature builder source drift: "
            f"{actual} != {FROZEN_FEATURE_BUILDER_GIT_BLOB_SHA}"
        )
    return actual


def _canonical(team: str) -> str:
    if not isinstance(team, str) or not team.strip():
        raise ValueError("empty team identity")
    value = team.strip()
    known = SERIE_A_RUNTIME_CONFIG.aliases.get(value, value)
    return V2_HISTORICAL_TEAM_ALIASES.get(known, known)




def _validate_history(history: pd.DataFrame) -> pd.DataFrame:
    missing = REQUIRED - set(history.columns)
    if missing:
        raise ValueError("historical source lacks required football stats: " + ", ".join(sorted(missing)))
    frame = history.copy()
    # Date-only embargo runs before any result/score/stat column is inspected.
    frame["_match_date"] = _assert_no_protected_season_history(frame)
    if frame["FTR"].isna().any() or not frame["FTR"].isin(("H", "D", "A")).all():
        raise ValueError("invalid/missing historical result")
    for field in ("FTHG", "FTAG", *STATS):
        frame[field] = pd.to_numeric(frame[field], errors="coerce")
        if frame[field].isna().any() or (frame[field] < 0).any():
            raise ValueError("unverified or missing history stat: " + field)
    if ((frame["FTHG"] > frame["FTAG"]) != (frame["FTR"] == "H")).any() or (
        (frame["FTHG"] < frame["FTAG"]) != (frame["FTR"] == "A")
    ).any():
        raise ValueError("historical full-time result does not match goals")
    frame["_home"] = frame["HomeTeam"].map(_canonical)
    frame["_away"] = frame["AwayTeam"].map(_canonical)
    if (frame["_home"] == frame["_away"]).any() or frame.duplicated(["_match_date", "_home", "_away"]).any():
        raise ValueError("historical fixture identity collision")
    return frame.sort_values(["_match_date", "_home", "_away"], kind="stable")


def _stats_asof(frame: pd.DataFrame, *, before_day: datetime) -> dict[str, deque]:
    """Strictly exclude ALL same-UTC-calendar-day matches: historic data have no reliable kickoff clock."""
    histories: dict[str, deque] = defaultdict(lambda: deque(maxlen=30))
    usable = frame.loc[frame["_match_date"] < pd.Timestamp(before_day.date())]
    for _, match in usable.iterrows():
        row = match.to_dict()
        home, away = row["_home"], row["_away"]
        hg, ag = float(row["FTHG"]), float(row["FTAG"])
        hp, ap = (3.0, 0.0) if hg > ag else ((0.0, 3.0) if hg < ag else (1.0, 1.0))
        histories[home].append(TeamMatch(hp, hg, ag, float(row["HC"]), float(row["AC"]),
                                         float(row["HY"]), float(row["HR"]), True))
        histories[away].append(TeamMatch(ap, ag, hg, float(row["AC"]), float(row["HC"]),
                                         float(row["AY"]), float(row["AR"]), False))
    return histories


def build_manifest(history: pd.DataFrame, quotes: list[dict]) -> dict:
    _require_frozen_inference_scope()
    # This is deliberately before candidate loading, quote iteration, or any
    # historical outcome/stat processing.
    _assert_no_protected_season_history(history)
    _verify_original_feature_builder()
    original = load_verified_original()
    names = list(original["features"])
    if names != list(FEATURE_SETS["ALL_FOOTBALL"]):
        raise ValueError("original V2 feature order drift")
    frame = _validate_history(history)
    selected: dict[str, tuple[datetime, dict]] = {}
    for row in quotes:
        if row.get("league") != "SERIE_A":
            raise ValueError("quotes must be Serie A only")
        event_id = str(row.get("event_id") or "").strip()
        if not event_id:
            raise ValueError("missing event id")
        home, away = _canonical(row["home_team"]), _canonical(row["away_team"])
        if home == away:
            raise ValueError("same home and away team")
        kickoff = parse_utc(row["commence_time_utc"])
        quote_time = parse_utc(row["snapshot_time_utc"])
        if quote_time >= kickoff:
            raise ValueError("quote is at/after kickoff")
        identity = (row["home_team"], row["away_team"], kickoff)
        prior = selected.get(event_id)
        if prior and prior[1]["_identity"] != identity:
            raise ValueError("event id maps to conflicting fixtures")
        selected_row = {**row, "_identity": identity}
        if not prior or prior[0] < quote_time:
            selected[event_id] = (quote_time, selected_row)
        elif prior[0] == quote_time:
            raise ValueError("duplicate quote observation")
    manifests = []
    for event_id, (quote_time, row) in sorted(selected.items()):
        cutoff = datetime.combine(quote_time.date(), datetime.min.time(), tzinfo=timezone.utc)
        histories = _stats_asof(frame, before_day=quote_time)
        home = _canonical(row["home_team"])
        away = _canonical(row["away_team"])
        # Exposure is descriptive, not a new trained feature/selection gate.
        # The old-season source may be many months stale; preserve the exact
        # number of historical matches and last *date-only* sample for audit.
        usable = frame.loc[frame["_match_date"] < pd.Timestamp(quote_time.date())]
        history_coverage = {}
        for role, team, venue in (("home", home, True), ("away", away, False)):
            team_rows = usable.loc[
                (usable["_home"] == team) | (usable["_away"] == team),
                "_match_date",
            ]
            prior_history = histories[team]
            history_coverage[role] = {
                "historical_team": team,
                "prior_matches_in_frozen_30_match_window": len(prior_history),
                "prior_matches_at_fixture_venue_in_window": sum(
                    m.venue_home is venue for m in prior_history
                ),
                "last_historical_match_date": (
                    team_rows.max().date().isoformat() if not team_rows.empty else None
                ),
                "days_since_last_historical_match": (
                    (quote_time.date() - team_rows.max().date()).days
                    if not team_rows.empty else None
                ),
                "source_contains_no_2026_27_results": bool(
                    not (usable["_match_date"] >= pd.Timestamp("2026-07-01")).any()
                ),
            }
        sides = {}
        sides.update(_snapshot(histories[home], "home"))
        sides.update(_snapshot(histories[away], "away"))
        values = {}
        for field in names:
            suffix = field.removeprefix("diff_")
            h, a = sides["home_" + suffix], sides["away_" + suffix]
            values[field] = None if pd.isna(h) or pd.isna(a) else float(h - a)
        manifests.append({
            "event_id": event_id,
            "home_team": row["home_team"],
            "away_team": row["away_team"],
            "commence_time_utc": parse_utc(row["commence_time_utc"]).isoformat(),
            "feature_history_cutoff_utc": cutoff.isoformat(),
            "features": values,
            # Not used by the original 19-feature candidate; diagnostic only.
            "history_coverage": history_coverage,
            "observed_frozen_feature_count": sum(v is not None for v in values.values()),
            "median_imputed_frozen_feature_count": sum(v is None for v in values.values()),
        })
    return {
        "schema_version": "SERIE_A_V2_DATE_ONLY_DIAGNOSTIC_FEATURES_V1",
        "candidate_sha256": original["artifact_sha256"],
        "feature_count": len(names),
        "historical_match_rows": len(frame),
        "feature_manifests": manifests,
        "independently_attested_information_time": False,
        "eligible_for_frozen_prospective_cohort": False,
        "eligible_for_product_publication": False,
        "paid_provider_requests": 0,
        "database_writes": 0,
    }


def _write_protected_outcome_block(path: Path, reason: str) -> dict:
    report = {
        "schema_version": "SERIE_A_V2_PROTECTED_OUTCOME_GATE_BLOCK_V1",
        "mode": "PROTECTED_2026_27_OUTCOME_GATE_BLOCKED",
        "block_reason": str(reason),
        "history_date_column_only_preflight": True,
        "protected_2026_27_outcomes_read": False,
        "history_outcome_columns_read": False,
        "saved_quote_rows_read": False,
        "frozen_candidate_read": False,
        "model_inference_performed": False,
        "supabase_reads": 0,
        "supabase_writes": 0,
        "paid_provider_calls": 0,
        "target_outcomes_read": False,
        "eligible_for_frozen_prospective_cohort": False,
        "eligible_for_product_publication": False,
        "no_bet": True,
    }
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--existing-history-csv", required=True, type=Path)
    p.add_argument("--saved-quotes-json", required=True, type=Path)
    p.add_argument("--manifest-json", required=True, type=Path)
    p.add_argument("--audit-json", required=True, type=Path)
    args = p.parse_args()
    if args.manifest_json == args.audit_json:
        raise ValueError("audit and manifest paths must differ")

    # Do not open even the date column until the provider's narrow frozen-
    # inference research scope is explicitly cleared.
    try:
        _require_frozen_inference_scope()
    except PermissionError as exc:
        from market_anchor_v2_source_rights import write_research_scope_blocked_report

        report = write_research_scope_blocked_report(
            args.audit_json, "SERIE_A_V2_ASOF_FEATURE_MANIFEST", str(exc)
        )
        print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
        return

    # If rights are later granted, inspect ONLY the date column first. Any
    # 2026/27 row blocks before result/score/stat columns or saved quotes open.
    date_only = pd.read_csv(args.existing_history_csv, usecols=["Date"])
    try:
        _assert_no_protected_season_history(date_only)
    except ProtectedSeasonOutcomeError as exc:
        report = _write_protected_outcome_block(args.audit_json, str(exc))
        print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
        return

    historical_bytes = args.existing_history_csv.read_bytes()
    history = pd.read_csv(args.existing_history_csv)
    quotes = json.loads(args.saved_quotes_json.read_text(encoding="utf-8"))
    if not isinstance(quotes, list):
        raise ValueError("saved quotes must be a JSON array")
    result = build_manifest(history, quotes)
    args.manifest_json.parent.mkdir(parents=True, exist_ok=True)
    args.manifest_json.write_text(json.dumps(result["feature_manifests"], indent=2), encoding="utf-8")
    audit = {k: v for k, v in result.items() if k != "feature_manifests"}
    audit["existing_history_sha256"] = hashlib.sha256(historical_bytes).hexdigest()
    audit["saved_quotes_sha256"] = hashlib.sha256(args.saved_quotes_json.read_bytes()).hexdigest()
    args.audit_json.parent.mkdir(parents=True, exist_ok=True)
    args.audit_json.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
