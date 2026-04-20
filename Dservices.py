"""
discipline_service.py — Bowling discipline business logic. Reads from data.py.

Discipline score formula
------------------------
    score = ((total_deliveries - illegal_deliveries) / total_deliveries) * 100

An illegal delivery is any wide or no-ball. Byes and leg-byes are NOT illegal
deliveries — they result from batting or keeping errors, not bowling errors.

Rating bands
------------
    95–100  → Excellent
    85–94   → Good
    70–84   → Average
    < 70    → Poor

worst_offender
--------------
The bowler with the highest illegal delivery count.
Ties are broken by the lowest discipline score (most runs conceded per over).
Returns None if the innings had zero illegal deliveries.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Optional

from Wdata import BALL_EVENTS, BOWLING_SCORECARDS, INNINGS_BY_ID
from Dmodels import BowlerDiscipline, DisciplineResponse
from cricket_utils import safe_extra_type, safe_int, safe_str


class InningsNotFoundError(Exception):
    pass


class DisciplineService:

    def get_discipline(self, innings_id: int) -> DisciplineResponse:
        innings = INNINGS_BY_ID.get(innings_id)
        if not innings:
            raise InningsNotFoundError(innings_id)

        balls        = BALL_EVENTS.get(innings_id, [])
        bowler_rows  = BOWLING_SCORECARDS.get(innings_id, [])
        bowlers      = self._calc_bowler_discipline(balls, bowler_rows)
        totals       = self._calc_innings_totals(bowlers)
        worst        = self._find_worst_offender(bowlers)
        score        = self._score(totals["total_deliveries"], totals["illegal_deliveries"])

        return DisciplineResponse(
            innings_id         = innings_id,
            innings_number     = safe_int(innings.get("innings_number")),
            batting_team       = safe_str(innings.get("batting_team"), "TBD"),
            bowling_team       = safe_str(innings.get("bowling_team"), "TBD"),
            total_deliveries   = totals["total_deliveries"],
            legal_deliveries   = totals["legal_deliveries"],
            illegal_deliveries = totals["illegal_deliveries"],
            wides              = totals["wides"],
            no_balls           = totals["no_balls"],
            discipline_score   = score,
            rating             = self._rating(score),
            bowlers            = sorted(bowlers, key=lambda b: (b.discipline_score, -b.illegal_deliveries)),
            worst_offender     = worst,
        )

    # ------------------------------------------------------------------
    # Calculation helpers (pure — fully unit-testable)
    # ------------------------------------------------------------------

    @staticmethod
    def _calc_bowler_discipline(
        balls: List[Dict[str, Any]],
        bowler_rows: List[Dict[str, Any]],
    ) -> List[BowlerDiscipline]:
        """
        Aggregate ball events per bowler to produce per-bowler discipline rows.
        Only wides and no-balls are counted as illegal deliveries.
        """
        name_lookup = {
            safe_int(r.get("player_id"), default=-1, minimum=-1): safe_str(r.get("player_name"), "Unknown")
            for r in bowler_rows
        }

        stats: Dict[int, Dict[str, int]] = defaultdict(lambda: {
            "total": 0, "wides": 0, "no_balls": 0
        })

        for b in balls:
            pid = safe_int(b.get("bowler_id"), default=-1, minimum=-1)
            if pid < 0:
                continue
            stats[pid]["total"] += 1
            extra_type = safe_extra_type(b)
            if extra_type == "wide":
                stats[pid]["wides"] += 1
            elif extra_type == "no_ball":
                stats[pid]["no_balls"] += 1

        rows = []
        for pid, s in stats.items():
            illegal = s["wides"] + s["no_balls"]
            legal   = s["total"] - illegal
            score   = DisciplineService._score(s["total"], illegal)
            rows.append(BowlerDiscipline(
                bowler_name        = name_lookup.get(pid, f"Player {pid}"),
                total_deliveries   = s["total"],
                legal_deliveries   = legal,
                illegal_deliveries = illegal,
                wides              = s["wides"],
                no_balls           = s["no_balls"],
                discipline_score   = score,
                rating             = DisciplineService._rating(score),
            ))
        return rows

    @staticmethod
    def _calc_innings_totals(bowlers: List[BowlerDiscipline]) -> Dict[str, int]:
        """Sum per-bowler stats into innings-level totals."""
        return {
            "total_deliveries":   sum(b.total_deliveries   for b in bowlers),
            "legal_deliveries":   sum(b.legal_deliveries   for b in bowlers),
            "illegal_deliveries": sum(b.illegal_deliveries for b in bowlers),
            "wides":              sum(b.wides              for b in bowlers),
            "no_balls":           sum(b.no_balls           for b in bowlers),
        }

    @staticmethod
    def _find_worst_offender(bowlers: List[BowlerDiscipline]) -> Optional[BowlerDiscipline]:
        """
        Return the bowler with the most illegal deliveries.
        Ties broken by lowest discipline score.
        Returns None if every bowler was perfectly disciplined.
        """
        offenders = [b for b in bowlers if b.illegal_deliveries > 0]
        if not offenders:
            return None
        return max(offenders, key=lambda b: (b.illegal_deliveries, -b.discipline_score))

    @staticmethod
    def _score(total_deliveries: int, illegal_deliveries: int) -> float:
        """
        Discipline score = (legal / total) * 100.
        Returns 100.0 for a perfect over or if no deliveries have been bowled.
        """
        total_deliveries = safe_int(total_deliveries)
        illegal_deliveries = min(safe_int(illegal_deliveries), total_deliveries)
        if total_deliveries == 0:
            return 100.0
        legal = total_deliveries - illegal_deliveries
        return round((legal / total_deliveries) * 100, 2)

    @staticmethod
    def _rating(score: float) -> str:
        """
        Map a discipline score to a human-readable rating.
            95–100  → Excellent
            85–94   → Good
            70–84   → Average
            < 70    → Poor
        """
        if score >= 95:
            return "Excellent"
        if score >= 85:
            return "Good"
        if score >= 70:
            return "Average"
        return "Poor"
