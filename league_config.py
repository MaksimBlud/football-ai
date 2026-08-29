"""Central inert league configuration.

Configuration is deliberately separate from collection activation.
A resolved Odds API sport key alone never enables generic collection.
Dedicated operational workflows are tracked separately.
"""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class LeagueConfig:
    identifier:str; name:str; timezone:str; odds_api_sport_key:str|None; collection_enabled:bool; operational_collection_enabled:bool=False
    @property
    def collection_ready(self)->bool:return bool(self.collection_enabled and self.odds_api_sport_key)
    @property
    def operational_collection_ready(self)->bool:return bool(self.operational_collection_enabled and self.odds_api_sport_key)

EPL=LeagueConfig("EPL","Premier League","Europe/London","soccer_epl",True,True)
LA_LIGA=LeagueConfig("LA_LIGA","La Liga","Europe/Madrid","soccer_spain_la_liga",True,True)
RPL=LeagueConfig("RPL","Russian Premier League","Europe/Moscow","soccer_russia_premier_league",False,True)
SERIE_A=LeagueConfig("SERIE_A","Serie A","Europe/Rome","soccer_italy_serie_a",True,True)
BUNDESLIGA=LeagueConfig("BUNDESLIGA","Bundesliga","Europe/Berlin","soccer_germany_bundesliga",True,True)
LIGUE_1=LeagueConfig("LIGUE_1","Ligue 1","Europe/Paris","soccer_france_ligue_one",True,True)
EREDIVISIE=LeagueConfig("EREDIVISIE","Eredivisie","Europe/Amsterdam","soccer_netherlands_eredivisie",True,True)
_CONFIGURED=(EPL,LA_LIGA,RPL,SERIE_A,BUNDESLIGA,LIGUE_1,EREDIVISIE)
LEAGUES={league.identifier:league for league in _CONFIGURED}
def validate_league_identifier(identifier):
    if identifier not in LEAGUES:raise ValueError(f"Unknown league identifier: {identifier!r}")
    return identifier
def get_league_config(identifier):validate_league_identifier(identifier);return LEAGUES[identifier]
def configured_leagues():return _CONFIGURED
def collection_ready_leagues():return tuple(l for l in _CONFIGURED if l.collection_ready)
def operational_collection_ready_leagues():return tuple(l for l in _CONFIGURED if l.operational_collection_ready)
def is_collection_ready(identifier):return get_league_config(identifier).collection_ready
def is_operational_collection_ready(identifier):return get_league_config(identifier).operational_collection_ready
