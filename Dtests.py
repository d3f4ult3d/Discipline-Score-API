"""
discipline_tests.py — Unit tests for DisciplineService helpers.

All tests run without a database — helpers are pure functions.

Run:
    pytest discipline_tests.py -v
"""
import pytest
from Dservices import DisciplineService


# ------------------------------------------------------------------
# _score
# ------------------------------------------------------------------
class TestScore:
    def test_perfect_score(self):
        assert DisciplineService._score(10, 0) == 100.0

    def test_all_illegal(self):
        assert DisciplineService._score(10, 10) == 0.0

    def test_one_illegal_in_six(self):
        assert DisciplineService._score(6, 1) == pytest.approx(83.33, abs=0.01)

    def test_zero_deliveries_returns_100(self):
        assert DisciplineService._score(0, 0) == 100.0

    def test_two_illegal_in_ten(self):
        assert DisciplineService._score(10, 2) == 80.0


# ------------------------------------------------------------------
# _rating
# ------------------------------------------------------------------
class TestRating:
    def test_excellent(self):
        assert DisciplineService._rating(100.0) == "Excellent"
        assert DisciplineService._rating(95.0)  == "Excellent"

    def test_good(self):
        assert DisciplineService._rating(94.9) == "Good"
        assert DisciplineService._rating(85.0) == "Good"

    def test_average(self):
        assert DisciplineService._rating(84.9) == "Average"
        assert DisciplineService._rating(70.0) == "Average"

    def test_poor(self):
        assert DisciplineService._rating(69.9) == "Poor"
        assert DisciplineService._rating(0.0)  == "Poor"


# ------------------------------------------------------------------
# _calc_bowler_discipline
# ------------------------------------------------------------------
BOWLER_ROWS = [
    {"player_id": 10, "player_name": "Deepak Chahar"},
    {"player_id": 11, "player_name": "Ravindra Jadeja"},
]

BALLS = [
    # Chahar: 4 legal, 1 wide, 1 no_ball → 6 total, 2 illegal
    {"bowler_id": 10, "extra_type": None,      "runs_scored": 0, "extras": 0, "is_wicket": False},
    {"bowler_id": 10, "extra_type": None,      "runs_scored": 4, "extras": 0, "is_wicket": False},
    {"bowler_id": 10, "extra_type": "wide",    "runs_scored": 0, "extras": 1, "is_wicket": False},
    {"bowler_id": 10, "extra_type": None,      "runs_scored": 1, "extras": 0, "is_wicket": False},
    {"bowler_id": 10, "extra_type": "no_ball", "runs_scored": 0, "extras": 1, "is_wicket": False},
    {"bowler_id": 10, "extra_type": None,      "runs_scored": 6, "extras": 0, "is_wicket": False},
    # Jadeja: 6 legal, 0 illegal → 6 total, 0 illegal
    {"bowler_id": 11, "extra_type": None,      "runs_scored": 1, "extras": 0, "is_wicket": False},
    {"bowler_id": 11, "extra_type": None,      "runs_scored": 0, "extras": 0, "is_wicket": True},
    {"bowler_id": 11, "extra_type": None,      "runs_scored": 4, "extras": 0, "is_wicket": False},
    {"bowler_id": 11, "extra_type": None,      "runs_scored": 0, "extras": 0, "is_wicket": False},
    {"bowler_id": 11, "extra_type": None,      "runs_scored": 6, "extras": 0, "is_wicket": False},
    {"bowler_id": 11, "extra_type": None,      "runs_scored": 1, "extras": 0, "is_wicket": False},
]


