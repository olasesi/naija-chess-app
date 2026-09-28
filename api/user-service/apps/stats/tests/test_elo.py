import pytest
from apps.stats.elo import calculate_rating, expected_score, get_k_factor


class TestELO:
    def test_expected_score_equal_ratings(self):
        assert expected_score(1200, 1200) == 0.5

    def test_expected_score_higher_rating(self):
        assert expected_score(1600, 1200) > 0.5
        assert expected_score(1200, 1600) < 0.5

    def test_rating_increases_on_win(self):
        new = calculate_rating(1200, 1200, 1.0)
        assert new > 1200

    def test_rating_decreases_on_loss(self):
        new = calculate_rating(1200, 1200, 0.0)
        assert new < 1200

    def test_rating_draw_equal(self):
        new = calculate_rating(1200, 1200, 0.5)
        assert new == 1200

    def test_k_factor_tiers(self):
        assert get_k_factor(1000) == 32
        assert get_k_factor(2200) == 24
        assert get_k_factor(2500) == 16
