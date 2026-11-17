"""Local-only manual Footiqo intake for original MARKET_ANCHOR_1X2_V2.

This module never contacts Footiqo, Supabase, GitHub, or an odds provider.
It accepts a user-exported CSV only after a metadata-only 30-event gate file
has been validated, archives the exact bytes outside the repository, and
builds the unchanged original 19-feature vector from the 17 documented fields.
The two undocumented red-card features remain missing for the frozen imputer.
No probabilities, predictions, bets, or product artifacts are produced.
"""
from __future__ import annotations

import argparse
from collections import defaultdict, deque
from datetime import date, datetime, timezone
from io import BytesIO
import hashlib
import json
import math
import os
import re
from pathlib import Path
import shutil
import tempfile
from typing import Any, Callable, Mapping

import pandas as pd

from historical_football_signal_lab import FEATURE_SETS, TeamMatch, _snapshot
from serie_a_runtime_config import SERIE_A_RUNTIME_CONFIG

REPOSITORY_ROOT = Path(__file__).resolve().parent
RIGHTS_PATH = Path("research/source_rights/footiqo.json")
CANDIDATE_PATH = Path("research/models/market_anchor_v2_serie_a_frozen_candidate.json")
FEATURE_BUILDER_PATH = Path("historical_football_signal_lab.py")

EXPECTED_RIGHTS_GIT_BLOB_SHA1 = "c42ee1f02e660bce2ea35ae37f444a30a7717b7e"
EXPECTED_CANDIDATE_GIT_BLOB_SHA1 = "ac1303f6b096664983fbf52443bd0a381b23ba21"
EXPECTED_FEATURE_BUILDER_GIT_BLOB_SHA1 = "401b3a0893371bfa4a488ec92a4a54af2678c8f7"
EXPECTED_CANDIDATE_SHA256 = "a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6"
EXPECTED_TRAINING_FINGERPRINT = "f27ab985ae90bb8e94ba8d548847695888c232f43b3e9be93074f39e1a7a5098"
MIN_CURRENT_SEASON_FIXTURE_IDENTITIES = 30
CURRENT_SEASON_START = date(2026, 7, 1)
SCHEMA_VERSION = "MARKET_ANCHOR_1X2_V2_FOOTIQO_MANUAL_INTAKE_V1"
FEATURE_GATE_COLUMNS = ("match_date", "home_team", "away_team")
SOURCE_COLUMNS = (
    "Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR",
    "HCFT", "ACFT", "HYCFT", "AYCFT",
)
QUOTE_KEYS = {
    "event_id", "league", "home_team", "away_team",
    "commence_time_utc", "snapshot_time_utc",
}
V2_HISTORICAL_TEAM_ALIASES = {"Atalanta BC": "Atalanta"}
RED_FEATURES = ("diff_red_5", "diff_red_10")
SOURCE_FIELD_MAP = {
    "HCFT": "HC",
    "ACFT": "AC",
    "HYCFT": "HY",
    "AYCFT": "AY",
}


def _git_blob_sha1(raw: bytes) -> str:
    return hashlib.sha1(f"blob {len(raw)}\0".encode("ascii") + raw).hexdigest()


def _read_pinned_json(path: Path, expected_blob_sha1: str, label: str) -> tuple[dict, str]:
    raw = path.read_bytes()
    actual = _git_blob_sha1(raw)
    if actual != expected_blob_sha1:
        raise ValueError(f"{label} Git blob changed: {actual} != {expected_blob_sha1}")
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    return value, actual


