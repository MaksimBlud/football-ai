"""Deployment-safe Football AI product web application.

The web deployment is read-only. It consumes immutable prediction snapshots and
stored bookmaker snapshots from Supabase using a low-privilege publishable key
when available. It never imports model code or production artifacts.
"""

from functools import lru_cache

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from product_portfolio_risk import PORTFOLIO_RISK_SCHEMA_VERSION, build_portfolio_risk_view
from product_snapshot_store import load_product_market_view


app = FastAPI(
    title="Football AI Product",
    description="Read-only product view over durable model and market snapshots",
    version="2.2.0",
)


@lru_cache(maxsize=1)
def _supabase_client():
    from supabase import create_client
    from config import SUPABASE_KEY, SUPABASE_PUBLISHABLE_KEY, SUPABASE_URL

    key = SUPABASE_PUBLISHABLE_KEY or SUPABASE_KEY
    if not SUPABASE_URL or not key:
        raise RuntimeError("Supabase web credentials are not configured")
    return create_client(SUPABASE_URL, key)


def _credential_mode() -> str:
    from config import SUPABASE_KEY, SUPABASE_PUBLISHABLE_KEY

    if SUPABASE_PUBLISHABLE_KEY:
        return "publishable"
    if SUPABASE_KEY:
        return "server_fallback"
    return "missing"


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
        "credential_mode": _credential_mode(),
        "match_identity": "stable_product_match_id",
        "portfolio_risk_version": PORTFOLIO_RISK_SCHEMA_VERSION,
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


@app.get("/portfolio-risk-view")
def portfolio_risk_view():
    """Return structural risk analysis without creating positions or stakes."""
    return build_portfolio_risk_view(product_market_view())


@app.get("/product-market-view/{match_id}")
def product_market_match(match_id: str):
    payload = product_market_view()
    match_id = str(match_id or "").strip()
    if not match_id:
        raise HTTPException(status_code=404, detail="Матч не найден")

    item = next(
        (
            match
            for match in payload["matches"]
            if match.get("match", {}).get("product_match_id") == match_id
        ),
        None,
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Матч не найден")

    return {
        "schema_version": payload["schema_version"],
        "fixture_identity": payload["fixture_identity"],
        "selection_policy": payload["selection_policy"],
        "market_readiness": payload["market_readiness"],
        "data_source": payload.get("data_source"),
        "match_id": match_id,
        "match": item,
    }
