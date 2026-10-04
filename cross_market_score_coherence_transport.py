"""Transport-only launcher for CROSS_MARKET_SCORE_COHERENCE_V1.

Reuses the already-proven pinned Football-Data mirror fallback. The experiment's
research contract, transforms, thresholds, temporal splits and gates remain in
cross_market_score_coherence_v1.py.
"""
from __future__ import annotations

import cross_market_score_coherence_v1 as experiment
from cross_league_direct_markets_transport import (
    _official_or_pinned_mirror_get,
)


def main() -> None:
    experiment.requests.get = _official_or_pinned_mirror_get
    experiment.main()


if __name__ == "__main__":
    main()
