"""Offline-only receipt/SHA gate for a future private Big Balls source archive.

This module performs no HTTP, storage, Supabase, feature calculation, inference,
or outcome evaluation. The current provider-rights manifest intentionally denies
integration, so a real archive cannot pass until the owner-approved manifest is
changed in a separately reviewed research PR.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any, Mapping


class ArchiveGateError(ValueError):
    """Raised when a source archive cannot be admitted as a pre-quote input."""


def _utc(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ArchiveGateError(f"{field} must be an offset-aware UTC timestamp")
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError as exc:
        raise ArchiveGateError(f"{field} must be an offset-aware UTC timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ArchiveGateError(f"{field} must be an offset-aware UTC timestamp")
    return parsed.astimezone(timezone.utc)


def _sha256(raw: bytes, expected: Any, field: str) -> str:
    if not isinstance(raw, bytes):
        raise ArchiveGateError(f"{field} raw body must be bytes")
    if not isinstance(expected, str) or re.fullmatch(r"[0-9a-fA-F]{64}", expected) is None:
        raise ArchiveGateError(f"{field} SHA-256 must be 64 hexadecimal characters")
    actual = hashlib.sha256(raw).hexdigest()
    if actual != expected.lower():
        raise ArchiveGateError(f"{field} SHA-256 mismatch")
    return actual


def _json_body(raw: bytes, field: str) -> Mapping[str, Any]:
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ArchiveGateError(f"{field} body is not valid UTF-8 JSON") from exc
    if not isinstance(value, dict):
        raise ArchiveGateError(f"{field} body must be a JSON object")
    return value


def _nonnegative_int(value: Any, field: str) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def validate_private_prequote_archive(
    *,
    rights_manifest: Mapping[str, Any],
    archive_manifest: Mapping[str, Any],
    match_body: bytes,
    statistics_body: bytes,
    quote_match_id: str,
    quote_snapshot_time_utc: str,
    quote_created_at_utc: str,
    target_kickoff_utc: str,
    expected_candidate_sha256: str,
) -> dict[str, Any]:
    """Validate an already-captured synthetic/private source bundle.

    The function deliberately requires explicit project authorization and
    private storage. Receipt times prove only when this project possessed the
    exact bytes; they do not prove the provider's upstream first-observation or
    per-field correction times. Missing statistics remain missing; no zero,
    median, feature value, or prediction is fabricated here.
    """
    for key in ("integration_allowed", "automated_capture_authorized", "frozen_inference_authorized"):
        if rights_manifest.get(key) is not True:
            raise ArchiveGateError(f"provider rights do not authorize {key}")

    if archive_manifest.get("provider") != "Big Balls Sports Data":
        raise ArchiveGateError("unexpected source provider")
    if archive_manifest.get("provider_plan") != "free":
        raise ArchiveGateError("only the documented Free plan is admissible")
    if archive_manifest.get("storage_visibility") != "private":
        raise ArchiveGateError("raw source storage must be private")
    if archive_manifest.get("public_raw_artifact_uploaded") is not False:
        raise ArchiveGateError("public raw-source artifact publication is forbidden")
    if archive_manifest.get("paid_provider_calls") != 0:
        raise ArchiveGateError("paid provider calls are forbidden")
    if archive_manifest.get("paid_odds_used") is not False:
        raise ArchiveGateError("paid odds use is forbidden")

    if rights_manifest.get("provider") != "Big Balls Sports Data":
        raise ArchiveGateError("provider rights manifest does not match Big Balls Sports Data")

    if not isinstance(expected_candidate_sha256, str):
        raise ArchiveGateError("expected candidate SHA-256 is invalid")
    expected = expected_candidate_sha256.lower()
    if re.fullmatch(r"[0-9a-f]{64}", expected) is None:
        raise ArchiveGateError("expected candidate SHA-256 is invalid")
    if archive_manifest.get("candidate_sha256") != expected:
        raise ArchiveGateError("archive candidate SHA-256 does not match frozen V2")

    source_id = archive_manifest.get("source_match_id")
    target_id = archive_manifest.get("target_match_id")
    if not isinstance(source_id, str) or not source_id.strip():
        raise ArchiveGateError("source_match_id is required")
    if not isinstance(target_id, str) or not target_id.strip():
        raise ArchiveGateError("target_match_id is required")
    if source_id == target_id:
        raise ArchiveGateError("source and target match IDs must differ")
    if quote_match_id != target_id:
        raise ArchiveGateError("quote match ID does not match target match ID")

    if archive_manifest.get("match_endpoint") != f"/v1/matches/{source_id}":
        raise ArchiveGateError("unexpected match endpoint")
    if archive_manifest.get("statistics_endpoint") != f"/v1/matches/{source_id}/statistics":
        raise ArchiveGateError("unexpected statistics endpoint")

    match_sha = _sha256(match_body, archive_manifest.get("match_body_sha256"), "match body")
    stats_sha = _sha256(
        statistics_body,
        archive_manifest.get("statistics_body_sha256"),
        "statistics body",
    )

    match_received = _utc(archive_manifest.get("match_received_at_utc"), "match_received_at_utc")
    stats_received = _utc(
        archive_manifest.get("statistics_received_at_utc"),
        "statistics_received_at_utc",
    )
    archive_created = _utc(
        archive_manifest.get("archive_created_at_utc"),
        "archive_created_at_utc",
    )
    quote_snapshot = _utc(quote_snapshot_time_utc, "quote_snapshot_time_utc")
    quote_created = _utc(quote_created_at_utc, "quote_created_at_utc")
    target_kickoff = _utc(target_kickoff_utc, "target_kickoff_utc")

    if not quote_snapshot <= quote_created < target_kickoff:
        raise ArchiveGateError("quote chronology must satisfy snapshot <= created_at < target kickoff")

    match_payload = _json_body(match_body, "match")
    match = match_payload.get("data")
    if not isinstance(match, dict):
        raise ArchiveGateError("match response data must be an object")
    if match.get("id") != source_id:
        raise ArchiveGateError("match response ID does not match archive manifest")
    if str(match.get("sport", "")).casefold() != "football":
        raise ArchiveGateError("source match must be football")
    league = re.sub(r"[^a-z]", "", str(match.get("league", "")).casefold())
    if "seriea" not in league:
        raise ArchiveGateError("source match must belong to Serie A")
    if match.get("status") != "finished":
        raise ArchiveGateError("source match must be finished")

    source_kickoff = _utc(match.get("kickoff_utc"), "source kickoff")
    score = match.get("score")
    if not isinstance(score, dict) or not all(
        _nonnegative_int(score.get(side), f"score.{side}") for side in ("home", "away")
    ):
        raise ArchiveGateError("finished source match must carry both final scores")

    home = match.get("home")
    away = match.get("away")
    if not isinstance(home, dict) or not isinstance(away, dict):
        raise ArchiveGateError("match home/away identities are required")
    home_id = home.get("id")
    away_id = away.get("id")
    if not isinstance(home_id, str) or not home_id or not isinstance(away_id, str) or not away_id:
        raise ArchiveGateError("match home/away IDs are required")

    stats_payload = _json_body(statistics_body, "statistics")
    stats_data = stats_payload.get("data")
    stats_meta = stats_payload.get("meta")
    if not isinstance(stats_data, dict) or not isinstance(stats_meta, dict):
        raise ArchiveGateError("statistics response data and meta objects are required")
    if stats_meta.get("available") is not True:
        raise ArchiveGateError("provider reports that match statistics are unavailable")

    stats_home = stats_data.get("home")
    stats_away = stats_data.get("away")
    if not isinstance(stats_home, dict) or not isinstance(stats_away, dict):
        raise ArchiveGateError("both team-stat objects are required")
    if stats_home.get("team_id") != home_id or stats_away.get("team_id") != away_id:
        raise ArchiveGateError("statistics team IDs do not match the source match sides")

    missing_stat_fields: list[str] = []
    for side_name, side in (("home", stats_home), ("away", stats_away)):
        for field in ("corner_kicks", "yellow_cards", "red_cards"):
            value = side.get(field)
            if value is None:
                missing_stat_fields.append(f"{side_name}.{field}")
            elif not _nonnegative_int(value, f"{side_name}.{field}"):
                raise ArchiveGateError(f"{side_name}.{field} must be a nonnegative integer or null")

    if not source_kickoff < match_received or not source_kickoff < stats_received:
        raise ArchiveGateError("post-match source receipts must follow the source match kickoff")
    if archive_created < max(match_received, stats_received):
        raise ArchiveGateError("archive creation must not precede source receipt")
    if not match_received < quote_snapshot or not stats_received < quote_snapshot:
        raise ArchiveGateError("source receipt times must strictly precede the quote snapshot")
    if not archive_created < quote_snapshot:
        raise ArchiveGateError("private source archive must strictly precede the quote snapshot")
    if not source_kickoff < quote_snapshot:
        raise ArchiveGateError("source match must precede the target quote")

    return {
        "status": "VERIFIED_PRIVATE_PREQUOTE_LAGGED_SOURCE",
        "source_match_id": source_id,
        "target_match_id": target_id,
        "candidate_sha256": expected,
        "match_body_sha256": match_sha,
        "statistics_body_sha256": stats_sha,
        "missing_stat_fields": missing_stat_fields,
        "upstream_first_observation_proven": False,
        "feature_values_imputed": False,
        "feature_calculation_performed": False,
        "model_inference_performed": False,
        "supabase_write_performed": False,
        "public_raw_artifact_uploaded": False,
        "no_bet": True,
    }
