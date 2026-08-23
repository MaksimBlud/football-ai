"""Safe La Liga V1 prediction runtime.

V1 baseline uses the already collected market consensus.

Important:
- does NOT reuse the EPL production model;
- does NOT pretend unknown La Liga teams have EPL history;
- performs no Odds API request;
- performs no Supabase write;
- reads the latest La Liga market shadow only;
- emits an explicit MARKET_BASELINE prediction source.

A future league-trained AI model can replace the prediction provider
without changing the output contract.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from league_config import LA_LIGA


INPUT_PATH = Path(
    "experiments/la_liga_market_shadow.csv"
)

OUTPUT_PATH = Path(
    "experiments/la_liga_predictions.csv"
)

PREDICTION_SOURCE = "MARKET_BASELINE"
AI_MODEL_USED = False

OUTPUT_COLUMNS = [
    "league",
    "event_id",
    "commence_time_utc",
    "home_team",
    "away_team",
    "prediction",
    "confidence",
    "home_probability",
    "draw_probability",
    "away_probability",
    "prediction_source",
    "ai_model_used",
    "market_only",
    "research_only",
]


ARGMAX_TO_PREDICTION = {
    "H": "HOME",
    "D": "DRAW",
    "A": "AWAY",
}


def load_market_shadow(
    path: Path = INPUT_PATH,
) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"Market shadow not found: {path}"
        )

    frame = pd.read_csv(path)

    required = {
        "league",
        "event_id",
        "commence_time_utc",
        "home_team",
        "away_team",
        "market_home_probability",
        "market_draw_probability",
        "market_away_probability",
        "market_argmax",
        "market_shadow_status",
    }

    missing = required - set(
        frame.columns
    )

    if missing:
        raise ValueError(
            "Market shadow missing columns: "
            + ", ".join(
                sorted(missing)
            )
        )

    return frame


def build_predictions(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    frame = frame.copy()

    frame = frame[
        (
            frame["league"]
            == LA_LIGA.identifier
        )
        & (
            frame["market_shadow_status"]
            == "OK"
        )
    ].copy()

    records = []

    for _, row in frame.iterrows():
        argmax = str(
            row["market_argmax"]
        )

        if argmax not in (
            ARGMAX_TO_PREDICTION
        ):
            continue

        home_probability = float(
            row[
                "market_home_probability"
            ]
        )

        draw_probability = float(
            row[
                "market_draw_probability"
            ]
        )

        away_probability = float(
            row[
                "market_away_probability"
            ]
        )

        confidence = max(
            home_probability,
            draw_probability,
            away_probability,
        )

        records.append({
            "league":
                LA_LIGA.identifier,

            "event_id":
                row["event_id"],

            "commence_time_utc":
                row[
                    "commence_time_utc"
                ],

            "home_team":
                row["home_team"],

            "away_team":
                row["away_team"],

            "prediction":
                ARGMAX_TO_PREDICTION[
                    argmax
                ],

            "confidence":
                confidence,

            "home_probability":
                home_probability,

            "draw_probability":
                draw_probability,

            "away_probability":
                away_probability,

            "prediction_source":
                PREDICTION_SOURCE,

            "ai_model_used":
                AI_MODEL_USED,

            "market_only":
                True,

            "research_only":
                True,
        })

    result = pd.DataFrame(
        records,
        columns=OUTPUT_COLUMNS,
    )

    if not result.empty:
        result = (
            result
            .sort_values(
                [
                    "commence_time_utc",
                    "home_team",
                ]
            )
            .reset_index(drop=True)
        )

    return result


def write_predictions(
    frame: pd.DataFrame,
    path: Path = OUTPUT_PATH,
) -> None:
    experiments = Path(
        "experiments"
    ).resolve()

    resolved = path.resolve()

    if experiments not in (
        resolved.parents
    ):
        raise ValueError(
            "Output must remain under experiments/"
        )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    frame.to_csv(
        path,
        index=False,
    )


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--input",
        type=Path,
        default=INPUT_PATH,
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_PATH,
    )

    args = parser.parse_args()

    frame = load_market_shadow(
        args.input
    )

    predictions = build_predictions(
        frame
    )

    write_predictions(
        predictions,
        args.output,
    )

    print("=" * 72)
    print(
        "LA LIGA V1 PREDICTION RUNTIME"
    )
    print("=" * 72)

    print(
        "source:",
        PREDICTION_SOURCE,
    )

    print(
        "AI model used:",
        AI_MODEL_USED,
    )

    print(
        "predictions:",
        len(predictions),
    )

    if not predictions.empty:
        print()
        print(
            predictions[
                [
                    "home_team",
                    "away_team",
                    "prediction",
                    "confidence",
                    "home_probability",
                    "draw_probability",
                    "away_probability",
                ]
            ].to_string(
                index=False
            )
        )

    print()
    print(
        "output:",
        args.output,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
