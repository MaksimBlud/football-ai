"""Free, outcome-blind, non-admissible LIVE Serie A V2 research diagnostic.

This reads already-persisted 1X2 quotes and publicly accessible Football-Data
history; it NEVER calls the paid Odds API or inserts into Supabase. Crucially,
newly downloaded history CANNOT be represented as verified at older quote time.
The 19-feature V2 outputs are DIAGNOSTIC ONLY, not prospective observations.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
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
MAX_PUBLIC_SOURCE_FILES = len(SERIE_A_RUNTIME_CONFIG.historical_source.season_codes) + 1


def _source_codes() -> list[str]:
    historical = list(SERIE_A_RUNTIME_CONFIG.historical_source.season_codes)
    current = SERIE_A_RUNTIME_CONFIG.finished_results_source.season_code
    if current in historical:
        raise RuntimeError("current Serie A season duplicated in history contract")
    return historical + [current]


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
        response = get(url, timeout=30)
        if response.status_code != 200:
            raise RuntimeError(f"Public Serie A CSV unavailable: season={code}, http={response.status_code}")
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
        if code != SERIE_A_RUNTIME_CONFIG.finished_results_source.season_code and not outcome.isin(("H","D","A")).all():
            raise RuntimeError(f"Historical Serie A season {code} includes unverified outcomes")
        if code == SERIE_A_RUNTIME_CONFIG.finished_results_source.season_code:
            if not outcome.isin(("H","D","A","")).all():
                raise RuntimeError("Current public Serie A data has an invalid result field")
            frame = frame.loc[outcome.isin(("H","D","A"))].copy()
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


def make_report(quotes: list[dict], history: pd.DataFrame, source_audit: list[dict], *,
                as_of_utc: datetime) -> dict:
    if not source_audit:
        raise ValueError("history provenance required")
    if as_of_utc.tzinfo is None:
        raise ValueError("as-of timestamp needs UTC timezone")
    quote_times = [parse_utc(q["snapshot_time_utc"]) for q in quotes]
    source_times = [parse_utc(entry["source_observed_at_utc"]) for entry in source_audit]
    manifest = build_manifest(history, quotes)
    preview = shadow_preview(quotes, manifest["feature_manifests"], as_of_utc=as_of_utc)
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
        "diagnostic_blocked", "eligible_for_frozen_prospective_cohort",
        "eligible_for_product_publication", "no_bet",
    )}
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
