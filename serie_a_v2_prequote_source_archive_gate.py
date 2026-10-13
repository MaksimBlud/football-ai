"""Verify old-season source archive integrity before a *later* Serie A quote.

No provider requests, database access, protected 2026/27 scores, model inference,
or promotion. GitHub artifact digest and upload time must come from an independent
GitHub metadata read; caller-supplied values alone are not an attestation.
A READY result is SOURCE-TIMING-ONLY, never frozen prospective admission.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from io import BytesIO
import json
from pathlib import Path
from typing import Any, Mapping
import zipfile

import pandas as pd

from serie_a_v2_live_diagnostic_report import _source_codes, PUBLIC_BASE
from serie_a_v2_frozen_shadow_preview import FROZEN_SHA, parse_utc, _guard_outcome_free
from serie_a_v2_asof_feature_manifest import REQUIRED, _validate_history

ARCHIVE_REPORT = "serie_a_v2_real_quote_diagnostic.json"
SOURCE_DIR = "serie_a_v2_source_capture/"
CUTOFF_DAY = pd.Timestamp("2026-07-01")
MAX_ZIP_BYTES = 12_000_000
MAX_CSV_BYTES = 2_000_000


def verify_archive(archive_path: Path, quotes: list[Mapping[str, Any]], *,
                   as_of_utc: datetime,
                   github_artifact_sha256: str | None = None,
                   github_artifact_created_at_utc: str | None = None) -> dict:
    """Fail closed for any missing, mutated, unexpected or post-freeze CSV.

    A SHA supplied by a caller is only checked for equality; an independently
    authenticated GitHub API digest+timestamp is required to trust it as evidence.
    No quote can be called source-before-quote verified without BOTH values.
    """
    if as_of_utc.tzinfo is None:
        raise ValueError("as_of_utc requires timezone")
    now = as_of_utc.astimezone(timezone.utc)
    expected_names = {SOURCE_DIR + f"serie_a_{code}.csv" for code in _source_codes()}
    required_paths = expected_names | {ARCHIVE_REPORT}
    if archive_path.stat().st_size > MAX_ZIP_BYTES:
        raise ValueError("oversized source archive")
    archive_bytes = archive_path.read_bytes()
    digest = hashlib.sha256(archive_bytes).hexdigest()
    sha_matches_github = False
    if github_artifact_sha256 is not None:
        if len(github_artifact_sha256) != 64 or any(c not in "0123456789abcdef" for c in github_artifact_sha256):
            raise ValueError("invalid GitHub artifact digest")
        if digest != github_artifact_sha256:
            raise ValueError("GitHub artifact archive digest mismatch")
        sha_matches_github = True
    uploaded = (parse_utc(github_artifact_created_at_utc)
                if github_artifact_created_at_utc is not None else None)
    if uploaded is not None and uploaded > now:
        raise ValueError("future GitHub artifact timestamp")
    source_times = []
    with zipfile.ZipFile(archive_path, "r") as z:
        names = z.namelist()
        if len(names) != len(required_paths) or set(names) != required_paths:
            raise ValueError("source archive files do not match strictly frozen season list")
        for info in z.infolist():
            if info.file_size > MAX_CSV_BYTES and info.filename != ARCHIVE_REPORT:
                raise ValueError("oversized archived CSV")
            if info.file_size > 3_000_000 and info.filename == ARCHIVE_REPORT:
                raise ValueError("oversized archived source audit")
        report = json.loads(z.read(ARCHIVE_REPORT))
        if report.get("frozen_candidate_sha256") != FROZEN_SHA:
            raise ValueError("archived frozen candidate mismatch")
        if report.get("2026_27_public_results_downloaded") is not False:
            raise ValueError("protected season outcome embargo not proven")
        if report.get("protect_2026_27_prospective_outcomes") is not True:
            raise ValueError("missing protected season embargo flag")
        audits = report.get("public_source_files")
        if not isinstance(audits, list) or len(audits) != len(expected_names):
            raise ValueError("source audit incomplete")
        seen = set()
        frames = []
        for item in audits:
            code = item.get("season_code")
            expected_name = SOURCE_DIR + f"serie_a_{code}.csv"
            expected_url = f"{PUBLIC_BASE}/{code}/I1.csv"
            if (code not in _source_codes() or code in seen
                or item.get("archived_source_name") != f"serie_a_{code}.csv"
                or item.get("source_url") != expected_url):
                raise ValueError("unexpected protected or duplicate source metadata")
            seen.add(code)
            raw = z.read(expected_name)
            if hashlib.sha256(raw).hexdigest() != item.get("csv_sha256"):
                raise ValueError("archived source CSV SHA256 mismatch")
            observed = parse_utc(item["source_observed_at_utc"])
            if observed > now:
                raise ValueError("future source observation")
            if uploaded is not None and observed > uploaded:
                raise ValueError("source capture after GitHub artifact upload")
            source_times.append(observed)
            frame = pd.read_csv(BytesIO(raw), low_memory=False)
            if len(frame) != item.get("completed_source_rows"):
                raise ValueError("source row-count mismatch")
            if not REQUIRED.issubset(frame.columns):
                raise ValueError("historical source statistics incomplete")
            frames.append(frame[list(REQUIRED)].copy())
        historical = _validate_history(pd.concat(frames, ignore_index=True))
        if (historical["_match_date"] >= CUTOFF_DAY).any():
            raise ValueError("protected prospective season result in old-season CSV")
    if not source_times:
        raise ValueError("empty old-season source capture")
    eligible_quote_count = 0
    reasons = {"ARCHIVE_NOT_BEFORE_QUOTE": 0, "UNATTESTED_GITHUB_METADATA": 0}
    seen_quotes = set()
    evidence = []
    for q in quotes:
        _guard_outcome_free(q)
        if q.get("league") != "SERIE_A":
            raise ValueError("only Serie A quote identities allowed")
        event = q.get("event_id")
        if not isinstance(event, str) or not event.strip():
            raise ValueError("empty quote event id")
        quote_time = parse_utc(q["snapshot_time_utc"])
        kickoff = parse_utc(q["commence_time_utc"])
        if not quote_time < kickoff or quote_time > now:
            raise ValueError("invalid quote timing")
        key = (event, quote_time)
        if key in seen_quotes:
            raise ValueError("duplicate exact quote observation")
        seen_quotes.add(key)
        before = all(ts < quote_time for ts in source_times)
        if uploaded is not None:
            before = before and uploaded < quote_time
        if not before:
            reasons["ARCHIVE_NOT_BEFORE_QUOTE"] += 1
        anchored = sha_matches_github and uploaded is not None
        if not anchored:
            reasons["UNATTESTED_GITHUB_METADATA"] += 1
        ready = before and anchored
        eligible_quote_count += int(ready)
        evidence.append({
            "event_id": event,
            "quote_time_utc": quote_time.isoformat(),
            "source_archive_before_quote": ready,
            "frozen_prospective_eligible": False,
            "product_publishable": False,
        })
    return {
        "schema_version": "SERIE_A_V2_PREQUOTE_SOURCE_ARCHIVE_GATE_V1",
        "mode": "SOURCE_TIMING_ONLY_NOT_FROZEN_PROSPECTIVE",
        "original_candidate_sha256": FROZEN_SHA,
        "archived_csv_count": len(source_times),
        "historical_match_rows": len(historical),
        "archive_sha256": digest,
        "github_digest_matched": sha_matches_github,
        "github_artifact_created_at_utc": uploaded.isoformat() if uploaded else None,
        "quotes_checked": len(quotes),
        "source_archive_prequote_ready": eligible_quote_count,
        "blocked": reasons,
        "by_quote": evidence,
        "independently_authenticated_github_metadata": False,
        "requires_frozen_incumbent_and_same_information_time_features": True,
        "eligible_for_frozen_prospective_cohort": False,
        "eligible_for_product_publication": False,
        "no_bet": True,
        "paid_provider_calls": 0,
        "supabase_writes": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--quotes-json", type=Path, required=True)
    parser.add_argument("--github-artifact-sha256", default=None)
    parser.add_argument("--github-artifact-created-at-utc", default=None)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    quotes = json.loads(args.quotes_json.read_text(encoding="utf-8"))
    if not isinstance(quotes, list):
        raise ValueError("quotes JSON must be a list")
    result = verify_archive(
        args.archive, quotes, as_of_utc=datetime.now(timezone.utc),
        github_artifact_sha256=args.github_artifact_sha256,
        github_artifact_created_at_utc=args.github_artifact_created_at_utc,
    )
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in (
        "mode", "quotes_checked", "source_archive_prequote_ready",
        "historical_match_rows", "github_digest_matched", "blocked",
        "eligible_for_frozen_prospective_cohort", "paid_provider_calls",
    )}, sort_keys=True))


if __name__ == "__main__":
    main()