def load_frozen_contract() -> dict:
    root = REPOSITORY_ROOT
    builder_raw = (root / FEATURE_BUILDER_PATH).read_bytes()
    builder_sha = _git_blob_sha1(builder_raw)
    if builder_sha != EXPECTED_FEATURE_BUILDER_GIT_BLOB_SHA1:
        raise ValueError("original V2 feature-builder source drift")

    candidate, candidate_blob = _read_pinned_json(
        root / CANDIDATE_PATH, EXPECTED_CANDIDATE_GIT_BLOB_SHA1, "frozen candidate"
    )
    features = list(FEATURE_SETS["ALL_FOOTBALL"])
    if (
        candidate.get("experiment_id") != "MARKET_ANCHOR_1X2_V2"
        or candidate.get("artifact_sha256") != EXPECTED_CANDIDATE_SHA256
        or candidate.get("training_fingerprint_sha256") != EXPECTED_TRAINING_FINGERPRINT
        or candidate.get("features") != features
        or len(features) != 19
        or len(candidate.get("weights", [])) != 20
        or any(not isinstance(row, list) or len(row) != 2 for row in candidate.get("weights", []))
        or candidate.get("training_rows") != 3799
        or candidate.get("active_lambda") != 0.0
        or candidate.get("shadow_residual_lambda") != 1.0
        or candidate.get("stability_gate_passed") is not False
        or candidate.get("automatic_promotion") is not False
    ):
        raise ValueError("original frozen MARKET_ANCHOR_1X2_V2 contract mismatch")
    return {
        "candidate": candidate,
        "candidate_git_blob_sha1": candidate_blob,
        "feature_builder_git_blob_sha1": builder_sha,
        "features": features,
    }


def load_manual_rights() -> dict:
    manifest, blob_sha = _read_pinned_json(
        REPOSITORY_ROOT / RIGHTS_PATH,
        EXPECTED_RIGHTS_GIT_BLOB_SHA1,
        "Footiqo rights manifest",
    )
    rights = manifest.get("rights", {})
    access = manifest.get("free_access", {})
    provenance = manifest.get("provenance", {})
    if not (
        manifest.get("decision") == "HOLD"
        and rights.get("dataset_policy_explicitly_permits_personal_noncommercial_research") is True
        and rights.get("dataset_policy_permits_manual_exports") is True
        and rights.get("dataset_policy_explicitly_permits_private_storage_of_legitimately_obtained_files") is True
        and rights.get("dataset_policy_requires_written_authorization_for_automated_extraction") is True
        and rights.get("explicit_commercial_product_use_permission") is False
        and rights.get("upstream_field_level_rights_verified") is False
        and access.get("automated_export_without_written_authorization") is False
        and access.get("public_api_available") is False
        and provenance.get("automated_capture_authorized") is False
    ):
        raise ValueError("Footiqo rights manifest no longer supports this manual-only research boundary")
    return {"manifest": manifest, "git_blob_sha1": blob_sha}


def _utc(value: Any, label: str) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError(f"{label} must be ISO-8601") from exc
    else:
        raise ValueError(f"{label} must be an ISO-8601 timestamp")
    if parsed.tzinfo is None:
        raise ValueError(f"{label} must include a timezone")
    return parsed.astimezone(timezone.utc)


