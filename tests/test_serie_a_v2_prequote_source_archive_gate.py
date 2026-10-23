"""Immutable source archive / time-order gate regressions, no prospective outcomes."""
from datetime import datetime, timedelta, timezone, tzinfo
import hashlib
from io import StringIO
import json
from pathlib import Path
import zipfile

import pytest

from serie_a_v2_frozen_shadow_preview import FROZEN_SHA
from serie_a_v2_live_diagnostic_report import PUBLIC_BASE, _source_codes
from serie_a_v2_prequote_source_archive_gate import (
    ARCHIVE_REPORT, SOURCE_DIR, verify_archive,
)

AFTER = datetime(2026, 10, 15, 12, tzinfo=timezone.utc)
OBSERVED = datetime(2026, 10, 13, 15, 22, tzinfo=timezone.utc)
UPLOADED = "2026-10-13T15:22:55Z"


def quote(when="2026-10-13T14:48:53Z"):
    return {
        "league": "SERIE_A", "event_id": "free-archive-evidence-test",
        "snapshot_time_utc": when, "commence_time_utc": "2026-10-16T18:45:00Z",
    }


def csv_history(code):
    # One synthetic pre-2026/27 match per archived historical season,
    # distinct date and exact original Football-Data stats.
    season_year = 2000 + int(code[:2])
    return (
        "Date,HomeTeam,AwayTeam,FTHG,FTAG,FTR,HC,AC,HY,AY,HR,AR\n"
        f"01/10/{season_year},Juventus,Napoli,1,0,H,4,3,2,1,0,0\n"
    ).encode()


def make_archive(tmp_path, *, change=None, flags=None, observed=OBSERVED, rehash_changes=False):
    audits = []
    raw_by_path = {}
    for code in _source_codes():
        path = SOURCE_DIR + f"serie_a_{code}.csv"
        body = csv_history(code)
        raw_by_path[path] = body
        audits.append({
            "season_code": code,
            "source_url": f"{PUBLIC_BASE}/{code}/I1.csv",
            "csv_sha256": hashlib.sha256(body).hexdigest(),
            "archived_source_name": f"serie_a_{code}.csv",
            "source_observed_at_utc": observed.isoformat(),
            "completed_source_rows": 1,
        })
    if change is not None:
        raw_by_path.update(change)
        if rehash_changes:
            for item in audits:
                source_name = SOURCE_DIR + item['archived_source_name']
                item['csv_sha256'] = hashlib.sha256(raw_by_path[source_name]).hexdigest()
    report = {
        "frozen_candidate_sha256": FROZEN_SHA,
        "2026_27_public_results_downloaded": False,
        "protect_2026_27_prospective_outcomes": True,
        "public_source_files": audits,
    }
    if flags is not None:
        report.update(flags)
    path = tmp_path / "capture.zip"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(ARCHIVE_REPORT, json.dumps(report))
        for name, raw in raw_by_path.items():
            z.writestr(name, raw)
    return path, hashlib.sha256(path.read_bytes()).hexdigest()


def test_current_saved_quote_cannot_be_backdated_by_later_public_sources(tmp_path):
    archive, digest = make_archive(tmp_path)
    result = verify_archive(
        archive, [quote()], as_of_utc=AFTER,
        github_artifact_sha256=digest, github_artifact_created_at_utc=UPLOADED,
    )
    assert result["historical_match_rows"] == 10
    assert result["archived_csv_count"] == 10
    assert result["quotes_checked"] == 1
    assert result["source_archive_prequote_ready"] == 0
    assert result["blocked"]["ARCHIVE_NOT_BEFORE_QUOTE"] == 1
    assert result["github_digest_matched"] is True
    assert result["eligible_for_frozen_prospective_cohort"] is False
    assert result["no_bet"] is True
    assert result["paid_provider_calls"] == result["supabase_writes"] == 0


