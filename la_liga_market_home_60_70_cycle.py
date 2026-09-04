"""Read-only operational cycle for LA_LIGA_MARKET_HOME_60_70_V1."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from la_liga_market_home_60_70_prospective import (
    CANDIDATE_ID,
    EVALUATION_NOT_BEFORE_UTC,
    IMPLEMENTATION_FREEZE_UTC,
    attach_results_for_explicit_evaluation,
    build_canonical_decisions,
    descriptive_evaluation,
    settlement_identity,
)

OUTPUT_DIR = Path("artifacts/la_liga_market_home_60_70_v1")
PAGE_SIZE = 1000


def _client():
    from database import supabase
    return supabase


def _fetch_pages(client, table: str, columns: str, filters: tuple[tuple[str, str], ...] = ()) -> list[dict]:
    rows: list[dict] = []
    start = 0
    while True:
        query = client.table(table).select(columns)
        for column, value in filters:
            query = query.eq(column, value)
        response = query.range(start, start + PAGE_SIZE - 1).execute()
        page = list(response.data or [])
        rows.extend(page)
        if len(page) < PAGE_SIZE:
            break
        start += PAGE_SIZE
    return rows


def load_ledger(client) -> pd.DataFrame:
    columns = (
        "prediction_key,league,event_id,home_team,away_team,kickoff_utc,snapshot_time_utc,"
        "market_home_prob,market_draw_prob,market_away_prob,market_pick,prediction_mode"
    )
    return pd.DataFrame(_fetch_pages(client, "league_prediction_ledger", columns, (("league", "LA_LIGA"),)))


def load_odds_snapshots(client) -> pd.DataFrame:
    columns = (
        "league,event_id,snapshot_time_utc,commence_time_utc,home_team,away_team,"
        "home_odds,draw_odds,away_odds"
    )
    return pd.DataFrame(_fetch_pages(client, "odds_snapshots", columns, (("league", "LA_LIGA"),)))


def load_result_identities(client) -> pd.DataFrame:
    columns = "league,match_date,home_team,away_team"
    return pd.DataFrame(_fetch_pages(client, "league_finished_results", columns, (("league", "LA_LIGA"),)))


def load_result_values(client) -> pd.DataFrame:
    columns = "league,match_date,home_team,away_team,result"
    return pd.DataFrame(_fetch_pages(client, "league_finished_results", columns, (("league", "LA_LIGA"),)))


def _identity_readiness(decisions: pd.DataFrame, result_identities: pd.DataFrame) -> dict:
    tagged = settlement_identity(decisions)
    if tagged.empty:
        return {
            "final_tagged": 0,
            "settled_identity_count": 0,
            "unsettled_identity_count": 0,
            "evaluation_not_before_utc": EVALUATION_NOT_BEFORE_UTC.isoformat(),
        }
    results = result_identities.copy()
    required = {"league", "match_date", "home_team", "away_team"}
    missing = required.difference(results.columns)
    if missing:
        raise ValueError(f"Result identities missing columns: {sorted(missing)}")
    results = results.loc[results["league"].astype(str) == "LA_LIGA"].copy()
    results["match_date"] = pd.to_datetime(results["match_date"], errors="coerce").dt.date.astype(str)
    keys = ["league", "match_date", "home_team", "away_team"]
    if results.duplicated(keys).any():
        raise RuntimeError("Finished-result identity is not unique")
    joined = tagged.merge(results[keys].assign(settled_identity=True), on=keys, how="left", validate="one_to_one")
    settled = int(joined["settled_identity"].fillna(False).sum())
    return {
        "final_tagged": int(len(tagged)),
        "settled_identity_count": settled,
        "unsettled_identity_count": int(len(tagged) - settled),
        "evaluation_not_before_utc": EVALUATION_NOT_BEFORE_UTC.isoformat(),
    }


def run(*, evaluate: bool = False, now_utc: pd.Timestamp | str | None = None) -> dict:
    now = pd.Timestamp.now(tz="UTC") if now_utc is None else pd.Timestamp(now_utc)
    if now.tzinfo is None:
        now = now.tz_localize("UTC")
    else:
        now = now.tz_convert("UTC")

    client = _client()
    ledger = load_ledger(client)
    odds = load_odds_snapshots(client)
    decisions, audit = build_canonical_decisions(ledger, odds, now_utc=now)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    decisions.to_csv(OUTPUT_DIR / "candidate_decisions_without_outcomes.csv", index=False)

    readiness = _identity_readiness(decisions, load_result_identities(client))
    status = {
        "candidate_id": CANDIDATE_ID,
        "implementation_freeze_utc": IMPLEMENTATION_FREEZE_UTC.isoformat(),
        "now_utc": now.isoformat(),
        "audit": audit,
        "readiness": readiness,
        "outcome_values_queried": False,
        "evaluation_allowed_now": bool(now >= EVALUATION_NOT_BEFORE_UTC),
    }
    (OUTPUT_DIR / "accumulation_status.json").write_text(json.dumps(status, indent=2, sort_keys=True))

    print(json.dumps(status, indent=2, sort_keys=True))
    print("READ_ONLY_ACCUMULATION: result values not queried; no production writes; no threshold tuning")

    if not evaluate:
        print("OUTCOME_EVALUATION_GATED: explicit --evaluate required after 2027-06-01T00:00:00Z")
        return {"status": "ACCUMULATING", **status}

    if now < EVALUATION_NOT_BEFORE_UTC:
        raise RuntimeError(
            f"PROSPECTIVE_EVALUATION_TIME_GATE: now={now.isoformat()} "
            f"not_before={EVALUATION_NOT_BEFORE_UTC.isoformat()}"
        )

    settled = attach_results_for_explicit_evaluation(decisions, load_result_values(client))
    summary, monthly, descriptive_state = descriptive_evaluation(settled)
    summary.to_csv(OUTPUT_DIR / "explicit_evaluation_summary.csv", index=False)
    monthly.to_csv(OUTPUT_DIR / "explicit_evaluation_by_month.csv", index=False)
    evaluation_status = {
        "candidate_id": CANDIDATE_ID,
        "descriptive_state": descriptive_state,
        "outcome_values_queried": True,
        "research_only": True,
        "production_promotion": False,
    }
    (OUTPUT_DIR / "explicit_evaluation_status.json").write_text(
        json.dumps(evaluation_status, indent=2, sort_keys=True)
    )
    print(summary.to_string(index=False))
    if not monthly.empty:
        print(monthly.to_string(index=False))
    print(json.dumps(evaluation_status, indent=2, sort_keys=True))
    return {"status": "EVALUATED_RESEARCH_ONLY", **evaluation_status}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evaluate", action="store_true")
    args = parser.parse_args()
    run(evaluate=args.evaluate)


if __name__ == "__main__":
    main()