def _canonical_team(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("empty team identity")
    value = value.strip()
    known = SERIE_A_RUNTIME_CONFIG.aliases.get(value, value)
    return V2_HISTORICAL_TEAM_ALIASES.get(known, known)


def _assert_outside_repository(path: Path, label: str) -> Path:
    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        raise ValueError(f"{label} must be an absolute path")
    cursor = candidate
    while cursor != cursor.parent:
        if cursor.is_symlink():
            raise ValueError(f"{label} must not traverse a symlink")
        cursor = cursor.parent
    resolved = candidate.resolve(strict=False)
    root = REPOSITORY_ROOT.resolve()
    if resolved == root or root in resolved.parents:
        raise ValueError(f"{label} must be outside the public repository")
    return resolved


def _validate_gate_metadata(raw: bytes, *, checked_at: datetime) -> dict:
    if not raw:
        raise ValueError("metadata-only feature gate file is empty")
    frame = pd.read_csv(BytesIO(raw), dtype=str, keep_default_na=False)
    if tuple(frame.columns) != FEATURE_GATE_COLUMNS:
        raise ValueError(
            "feature gate export must contain exactly match_date,home_team,away_team; "
            "score/result columns are forbidden"
        )
    identities: set[tuple[str, str, str]] = set()
    dates: list[date] = []
    for row in frame.to_dict(orient="records"):
        match_date_text = str(row["match_date"]).strip()
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", match_date_text):
            raise ValueError("match_date must be canonical YYYY-MM-DD in metadata-only feature gate")
        try:
            match_date = date.fromisoformat(match_date_text)
        except ValueError as exc:
            raise ValueError("invalid canonical match_date in metadata-only feature gate") from exc
        if match_date < CURRENT_SEASON_START:
            raise ValueError("feature gate metadata includes a fixture before current 2026/27 season start")
        if match_date >= checked_at.date():
            raise ValueError("feature gate metadata includes a same-day or future fixture")
        home = _canonical_team(row["home_team"])
        away = _canonical_team(row["away_team"])
        if home == away:
            raise ValueError("invalid same-team identity in feature gate metadata")
        identities.add((match_date.isoformat(), home, away))
        dates.append(match_date)
    if len(identities) < MIN_CURRENT_SEASON_FIXTURE_IDENTITIES:
        raise ValueError(
            f"feature-input gate closed: {len(identities)} unique current-season fixture identities "
            f"< {MIN_CURRENT_SEASON_FIXTURE_IDENTITIES}"
        )
    return {
        "raw_metadata_rows": len(frame),
        "canonical_unique_current_season_fixture_identities": len(identities),
        "minimum_required_current_season_fixture_identities": MIN_CURRENT_SEASON_FIXTURE_IDENTITIES,
        "current_season_start": CURRENT_SEASON_START.isoformat(),
        "completion_status_independently_verified": False,
        "primary_competition_independently_verified": False,
        "evaluation_outcome_gate_satisfied": False,
        "latest_match_date": max(dates).isoformat() if dates else None,
        "metadata_fields": list(FEATURE_GATE_COLUMNS),
        "outcome_fields_read": False,
        "metadata_only_export": True,
        "gate_checked_at_utc": checked_at.isoformat(),
    }


def _normalise_source(raw: bytes, *, received_at: datetime) -> tuple[pd.DataFrame, dict]:
    if not raw:
        raise ValueError("manual Footiqo CSV is empty")
    frame = pd.read_csv(BytesIO(raw), low_memory=False)
    missing = set(SOURCE_COLUMNS) - set(frame.columns)
    if missing:
        raise ValueError("manual Footiqo CSV missing documented fields: " + ", ".join(sorted(missing)))

    nonblank = frame["Date"].notna() & frame["Date"].astype(str).str.strip().ne("")
    parsed = pd.to_datetime(frame["Date"], dayfirst=True, format="mixed", errors="coerce")
    if parsed.loc[nonblank].isna().any():
        raise ValueError("manual Footiqo CSV contains an unparseable date")
    frame = frame.loc[nonblank].copy()
    frame["_match_date"] = parsed.loc[nonblank].dt.date
    frame["_ftr"] = frame["FTR"].fillna("").astype(str).str.strip().str.upper()
    valid_result = frame["_ftr"].isin(("H", "D", "A"))
    capture_day = received_at.date()

    future_completed = (frame["_match_date"] > capture_day) & valid_result
    if future_completed.any():
        raise ValueError("manual Footiqo CSV contains a completed result after receipt time")

    season_rows = frame.loc[frame["_match_date"] >= CURRENT_SEASON_START].copy()
    prior_day = season_rows.loc[
        (season_rows["_match_date"] < capture_day) & season_rows["_ftr"].isin(("H", "D", "A"))
    ].copy()
    if prior_day.empty:
        raise ValueError("manual Footiqo CSV has no completed current-season prior-day rows")

    numeric_map = {
        "FTHG": "FTHG", "FTAG": "FTAG",
        "HCFT": "HC", "ACFT": "AC",
        "HYCFT": "HY", "AYCFT": "AY",
    }
    for source, target in numeric_map.items():
        prior_day[target] = pd.to_numeric(prior_day[source], errors="coerce")
        if (
            prior_day[target].isna().any()
            or (prior_day[target] < 0).any()
            or not all(math.isfinite(float(value)) for value in prior_day[target])
        ):
            raise ValueError(f"completed manual Footiqo row has missing/invalid {source}")

    prior_day["FTR"] = prior_day["_ftr"]
    expected_ftr = pd.Series("D", index=prior_day.index)
    expected_ftr.loc[prior_day["FTHG"] > prior_day["FTAG"]] = "H"
    expected_ftr.loc[prior_day["FTHG"] < prior_day["FTAG"]] = "A"
    if not expected_ftr.eq(prior_day["FTR"]).all():
        raise ValueError("manual Footiqo full-time result does not match goals")

    prior_day["_home"] = prior_day["HomeTeam"].map(_canonical_team)
    prior_day["_away"] = prior_day["AwayTeam"].map(_canonical_team)
    if (
        prior_day["_home"].eq(prior_day["_away"]).any()
        or prior_day.duplicated(["_match_date", "_home", "_away"]).any()
    ):
        raise ValueError("manual Footiqo fixture identity collision")

    normalised = pd.DataFrame({
        "Date": prior_day["_match_date"].map(lambda d: d.strftime("%d/%m/%Y")),
        "HomeTeam": prior_day["_home"],
        "AwayTeam": prior_day["_away"],
        "FTHG": prior_day["FTHG"].astype(float),
        "FTAG": prior_day["FTAG"].astype(float),
        "FTR": prior_day["FTR"],
        "HC": prior_day["HC"].astype(float),
        "AC": prior_day["AC"].astype(float),
        "HY": prior_day["HY"].astype(float),
        "AY": prior_day["AY"].astype(float),
        # The reviewed Footiqo Serie A table does not document red cards.
        # Preserve missingness; never infer red cards from yellow-card fields.
        "HR": float("nan"),
        "AR": float("nan"),
        "_match_date": pd.to_datetime(prior_day["_match_date"]),
    }).sort_values(["_match_date", "HomeTeam", "AwayTeam"], kind="stable")

    return normalised.reset_index(drop=True), {
        "source_rows_total": len(frame),
        "current_season_rows": len(season_rows),
        "completed_prior_day_rows": len(normalised),
        "incomplete_or_unplayed_prior_rows_excluded": int(
            ((season_rows["_match_date"] < capture_day) & ~season_rows["_ftr"].isin(("H", "D", "A"))).sum()
        ),
        "same_day_rows_excluded_without_kickoff_clock": int(
            (season_rows["_match_date"] == capture_day).sum()
        ),
        "red_card_source_fields": [],
        "red_card_features_unobserved": list(RED_FEATURES),
        "mapped_source_fields": list(SOURCE_COLUMNS),
    }


def capture_manual_export(
    *,
    source_csv: Path,
    gate_metadata_csv: Path,
    private_store_dir: Path,
    manual_export_confirmed: bool,
    noncommercial_research_confirmed: bool,
    private_storage_confirmed: bool,
    now: datetime | None = None,
) -> Path:
    """Archive a manually exported CSV locally; metadata gate is read first."""
    if not (manual_export_confirmed and noncommercial_research_confirmed and private_storage_confirmed):
        raise ValueError(
            "manual export, non-commercial research, and private-storage confirmations are required"
        )
    contract = load_frozen_contract()
    rights = load_manual_rights()
    store = _assert_outside_repository(Path(private_store_dir), "private storage directory")
    source_path = _assert_outside_repository(Path(source_csv), "manual source CSV")
    gate_path = _assert_outside_repository(Path(gate_metadata_csv), "metadata-only gate CSV")
    if not gate_path.is_file():
        raise ValueError("metadata-only gate CSV must exist before source intake")
    store.mkdir(parents=True, exist_ok=True)
    if store.is_symlink():
        raise ValueError("private storage directory must not be a symlink")

    clock = _utc(now or datetime.now(timezone.utc), "capture clock")
    gate_raw = gate_path.read_bytes()
    gate_summary = _validate_gate_metadata(gate_raw, checked_at=clock)
    # Do not even stat/open the protected source CSV until the metadata-only
    # 30-event feature-input gate above has passed.
    if not source_path.is_file():
        raise ValueError("manual source CSV must exist after the metadata-only gate passes")
    source_raw = source_path.read_bytes()
    source_received_at = _utc(datetime.now(timezone.utc) if now is None else now, "source receipt clock")
    normalised, source_summary = _normalise_source(source_raw, received_at=source_received_at)

    source_sha = hashlib.sha256(source_raw).hexdigest()
    gate_sha = hashlib.sha256(gate_raw).hexdigest()
    final_dir = store / (
        "footiqo_manual_" + source_received_at.strftime("%Y%m%dT%H%M%S%fZ")
        + "_" + source_sha[:12]
    )
    if final_dir.exists() or final_dir.is_symlink():
        raise ValueError("manual source archive destination already exists")

    staging = Path(tempfile.mkdtemp(prefix=".footiqo-stage-", dir=store))
    published = False
    try:
        (staging / "raw_source.csv").write_bytes(source_raw)
        (staging / "gate_metadata.csv").write_bytes(gate_raw)
        if hashlib.sha256((staging / "raw_source.csv").read_bytes()).hexdigest() != source_sha:
            raise ValueError("persisted manual source bytes failed SHA256 verification")
        if hashlib.sha256((staging / "gate_metadata.csv").read_bytes()).hexdigest() != gate_sha:
            raise ValueError("persisted metadata gate bytes failed SHA256 verification")
        os.replace(staging, final_dir)
        published = True
        published_at = _utc(datetime.now(timezone.utc) if now is None else now, "archive publication clock")
        manifest = {
            "schema_version": SCHEMA_VERSION,
            "provider": "Footiqo",
            "manual_export": True,
            "automated_access": False,
            "api_requests": 0,
            "noncommercial_research_only": True,
            "private_storage_confirmed": True,
            "commercial_product_use_permitted": False,
            "source_observation_time_known": False,
            "source_correction_time_known": False,
            "timestamp_attestation_verified": False,
            "timestamp_attestation_level": "LOCAL_CLOCK_UNATTESTED_MUTABLE_MANIFEST",
            "source_received_at_utc": source_received_at.isoformat(),
            "archive_published_at_utc": published_at.isoformat(),
            "raw_source_file": "raw_source.csv",
            "raw_source_sha256": source_sha,
            "raw_source_bytes": len(source_raw),
            "gate_metadata_file": "gate_metadata.csv",
            "gate_metadata_sha256": gate_sha,
            "gate_summary": gate_summary,
            "source_summary": source_summary,
            "candidate_sha256": contract["candidate"]["artifact_sha256"],
            "candidate_git_blob_sha1": contract["candidate_git_blob_sha1"],
            "training_fingerprint_sha256": contract["candidate"]["training_fingerprint_sha256"],
            "feature_builder_git_blob_sha1": contract["feature_builder_git_blob_sha1"],
            "rights_manifest_git_blob_sha1": rights["git_blob_sha1"],
            "eligible_for_frozen_prospective_cohort": False,
            "eligible_for_product_publication": False,
            "research_only": True,
            "no_bet": True,
        }
        (final_dir / "manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
        )
        return final_dir
    except Exception:
        if published and final_dir.exists():
            shutil.rmtree(final_dir, ignore_errors=True)
        raise
    finally:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)


