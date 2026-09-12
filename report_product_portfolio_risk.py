"""Read-only Product Portfolio / Risk Layer v1 report.

Loads the same durable product market view used by the web app and prints the
pure structural portfolio-risk contract. It performs no Supabase writes, model
inference, Odds API calls, bankroll allocation, stake sizing or bet placement.
"""

from __future__ import annotations

import json

from product_portfolio_risk import build_portfolio_risk_view
from product_snapshot_store import load_product_market_view


def main() -> None:
    from database import supabase

    product_view = load_product_market_view(supabase)
    report = build_portfolio_risk_view(product_view)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    print("PASS: READ-ONLY PRODUCT PORTFOLIO RISK REPORT COMPLETE")


if __name__ == "__main__":
    main()
