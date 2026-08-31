from pathlib import Path
from types import SimpleNamespace

import pandas as pd

import historical_strategy_runner as runner
from historical_strategy_lab import prepare_market_frame, write_reports


def test_download_league_history_uses_point_in_time_season_codes(tmp_path, monkeypatch):
    calls = []

    class Response:
        content = b"Date,HomeTeam,AwayTeam,FTHG,FTAG,FTR,AvgH,AvgD,AvgA\n"

        def raise_for_status(self):
            return None

    def fake_get(url, timeout):
        calls.append((url, timeout))
        return Response()

    monkeypatch.setattr(runner.requests, "get", fake_get)
    config = SimpleNamespace(
        historical_source=SimpleNamespace(
            season_codes={"2425": "2024-2025"},
            competition_code="E0",
        )
    )

    paths = runner.download_league_history(config, "epl", tmp_path)

    assert paths == [tmp_path / "epl_2024_2025.csv"]
    assert paths[0].exists()
    assert calls == [("https://www.football-data.co.uk/mmz4281/2425/E0.csv", 60)]


def test_prepare_market_frame_orders_path_dependent_metrics_chronologically():
    frame = pd.DataFrame(
        [
            {
                "league": "EPL",
                "season": "2024-2025",
                "match_date": "2025-01-02",
                "result": "A",
                "market_home_odds": 1.50,
                "market_draw_odds": 4.00,
                "market_away_odds": 6.00,
            },
            {
                "league": "EPL",
                "season": "2024-2025",
                "match_date": "2025-01-01",
                "result": "H",
                "market_home_odds": 1.50,
                "market_draw_odds": 4.00,
                "market_away_odds": 6.00,
            },
        ]
    )

    prepared = prepare_market_frame(frame)

    assert prepared["match_date"].dt.strftime("%Y-%m-%d").tolist() == ["2025-01-01", "2025-01-02"]
    assert prepared["profit"].tolist() == [0.5, -1.0]


def test_write_reports_creates_auditable_match_level_output(tmp_path):
    frame = pd.DataFrame(
        [
            {
                "league": "EPL",
                "season": "2024-2025",
                "match_date": "2025-01-01",
                "result": "H",
                "market_home_odds": 1.80,
                "market_draw_odds": 3.50,
                "market_away_odds": 4.50,
            }
        ]
    )

    reports = write_reports(frame, tmp_path)

    assert set(reports) == {"overall", "confidence", "odds", "league_season", "prepared"}
    assert all(Path(path).exists() for path in reports.values())
    prepared = pd.read_csv(reports["prepared"])
    assert prepared.loc[0, "market_pick"] == "H"
    assert bool(prepared.loc[0, "won"])
