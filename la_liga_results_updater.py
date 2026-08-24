"""Automatic finished-result updater for La Liga 2026/27.

Research/data ingestion only.

Source:
Football-Data.co.uk SP1 CSV.

Properties:
- public repository-supported source;
- canonical project team names;
- finished matches only;
- deterministic;
- idempotent;
- conflicting completed results are never silently overwritten;
- atomic output write;
- no Supabase write;
- no training;
- no production model access.
"""

from __future__ import annotations

import argparse
import io
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

import pandas as pd

from normalize_la_liga_history import (
    ALIASES,
    ALLOWED_COLD_START,
)


ROOT = Path(__file__).resolve().parent

SEASON = "2026-2027"
LEAGUE = "LA_LIGA"
SEASON_CODE = "2627"
COMPETITION = "SP1"

SOURCE_URL = (
    "https://www.football-data.co.uk/"
    f"mmz4281/{SEASON_CODE}/{COMPETITION}.csv"
)

OUTPUT_PATH = (
    ROOT
    / "data"
    / "la_liga_2026_2027_results.csv"
)

HISTORICAL_PATH = (
    ROOT
    / "data"
    / "la_liga_official_history_2016_2026_normalized.csv"
)

SOURCE_NAME = "FOOTBALL_DATA_CSV"

# Football-Data current-season source names that differ
# from the canonical project naming.
SOURCE_ALIASES = {
    "Dep. A Coruna": "Deportivo La Coruña",
    "Atl. Madrid": "Atlético Madrid",
    "Rayo Vallecano": "Vallecano",
}

OUTPUT_COLUMNS = [
    "season",
    "league",
    "match_date",
    "match_time",
    "home_team",
    "away_team",
    "home_goals",
    "away_goals",
    "result",
    "source",
    "source_competition",
    "source_updated_at_utc",
]

FIXTURE_KEY = [
    "season",
    "match_date",
    "home_team",
    "away_team",
]


class ResultsSourceError(RuntimeError):
    pass


class ResultsConflictError(RuntimeError):
    pass


class UnknownTeamError(RuntimeError):
    pass


def canonical_team_set() -> set[str]:
    teams: set[str] = set()

    if HISTORICAL_PATH.exists():
        history = pd.read_csv(
            HISTORICAL_PATH,
            usecols=[
                "home_team",
                "away_team",
            ],
        )

        teams.update(
            history[
                "home_team"
            ].dropna().astype(str)
        )

        teams.update(
            history[
                "away_team"
            ].dropna().astype(str)
        )

    teams.update(
        ALIASES.values()
    )

    teams.update(
        ALLOWED_COLD_START
    )

    # Accept canonical values that already occur as alias keys/values.
    teams.update(
        [
            "Barcelona",
            "Real Madrid",
            "Sevilla",
            "Valencia",
            "Villarreal",
            "Getafe",
            "Levante",
        ]
    )

    return teams


def normalize_team(
    raw_name: object,
    allowed: set[str],
) -> str:
    name = str(
        raw_name
    ).strip()

    canonical = SOURCE_ALIASES.get(
        name,
        ALIASES.get(
            name,
            name,
        ),
    )

    # Football-Data has historically used "Santander"
    # for Racing Santander in some older datasets.
    if name == "Santander":
        canonical = (
            "Real Racing Club de Santander"
        )

    if canonical not in allowed:
        raise UnknownTeamError(
            "Unknown La Liga team from "
            f"Football-Data: {name!r}"
        )

    return canonical


def result_from_goals(
    home_goals: int,
    away_goals: int,
) -> str:
    if home_goals > away_goals:
        return "H"

    if home_goals < away_goals:
        return "A"

    return "D"


def fetch_source(
    *,
    url: str = SOURCE_URL,
    timeout: int = 30,
) -> pd.DataFrame:
    request = Request(
        url,
        headers={
            "User-Agent":
                "football-ai/1.0",
        },
    )

    try:
        with urlopen(
            request,
            timeout=timeout,
        ) as response:
            payload = response.read()

    except Exception as exc:
        raise ResultsSourceError(
            "Football-Data CSV unavailable: "
            f"{exc}"
        ) from exc

    try:
        return pd.read_csv(
            io.BytesIO(payload)
        )

    except Exception as exc:
        raise ResultsSourceError(
            "Football-Data CSV parse failed: "
            f"{exc}"
        ) from exc


