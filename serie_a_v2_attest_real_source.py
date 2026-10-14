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

from serie_a_v2_forward_capture import (
    REPOSITORY, discover_archives, get_archive, verify_source_run,
)
from serie_a_v2_prequote_source_archive_gate import verify_archive


def attest_latest_source(*, token: str, now: datetime, discover=discover_archives,
                         load=get_archive, verify_run=verify_source_run) -> dict:
    if now.tzinfo is None:
        raise ValueError("source attestation needs an aware UTC clock")
    at = now.astimezone(timezone.utc)
    archives = discover(token=token)
    eligible = [x for x in archives if x["created_at"] < at]
    if not eligible:
        raise RuntimeError("no original historical V2 GitHub source archive available")
    archive = max(eligible, key=lambda x: (x["created_at"], x["artifact_id"]))
    parent = verify_run(archive, quote_time=at, token=token)
    if not isinstance(parent, dict) or not parent.get("run_completed_at_utc"):
        raise ValueError("source workflow parent attestation missing")
    raw = load(archive["artifact_id"], token=token)
    with TemporaryDirectory() as tmpdir:
        archive_path = Path(tmpdir) / "original-history.zip"
        archive_path.write_bytes(raw)
        proven = verify_archive(
            archive_path, [], as_of_utc=at,
            github_artifact_sha256=archive["sha256"],
            github_artifact_created_at_utc=archive["created_at"].isoformat(),
        )
    if (not proven["github_digest_matched"]
            or proven["archived_csv_count"] != 10
            or proven["historical_match_rows"] <= 0
            or proven["quotes_checked"] != 0
            or proven["eligible_for_frozen_prospective_cohort"]
            or not proven["no_bet"]):
        raise ValueError("real original V2 source proof incomplete")
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
