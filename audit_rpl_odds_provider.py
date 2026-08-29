"""Read-only RPL provider audit against The Odds API.

Consumes one h2h API request. Performs no Supabase or local persistence writes.
"""

from __future__ import annotations

from league_runtime_config import RPL_RUNTIME_CONFIG
from the_odds_service import get_h2h_odds


def main() -> None:
    sport_key = RPL_RUNTIME_CONFIG.identity.odds_sport_key
    if not sport_key:
        raise RuntimeError("RPL Odds API sport key is missing")

    result = get_h2h_odds(sport_key)
    events = result["events"]

    print("=" * 88)
    print("RPL THE ODDS API PROVIDER AUDIT — READ ONLY")
    print("=" * 88)
    print("sport key:", sport_key)
    print("events:", len(events))
    print("quota:", result["quota"])

    teams = sorted(
        {
            str(name).strip()
            for event in events
            for name in (event.get("home_team"), event.get("away_team"))
            if name
        }
    )
    print("teams:", teams)
    print("fixtures:")
    for event in sorted(events, key=lambda row: str(row.get("commence_time", ""))):
        print(
            " ",
            event.get("commence_time"),
            "|",
            event.get("home_team"),
            "vs",
            event.get("away_team"),
            "| bookmakers=",
            len(event.get("bookmakers") or []),
        )

    print("Supabase writes:", False)
    print("production model used:", False)
    print("Structural V2 used:", False)
    print("PASS: READ-ONLY PROVIDER AUDIT COMPLETE")


if __name__ == "__main__":
    main()
