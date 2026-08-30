import pytest

import normalize_la_liga_history as normalization


@pytest.mark.parametrize(
    ("source", "canonical"),
    [
        ("Alaves", "Alavés"),
        ("Espanol", "Espanyol"),
        ("Vallecano", "Rayo Vallecano"),
    ],
)
def test_current_la_liga_provider_aliases_are_canonical(source, canonical):
    assert normalization.normalize_team(source) == canonical
    assert canonical not in normalization.ALLOWED_COLD_START


def test_racing_remains_explicit_cold_start():
    assert "Real Racing Club de Santander" in normalization.ALLOWED_COLD_START
