"""Independently attest actual (not synthetic) approved V2 historical source ZIP.

Runs in read-only GitHub Actions on main. This deliberately does NOT read odds,
future 2026/27 results, or make a V2 forecast. It is a prerequisite source proof
used to surface errors in the real artifact layout / GitHub response early.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import zipfile
import zlib

from pandas.errors import ParserError
from requests import HTTPError

from serie_a_v2_forward_capture import (
    REPOSITORY, SOURCE_WORKFLOW_PATH, discover_archives, get_archive, verify_source_run,
)
from serie_a_v2_prequote_source_archive_gate import verify_archive
from market_anchor_v2_source_rights import (
    require_personal_research_inference_scope,
    write_research_scope_blocked_report,
)


def _artifact_rejection(artifact_id, exc):
    return {
        "artifact_id": artifact_id,
        "error_type": type(exc).__name__,
        "reason": str(exc),
    }


def _is_missing_github_resource(exc):
    if isinstance(exc, HTTPError):
        return getattr(getattr(exc, "response", None), "status_code", None) == 404
    # The guarded original V2 GitHub JSON boundary normalizes non-200
    # responses to RuntimeError rather than requests.HTTPError.
    return (
        isinstance(exc, RuntimeError)
        and str(exc) == "GitHub API request failed with HTTP 404"
    )


def attest_latest_source(*, token: str, now: datetime, discover=discover_archives,
                         load=get_archive, verify_run=verify_source_run) -> dict:
    """Attest the newest fully verified source archive, not merely the newest upload.

    A failed workflow may still publish a partial artifact because its upload step
    uses if: always(). Such an artifact must be rejected without preventing
    fallback to an older, independently verified source archive. Transient
    GitHub/network failures still abort; only candidate-specific provenance,
    digest, archive-format, and missing-resource failures are skipped.
    """
    from market_anchor_v2_direct_access import require_v2_source_capture_access
    require_v2_source_capture_access()
    if (
        not isinstance(now, datetime)
        or now.tzinfo is None
        or now.utcoffset() is None
    ):
        raise ValueError("source attestation needs an aware UTC clock")
    at = now.astimezone(timezone.utc)
    archives = discover(token=token)
    if not isinstance(archives, list):
        raise ValueError("source archive discovery must return a list")

    eligible = []
    for archive in archives:
        if not isinstance(archive, dict):
            raise ValueError("malformed source archive metadata")
        created_at = archive.get("created_at")
        if (
            not isinstance(created_at, datetime)
            or created_at.tzinfo is None
            or created_at.utcoffset() is None
        ):
            raise ValueError("source artifact creation time must be timezone-aware")
        if created_at.astimezone(timezone.utc) < at:
            eligible.append(archive)
    if not eligible:
        raise RuntimeError("no original historical V2 GitHub source archive available")

    eligible.sort(
        key=lambda item: (
            item["created_at"].astimezone(timezone.utc),
            item.get("artifact_id", 0),
        ),
        reverse=True,
    )
    rejected = []
    selected = None
    last_error = None

    for candidate_index, archive in enumerate(eligible):
        artifact_id = archive.get("artifact_id")
        try:
            if type(artifact_id) is not int or artifact_id <= 0:
                raise ValueError("invalid source artifact id")
            if type(archive.get("run_id")) is not int or archive["run_id"] <= 0:
                raise ValueError("invalid source parent run id")
            head_sha = archive.get("head_sha")
            if not isinstance(head_sha, str) or len(head_sha) != 40:
                raise ValueError("invalid source parent head SHA")

            parent = verify_run(archive, quote_time=at, token=token)
            if not isinstance(parent, dict) or not parent.get("run_completed_at_utc"):
                raise ValueError("source workflow parent attestation missing")
            if (
                parent.get("workflow_path") != SOURCE_WORKFLOW_PATH
                or parent.get("run_id") != archive["run_id"]
                or parent.get("run_head_sha") != head_sha
            ):
                raise ValueError("source workflow parent identity mismatch")

            completed_raw = parent["run_completed_at_utc"]
            if not isinstance(completed_raw, str):
                raise ValueError("source parent completion time missing")
            completed = datetime.fromisoformat(completed_raw.replace("Z", "+00:00"))
            if completed.tzinfo is None or completed.utcoffset() is None:
                raise ValueError("source parent completion time must be timezone-aware")
            completed = completed.astimezone(timezone.utc)
            created = archive["created_at"].astimezone(timezone.utc)
            if completed >= at or created > completed:
                raise ValueError("source parent completion time is not strictly after upload and before attestation")

            raw = load(artifact_id, token=token)
            if not isinstance(raw, bytes) or not raw:
                raise ValueError("source archive loader returned no bytes")
            with TemporaryDirectory() as tmpdir:
                archive_path = Path(tmpdir) / "original-history.zip"
                archive_path.write_bytes(raw)
                proven = verify_archive(
                    archive_path, [], as_of_utc=at,
                    github_artifact_sha256=archive["sha256"],
                    github_artifact_created_at_utc=archive["created_at"].isoformat(),
                )
            if (
                not proven["github_digest_matched"]
                or proven["archived_csv_count"] != 10
                or proven["historical_match_rows"] <= 0
                or proven["quotes_checked"] != 0
                or proven["eligible_for_frozen_prospective_cohort"]
                or not proven["no_bet"]
            ):
                raise ValueError("real original V2 source proof incomplete")
        except (HTTPError, RuntimeError) as exc:
            if not _is_missing_github_resource(exc):
                raise
            rejected.append(_artifact_rejection(artifact_id, exc))
            last_error = exc
            continue
        except (
            ValueError, KeyError, TypeError, zipfile.BadZipFile,
            EOFError, zlib.error, ParserError, UnicodeError,
        ) as exc:
            rejected.append(_artifact_rejection(artifact_id, exc))
            last_error = exc
            continue

        selected = (candidate_index, archive, parent, proven)
        break

    if selected is None:
        if last_error is None:
            raise RuntimeError("no original historical V2 GitHub source archive passed verification")
        raise ValueError(
            "no fully verified original historical V2 GitHub source archive; "
            f"rejected {len(rejected)} candidate(s): {type(last_error).__name__}: {last_error}"
        ) from last_error

    candidate_index, archive, parent, proven = selected
    return {
        "schema_version": "SERIE_A_ORIGINAL_V2_REAL_SOURCE_ATTESTATION_V1",
        "mode": "SOURCE_ARCHIVE_ONLY_NO_PREDICTION_NO_BET",
        "checked_at_utc": at.isoformat(),
        "source_artifact_id": archive["artifact_id"],
        "source_artifact_created_at_utc": archive["created_at"].isoformat(),
        "source_artifact_sha256": archive["sha256"],
        "source_run_id": archive["run_id"],
        "source_run_head_sha": archive["head_sha"],
        "source_run_provenance": parent,
        "source_candidates_examined": candidate_index + 1,
        "rejected_source_artifacts": rejected,
        "source_candidate_fallback_used": candidate_index > 0,
        "verified_pre_prospective_source_files": proven["archived_csv_count"],
        "verified_historical_results": proven["historical_match_rows"],
        "verified_original_v2_sha256": proven["original_candidate_sha256"],
        "source_archive_sha256_verified": True,
        "old_season_only": True,
        "protected_2026_27_results_read": False,
        "quotes_read": 0,
        "forecasts_created": 0,
        "eligible_for_frozen_prospective_cohort": False,
        "eligible_for_product_publication": False,
        "no_bet": True,
        "paid_provider_calls": 0,
        "supabase_reads": 0,
        "supabase_writes": 0,
        "model_refit_or_promotion": False,
    }

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if os.environ.get("GITHUB_REPOSITORY") != REPOSITORY:
        raise RuntimeError("source proof must run in original GitHub repository")
    try:
        from market_anchor_v2_direct_access import require_v2_source_capture_access
        require_v2_source_capture_access()
    except PermissionError as exc:
        report = write_research_scope_blocked_report(
            args.output,
            "SERIE_A_ORIGINAL_V2_SOURCE_ATTESTATION",
            str(exc),
        )
        print(json.dumps(report, sort_keys=True))
        return
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        raise RuntimeError("GITHUB_TOKEN actions:read missing")
    proof = attest_latest_source(token=token, now=datetime.now(timezone.utc))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(proof, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(json.dumps({k: proof[k] for k in (
        "mode", "source_artifact_id", "source_run_id",
        "verified_pre_prospective_source_files", "verified_historical_results",
        "source_archive_sha256_verified", "forecasts_created",
        "paid_provider_calls", "no_bet",
    )}, sort_keys=True))


if __name__ == "__main__":
    main()