def _load_verified_capture(capture_dir: Path) -> tuple[dict, pd.DataFrame]:
    capture = _assert_outside_repository(Path(capture_dir), "manual source archive")
    manifest_path = capture / "manifest.json"
    if capture.is_symlink() or not manifest_path.is_file():
        raise ValueError("manual source archive manifest missing or path is unsafe")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != SCHEMA_VERSION or manifest.get("manual_export") is not True:
        raise ValueError("unsupported manual source archive")
    if not (
        manifest.get("automated_access") is False
        and manifest.get("noncommercial_research_only") is True
        and manifest.get("private_storage_confirmed") is True
        and manifest.get("commercial_product_use_permitted") is False
        and manifest.get("source_observation_time_known") is False
        and manifest.get("source_correction_time_known") is False
        and manifest.get("timestamp_attestation_verified") is False
        and manifest.get("timestamp_attestation_level") == "LOCAL_CLOCK_UNATTESTED_MUTABLE_MANIFEST"
        and manifest.get("eligible_for_frozen_prospective_cohort") is False
        and manifest.get("eligible_for_product_publication") is False
    ):
        raise ValueError("manual Footiqo archive has an unsafe rights/provenance classification")
    contract = load_frozen_contract()
    rights = load_manual_rights()
    if (
        manifest.get("candidate_sha256") != contract["candidate"]["artifact_sha256"]
        or manifest.get("candidate_git_blob_sha1") != contract["candidate_git_blob_sha1"]
        or manifest.get("feature_builder_git_blob_sha1") != contract["feature_builder_git_blob_sha1"]
        or manifest.get("rights_manifest_git_blob_sha1") != rights["git_blob_sha1"]
    ):
        raise ValueError("manual archive is not bound to the exact frozen V2/source-rights contract")

    gate_raw = (capture / "gate_metadata.csv").read_bytes()
    if hashlib.sha256(gate_raw).hexdigest() != manifest.get("gate_metadata_sha256"):
        raise ValueError("metadata-only gate archive SHA256 mismatch")
    gate_checked = _utc(manifest["gate_summary"]["gate_checked_at_utc"], "gate check time")
    gate_summary = _validate_gate_metadata(gate_raw, checked_at=gate_checked)
    for key in (
        "raw_metadata_rows", "canonical_unique_current_season_fixture_identities",
        "minimum_required_current_season_fixture_identities", "current_season_start",
        "completion_status_independently_verified", "primary_competition_independently_verified",
        "evaluation_outcome_gate_satisfied", "latest_match_date",
        "metadata_fields", "outcome_fields_read", "metadata_only_export",
    ):
        if gate_summary.get(key) != manifest["gate_summary"].get(key):
            raise ValueError("metadata-only feature gate summary does not match archived gate bytes")

    source_raw = (capture / "raw_source.csv").read_bytes()
    if hashlib.sha256(source_raw).hexdigest() != manifest.get("raw_source_sha256"):
        raise ValueError("manual Footiqo source archive SHA256 mismatch")
    source_received = _utc(manifest["source_received_at_utc"], "source receipt time")
    published = _utc(manifest["archive_published_at_utc"], "archive publication time")
    if not gate_checked <= source_received <= published:
        raise ValueError("metadata gate, source receipt and archive publication chronology is invalid")
    history, source_summary = _normalise_source(source_raw, received_at=source_received)
    if source_summary != manifest.get("source_summary"):
        raise ValueError("manual source summary does not match the SHA-verified source bytes")
    return manifest, history


