"""Read-only live coverage and normalization audit for Multi-Market Card V1."""
from __future__ import annotations
import json
from pathlib import Path
from league_config import operational_collection_ready_leagues
from multi_market_card import build_multi_market_card
from multi_market_odds import EVENT_MARKETS, FEATURED_MARKETS, fetch_event_markets, fetch_quota_status, fetch_sport_markets, summarize_market_coverage

OUTPUT = Path("artifacts/multi_market_coverage.json")
MIN_AUDIT_REMAINING = 500


def main() -> None:
    quota = fetch_quota_status()  # provider documents /sports as zero-cost
    remaining = quota.get("remaining")
    if remaining is not None and int(remaining) < MIN_AUDIT_REMAINING:
        report = {"status": "SKIPPED_LOW_QUOTA", "quota": quota, "minimum_required": MIN_AUDIT_REMAINING,
                  "leagues": {}, "featured_markets": list(FEATURED_MARKETS), "event_markets": list(EVENT_MARKETS)}
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False, indent=2)); return

    report = {"status": "AUDITED", "quota_before": quota, "leagues": {}, "featured_markets": list(FEATURED_MARKETS), "event_markets": list(EVENT_MARKETS)}
    for league in operational_collection_ready_leagues():
        events, featured_quota = fetch_sport_markets(league.odds_api_sport_key, regions="eu")
        entry = {"sport_key": league.odds_api_sport_key, "events_returned": len(events), "featured_quota": featured_quota, "sample_event": None}
        if events:
            event = sorted(events, key=lambda x: x.get("commence_time") or "")[0]
            event_payload, event_quota = fetch_event_markets(league.odds_api_sport_key, event["id"], regions="eu")
            entry["sample_event"] = {"event_id": event.get("id"), "commence_time": event.get("commence_time"),
                "home_team": event.get("home_team"), "away_team": event.get("away_team"),
                "coverage": summarize_market_coverage(event_payload), "canonical_card": build_multi_market_card(event_payload), "event_quota": event_quota}
        report["leagues"][league.identifier] = entry
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))

if __name__ == "__main__": main()
