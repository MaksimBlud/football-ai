"""Scheduled outcome-free cycle for EPL_AI_MARKET_PAIR_V1.

This collector reads only canonical market data plus historical ``matches`` used by the
existing no-odds model. It never reads target settlement/result tables and performs
append-only writes to ``epl_ai_market_pair_ledger``.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import pandas as pd

from database import supabase
from epl_ai_market_pair_collector import (
    CALIBRATOR_PATH,
    EXPERIMENT_ID,
    LEAGUE,
    MODEL_PATH,
    build_pair_rows,
    canonical_market_candidates,
    load_model_bundle,
    verify_model_bundle_unchanged,
)

OUTPUT_DIR = Path("artifacts/epl_ai_market_pair_v1")
PAIR_TABLE = "epl_ai_market_pair_ledger"
PAGE_SIZE = 1000

LEDGER_COLUMNS = ",".join(
    [
        "prediction_key",
        "league",
        "event_id",
        "home_team",
        "away_team",
        "kickoff_utc",
        "prediction_time_utc",
        "snapshot_time_utc",
        "market_home_prob",
        "market_draw_prob",
        "market_away_prob",
        "prediction_mode",
    ]
)
ODDS_COLUMNS = ",".join(
    [
        "league",
        "event_id",
        "snapshot_time_utc",
        "commence_time_utc",
        "home_team",
        "away_team",
        "home_odds",
        "draw_odds",
        "away_odds",
    ]
)
HISTORY_COLUMNS = ",".join(
    [
        "season",
        "league",
        "match_date",
        "match_time",
        "home_team",
        "away_team",
        "home_goals",
        "away_goals",
        "result",
        "home_shots",
        "away_shots",
        "home_shots_target",
        "away_shots_target",
    ]
)


def _read_paginated(table: str, columns: str, *, filters: dict[str, str] | None = None) -> pd.DataFrame:
    rows: list[dict] = []
    start = 0
    while True:
        query = supabase.table(table).select(columns)
        for column, value in (filters or {}).items():
            query = query.eq(column, value)
        response = query.range(start, start + PAGE_SIZE - 1).execute()
        batch = response.data or []
        rows.extend(batch)
        if len(batch) < PAGE_SIZE:
            break
        start += PAGE_SIZE
    return pd.DataFrame(rows)


def _existing_pair_keys(keys: list[str]) -> set[str]:
    if not keys:
        return set()
    existing: set[str] = set()
    for start in range(0, len(keys), 200):
        chunk = keys[start : start + 200]
        response = supabase.table(PAIR_TABLE).select("pair_key").in_("pair_key", chunk).execute()
        existing.update(str(row["pair_key"]) for row in (response.data or []))
    return existing


def _append_new_pairs(frame: pd.DataFrame) -> tuple[int, int]:
    if frame.empty:
        return 0, 0
    records = frame.to_dict(orient="records")
    keys = [str(record["pair_key"]) for record in records]
    existing = _existing_pair_keys(keys)
    pending = [record for record in records if str(record["pair_key"]) not in existing]
    if pending:
        supabase.table(PAIR_TABLE).insert(pending).execute()
    return len(pending), len(existing)


def main() -> None:
    generated_at = pd.Timestamp.now(tz="UTC")
    code_commit_sha = os.getenv("GITHUB_SHA", "LOCAL_OR_UNKNOWN")

    # Load and hash artifacts once. The same in-memory objects are used for every row.
    bundle = load_model_bundle(MODEL_PATH, CALIBRATOR_PATH)

    ledger = _read_paginated(
        "league_prediction_ledger",
        LEDGER_COLUMNS,
        filters={"league": LEAGUE, "prediction_mode": "MARKET_ONLY"},
    )
    odds = _read_paginated("odds_snapshots", ODDS_COLUMNS, filters={"league": LEAGUE})
    history = _read_paginated("matches", HISTORY_COLUMNS, filters={"league": LEAGUE})

    candidates = canonical_market_candidates(ledger, odds, now_utc=generated_at)
    pairs, excluded = build_pair_rows(
        candidates,
        history,
        bundle,
        generated_at_utc=generated_at,
        code_commit_sha=code_commit_sha,
    )

    # Fail if production artifacts changed at any point while this run was calculating.
    verify_model_bundle_unchanged(bundle, MODEL_PATH, CALIBRATOR_PATH)
    inserted, unchanged = _append_new_pairs(pairs)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    pairs.to_csv(OUTPUT_DIR / "candidate_pairs.csv", index=False)
    (OUTPUT_DIR / "excluded.json").write_text(
        json.dumps(excluded, indent=2, sort_keys=True), encoding="utf-8"
    )
    audit = {
        "experiment_id": EXPERIMENT_ID,
        "generated_at_utc": generated_at.isoformat(),
        "code_commit_sha": code_commit_sha,
        "model_artifact_sha256": bundle.model_sha256,
        "calibrator_artifact_sha256": bundle.calibrator_sha256,
        "ledger_rows_read": int(len(ledger)),
        "odds_rows_read": int(len(odds)),
        "history_rows_read": int(len(history)),
        "future_market_candidates": int(len(candidates)),
        "pair_rows_valid": int(len(pairs)),
        "pair_rows_inserted": int(inserted),
        "pair_rows_unchanged": int(unchanged),
        "excluded": excluded,
        "outcome_tables_read": [],
        "production_artifacts_modified": false if False else False,
    }
    (OUTPUT_DIR / "audit.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(audit, indent=2, sort_keys=True))
    print("RESEARCH ONLY: append-only future AI/market pairs; target outcomes are not read.")


if __name__ == "__main__":
    main()
