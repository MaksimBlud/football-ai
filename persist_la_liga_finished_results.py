"""Mirror authoritative La Liga finished results into generic canonical state.

The existing `la_liga_finished_results` table remains the La Liga durable
source. This bridge reads that immutable state and mirrors it into the shared
`league_finished_results` table so the canonical evaluator/calibration path
can settle La Liga prediction-ledger rows.

No result-source fetch, model use, training, promotion, or Structural V2
activation occurs here.
"""

from __future__ import annotations

import pandas as pd

from database import supabase
import la_liga_live_persistence as legacy
import league_supabase_persistence as canonical
from league_runtime_config import LA_LIGA_RUNTIME_CONFIG


LEAGUE = "LA_LIGA"


def load_authoritative_results(client=supabase) -> pd.DataFrame:
    frame = legacy.fetch_results(client)

    if frame.empty:
        return frame.copy()

    observed = set(
        frame["league"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    if observed != {LEAGUE}:
        raise ValueError(
            "Legacy La Liga results contain foreign league rows: "
            + repr(sorted(observed))
        )

    return frame.copy()


def persist_authoritative_results(client=supabase) -> dict[str, int]:
    frame = load_authoritative_results(client)

    metrics = canonical.persist_results(
        client,
        frame,
        LA_LIGA_RUNTIME_CONFIG,
    )

    if int(metrics.get("conflicts", 0)) != 0:
        raise RuntimeError(
            "Canonical La Liga finished-results bridge reported conflicts"
        )

    processed = (
        int(metrics.get("inserted", 0))
        + int(metrics.get("unchanged", 0))
    )

    if processed != len(frame):
        raise RuntimeError(
            "Canonical La Liga finished-results metrics do not cover input"
        )

    return {
        "input": len(frame),
        "inserted": int(metrics.get("inserted", 0)),
        "unchanged": int(metrics.get("unchanged", 0)),
        "conflicts": int(metrics.get("conflicts", 0)),
    }


def main() -> None:
    metrics = persist_authoritative_results()
    print("La Liga canonical finished-results bridge:", metrics)


if __name__ == "__main__":
    main()
