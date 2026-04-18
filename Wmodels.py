"""
wicket_models.py — Pydantic models for the wicket log endpoint.
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class WicketEvent(BaseModel):
    """A single wicket in innings order."""
    wicket_number:    int   = Field(..., description="Sequence position, e.g. 1 = first wicket")
    over_ball:        str   = Field(..., description="Formatted position, e.g. '6.3' = over 6 ball 3")
    score_at_fall:    str   = Field(..., description="Score when wicket fell, e.g. '47/1'")
    dismissed_player: str
    wicket_type:      str   = Field(..., description="bowled | caught | lbw | run_out | stumped | hit_wicket | retired_hurt | obstructing_field")
    bowler:           Optional[str] = Field(None, description="Credited bowler — None for run-outs")
    fielder:          Optional[str] = Field(None, description="Catcher, run-out fielder, or stumping keeper")
    notes:            Optional[str] = Field(None, description="Free-text detail, e.g. 'top edge to fine leg'")


class WicketLogResponse(BaseModel):
    """Ordered timeline of every wicket in the innings."""
    innings_id:     int
    innings_number: int
    batting_team:   str
    bowling_team:   str
    total_wickets:  int   = Field(..., description="Count of wickets — 0 for a wicketless innings")
    wickets:        List[WicketEvent] = Field(..., description="Empty list if no wickets have fallen")