class TestCalcBowlerDiscipline:
    def test_returns_one_row_per_bowler(self):
        result = DisciplineService._calc_bowler_discipline(BALLS, BOWLER_ROWS)
        assert len(result) == 2

    def test_chahar_illegal_count(self):
        result = DisciplineService._calc_bowler_discipline(BALLS, BOWLER_ROWS)
        chahar = next(b for b in result if b.bowler_name == "Deepak Chahar")
        assert chahar.illegal_deliveries == 2
        assert chahar.wides == 1
        assert chahar.no_balls == 1

    def test_chahar_total_deliveries(self):
        result = DisciplineService._calc_bowler_discipline(BALLS, BOWLER_ROWS)
        chahar = next(b for b in result if b.bowler_name == "Deepak Chahar")
        assert chahar.total_deliveries == 6

    def test_jadeja_perfect_discipline(self):
        result = DisciplineService._calc_bowler_discipline(BALLS, BOWLER_ROWS)
        jadeja = next(b for b in result if b.bowler_name == "Ravindra Jadeja")
        assert jadeja.illegal_deliveries == 0
        assert jadeja.discipline_score   == 100.0
        assert jadeja.rating             == "Excellent"

    def test_byes_not_counted_as_illegal(self):
        balls_with_bye = [{"bowler_id": 10, "extra_type": "bye",     "runs_scored": 0, "extras": 2, "is_wicket": False},
                          {"bowler_id": 10, "extra_type": "leg_bye", "runs_scored": 0, "extras": 1, "is_wicket": False}]
        result = DisciplineService._calc_bowler_discipline(balls_with_bye, BOWLER_ROWS)
        chahar = next((b for b in result if b.bowler_name == "Deepak Chahar"), None)
        assert chahar is not None
        assert chahar.illegal_deliveries == 0

    def test_empty_balls_returns_empty_list(self):
        assert DisciplineService._calc_bowler_discipline([], BOWLER_ROWS) == []


# ------------------------------------------------------------------
# _calc_innings_totals
# ------------------------------------------------------------------
class TestCalcInningsTotals:
    def test_totals_sum_correctly(self):
        bowlers = DisciplineService._calc_bowler_discipline(BALLS, BOWLER_ROWS)
        totals  = DisciplineService._calc_innings_totals(bowlers)
        assert totals["total_deliveries"]   == 12
        assert totals["illegal_deliveries"] == 2
        assert totals["legal_deliveries"]   == 10
        assert totals["wides"]              == 1
        assert totals["no_balls"]           == 1

    def test_zero_bowlers(self):
        totals = DisciplineService._calc_innings_totals([])
        assert totals["total_deliveries"] == 0
        assert totals["illegal_deliveries"] == 0


# ------------------------------------------------------------------
# _find_worst_offender
# ------------------------------------------------------------------
class TestFindWorstOffender:
    def test_returns_bowler_with_most_illegal(self):
        bowlers = DisciplineService._calc_bowler_discipline(BALLS, BOWLER_ROWS)
        worst   = DisciplineService._find_worst_offender(bowlers)
        assert worst is not None
        assert worst.bowler_name == "Deepak Chahar"

    def test_returns_none_when_no_illegal_deliveries(self):
        clean_balls = [b for b in BALLS if b["extra_type"] not in ("wide", "no_ball")]
        bowlers = DisciplineService._calc_bowler_discipline(clean_balls, BOWLER_ROWS)
        assert DisciplineService._find_worst_offender(bowlers) is None

    def test_tiebreak_by_lower_discipline_score(self):
        # Both bowlers have 2 illegal deliveries but different totals
        tied_balls = [
            # Chahar: 2 illegal out of 4 → score 50.0
            {"bowler_id": 10, "extra_type": "wide",    "runs_scored": 0, "extras": 1, "is_wicket": False},
            {"bowler_id": 10, "extra_type": "no_ball", "runs_scored": 0, "extras": 1, "is_wicket": False},
            {"bowler_id": 10, "extra_type": None,      "runs_scored": 0, "extras": 0, "is_wicket": False},
            {"bowler_id": 10, "extra_type": None,      "runs_scored": 0, "extras": 0, "is_wicket": False},
            # Jadeja: 2 illegal out of 6 → score 66.7
            {"bowler_id": 11, "extra_type": "wide",    "runs_scored": 0, "extras": 1, "is_wicket": False},
            {"bowler_id": 11, "extra_type": "no_ball", "runs_scored": 0, "extras": 1, "is_wicket": False},
            {"bowler_id": 11, "extra_type": None,      "runs_scored": 0, "extras": 0, "is_wicket": False},
            {"bowler_id": 11, "extra_type": None,      "runs_scored": 0, "extras": 0, "is_wicket": False},
            {"bowler_id": 11, "extra_type": None,      "runs_scored": 0, "extras": 0, "is_wicket": False},
            {"bowler_id": 11, "extra_type": None,      "runs_scored": 0, "extras": 0, "is_wicket": False},
        ]
        bowlers = DisciplineService._calc_bowler_discipline(tied_balls, BOWLER_ROWS)
        worst   = DisciplineService._find_worst_offender(bowlers)
        # Chahar has lower score (50.0) so is the worst offender
        assert worst.bowler_name == "Deepak Chahar"