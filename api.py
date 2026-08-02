from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from predict_match import predict_match
from teams import get_team_names

app = FastAPI(
    title="Football AI API",
    description="API прогнозирования футбольных матчей",
    version="1.0.0",
)


class PredictionRequest(BaseModel):
    home_team: str = Field(min_length=1)
    away_team: str = Field(min_length=1)
    home_odds: float = Field(gt=1)
    draw_odds: float = Field(gt=1)
    away_odds: float = Field(gt=1)


class PredictionResponse(BaseModel):
    home_team: str
    away_team: str
    prediction: str

    home_probability: float
    draw_probability: float
    away_probability: float

    home_last5_points: int
    away_last5_points: int

    home_elo: float
    away_elo: float


@app.get("/")
def root():
    return FileResponse("static/index.html")


@app.get("/health")
@app.get("/teams")
def teams():
    return get_team_names()
def health():
    return {
        "status": "healthy"
    }


@app.post(
    "/predict",
    response_model=PredictionResponse,
)
def create_prediction(request: PredictionRequest):
    try:
        return predict_match(
            home_team=request.home_team.strip(),
            away_team=request.away_team.strip(),
            home_odds=request.home_odds,
            draw_odds=request.draw_odds,
            away_odds=request.away_odds,
        )

    except (
        FileNotFoundError,
        ValueError,
        RuntimeError,
    ) as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error
