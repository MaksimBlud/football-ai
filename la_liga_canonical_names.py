"""Market-canonical La Liga team names for source normalization.

This module is pure configuration: no network, database, model, or artifact IO.
The target names match the live odds/prediction-ledger identity used by the
research pipeline.
"""
from __future__ import annotations

ALIASES = {
    "Alaves": "Alavés",
    "Ath Bilbao": "Athletic Bilbao",
    "Ath Madrid": "Atlético Madrid",
    "Atl. Madrid": "Atlético Madrid",
    "Osasuna": "CA Osasuna",
    "Celta": "Celta Vigo",
    "La Coruna": "Deportivo La Coruña",
    "Dep. A Coruna": "Deportivo La Coruña",
    "Elche": "Elche CF",
    "Espanol": "Espanyol",
    "Malaga": "Málaga",
    "Betis": "Real Betis",
    "Sociedad": "Real Sociedad",
    "Santander": "Real Racing Club de Santander",
    "Vallecano": "Rayo Vallecano",
}


def normalize_team(value: str) -> str:
    name = str(value).strip()
    if not name:
        raise ValueError("Empty La Liga team name")
    return ALIASES.get(name, name)
