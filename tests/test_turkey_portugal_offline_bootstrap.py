from datetime import date
from io import StringIO

import pandas as pd
import pytest

from football_data_history_source import (
    completed_european_season_codes,
    download_configured_history,
    football_data_csv_url,
)
from primeira_liga_runtime_config import PRIMEIRA_LIGA_RUNTIME_CONFIG
from turkey_super_lig_runtime_config import TURKEY_SUPER_LIG_RUNTIME_CONFIG


def complete_csv(team_count=4):
    teams = [f"Team {index}" for index in range(team_count)]
    rows = []
    day = 1
    for home in teams:
        for away in teams:
            if home == away:
                continue
            rows.append(
                {
                    "Date": f"{day:02d}/08/2025",
                    "HomeTeam": home,
                    "AwayTeam": away,
                    "FTHG": 1,
                    "FTAG": 0,
                    "FTR": "H",
                }
            )
            day += 1
    return pd.DataFrame(rows).to_csv(index=False).encode()


class FakeResponse:
    def __init__(self, content):
        self.content = content

    def raise_for_status(self):
        return None


def test_completed_history_excludes_current_2026_27_season():
    as_of = date(2026, 9, 5)
    for config in (
        TURKEY_SUPER_LIG_RUNTIME_CONFIG,
        PRIMEIRA_LIGA_RUNTIME_CONFIG,
    ):
        seasons = completed_european_season_codes(config, as_of=as_of)
        assert len(seasons) == 10
        assert seasons["2526"] == "2025-2026"
        assert "2627" not in seasons


def test_football_data_urls_use_runtime_competition_codes():
    assert football_data_csv_url(
        season_code="2526",
        competition_code=TURKEY_SUPER_LIG_RUNTIME_CONFIG.historical_source.competition_code,
    ) == "https://www.football-data.co.uk/mmz4281/2526/T1.csv"
    assert football_data_csv_url(
        season_code="2526",
        competition_code=PRIMEIRA_LIGA_RUNTIME_CONFIG.historical_source.competition_code,
    ) == "https://www.football-data.co.uk/mmz4281/2526/P1.csv"


def test_download_validates_before_persisting(tmp_path):
    calls = []

    def fake_get(url, timeout):
        calls.append((url, timeout))
        return FakeResponse(complete_csv())

    reports = download_configured_history(
        config=TURKEY_SUPER_LIG_RUNTIME_CONFIG,
        raw_directory=tmp_path,
        file_prefix="turkey_super_lig",
        season_codes={"2526": "2025-2026"},
        request_get=fake_get,
    )

    path = tmp_path / "turkey_super_lig_2025_2026.csv"
    assert path.exists()
    assert reports[0]["status"] == "downloaded"
    assert reports[0]["rows"] == 12
    assert calls == [
        ("https://www.football-data.co.uk/mmz4281/2526/T1.csv", 30)
    ]


def test_invalid_download_is_never_persisted(tmp_path):
    def fake_get(url, timeout):
        return FakeResponse(b"<html>rate limited</html>")

    path = tmp_path / "primeira_liga_2025_2026.csv"
    with pytest.raises(ValueError, match="Invalid Football-Data CSV|missing columns"):
        download_configured_history(
            config=PRIMEIRA_LIGA_RUNTIME_CONFIG,
            raw_directory=tmp_path,
            file_prefix="primeira_liga",
            season_codes={"2526": "2025-2026"},
            request_get=fake_get,
        )
    assert not path.exists()
