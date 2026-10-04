"""Transport-only launcher for CROSS_MARKET_LEAD_LAG_V1.

Reuses the pinned Football-Data mirror fallback already proven in the repository.
The research contract remains entirely in cross_market_lead_lag_v1.py.
"""
from __future__ import annotations

import cross_market_lead_lag_v1 as experiment
from cross_league_direct_markets_transport import (
    _official_or_pinned_mirror_get,
)


def main() -> None:
    experiment.requests.get = _official_or_pinned_mirror_get
    experiment.main()


if __name__ == "__main__":
    main()
