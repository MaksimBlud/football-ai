from pathlib import Path

import pandas as pd

from league_historical_market import (
    choose_market_triplet,
    load_historical_market,
    no_vig_probabilities,
)

from league_runtime_config import (
    EPL_RUNTIME_CONFIG,
)


def test_no_vig_probabilities_sum_to_one():
    result = no_vig_probabilities(
        pd.Series(
            [2.0]
        ),
        pd.Series(
            [4.0]
        ),
        pd.Series(
            [4.0]
        ),
    )

    total = (
        result.iloc[0][
            "market_home_probability"
        ]
        +
        result.iloc[0][
            "market_draw_probability"
        ]
        +
        result.iloc[0][
            "market_away_probability"
        ]
    )

    assert abs(
        total - 1.0
    ) < 1e-12


def test_invalid_market_odds_rejected():
    result = no_vig_probabilities(
        pd.Series(
            [1.0]
        ),
        pd.Series(
            [3.0]
        ),
        pd.Series(
            [4.0]
        ),
    )

    assert not bool(
        result.iloc[0][
            "market_valid"
        ]
    )


def test_common_market_triplet_exists():
    frames = []

    for year in range(
        2016,
        2026,
    ):
        frames.append(
            pd.read_csv(
                Path(
                    f"data/raw/epl_{year}_{year + 1}.csv"
                )
            )
        )

    triplet = choose_market_triplet(
        frames
    )

    assert triplet.home
    assert triplet.draw
    assert triplet.away


def test_real_historical_market_contract():
    frame, triplet = (
        load_historical_market(
            config=EPL_RUNTIME_CONFIG,
            raw_directory=Path(
                "data/raw"
            ),
            file_prefix="epl",
        )
    )

    assert len(frame) == 3800

    assert (
        frame[
            "season"
        ].nunique()
        == 10
    )

    assert not frame.duplicated(
        subset=[
            "league",
            "season",
            "match_date",
            "home_team",
            "away_team",
        ]
    ).any()

    valid = frame.loc[
        frame[
            "market_valid"
        ].astype(bool)
    ]

    assert len(valid) > 3000

    probabilities = (
        valid[
            [
                "market_home_probability",
                "market_draw_probability",
                "market_away_probability",
            ]
        ]
        .sum(
            axis=1
        )
    )

    assert (
        probabilities
        .sub(1.0)
        .abs()
        .max()
        < 1e-10
    )

    assert set(
        valid[
            "market_argmax"
        ].dropna()
    ).issubset(
        {
            "H",
            "D",
            "A",
        }
    )

    assert triplet.source