def build_manifest_from_capture(capture_dir: Path, quotes: list[Mapping[str, Any]]) -> dict:
    """Build only the unchanged original 19 feature inputs; never score outcomes."""
    manifest, history = _load_verified_capture(capture_dir)
    contract = load_frozen_contract()
    features_order = contract["features"]
    published = _utc(manifest["archive_published_at_utc"], "archive publication time")
    source_received = _utc(manifest["source_received_at_utc"], "source receipt time")
    selected_ids: set[str] = set()
    feature_rows = []

    for quote in quotes:
        if not isinstance(quote, Mapping) or set(quote) - QUOTE_KEYS:
            raise ValueError("quote input contains non-metadata or protected outcome fields")
        if set(quote) != QUOTE_KEYS:
            raise ValueError("quote input must contain exactly the six pre-match identity/time fields")
        if quote.get("league") != "SERIE_A":
            raise ValueError("manual Footiqo intake is restricted to Serie A")
        event_id = str(quote.get("event_id") or "").strip()
        if not event_id or event_id in selected_ids:
            raise ValueError("missing or duplicate quote event_id")
        selected_ids.add(event_id)
        home_raw, away_raw = quote.get("home_team"), quote.get("away_team")
        home, away = _canonical_team(home_raw), _canonical_team(away_raw)
        if home == away:
            raise ValueError("quote has identical canonical home and away teams")
        quote_time = _utc(quote.get("snapshot_time_utc"), "quote snapshot time")
        kickoff = _utc(quote.get("commence_time_utc"), "quote kickoff")
        if not published < quote_time:
            raise ValueError("manual source archive was not published strictly before quote")
        if not quote_time < kickoff:
            raise ValueError("quote is at/after kickoff")
        if not source_received <= published < quote_time:
            raise ValueError("manual source receipt/publication chronology is invalid")

        # Date-only match data cannot establish same-day kickoff ordering.
        cutoff_day = quote_time.date()
        usable = history.loc[history["_match_date"].dt.date < cutoff_day]
        histories: dict[str, deque] = defaultdict(lambda: deque(maxlen=30))
        for row in usable.sort_values(["_match_date", "HomeTeam", "AwayTeam"], kind="stable").itertuples():
            hg, ag = float(row.FTHG), float(row.FTAG)
            hp, ap = (3.0, 0.0) if hg > ag else ((0.0, 3.0) if hg < ag else (1.0, 1.0))
            histories[row.HomeTeam].append(TeamMatch(
                hp, hg, ag, float(row.HC), float(row.AC), float(row.HY), float("nan"), True
            ))
            histories[row.AwayTeam].append(TeamMatch(
                ap, ag, hg, float(row.AC), float(row.HC), float(row.AY), float("nan"), False
            ))

        home_snapshot = _snapshot(histories[home], "home")
        away_snapshot = _snapshot(histories[away], "away")
        vector: dict[str, float | None] = {}
        for feature in features_order:
            suffix = feature.removeprefix("diff_")
            h = home_snapshot["home_" + suffix]
            a = away_snapshot["away_" + suffix]
            vector[feature] = None if pd.isna(h) or pd.isna(a) else float(h - a)

        feature_rows.append({
            "event_id": event_id,
            "league": "SERIE_A",
            "home_team": home_raw,
            "away_team": away_raw,
            "commence_time_utc": kickoff.isoformat(),
            "snapshot_time_utc": quote_time.isoformat(),
            "feature_history_cutoff_utc": datetime.combine(
                cutoff_day, datetime.min.time(), tzinfo=timezone.utc
            ).isoformat(),
            "features": vector,
            "feature_order": list(features_order),
            "observed_frozen_feature_count": sum(value is not None for value in vector.values()),
            "median_imputed_frozen_feature_count": sum(value is None for value in vector.values()),
            "missing_feature_names": [name for name, value in vector.items() if value is None],
            "source_archive_sha256": manifest["raw_source_sha256"],
            "source_archive_published_at_utc": published.isoformat(),
            "source_archive_before_quote_verified": False,
            "project_possession_before_quote_verified": False,
            "local_archive_ordering_consistent": True,
            "timestamp_attestation_verified": False,
            "source_before_quote_verified": False,
            "upstream_observation_time_verified": False,
            "information_time_independently_attested": False,
            "feature_input_outcomes_used": True,
            "target_quote_outcomes_read": False,
            "probabilities_generated": False,
            "model_weights_applied": False,
            "eligible_for_frozen_prospective_cohort": False,
            "eligible_for_product_publication": False,
            "research_only": True,
            "no_bet": True,
        })

    return {
        "schema_version": "MARKET_ANCHOR_1X2_V2_FOOTIQO_MANUAL_FEATURES_V1",
        "experiment_id": "MARKET_ANCHOR_1X2_V2",
        "candidate_sha256": contract["candidate"]["artifact_sha256"],
        "training_fingerprint_sha256": contract["candidate"]["training_fingerprint_sha256"],
        "feature_count": 19,
        "feature_order": list(features_order),
        "source_provider": "Footiqo",
        "manual_export_only": True,
        "automated_access_authorized": False,
        "noncommercial_research_only": True,
        "source_archive_sha256": manifest["raw_source_sha256"],
        "source_archive_published_at_utc": published.isoformat(),
        "source_archive_before_quote_verified": False,
        "project_possession_before_quote_verified": False,
        "local_archive_ordering_consistent": True,
        "timestamp_attestation_verified": False,
        "source_before_quote_verified": False,
        "upstream_observation_time_verified": False,
        "information_time_independently_attested": False,
        "metadata_gate_attestation_level": "operator_supplied_local_metadata_csv_not_supabase_authenticated",
        "feature_input_gate_completion_status_independently_verified": False,
        "feature_input_gate_primary_competition_independently_verified": False,
        "evaluation_outcome_gate_opened": False,
        "gate_metadata_sha256": manifest["gate_metadata_sha256"],
        "feature_input_gate_fixture_identities": manifest["gate_summary"]["canonical_unique_current_season_fixture_identities"],
        "feature_input_gate_minimum_fixture_identities": MIN_CURRENT_SEASON_FIXTURE_IDENTITIES,
        "active_lambda": 0.0,
        "shadow_residual_lambda": 1.0,
        "stability_gate_passed": False,
        "automatic_promotion": False,
        "target_quote_outcomes_read": False,
        "probabilities_generated": False,
        "paid_provider_requests": 0,
        "direct_supabase_reads": 0,
        "supabase_writes": 0,
        "production_pkl_changed": False,
        "eligible_for_frozen_prospective_cohort": False,
        "eligible_for_product_publication": False,
        "research_only": True,
        "no_bet": True,
        "feature_rows": feature_rows,
    }


