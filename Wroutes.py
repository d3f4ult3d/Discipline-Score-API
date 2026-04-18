"""
wicket_routes.py — Wicket log route.
GET /api/v1/innings/{innings_id}/wickets
"""
from fastapi import APIRouter, HTTPException, status
from Wmodels import WicketLogResponse
from Wservices import InningsNotFoundError, WicketService

router = APIRouter()

@router.get("/innings/{innings_id}/wickets", response_model=WicketLogResponse, summary="Ordered wicket log for an innings")
def get_wicket_log(innings_id: int):
    try:
        return WicketService().get_wicket_log(innings_id)
    except InningsNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Innings '{innings_id}' not found.")