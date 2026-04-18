"""
wicket_tests.py — Unit tests for WicketService helpers.

All tests run without a database — helpers are pure functions.

Run:
    pytest wicket_tests.py -v
"""
import pytest
from Wservices import WicketService


# ------------------------------------------------------------------
# Shared fixtures
# ------------------------------------------------------------------

def make_row(
    over=1, ball=1, runs=0, extras=0,
    wicket_type="bowled",
    batsman="Batsman A",
    bowler="Bowler X",
    fielder=None,
    notes=None,
):
    return {
        "over_number":  over,
        "ball_number":  ball,
        "runs_scored":  runs,
        "extras":       extras,
        "wicket_type":  wicket_type,
        "batsman_name": batsman,
        "bowler_name":  bowler,
        "fielder_name": fielder,
        "notes":        notes,
    }


# ------------------------------------------------------------------
# _format_over_ball
# ------------------------------------------------------------------
class TestFormatOverBall:
    def test_standard(self):
        assert WicketService._format_over_ball(6, 3) == "6.3"

    def test_first_ball_first_over(self):
        assert WicketService._format_over_ball(1, 1) == "1.1"

    def test_last_ball_last_over(self):
        assert WicketService._format_over_ball(20, 6) == "20.6"


# ------------------------------------------------------------------
# _build_wicket_log — basic shape
# ------------------------------------------------------------------
class TestBuildWicketLogShape:
    def test_empty_rows_returns_empty_list(self):
        assert WicketService._build_wicket_log([]) == []

    def test_wicket_count_matches_rows(self):
        rows = [make_row(over=1, ball=3), make_row(over=3, ball=5)]
        result = WicketService._build_wicket_log(rows)
        assert len(result) == 2

    def test_wicket_numbers_are_sequential(self):
        rows = [make_row(over=1, ball=1), make_row(over=2, ball=2), make_row(over=3, ball=3)]
        result = WicketService._build_wicket_log(rows)
        assert [w.wicket_number for w in result] == [1, 2, 3]

    def test_over_ball_formatted_correctly(self):
        rows = [make_row(over=6, ball=3)]
        result = WicketService._build_wicket_log(rows)
        assert result[0].over_ball == "6.3"

    def test_dismissed_player_mapped(self):
        rows = [make_row(batsman="Rohit Sharma")]
        result = WicketService._build_wicket_log(rows)
        assert result[0].dismissed_player == "Rohit Sharma"

    def test_wicket_type_lowercased(self):
        rows = [make_row(wicket_type="Caught")]
        result = WicketService._build_wicket_log(rows)
        assert result[0].wicket_type == "caught"

    def test_notes_passed_through(self):
        rows = [make_row(notes="Top edge to fine leg")]
        result = WicketService._build_wicket_log(rows)
        assert result[0].notes == "Top edge to fine leg"

    def test_none_notes_stays_none(self):
        rows = [make_row(notes=None)]
        result = WicketService._build_wicket_log(rows)
        assert result[0].notes is None


# ------------------------------------------------------------------
# score_at_fall — running tally
# ------------------------------------------------------------------
class TestScoreAtFall:
    def test_first_wicket_no_runs(self):
        rows = [make_row(runs=0, extras=0)]
        result = WicketService._build_wicket_log(rows)
        assert result[0].score_at_fall == "0/1"

    def test_first_wicket_with_runs(self):
        rows = [make_row(runs=4, extras=0)]
        result = WicketService._build_wicket_log(rows)
        assert result[0].score_at_fall == "4/1"

    def test_second_wicket_accumulates(self):
        rows = [
            make_row(over=2, ball=1, runs=0,  extras=0),
            make_row(over=5, ball=3, runs=47, extras=0),
        ]
        result = WicketService._build_wicket_log(rows)
        assert result[0].score_at_fall == "0/1"
        assert result[1].score_at_fall == "47/2"

    def test_extras_included_in_score(self):
        rows = [make_row(runs=2, extras=1)]
        result = WicketService._build_wicket_log(rows)
        assert result[0].score_at_fall == "3/1"


# ------------------------------------------------------------------
# Bowler / fielder suppression rules
# ------------------------------------------------------------------
class TestBowlerFielderRules:
    def test_bowled_has_bowler_no_fielder(self):
        rows = [make_row(wicket_type="bowled", bowler="Chahar", fielder="Dhoni")]
        result = WicketService._build_wicket_log(rows)
        assert result[0].bowler  == "Chahar"
        assert result[0].fielder is None

    def test_lbw_has_bowler_no_fielder(self):
        rows = [make_row(wicket_type="lbw", bowler="Jadeja", fielder="Dhoni")]
        result = WicketService._build_wicket_log(rows)
        assert result[0].bowler  == "Jadeja"
        assert result[0].fielder is None

    def test_caught_has_bowler_and_fielder(self):
        rows = [make_row(wicket_type="caught", bowler="Chahar", fielder="Dhoni")]
        result = WicketService._build_wicket_log(rows)
        assert result[0].bowler  == "Chahar"
        assert result[0].fielder == "Dhoni"

    def test_stumped_has_bowler_and_fielder(self):
        rows = [make_row(wicket_type="stumped", bowler="Jadeja", fielder="Dhoni")]
        result = WicketService._build_wicket_log(rows)
        assert result[0].bowler  == "Jadeja"
        assert result[0].fielder == "Dhoni"

    def test_run_out_has_fielder_no_bowler(self):
        rows = [make_row(wicket_type="run_out", bowler="Chahar", fielder="Gaikwad")]
        result = WicketService._build_wicket_log(rows)
        assert result[0].bowler  is None
        assert result[0].fielder == "Gaikwad"

    def test_retired_hurt_has_no_bowler(self):
        rows = [make_row(wicket_type="retired_hurt", bowler="Chahar", fielder=None)]
        result = WicketService._build_wicket_log(rows)
        assert result[0].bowler is None

    def test_hit_wicket_has_bowler_no_fielder(self):
        rows = [make_row(wicket_type="hit_wicket", bowler="Chahar", fielder="Dhoni")]
        result = WicketService._build_wicket_log(rows)
        assert result[0].bowler  == "Chahar"
        assert result[0].fielder is None

    def test_missing_bowler_name_returns_none(self):
        row = make_row(wicket_type="caught", bowler=None, fielder="Dhoni")
        result = WicketService._build_wicket_log([row])
        assert result[0].bowler is None