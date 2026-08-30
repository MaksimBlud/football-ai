"""Standalone read-only Research Viewer web app.

Run locally with:
    uvicorn research_viewer_app:app --host 0.0.0.0 --port 8001

The app exposes no write, training, promotion, or activation endpoints.
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from database import supabase
from research_viewer import fetch_viewer_payload


app = FastAPI(
    title="Football AI Research Viewer",
    description="Read-only canonical multi-league research viewer",
    version="1.0.0",
)


@app.get("/")
def viewer_page():
    return FileResponse("static/research_viewer.html")


@app.get("/health")
def health():
    return {"status": "healthy", "mode": "READ_ONLY_RESEARCH"}


@app.get("/api/research-viewer")
def research_viewer_data():
    try:
        return fetch_viewer_payload(supabase)
    except Exception as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
