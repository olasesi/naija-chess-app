import pytest
from apps.ratings.glicko2 import (
    calculate_rating_period,
    expected_score_vs_opponent,
    glicko2_scale,
    glicko1_scale,
    adjust_rd_for_inactivity,
    g,
    E,
)


class TestGlicko2:
    def test_scale_roundtrip(self):
        r, rd, sigma = 1500.0, 350.0, 0.06
        mu, phi, s = glicko2_scale(r, rd, sigma)
        r2, rd2, s2 = glicko1_scale(mu, phi, s)
        assert abs(r - r2) < 0.01
        assert abs(rd - rd2) < 0.01
        assert abs(sigma - s2) < 0.01

    def test_g_function(self):
        assert g(0.0) == 1.0
        assert g(1.0) < 1.0
        assert g(2.0) < g(1.0)

    def test_E_equals_half_for_equal_ratings(self):
        prob = E(0.0, 0.0, 0.0)
        assert abs(prob - 0.5) < 0.001

    def test_E_higher_for_better_player(self):
        assert E(1.0, 0.0, 0.0) > 0.5
        assert E(0.0, 1.0, 0.0) < 0.5

    def test_expected_score_vs_opponent(self):
        exp = expected_score_vs_opponent(1500, 350, 1500, 350)
        assert abs(exp - 0.5) < 0.01

    def test_rating_increases_after_win(self):
        r, rd, sigma = calculate_rating_period(
            1500.0, 350.0, 0.06,
            opponents=[(1500.0, 350.0, 1.0)],
        )
        assert r > 1500

    def test_rating_decreases_after_loss(self):
        r, rd, sigma = calculate_rating_period(
            1500.0, 350.0, 0.06,
            opponents=[(1500.0, 350.0, 0.0)],
        )
        assert r < 1500

    def test_win_against_stronger_player_gains_more(self):
        r1, _, _ = calculate_rating_period(1500, 200, 0.06, opponents=[(1700, 200, 1.0)])
        r2, _, _ = calculate_rating_period(1500, 200, 0.06, opponents=[(1300, 200, 1.0)])
        assert r1 > r2

    def test_rating_change_smaller_with_low_rd(self):
        r1, _, _ = calculate_rating_period(1500, 350, 0.06, opponents=[(1500, 350, 1.0)])
        r2, _, _ = calculate_rating_period(1500, 100, 0.06, opponents=[(1500, 100, 1.0)])
        assert r1 > r2  # Higher RD = bigger change

    def test_adjust_rd_for_inactivity(self):
        rd = adjust_rd_for_inactivity(100, 10)
        assert rd > 100
        assert rd <= 350

    def test_no_opponents_returns_same_rating(self):
        r, rd, sigma = calculate_rating_period(1500.0, 100.0, 0.06, opponents=[])
        assert abs(r - 1500) < 0.1
        assert rd > 100  # RD increased due to sigma
