"""
routes.py — Scoreboard route.
GET /api/v1/scoreboard/{match_code}
"""
from fastapi import APIRouter, HTTPException, status
from Smodels import ScoreboardResponse
from Sservices import MatchNotFoundError, ScoreboardService

router = APIRouter()

@router.get("/scoreboard/{match_code}", response_model=ScoreboardResponse, summary="Live scoreboard for a match")
def get_scoreboard(match_code: str):
    try:
        return ScoreboardService().get_scoreboard(match_code)
    except MatchNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Match '{match_code}' not found.")