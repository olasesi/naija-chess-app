"""
ELO rating calculation (Glicko-2 ready for future upgrade).

Standard ELO with K-factor adjustment:
    - K=32 for players below 2100
    - K=24 for players 2100-2400
    - K=16 for players above 2400
"""


def get_k_factor(rating: int) -> int:
    if rating < 2100:
        return 32
    elif rating < 2400:
        return 24
    return 16


def expected_score(rating_a: int, rating_b: int) -> float:
    """Probability that player A beats player B."""
    return 1.0 / (1.0 + 10.0 ** ((rating_b - rating_a) / 400.0))


def calculate_rating(
    current_rating: int,
    opponent_rating: int,
    score: float,  # 1.0 = win, 0.5 = draw, 0.0 = loss
) -> int:
    """Calculate new rating after a game."""
    expected = expected_score(current_rating, opponent_rating)
    k = get_k_factor(current_rating)
    return round(current_rating + k * (score - expected))