def normalize_source(
    source: pd.DataFrame,
    *,
    updated_at_utc: str | None = None,
) -> pd.DataFrame:
    required = {
        "Date",
        "HomeTeam",
        "AwayTeam",
        "FTHG",
        "FTAG",
        "FTR",
    }

    missing = (
        required
        - set(source.columns)
    )

    if missing:
        raise ResultsSourceError(
            "Football-Data schema missing: "
            + ", ".join(
                sorted(missing)
            )
        )

    frame = source.copy()

    # Only completed fixtures qualify.
    frame["FTHG"] = pd.to_numeric(
        frame["FTHG"],
        errors="coerce",
    )

    frame["FTAG"] = pd.to_numeric(
        frame["FTAG"],
        errors="coerce",
    )

    frame["FTR"] = (
        frame["FTR"]
        .astype("string")
        .str.strip()
        .str.upper()
    )

    frame = frame[
        frame["FTHG"].notna()
        & frame["FTAG"].notna()
        & frame["FTR"].isin(
            ["H", "D", "A"]
        )
    ].copy()

    if frame.empty:
        return pd.DataFrame(
            columns=OUTPUT_COLUMNS
        )

    # Football-Data uses day-first dates.
    frame["match_date"] = (
        pd.to_datetime(
            frame["Date"],
            dayfirst=True,
            errors="raise",
        )
        .dt.strftime(
            "%Y-%m-%d"
        )
    )

    if "Time" in frame.columns:
        frame["match_time"] = (
            frame["Time"]
            .fillna("")
            .astype(str)
            .str.strip()
        )
    else:
        frame["match_time"] = ""

    allowed = canonical_team_set()

    frame["home_team"] = [
        normalize_team(
            value,
            allowed,
        )
        for value in frame[
            "HomeTeam"
        ]
    ]

    frame["away_team"] = [
        normalize_team(
            value,
            allowed,
        )
        for value in frame[
            "AwayTeam"
        ]
    ]

    frame["home_goals"] = (
        frame["FTHG"]
        .astype(int)
    )

    frame["away_goals"] = (
        frame["FTAG"]
        .astype(int)
    )

    derived = [
        result_from_goals(
            home,
            away,
        )
        for home, away in zip(
            frame["home_goals"],
            frame["away_goals"],
        )
    ]

    source_result = (
        frame["FTR"]
        .astype(str)
        .tolist()
    )

    mismatches = [
        index
        for index, (
            expected,
            actual,
        ) in enumerate(
            zip(
                derived,
                source_result,
            )
        )
        if expected != actual
    ]

    if mismatches:
        raise ResultsSourceError(
            "Football-Data FTR conflicts "
            "with full-time goals"
        )

    frame["result"] = derived

    frame["season"] = SEASON
    frame["league"] = LEAGUE
    frame["source"] = SOURCE_NAME
    frame[
        "source_competition"
    ] = COMPETITION

    if updated_at_utc is None:
        updated_at_utc = (
            datetime.now(
                timezone.utc
            )
            .isoformat()
        )

    frame[
        "source_updated_at_utc"
    ] = updated_at_utc

    output = frame[
        OUTPUT_COLUMNS
    ].copy()

    # Exact duplicate source fixtures are harmless.
    duplicate_groups = (
        output.groupby(
            FIXTURE_KEY,
            dropna=False,
        )
    )

    rows = []

    for _, group in duplicate_groups:
        signatures = set(
            zip(
                group[
                    "home_goals"
                ].astype(int),
                group[
                    "away_goals"
                ].astype(int),
                group[
                    "result"
                ].astype(str),
            )
        )

        if len(signatures) > 1:
            raise ResultsConflictError(
                "Conflicting duplicate fixture "
                "inside source"
            )

        rows.append(
            group.iloc[-1]
        )

    output = pd.DataFrame(
        rows,
        columns=OUTPUT_COLUMNS,
    )

    return (
        output
        .sort_values(
            FIXTURE_KEY
        )
        .reset_index(drop=True)
    )


def normalize_existing(
    existing: pd.DataFrame,
) -> pd.DataFrame:
    if existing.empty:
        return pd.DataFrame(
            columns=OUTPUT_COLUMNS
        )

    missing = (
        set(
            OUTPUT_COLUMNS
        )
        - set(existing.columns)
    )

    if missing:
        raise ResultsConflictError(
            "Existing results schema missing: "
            + ", ".join(
                sorted(missing)
            )
        )

    result = existing[
        OUTPUT_COLUMNS
    ].copy()

    if result.duplicated(
        subset=FIXTURE_KEY,
        keep=False,
    ).any():
        raise ResultsConflictError(
            "Existing results contain "
            "duplicate fixture keys"
        )

    return result


