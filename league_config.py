"""Central inert league configuration.

Configuration is deliberately separate from collection activation.
A resolved Odds API sport key alone never enables collection.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LeagueConfig:
    identifier: str
    name: str
    timezone: str
    odds_api_sport_key: str | None
    collection_enabled: bool

    @property
    def collection_ready(self) -> bool:
        return bool(
            self.collection_enabled
            and self.odds_api_sport_key
        )


EPL = LeagueConfig(
    identifier="EPL",
    name="Premier League",
    timezone="Europe/London",
    odds_api_sport_key="soccer_epl",
    collection_enabled=True,
)

LA_LIGA = LeagueConfig(
    identifier="LA_LIGA",
    name="La Liga",
    timezone="Europe/Madrid",
    odds_api_sport_key="soccer_spain_la_liga",
    collection_enabled=True,
)

RPL = LeagueConfig(
    identifier="RPL",
    name="Russian Premier League",
    timezone="Europe/Moscow",
    odds_api_sport_key="soccer_russia_premier_league",
    # Manual-only until the first persisted snapshot and durable-cycle audit pass.
    collection_enabled=False,
)

_CONFIGURED = (
    EPL,
    LA_LIGA,
    RPL,
)

LEAGUES = {
    league.identifier: league
    for league in _CONFIGURED
}


def validate_league_identifier(
    identifier: str,
) -> str:
    if identifier not in LEAGUES:
        raise ValueError(
            f"Unknown league identifier: {identifier!r}"
        )

    return identifier


def get_league_config(
    identifier: str,
) -> LeagueConfig:
    validate_league_identifier(identifier)
    return LEAGUES[identifier]


def configured_leagues() -> tuple[LeagueConfig, ...]:
    """Return deterministic configured-league order."""

    return _CONFIGURED


def collection_ready_leagues() -> tuple[LeagueConfig, ...]:
    return tuple(
        league
        for league in _CONFIGURED
        if league.collection_ready
    )


def is_collection_ready(
    identifier: str,
) -> bool:
    return get_league_config(
        identifier
    ).collection_ready
