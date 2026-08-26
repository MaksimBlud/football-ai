"""Generic Market vs Structural V2 live evaluator."""

from __future__ import annotations

import numpy as np
import pandas as pd

from league_runtime_config import (
    LeagueRuntimeConfig,
)


PROBABILITY_COLUMNS = {
    "market": (
        "market_home_probability",
        "market_draw_probability",
        "market_away_probability",
    ),
    "v2": (
        "shadow_home_probability",
        "shadow_draw_probability",
        "shadow_away_probability",
    ),
}


def validate_league(
    frame: pd.DataFrame,
    config: LeagueRuntimeConfig,
    *,
    label: str,
) -> None:
    if frame.empty:
        return

    if "league" not in frame.columns:
        raise ValueError(
            f"{label} missing league column"
        )

    observed = set(
        frame["league"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    expected = {
        config.identity.identifier
    }

    if observed != expected:
        raise ValueError(
            f"{label} league mismatch: "
            f"expected={sorted(expected)}, "
            f"observed={sorted(observed)}"
        )


def canonical_pre_kickoff(
    history: pd.DataFrame,
    config: LeagueRuntimeConfig,
) -> pd.DataFrame:
    validate_league(
        history,
        config,
        label="history",
    )

    if history.empty:
        return history.copy()

    work = history.copy()

    work[
        "snapshot_time_utc"
    ] = pd.to_datetime(
        work[
            "snapshot_time_utc"
        ],
        utc=True,
        errors="coerce",
    )

    work[
        "commence_time_utc"
    ] = pd.to_datetime(
        work[
            "commence_time_utc"
        ],
        utc=True,
        errors="coerce",
    )

    work = work.dropna(
        subset=[
            "event_id",
            "snapshot_time_utc",
            "commence_time_utc",
        ]
    ).copy()

    work = work[
        work[
            "snapshot_time_utc"
        ]
        < work[
            "commence_time_utc"
        ]
    ].copy()

    work = work.sort_values(
        "snapshot_time_utc"
    )

    work = work.drop_duplicates(
        subset=[
            "league",
            "event_id",
        ],
        keep="last",
    )

    return work.reset_index(
        drop=True
    )


def result_code_to_index(
    value: str,
) -> int:
    mapping = {
        "H": 0,
        "D": 1,
        "A": 2,
    }

    if value not in mapping:
        raise ValueError(
            f"Unknown result code: {value!r}"
        )

    return mapping[
        value
    ]


def probability_metrics(
    settled: pd.DataFrame,
    prefix: str,
) -> dict:
    columns = (
        PROBABILITY_COLUMNS[
            prefix
        ]
    )

    if settled.empty:
        return {
            "rows": 0,
            "accuracy": None,
            "logloss": None,
            "brier": None,
        }

    probability = (
        settled[
            list(
                columns
            )
        ]
        .astype(float)
        .to_numpy()
    )

    if (
        not np.isfinite(
            probability
        ).all()
    ):
        raise ValueError(
            "Nonfinite probabilities"
        )

    probability = (
        probability
        / probability.sum(
            axis=1,
            keepdims=True,
        )
    )

    y = np.array(
        [
            result_code_to_index(
                value
            )
            for value
            in settled[
                "result"
            ]
        ],
        dtype=int,
    )

    prediction = np.argmax(
        probability,
        axis=1,
    )

    accuracy = float(
        np.mean(
            prediction
            == y
        )
    )

    selected = probability[
        np.arange(
            len(y)
        ),
        y,
    ]

    logloss = float(
        -np.mean(
            np.log(
                np.clip(
                    selected,
                    1e-15,
                    1.0,
                )
            )
        )
    )

    one_hot = np.eye(
        3
    )[y]

    brier = float(
        np.mean(
            np.sum(
                (
                    probability
                    - one_hot
                )
                ** 2,
                axis=1,
            )
        )
    )

    return {
        "rows": int(
            len(settled)
        ),
        "accuracy": accuracy,
        "logloss": logloss,
        "brier": brier,
    }


def evaluate(
    history: pd.DataFrame,
    results: pd.DataFrame,
    config: LeagueRuntimeConfig,
) -> dict:
    validate_league(
        results,
        config,
        label="results",
    )

    canonical = (
        canonical_pre_kickoff(
            history,
            config,
        )
    )

    if (
        canonical.empty
        or results.empty
    ):
        return {
            "status":
                "NO_SETTLED_MATCHES",
            "settled_matches":
                0,
        }

    join_keys = [
        "league",
        "home_team",
        "away_team",
    ]

    if (
        "match_date"
        in canonical.columns
        and "match_date"
        in results.columns
    ):
        join_keys.append(
            "match_date"
        )

    settled = canonical.merge(
        results,
        on=join_keys,
        how="inner",
        suffixes=(
            "",
            "_result",
        ),
    )

    if settled.empty:
        return {
            "status":
                "NO_SETTLED_MATCHES",
            "settled_matches":
                0,
        }

    market = (
        probability_metrics(
            settled,
            "market",
        )
    )

    v2 = (
        probability_metrics(
            settled,
            "v2",
        )
    )

    correction_only = settled[
        settled[
            "correction_enabled"
        ].astype(bool)
    ].copy()

    correction_market = (
        probability_metrics(
            correction_only,
            "market",
        )
    )

    correction_v2 = (
        probability_metrics(
            correction_only,
            "v2",
        )
    )

    return {
        "status": "EVALUATED",
        "settled_matches":
            int(
                len(settled)
            ),
        "corrected_matches":
            int(
                len(
                    correction_only
                )
            ),
        "all_matches": {
            "market": market,
            "v2": v2,
            "accuracy_gap":
                (
                    v2[
                        "accuracy"
                    ]
                    - market[
                        "accuracy"
                    ]
                ),
            "logloss_gap":
                (
                    v2[
                        "logloss"
                    ]
                    - market[
                        "logloss"
                    ]
                ),
            "brier_gap":
                (
                    v2[
                        "brier"
                    ]
                    - market[
                        "brier"
                    ]
                ),
        },
        "correction_only": {
            "market":
                correction_market,
            "v2":
                correction_v2,
            "logloss_gap":
                (
                    None
                    if not len(
                        correction_only
                    )
                    else (
                        correction_v2[
                            "logloss"
                        ]
                        - correction_market[
                            "logloss"
                        ]
                    )
                ),
            "brier_gap":
                (
                    None
                    if not len(
                        correction_only
                    )
                    else (
                        correction_v2[
                            "brier"
                        ]
                        - correction_market[
                            "brier"
                        ]
                    )
                ),
        },
    }
