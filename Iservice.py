"""
innings_service.py — Innings summary business logic. Reads from data.py.
"""
from __future__ import annotations
from collections import defaultdict
from typing import Any, Dict, List, Optional
from Wdata import BALL_EVENTS, BATTING_SCORECARDS, BOWLING_SCORECARDS, INNINGS_BY_ID
from Imodels import BatterInfo, BatterSummary, BowlerInfo, BowlerSummary, InningsSummaryResponse


class InningsNotFoundError(Exception):
    pass


class InningsSummaryService:

    def get_innings_summary(self, innings_id: int) -> InningsSummaryResponse:
        innings = INNINGS_BY_ID.get(innings_id)
        if not innings:
            raise InningsNotFoundError(innings_id)
        balls        = BALL_EVENTS.get(innings_id, [])
        batter_rows  = BATTING_SCORECARDS.get(innings_id, [])
        bowler_rows  = BOWLING_SCORECARDS.get(innings_id, [])
        totals       = self._calc_innings_totals(balls)
        batters      = self._calc_batter_summaries(balls, batter_rows)
        bowlers      = self._calc_bowler_summaries(balls, bowler_rows)
        return InningsSummaryResponse(
            innings_id     = innings_id,
            innings_number = innings["innings_number"],
            batting_team   = innings["batting_team"],
            bowling_team   = innings["bowling_team"],
            total_runs     = totals["total_runs"],
            wickets        = totals["wickets"],
            legal_balls    = totals["legal_balls"],
            overs          = self._calc_overs(totals["legal_balls"]),
            run_rate       = self._calc_run_rate(totals["total_runs"], totals["legal_balls"]),
            extras         = totals["extras"],
            wides          = totals["wides"],
            no_balls       = totals["no_balls"],
            batters        = batters,
            bowlers        = bowlers,
            top_batter     = self._calc_top_batter(batters),
            top_bowler     = self._calc_top_bowler(bowlers),
            recent_balls   = self._calc_ball_symbols(balls[-12:]),
        )

    @staticmethod
    def _calc_innings_totals(balls):
        total_runs = wickets = legal_balls = extras = wides = no_balls = 0
        for b in balls:
            total_runs += b["runs_scored"] + b.get("extras", 0)
            extras     += b.get("extras", 0)
            if b.get("extra_type") == "wide":
                wides += 1
            elif b.get("extra_type") == "no_ball":
                no_balls += 1
            else:
                legal_balls += 1
            if b["is_wicket"]:
                wickets += 1
        return {"total_runs": total_runs, "wickets": wickets, "legal_balls": legal_balls,
                "extras": extras, "wides": wides, "no_balls": no_balls}

    @staticmethod
    def _calc_batter_summaries(balls, batter_rows):
        meta = {r["player_id"]: r for r in batter_rows}
        stats: Dict[int, Dict] = defaultdict(lambda: {"runs": 0, "balls_faced": 0, "fours": 0, "sixes": 0, "dot_balls": 0})
        for b in balls:
            pid = b.get("batsman_id")
            if pid is None:
                continue
            s = stats[pid]
            if b.get("extra_type") != "wide":
                s["balls_faced"] += 1
                if b["runs_scored"] == 0 and not b["is_wicket"]:
                    s["dot_balls"] += 1
            s["runs"] += b["runs_scored"]
            if b["runs_scored"] == 4:
                s["fours"] += 1
            elif b["runs_scored"] == 6:
                s["sixes"] += 1
        summaries = []
        for pid, s in stats.items():
            m = meta.get(pid, {"player_name": f"Player {pid}", "is_out": False})
            sr = round((s["runs"] / s["balls_faced"]) * 100, 2) if s["balls_faced"] else 0.0
            summaries.append(BatterSummary(
                name=m["player_name"], runs=s["runs"], balls_faced=s["balls_faced"],
                fours=s["fours"], sixes=s["sixes"], dot_balls=s["dot_balls"],
                strike_rate=sr, is_out=m["is_out"],
            ))
        return sorted(summaries, key=lambda x: (-x.runs, -x.balls_faced))

    @staticmethod
    def _calc_bowler_summaries(balls, bowler_rows):
        name_lookup = {r["player_id"]: r["player_name"] for r in bowler_rows}
        stats: Dict[int, Dict] = defaultdict(lambda: {"legal_balls": 0, "wickets": 0, "runs_conceded": 0, "wides": 0, "no_balls": 0, "dot_balls": 0})
        for b in balls:
            pid = b.get("bowler_id")
            if pid is None:
                continue
            s = stats[pid]
            s["runs_conceded"] += b["runs_scored"] + b.get("extras", 0)
            if b.get("extra_type") == "wide":
                s["wides"] += 1
            elif b.get("extra_type") == "no_ball":
                s["no_balls"] += 1
            else:
                s["legal_balls"] += 1
                if b["runs_scored"] == 0 and not b["is_wicket"]:
                    s["dot_balls"] += 1
            if b["is_wicket"]:
                s["wickets"] += 1
        summaries = []
        for pid, s in stats.items():
            overs_dec = round(s["legal_balls"] / 6, 4)
            economy   = round(s["runs_conceded"] / overs_dec, 2) if overs_dec else 0.0
            summaries.append(BowlerSummary(
                name=name_lookup.get(pid, f"Player {pid}"),
                legal_balls=s["legal_balls"],
                overs=f"{s['legal_balls'] // 6}.{s['legal_balls'] % 6}",
                wickets=s["wickets"], runs_conceded=s["runs_conceded"],
                wides=s["wides"], no_balls=s["no_balls"],
                dot_balls=s["dot_balls"], economy=economy,
            ))
        return sorted(summaries, key=lambda x: (-x.wickets, x.economy))

    @staticmethod
    def _calc_top_batter(batters):
        if not batters:
            return None
        active = [b for b in batters if not b.is_out] or batters
        best   = max(active, key=lambda b: b.runs)
        return BatterInfo(name=best.name, runs=best.runs, balls=best.balls_faced,
                          fours=best.fours, sixes=best.sixes, strike_rate=best.strike_rate)

    @staticmethod
    def _calc_top_bowler(bowlers):
        if not bowlers:
            return None
        best = max(bowlers, key=lambda b: (b.wickets, -b.economy))
        return BowlerInfo(name=best.name, overs=round(best.legal_balls / 6, 4),
                          wickets=best.wickets, runs_conceded=best.runs_conceded, economy=best.economy)

    @staticmethod
    def _calc_overs(legal_balls):
        return f"{legal_balls // 6}.{legal_balls % 6}"

    @staticmethod
    def _calc_run_rate(total_runs, legal_balls):
        if legal_balls == 0:
            return 0.0
        return round(total_runs / (legal_balls / 6), 2)

    @staticmethod
    def _calc_ball_symbols(balls):
        symbols = []
        for b in balls:
            if b["is_wicket"]:
                symbols.append("W")
            elif b.get("extra_type") == "wide":
                symbols.append("Wd")
            elif b.get("extra_type") == "no_ball":
                symbols.append("Nb")
            elif b["runs_scored"] == 0:
                symbols.append("•")
            else:
                symbols.append(str(b["runs_scored"]))
        return symbols