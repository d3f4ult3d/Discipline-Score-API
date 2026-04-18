"""
innings_routes.py — Innings summary route.
GET /api/v1/innings/{innings_id}/summary
"""
from fastapi import APIRouter, HTTPException, status
from Imodels import InningsSummaryResponse
from Iservice import InningsNotFoundError, InningsSummaryService

router = APIRouter()

@router.get("/innings/{innings_id}/summary", response_model=InningsSummaryResponse, summary="Full innings summary")
def get_innings_summary(innings_id: int):
    try:
        return InningsSummaryService().get_innings_summary(innings_id)
    except InningsNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Innings '{innings_id}' not found.")