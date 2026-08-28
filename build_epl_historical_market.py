"""Build EPL historical no-vig market baseline.

Offline research only.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from league_historical_market import (
    load_historical_market,
)

from league_runtime_config import (
    EPL_RUNTIME_CONFIG,
)


OUTPUT = Path(
    "data/epl_historical_market_2016_2026.csv"
)


def multiclass_log_loss(
    frame: pd.DataFrame,
) -> float:
    mapping = {
        "H":
            "market_home_probability",
        "D":
            "market_draw_probability",
        "A":
            "market_away_probability",
    }

    probabilities = []

    for row in frame.itertuples():
        column = mapping[
            row.result
        ]

        probabilities.append(
            getattr(
                row,
                column,
            )
        )

    series = pd.Series(
        probabilities,
        dtype=float,
    ).clip(
        lower=1e-15,
        upper=1.0,
    )

    return float(
        (
            -series.map(
                __import__("math").log
            )
        ).mean()
    )


def multiclass_brier(
    frame: pd.DataFrame,
) -> float:
    total = 0.0

    for row in frame.itertuples():
        targets = {
            "H": 0.0,
            "D": 0.0,
            "A": 0.0,
        }

        targets[
            row.result
        ] = 1.0

        total += (
            (
                row.market_home_probability
                - targets["H"]
            )
            ** 2
            +
            (
                row.market_draw_probability
                - targets["D"]
            )
            ** 2
            +
            (
                row.market_away_probability
                - targets["A"]
            )
            ** 2
        )

    return total / len(frame)


def main() -> None:
    frame, triplet = (
        load_historical_market(
            config=EPL_RUNTIME_CONFIG,
            raw_directory=Path(
                "data/raw"
            ),
            file_prefix="epl",
        )
    )

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    frame.to_csv(
        OUTPUT,
        index=False,
    )

    valid = frame.loc[
        frame[
            "market_valid"
        ].astype(bool)
    ].copy()

    accuracy = float(
        (
            valid[
                "market_argmax"
            ]
            ==
            valid[
                "result"
            ]
        ).mean()
    )

    print(
        "market source:",
        triplet.source,
    )

    print(
        "market columns:",
        triplet.home,
        triplet.draw,
        triplet.away,
    )

    print(
        "rows:",
        len(frame),
    )

    print(
        "valid market rows:",
        len(valid),
    )

    print(
        "coverage:",
        len(valid) / len(frame),
    )

    print(
        "market accuracy:",
        accuracy,
    )

    print(
        "market log loss:",
        multiclass_log_loss(
            valid
        ),
    )

    print(
        "market brier:",
        multiclass_brier(
            valid
        ),
    )

    print(
        "output:",
        OUTPUT,
    )


if __name__ == "__main__":
    main()
