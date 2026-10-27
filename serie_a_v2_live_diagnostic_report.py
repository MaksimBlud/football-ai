"""Free, outcome-blind, non-admissible LIVE Serie A V2 research diagnostic.

This reads already-persisted 1X2 quotes and publicly accessible Football-Data
history completed before the 2026/27 protected prospective cohort; it NEVER\ncalls the paid Odds API or inserts into Supabase. Crucially,
newly downloaded history CANNOT be represented as verified at older quote time.
The 19-feature V2 outputs are DIAGNOSTIC ONLY, not prospective observations.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from urllib.parse import urlsplit
import hashlib
from io import BytesIO
import json
from pathlib import Path

import pandas as pd
import requests

from serie_a_runtime_config import SERIE_A_RUNTIME_CONFIG
from serie_a_v2_asof_feature_manifest import build_manifest
from serie_a_v2_frozen_shadow_preview import (
    fetch_saved_upcoming_serie_a_quotes, parse_utc, shadow_preview,
)

PUBLIC_BASE = "https://www.football-data.co.uk/mmz4281"
PAID_PROVIDER_REQUESTS = 0
MAX_PUBLIC_SOURCE_FILES = len(SERIE_A_RUNTIME_CONFIG.historical_source.season_codes)


def _source_codes() -> list[str]:
    historical = list(SERIE_A_RUNTIME_CONFIG.historical_source.season_codes)
    current = SERIE_A_RUNTIME_CONFIG.finished_results_source.season_code
    # Hard embargo: no downloading 2026/27 scoreboard/CSV until the frozen
    # prospective outcome-read gate. Filtering after download is not enough.
    if current in historical or any(code >= current for code in historical):
        raise RuntimeError("protected Serie A prospective season cannot be read")
    return historical


def _assert_approved_history_url(url: str, *, season_code: str) -> None:
    """Require the exact HTTPS Football-Data CSV endpoint before making a request."""
    parts = urlsplit(url)
    expected_path = (
        f"/mmz4281/{season_code}/"
        f"{SERIE_A_RUNTIME_CONFIG.historical_source.competition_code}.csv"
    )
    expected_url = f"{PUBLIC_BASE}/{season_code}/{SERIE_A_RUNTIME_CONFIG.historical_source.competition_code}.csv"
    if (
        parts.scheme != "https"
        or parts.hostname != "www.football-data.co.uk"
        or parts.port not in (None, 443)
        or parts.username is not None
        or parts.password is not None
        or parts.path != expected_path
        or parts.query
        or parts.fragment
        or url != expected_url
    ):
        raise ValueError("historical source URL is not the approved HTTPS Football-Data endpoint")


def fetch_public_history(*, get=requests.get, capture_dir: Path | None = None) -> tuple[pd.DataFrame, list[dict]]:
    """Explicit, bounded configured public URLs; never odds API, never cache guess."""
    all_frames = []
    audit = []
    if capture_dir is not None:
        capture_dir.mkdir(parents=True, exist_ok=True)
    for code in _source_codes():
        if len(code) != 4 or not code.isdigit():
            raise ValueError("unexpected historical season code")
        url = f"{PUBLIC_BASE}/{code}/{SERIE_A_RUNTIME_CONFIG.historical_source.competition_code}.csv"
        _assert_approved_history_url(url, season_code=code)
        # Do not let requests follow a redirect to a different host/path. A
        # successful status alone is not source provenance; require the exact
        # approved final URL before touching response bytes.
        response = get(url, timeout=30, allow_redirects=False)
        if response.status_code != 200:
            raise RuntimeError(f"Public Serie A CSV unavailable: season={code}, http={response.status_code}")
        if getattr(response, "url", None) != url:
            raise RuntimeError(f"Public Serie A CSV returned an unexpected final URL: season={code}")
        body = response.content
        capture = datetime.now(timezone.utc)
        if capture_dir is not None:
            (capture_dir / f"serie_a_{code}.csv").write_bytes(body)
        frame = pd.read_csv(BytesIO(body), low_memory=False)
        required = {"Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR",
                    "HC", "AC", "HY", "AY", "HR", "AR"}
        missing = required - set(frame.columns)
        if missing:
            raise RuntimeError(f"Public Serie A source {code} missing stats: {sorted(missing)}")
        outcome = frame["FTR"].fillna("").astype(str).str.strip()
        if not outcome.isin(("H", "D", "A")).all():
            raise RuntimeError(f"Historical pre-freeze Serie A season {code} has missing/invalid results")
        frame = frame.loc[:, list(sorted(required))].copy()
        all_frames.append(frame)
        audit.append({
            "season_code": code,
            "source_url": url,
            "csv_sha256": hashlib.sha256(body).hexdigest(),
            "archived_source_name": f"serie_a_{code}.csv",
            "source_observed_at_utc": capture.isoformat(),
            "completed_source_rows": len(frame),
        })
    return pd.concat(all_frames, ignore_index=True), audit


# Freeze rule is stronger than merely omitting this season from the remote
# downloader. A caller may pass a concatenated frame or forged source audit.
# Disallow 2026/27 rows, even if later excluded by the as-of feature cutoff.
PROTECTED_SEASON_START = datetime(2026, 7, 1)


def _assert_original_v2_source_embargo(history: pd.DataFrame, audit: list[dict], *,
                                      as_of_utc: datetime) -> None:
    codes = _source_codes()
    if len(audit) != len(codes):
        raise ValueError("original V2 source audit must include exact pre-freeze seasons")
    seen = set()
    for source in audit:
        code = source.get("season_code")
        if code not in codes or code in seen:
            raise ValueError("original V2 source audit includes a protected or duplicate season")
        seen.add(code)
        expected_url = (
            f"{PUBLIC_BASE}/{code}/"
            f"{SERIE_A_RUNTIME_CONFIG.historical_source.competition_code}.csv"
        )
        if (source.get("source_url") != expected_url
                or source.get("archived_source_name") != f"serie_a_{code}.csv"):
            raise ValueError("original V2 source audit has an unexpected URL or source file")
        sha = source.get("csv_sha256")
        if not isinstance(sha, str) or len(sha) != 64 or any(x not in "0123456789abcdef" for x in sha):
            raise ValueError("original V2 source audit contains invalid SHA256")
        collected = parse_utc(source["source_observed_at_utc"])
        if collected > as_of_utc:
            raise ValueError("original V2 source observation in the future")
        nrows = source.get("completed_source_rows")
        if not isinstance(nrows, int) or isinstance(nrows, bool) or nrows <= 0:
            raise ValueError("original V2 source audit has no completed rows")
    if "Date" not in history.columns or history.empty:
        raise ValueError("original V2 historical dates missing")
    dates = pd.to_datetime(history["Date"], dayfirst=True, format="mixed", errors="raise")
    if dates.isna().any() or dates.dt.tz is not None:
        raise ValueError("original V2 date-only historical record invalid")
    if (dates >= PROTECTED_SEASON_START).any():
        raise ValueError("protected Serie A 2026/27 outcomes cannot enter original V2 diagnostic")


def make_report(quotes: list[dict], history: pd.DataFrame, source_audit: list[dict], *,
                as_of_utc: datetime) -> dict:
    if not source_audit:
        raise ValueError("history provenance required")
    if (
        not isinstance(as_of_utc, datetime)
        or as_of_utc.tzinfo is None
        or as_of_utc.utcoffset() is None
    ):
        raise ValueError("as-of timestamp needs UTC timezone")
    _assert_original_v2_source_embargo(
        history, source_audit, as_of_utc=as_of_utc.astimezone(timezone.utc)
    )
    quote_times = [parse_utc(q["snapshot_time_utc"]) for q in quotes]
    source_times = [parse_utc(entry["source_observed_at_utc"]) for entry in source_audit]
    manifest = build_manifest(history, quotes)
    original_inputs = manifest["feature_manifests"]
    # Completeness is reported on exact original 19-feature vectors, not a
    # tuned threshold, new predictor, or an additional eligibility gate.
    missingness = [{
        "event_id": item["event_id"],
        "home_team": item["home_team"],
        "away_team": item["away_team"],
        "observed_frozen_feature_count": item["observed_frozen_feature_count"],
        "median_imputed_frozen_feature_count": item["median_imputed_frozen_feature_count"],
        "history_coverage": item["history_coverage"],
    } for item in original_inputs]
    preview = shadow_preview(quotes, original_inputs, as_of_utc=as_of_utc)
    late_source_quotes = sum(any(t > quote for t in source_times) for quote in quote_times)
    # Date-only cutoff from original historical builder is NOT proof that this
    # downloaded file existed when the quotation was captured.
    assert not preview["eligible_for_product_publication"]
    assert all(not p["eligible_for_frozen_prospective_cohort"] for p in preview["previews"])
    return {
        "schema_version": "SERIE_A_V2_LIVE_DIAGNOSTIC_SOURCE_ATTESTATION_V1",
        "mode": "RESEARCH_ONLY_UNVERIFIED_PROVENANCE_NO_BET",
        "as_of_utc": as_of_utc.astimezone(timezone.utc).isoformat(),
        "frozen_candidate_sha256": manifest["candidate_sha256"],
        "historical_source": "FOOTBALL_DATA_CSV",
        "protect_2026_27_prospective_outcomes": True,
        "2026_27_public_results_downloaded": False,
        "history_stale_without_2026_27_form": True,
        "public_source_files": source_audit,
        "public_http_requests": len(source_audit),
        "paid_provider_requests": 0,
        "supabase_writes": 0,
        "model_training": False,
        "model_promotion": False,
        "independently_attested_feature_availability_at_quote": False,
        "quotes_with_source_observed_after_quote": late_source_quotes,
        "original_incumbent_asof_prediction_captured": False,
        "eligible_for_frozen_prospective_cohort": False,
        "eligible_for_product_publication": False,
        "no_bet": True,
        "history_rows": int(len(history)),
        "feature_count": manifest["feature_count"],
        "quoted_fixtures": len(quotes),
        "feature_rows_with_missing_values": sum(
            x["median_imputed_frozen_feature_count"] > 0 for x in missingness
        ),
        "feature_rows_all_median_imputed": sum(
            x["observed_frozen_feature_count"] == 0 for x in missingness
        ),
        "feature_rows_with_all_19_observed": sum(
            x["observed_frozen_feature_count"] == manifest["feature_count"] for x in missingness
        ),
        "per_fixture_feature_coverage": missingness,
        "diagnostic_scored": preview["scored"],
        "diagnostic_blocked": preview["blocked"],
        "diagnostic_previews": preview["previews"],
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--raw-source-dir", type=Path, required=True)
    args = p.parse_args()
    from database import supabase
    now = datetime.now(timezone.utc)
    quotes = fetch_saved_upcoming_serie_a_quotes(supabase, now=now)
    history, sources = fetch_public_history(capture_dir=args.raw_source_dir)
    report = make_report(quotes, history, sources, as_of_utc=datetime.now(timezone.utc))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True)+"\n", encoding="utf-8")
    summary = {key: report[key] for key in (
        "mode", "historical_source", "public_http_requests", "paid_provider_requests",
        "supabase_writes", "quoted_fixtures", "history_rows", "feature_count",
        "quotes_with_source_observed_after_quote", "diagnostic_scored",
        "diagnostic_blocked", "feature_rows_with_missing_values",
        "feature_rows_all_median_imputed", "feature_rows_with_all_19_observed",
        "eligible_for_frozen_prospective_cohort",
        "eligible_for_product_publication", "no_bet",
    )}
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
