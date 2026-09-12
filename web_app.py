"""Canonical web entrypoint for the Football AI product application.

`api.py` keeps the existing API surface. This entrypoint adds the versioned
product-market payload so list and match-detail UIs share one server-owned
calculation path.
"""

import pandas as pd
from fastapi import HTTPException

from api import app, upcoming_matches
from product_web import assemble_product_market_view


PRODUCT_PREDICTIONS_PATH = "data/upcoming_round_predictions.csv"


@app.get("/product-market-view")
def product_market_view():
    try:
        predictions_df = pd.read_csv(PRODUCT_PREDICTIONS_PATH)
    except FileNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=(
                "Файл прогнозов тура не найден. "
                "Сначала запустите predict_upcoming_round.py."
            ),
        ) from error

    predictions = predictions_df.to_dict(orient="records")
    odds_rows = upcoming_matches()

    return assemble_product_market_view(
        predictions,
        odds_rows,
    )


@app.get("/product-market-view/{match_id}")
def product_market_match(match_id: int):
    payload = product_market_view()
    matches = payload["matches"]

    if match_id < 0 or match_id >= len(matches):
        raise HTTPException(
            status_code=404,
            detail="Матч не найден",
        )

    return {
        "schema_version": payload["schema_version"],
        "fixture_identity": payload["fixture_identity"],
        "selection_policy": payload["selection_policy"],
        "market_readiness": payload["market_readiness"],
        "match_id": match_id,
        "match": matches[match_id],
    }