def test_later_quote_has_source_time_readiness_but_no_v2_prospective_admission(tmp_path):
    archive, digest = make_archive(tmp_path)
    result = verify_archive(
        archive, [quote("2026-10-14T12:00:00Z")], as_of_utc=AFTER,
        github_artifact_sha256=digest, github_artifact_created_at_utc=UPLOADED,
    )
    assert result["source_archive_prequote_ready"] == 1
    assert result["by_quote"][0]["source_archive_before_quote"] is True
    assert result["independently_authenticated_github_metadata"] is False
    assert result["eligible_for_frozen_prospective_cohort"] is False
    assert result["eligible_for_product_publication"] is False


def test_no_authenticated_metadata_never_qualifies_time_readiness(tmp_path):
    archive, digest = make_archive(tmp_path)
    result = verify_archive(archive, [quote("2026-10-14T12:00:00Z")], as_of_utc=AFTER)
    assert result["source_archive_prequote_ready"] == 0
    assert result["blocked"]["UNATTESTED_GITHUB_METADATA"] == 1


def test_mismatched_public_csv_hash_rejected_before_quote_classification(tmp_path):
    name = SOURCE_DIR + "serie_a_1617.csv"
    archive, digest = make_archive(tmp_path, change={name: csv_history("1617") + b"# tampered\n"})
    with pytest.raises(ValueError, match="CSV SHA256 mismatch"):
        verify_archive(archive, [quote()], as_of_utc=AFTER)


def test_wrong_archive_github_digest_refused(tmp_path):
    archive, digest = make_archive(tmp_path)
    with pytest.raises(ValueError, match="GitHub artifact archive digest mismatch"):
        verify_archive(archive, [quote()], as_of_utc=AFTER, github_artifact_sha256="0"*64)


def test_protected_season_file_and_future_result_hidden_in_old_season_rejected(tmp_path):
    archive, digest = make_archive(tmp_path, change={
        SOURCE_DIR + "serie_a_2627.csv": csv_history("2526"),
    })
    with pytest.raises(ValueError, match="strictly frozen season list"):
        verify_archive(archive, [quote()], as_of_utc=AFTER)
    # Recreate valid member set but inject a 2026/27 outcome in the 2025/26 CSV.
    name = SOURCE_DIR + "serie_a_2526.csv"
    forged = csv_history("2526").replace(b"01/10/2025", b"01/10/2026")
    archive, digest = make_archive(tmp_path, change={name: forged}, rehash_changes=True)
    with pytest.raises(ValueError, match="protected prospective season result"):
        verify_archive(archive, [quote()], as_of_utc=AFTER)


def test_quote_order_duplicate_and_future_clock_fail_closed(tmp_path):
    archive, digest = make_archive(tmp_path)
    with pytest.raises(ValueError, match="duplicate exact quote"):
        verify_archive(archive, [quote(), quote()], as_of_utc=AFTER)
    with pytest.raises(ValueError, match="invalid quote timing"):
        verify_archive(archive, [quote("2026-10-18T00:00:00Z")], as_of_utc=AFTER)



def test_quote_outcome_field_is_never_read_as_source_timing_evidence(tmp_path):
    archive, digest = make_archive(tmp_path)
    malicious = {**quote(), "result": "H"}
    with pytest.raises(ValueError, match="outcomes or settlement fields forbidden"):
        verify_archive(archive, [malicious], as_of_utc=AFTER)



class _NoOffsetTimezone(tzinfo):
    def utcoffset(self, dt):
        return None

    def dst(self, dt):
        return None

    def tzname(self, dt):
        return "NO_OFFSET"


def test_archive_gate_rejects_offsetless_clock_before_touching_archive(tmp_path):
    missing_archive = tmp_path / "must-not-be-opened.zip"
    invalid_clock = datetime(2026, 10, 15, 12, tzinfo=_NoOffsetTimezone())
    with pytest.raises(ValueError, match="as_of_utc requires timezone"):
        verify_archive(missing_archive, [], as_of_utc=invalid_clock)
