from database import supabase


def get_team_names():
    all_matches = []
    page_size = 1000
    start = 0

    while True:
        response = (
            supabase
            .table("matches")
            .select("home_team,away_team")
            .range(start, start + page_size - 1)
            .execute()
        )

        batch = response.data or []

        if not batch:
            break

        all_matches.extend(batch)

        if len(batch) < page_size:
            break

        start += page_size

    teams = set()

    for match in all_matches:
        home_team = match.get("home_team")
        away_team = match.get("away_team")

        if home_team:
            teams.add(home_team)

        if away_team:
            teams.add(away_team)

    return sorted(teams)
