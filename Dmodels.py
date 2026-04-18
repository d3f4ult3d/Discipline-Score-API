"""
discipline_models.py — Pydantic models for the bowling discipline endpoint.

Discipline score formula (documented here, enforced in discipline_service.py):
---------------------------------------------------------------------------
A bowler's discipline score is a percentage of their deliveries that were legal.

    discipline_score = ((total_deliveries - illegal_deliveries) / total_deliveries) * 100

Scale:
    95–100  → Excellent
    85–94   → Good
    70–84   → Average
    < 70    → Poor

Innings-level discipline score applies the same formula across all deliveries
bowled in the innings. A score of 100.0 means zero illegal deliveries.
---------------------------------------------------------------------------
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class BowlerDiscipline(BaseModel):
    """Discipline breakdown for a single bowler."""
    bowler_name:         str
    total_deliveries:    int   = Field(..., description="Legal balls + wides + no-balls bowled by this bowler")
    legal_deliveries:    int   = Field(..., description="Deliveries that were neither a wide nor a no-ball")
    illegal_deliveries:  int   = Field(..., description="wides + no-balls bowled by this bowler")
    wides:               int
    no_balls:            int
    discipline_score:    float = Field(..., description="(legal / total) × 100, rounded to 2 dp. 100.0 = perfect control")
    rating:              str   = Field(..., description="Excellent (≥95) | Good (85–94) | Average (70–84) | Poor (<70)")


class DisciplineResponse(BaseModel):
    """
    Innings-level bowling discipline report.

    Discipline score formula:
        score = ((total_deliveries - illegal_deliveries) / total_deliveries) * 100

    100.0 means every delivery in the innings was legal.
    The worst_offender is the bowler with the highest illegal delivery count;
    ties are broken by the lowest discipline score.
    """
    innings_id:          int
    innings_number:      int
    batting_team:        str
    bowling_team:        str

    # Innings-level totals
    total_deliveries:    int   = Field(..., description="Total deliveries bowled (legal + illegal)")
    legal_deliveries:    int
    illegal_deliveries:  int   = Field(..., description="Total wides + no-balls in the innings")
    wides:               int
    no_balls:            int
    discipline_score:    float = Field(..., description="Innings-level discipline score (0–100)")
    rating:              str   = Field(..., description="Excellent | Good | Average | Poor")

    # Per-bowler breakdown
    bowlers:             List[BowlerDiscipline] = Field(..., description="Every bowler, ordered worst to best discipline score")
    worst_offender:      Optional[BowlerDiscipline] = Field(None, description="Bowler with most illegal deliveries. None if innings has zero illegal deliveries")