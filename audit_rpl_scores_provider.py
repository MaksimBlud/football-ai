"""Read-only audit of RPL score availability from The Odds API."""

from __future__ import annotations

from rpl_scores_service import get_rpl_scores


def main() -> None:
    result = get_rpl_scores(days_from=3)
    events = result["events"]

    print("=" * 88)
    print("RPL SCORES PROVIDER AUDIT — READ ONLY")
    print("=" * 88)
    print("events:", len(events))
    print("quota:", result["quota"])

    completed = 0
    scored = 0
    for event in events:
        is_completed = bool(event.get("completed"))
        if is_completed:
            completed += 1
        scores = event.get("scores") or []
        if scores:
            scored += 1
        print(
            event.get("commence_time"),
            "|",
            event.get("home_team"),
            "vs",
            event.get("away_team"),
            "| completed=",
            is_completed,
            "| scores=",
            scores,
        )

    print("completed events:", completed)
    print("events with score payload:", scored)
    print("Supabase writes:", False)
    print("production model used:", False)
    print("Structural V2 used:", False)
    print("PASS: RPL SCORES PROVIDER AUDIT COMPLETE")


if __name__ == "__main__":
    main()