def merge_results(
    existing: pd.DataFrame,
    incoming: pd.DataFrame,
) -> tuple[
    pd.DataFrame,
    dict,
]:
    existing = normalize_existing(
        existing
    )

    if incoming.empty:
        return (
            existing.copy(),
            {
                "new_rows": 0,
                "unchanged_rows": 0,
                "conflicts": 0,
            },
        )

    existing_index = {
        tuple(
            row[column]
            for column in FIXTURE_KEY
        ): row
        for _, row in (
            existing.iterrows()
        )
    }

    additions = []
    unchanged = 0

    for _, row in (
        incoming.iterrows()
    ):
        key = tuple(
            row[column]
            for column in FIXTURE_KEY
        )

        previous = (
            existing_index.get(
                key
            )
        )

        if previous is None:
            additions.append(
                row
            )
            continue

        previous_signature = (
            int(
                previous[
                    "home_goals"
                ]
            ),
            int(
                previous[
                    "away_goals"
                ]
            ),
            str(
                previous[
                    "result"
                ]
            ),
        )

        incoming_signature = (
            int(
                row[
                    "home_goals"
                ]
            ),
            int(
                row[
                    "away_goals"
                ]
            ),
            str(
                row[
                    "result"
                ]
            ),
        )

        if (
            previous_signature
            != incoming_signature
        ):
            raise ResultsConflictError(
                "Conflicting completed result "
                f"for fixture {key}: "
                f"existing={previous_signature}, "
                f"incoming={incoming_signature}"
            )

        unchanged += 1

    if additions:
        additions_frame = (
            pd.DataFrame(
                additions
            )[
                OUTPUT_COLUMNS
            ]
        )

        combined = pd.concat(
            [
                existing,
                additions_frame,
            ],
            ignore_index=True,
        )
    else:
        combined = existing.copy()

    combined = (
        combined
        .sort_values(
            FIXTURE_KEY
        )
        .reset_index(drop=True)
    )

    if combined.duplicated(
        subset=FIXTURE_KEY
    ).any():
        raise ResultsConflictError(
            "Merge produced duplicate fixtures"
        )

    return (
        combined,
        {
            "new_rows":
                len(additions),
            "unchanged_rows":
                unchanged,
            "conflicts":
                0,
        },
    )


def atomic_write(
    frame: pd.DataFrame,
    path: Path,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fd, temporary_name = (
        tempfile.mkstemp(
            prefix=(
                path.name
                + "."
            ),
            suffix=".tmp",
            dir=path.parent,
        )
    )

    os.close(fd)

    temporary_path = Path(
        temporary_name
    )

    try:
        frame.to_csv(
            temporary_path,
            index=False,
        )

        os.replace(
            temporary_path,
            path,
        )

    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def update_results(
    *,
    output_path: Path = OUTPUT_PATH,
    source_frame: pd.DataFrame | None = None,
) -> dict:
    if source_frame is None:
        source_frame = (
            fetch_source()
        )

    normalized = normalize_source(
        source_frame
    )

    if output_path.exists():
        existing = pd.read_csv(
            output_path
        )
    else:
        existing = pd.DataFrame(
            columns=OUTPUT_COLUMNS
        )

    combined, merge_info = (
        merge_results(
            existing,
            normalized,
        )
    )

    # Preserve file bytes on exact reruns.
    if (
        merge_info["new_rows"]
        > 0
        or not output_path.exists()
    ):
        atomic_write(
            combined,
            output_path,
        )

    status = (
        "WAIT"
        if normalized.empty
        else "PASS"
    )

    detail = (
        "NO_FINISHED_MATCHES"
        if normalized.empty
        else "UPDATED"
    )

    return {
        "status":
            status,
        "detail":
            detail,
        "source":
            SOURCE_NAME,
        "source_url":
            SOURCE_URL,
        "fetched_rows":
            len(source_frame),
        "finished_rows":
            len(normalized),
        "new_rows":
            merge_info[
                "new_rows"
            ],
        "unchanged_rows":
            merge_info[
                "unchanged_rows"
            ],
        "conflicts":
            merge_info[
                "conflicts"
            ],
        "output_rows":
            len(combined),
        "output_path":
            str(output_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_PATH,
    )

    args = parser.parse_args()

    try:
        report = update_results(
            output_path=args.output,
        )

    except (
        ResultsSourceError,
        ResultsConflictError,
        UnknownTeamError,
    ) as exc:
        print(
            "results FAIL:"
            f"{type(exc).__name__} "
            f"{exc}"
        )

        return 1

    print("=" * 72)
    print("LA LIGA 2026/27 RESULTS UPDATE")
    print("=" * 72)

    for key, value in (
        report.items()
    ):
        print(
            f"{key:20} {value}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
