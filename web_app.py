"""Deployment-safe Football AI product web application.

This module intentionally does not import ``api.py`` or any model module. A clean
web deployment reads immutable model outputs from Supabase and never needs local
model artifacts or generated CSV files.
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from product_snapshot_store import load_product_market_view


app = FastAPI(
    title="Football AI Product",
    description="Read-only product view over durable model and market snapshots",
    version="2.0.0",
)


def _supabase_client():
    # Lazy import keeps module import/CI independent from deployment secrets.
    from database import supabase

    return supabase


@app.get("/")
def root():
    return FileResponse("static/index_v2.html")


@app.get("/match")
def match_page():
    return FileResponse("static/match.html")


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "mode": "durable-snapshot-reader",
    }


@app.get("/product-market-view")
def product_market_view():
    try:
        return load_product_market_view(_supabase_client())
    except Exception as error:
        raise HTTPException(
            status_code=503,
            detail="Не удалось загрузить сохранённые прогнозы.",
        ) from error


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
        "data_source": payload.get("data_source"),
        "match_id": match_id,
        "match": matches[match_id],
    }
