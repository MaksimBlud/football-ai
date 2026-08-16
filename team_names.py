TEAM_NAME_MAP = {
    "Manchester City": "Man City",
    "Manchester United": "Man United",
    "Newcastle United": "Newcastle",
    "Nottingham Forest": "Nott'm Forest",
    "Tottenham Hotspur": "Tottenham",
    "Brighton and Hove Albion": "Brighton",
    "Brighton & Hove Albion": "Brighton",
    "Ipswich Town": "Ipswich",
    "Hull City": "Hull",
    "Leeds United": "Leeds",
    "AFC Bournemouth": "Bournemouth",
}


def normalize_team_name(name):
    name = str(name).strip()

    return TEAM_NAME_MAP.get(
        name,
        name,
    )
