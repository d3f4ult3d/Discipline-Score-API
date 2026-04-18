"""
discipline_routes.py — Bowling discipline route.
GET /api/v1/innings/{innings_id}/discipline
"""
from fastapi import APIRouter, HTTPException, status

from Dmodels import DisciplineResponse
from Dservices import DisciplineService, InningsNotFoundError

router = APIRouter()


@router.get(
    "/innings/{innings_id}/discipline",
    response_model=DisciplineResponse,
    summary="Bowling discipline report for an innings",
    responses={
        200: {"description": "Discipline report returned successfully"},
        404: {"description": "Innings not found"},
    },
)
def get_discipline(innings_id: int):
    """
    Returns a full bowling discipline report for **innings_id**.

    **Discipline score** = `(legal_deliveries / total_deliveries) × 100`

    | Score   | Rating    |
    |---------|-----------|
    | 95–100  | Excellent |
    | 85–94   | Good      |
    | 70–84   | Average   |
    | < 70    | Poor      |

    **Illegal deliveries** = wides + no-balls only.
    Byes and leg-byes are not bowling errors and are excluded.

    `worst_offender` is `null` when the innings had zero illegal deliveries.
    `bowlers` is ordered worst to best discipline score so the frontend
    can render the list without any sorting.
    """
    try:
        return DisciplineService().get_discipline(innings_id)
    except InningsNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Innings '{innings_id}' not found.",
        )