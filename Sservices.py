"""
service.py — Scoreboard business logic. Reads from data.py.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from Wdata import BALL_EVENTS, BATTING_SCORECARDS, BOWLING_SCORECARDS, INNINGS, MATCHES
from Smodels import BatterInfo, BowlerInfo, ScoreboardResponse


class MatchNotFoundError(Exception):
    pass


class ScoreboardService:

    def get_scoreboard(self, match_code: str) -> ScoreboardResponse:
        match   = self._get_match(match_code)
        innings = self._get_active_innings(match["id"])
        if innings is None:
            return self._build_no_innings_response(match)
        iid     = innings["id"]
        batting = BATTING_SCORECARDS.get(iid, [])
        bowling = BOWLING_SCORECARDS.get(iid, [])
        balls   = BALL_EVENTS.get(iid, [])
        return ScoreboardResponse(
            match          = f"{match['home_team']} vs {match['away_team']}",
            match_code     = match["match_code"],
            venue          = match["venue"],
            match_type     = match["match_type"],
            innings_number = innings["innings_number"],
            batting_team   = innings["batting_team"],
            bowling_team   = innings["bowling_team"],
            score          = self._calc_score(balls),
            overs          = self._calc_overs(self._legal_balls(balls)),
            run_rate       = self._calc_run_rate(self._total_runs(balls), self._legal_balls(balls)),
            top_batter     = self._calc_top_batter(batting, balls),
            top_bowler     = self._calc_top_bowler(bowling, balls),
            recent_balls   = self._calc_ball_symbols(balls[-12:]),
            status         = match["status"],
        )

    @staticmethod
    def _get_match(match_code):
        match = MATCHES.get(match_code)
        if not match:
            raise MatchNotFoundError(match_code)
        return match

    @staticmethod
    def _get_active_innings(match_id):
        for inn in INNINGS.get(match_id, []):
            if inn["status"] == "in_progress":
                return inn
        completed = INNINGS.get(match_id, [])
        return completed[-1] if completed else None

    @staticmethod
    def _total_runs(balls):
        return sum(b["runs_scored"] + b.get("extras", 0) for b in balls)

    @staticmethod
    def _total_wickets(balls):
        return sum(1 for b in balls if b["is_wicket"])

    @staticmethod
    def _legal_balls(balls):
        return sum(1 for b in balls if b.get("extra_type") not in ("wide", "no_ball"))

    @staticmethod
    def _calc_score(balls):
        return f"{ScoreboardService._total_runs(balls)}/{ScoreboardService._total_wickets(balls)}"

    @staticmethod
    def _calc_overs(legal_balls):
        return f"{legal_balls // 6}.{legal_balls % 6}"

    @staticmethod
    def _calc_run_rate(total_runs, legal_balls):
        if legal_balls == 0:
            return 0.0
        return round(total_runs / (legal_balls / 6), 2)

    @staticmethod
    def _calc_strike_rate(runs, balls):
        if balls == 0:
            return 0.0
        return round((runs / balls) * 100, 2)

    @staticmethod
    def _calc_economy(runs, overs):
        if overs == 0:
            return 0.0
        return round(runs / overs, 2)

    @staticmethod
    def _calc_top_batter(cards, balls):
        if not cards:
            return None
        stats: Dict[int, Dict] = {}
        for b in balls:
            pid = b.get("batsman_id")
            if pid is None:
                continue
            if pid not in stats:
                stats[pid] = {"runs": 0, "balls": 0, "fours": 0, "sixes": 0}
            if b.get("extra_type") != "wide":
                stats[pid]["balls"] += 1
            stats[pid]["runs"] += b["runs_scored"]
            if b["runs_scored"] == 4:
                stats[pid]["fours"] += 1
            elif b["runs_scored"] == 6:
                stats[pid]["sixes"] += 1
        active = [c for c in cards if not c["is_out"]] or cards
        best   = max(active, key=lambda c: stats.get(c["player_id"], {}).get("runs", 0))
        s      = stats.get(best["player_id"], {"runs": 0, "balls": 0, "fours": 0, "sixes": 0})
        return BatterInfo(
            name        = best["player_name"],
            runs        = s["runs"],
            balls       = s["balls"],
            fours       = s["fours"],
            sixes       = s["sixes"],
            strike_rate = ScoreboardService._calc_strike_rate(s["runs"], s["balls"]),
        )

    @staticmethod
    def _calc_top_bowler(cards, balls):
        if not cards:
            return None
        stats: Dict[int, Dict] = {}
        for b in balls:
            pid = b.get("bowler_id")
            if pid is None:
                continue
            if pid not in stats:
                stats[pid] = {"runs": 0, "legal": 0, "wickets": 0}
            stats[pid]["runs"]    += b["runs_scored"] + b.get("extras", 0)
            stats[pid]["wickets"] += 1 if b["is_wicket"] else 0
            if b.get("extra_type") not in ("wide", "no_ball"):
                stats[pid]["legal"] += 1
        best = max(cards, key=lambda c: (
            stats.get(c["player_id"], {}).get("wickets", 0),
            -ScoreboardService._calc_economy(
                stats.get(c["player_id"], {}).get("runs", 0),
                round(stats.get(c["player_id"], {}).get("legal", 0) / 6, 4),
            ),
        ))
        s     = stats.get(best["player_id"], {"runs": 0, "legal": 0, "wickets": 0})
        overs = round(s["legal"] / 6, 4)
        return BowlerInfo(
            name          = best["player_name"],
            overs         = overs,
            wickets       = s["wickets"],
            runs_conceded = s["runs"],
            economy       = ScoreboardService._calc_economy(s["runs"], overs),
        )

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

    @staticmethod
    def _build_no_innings_response(match):
        return ScoreboardResponse(
            match=f"{match['home_team']} vs {match['away_team']}",
            match_code=match["match_code"], venue=match["venue"],
            match_type=match["match_type"], innings_number=0,
            batting_team="TBD", bowling_team="TBD",
            score="0/0", overs="0.0", run_rate=0.0,
            top_batter=None, top_bowler=None, recent_balls=[],
            status=match["status"],
        )