def _write_json_outside_repo(path: Path, value: dict) -> None:
    target = _assert_outside_repository(Path(path), "feature report output")
    if target.exists() or target.is_symlink():
        raise ValueError("feature report output must not already exist")
    target.parent.mkdir(parents=True, exist_ok=True)
    staging = target.with_name("." + target.name + ".tmp")
    if staging.exists() or staging.is_symlink():
        raise ValueError("feature report temporary path already exists")
    try:
        staging.write_text(json.dumps(value, indent=2, sort_keys=True), encoding="utf-8")
        os.replace(staging, target)
    finally:
        if staging.exists():
            staging.unlink()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    capture = commands.add_parser("capture", help="archive a manually exported CSV in private local storage")
    capture.add_argument("--source-csv", required=True, type=Path)
    capture.add_argument("--gate-metadata-csv", required=True, type=Path)
    capture.add_argument("--private-store-dir", required=True, type=Path)
    capture.add_argument("--manual-export-confirmed", action="store_true")
    capture.add_argument("--noncommercial-research-confirmed", action="store_true")
    capture.add_argument("--private-storage-confirmed", action="store_true")

    features = commands.add_parser("features", help="build original 19-feature inputs from a verified private archive")
    features.add_argument("--capture-dir", required=True, type=Path)
    features.add_argument("--quotes-json", required=True, type=Path)
    features.add_argument("--output-json", required=True, type=Path)

    args = parser.parse_args()
    if args.command == "capture":
        path = capture_manual_export(
            source_csv=args.source_csv,
            gate_metadata_csv=args.gate_metadata_csv,
            private_store_dir=args.private_store_dir,
            manual_export_confirmed=args.manual_export_confirmed,
            noncommercial_research_confirmed=args.noncommercial_research_confirmed,
            private_storage_confirmed=args.private_storage_confirmed,
        )
        print(json.dumps({"archive_dir": str(path), "raw_source_sha256": json.loads(
            (path / "manifest.json").read_text(encoding="utf-8")
        )["raw_source_sha256"]}, indent=2))
        return

    capture_dir = _assert_outside_repository(args.capture_dir, "manual source archive")
    # Verify the archive and its source SHA before reading any quote file.
    _load_verified_capture(capture_dir)
    quotes_path = _assert_outside_repository(args.quotes_json, "pre-match quote JSON")
    quotes = json.loads(quotes_path.read_text(encoding="utf-8"))
    if not isinstance(quotes, list):
        raise ValueError("pre-match quote JSON must be an array")
    report = build_manifest_from_capture(capture_dir, quotes)
    _write_json_outside_repo(args.output_json, report)
    print(json.dumps({
        "feature_rows": len(report["feature_rows"]),
        "candidate_sha256": report["candidate_sha256"],
        "source_archive_sha256": report["source_archive_sha256"],
        "probabilities_generated": False,
        "no_bet": True,
    }, indent=2))


if __name__ == "__main__":
    main()
