"""Standalone read-only Research Viewer web app.

The root page is the canonical Multi-Market V1 viewer. The previous statistics
viewer remains available at /legacy. No endpoint writes, trains, promotes, or
activates production behavior.
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from database import supabase
from research_viewer import fetch_viewer_payload

app = FastAPI(
    title="Football AI Research Viewer",
    description="Read-only canonical multi-league multi-market research viewer",
    version="1.2.0",
)

@app.get("/")
def viewer_page():
    return FileResponse("static/multi_market_viewer.html")

@app.get("/legacy")
def legacy_viewer_page():
    return FileResponse("static/research_viewer.html")

@app.get("/health")
def health():
    return {"status": "healthy", "mode": "READ_ONLY_RESEARCH", "viewer_version": "1.2.0", "multi_market": "schema-backed"}

@app.get("/api/research-viewer")
def research_viewer_data():
    try:
        return fetch_viewer_payload(supabase)
    except Exception as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
