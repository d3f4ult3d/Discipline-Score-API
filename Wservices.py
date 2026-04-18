"""
wicket_service.py — Wicket log business logic. Reads from data.py.
"""
from __future__ import annotations
from typing import Any, Dict, List
from Wdata import BALL_EVENTS, INNINGS_BY_ID
from Wmodels import WicketEvent, WicketLogResponse

NO_BOWLER_CREDIT = {"run_out", "retired_hurt", "obstructing_field"}
NO_FIELDER_TYPES = {"bowled", "lbw", "hit_wicket"}


class InningsNotFoundError(Exception):
    pass


class WicketService:

    def get_wicket_log(self, innings_id: int) -> WicketLogResponse:
        innings = INNINGS_BY_ID.get(innings_id)
        if not innings:
            raise InningsNotFoundError(innings_id)
        balls   = BALL_EVENTS.get(innings_id, [])
        wickets = self._build_wicket_log([b for b in balls if b["is_wicket"]])
        return WicketLogResponse(
            innings_id     = innings_id,
            innings_number = innings["innings_number"],
            batting_team   = innings["batting_team"],
            bowling_team   = innings["bowling_team"],
            total_wickets  = len(wickets),
            wickets        = wickets,
        )

    @staticmethod
    def _build_wicket_log(rows: List[Dict[str, Any]]) -> List[WicketEvent]:
        wickets      = []
        running_runs = 0
        wicket_count = 0
        for row in rows:
            running_runs += row.get("runs_scored", 0) + row.get("extras", 0)
            wicket_count += 1
            wicket_type   = (row.get("wicket_type") or "unknown").lower()
            bowler  = row.get("bowler_name")  if wicket_type not in NO_BOWLER_CREDIT else None
            fielder = row.get("fielder_name") if wicket_type not in NO_FIELDER_TYPES  else None
            wickets.append(WicketEvent(
                wicket_number    = wicket_count,
                over_ball        = f"{row['over_number']}.{row['ball_number']}",
                score_at_fall    = f"{running_runs}/{wicket_count}",
                dismissed_player = row.get("batsman_name") or "Unknown",
                wicket_type      = wicket_type,
                bowler           = bowler or None,
                fielder          = fielder or None,
                notes            = row.get("notes") or None,
            ))
        return wickets

    @staticmethod
    def _format_over_ball(over_number: int, ball_number: int) -> str:
        return f"{over_number}.{ball_number}"