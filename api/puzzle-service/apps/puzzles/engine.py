"""
Puzzle rating engine.

Implements a Glicko-2 style rating system for puzzle solving.

Glicko-2 works in "precision" space, not rating space:
    phi = RD * sqrt(3) / G_SCALE
    RD  = phi * G_SCALE / sqrt(3)

`phi` is inversely related to certainty, so a large phi means a large RD
(unreliable rating). Updates shrink phi, which grows certainty.
"""
from dataclasses import dataclass
from math import pi, sqrt, log, exp

# Glicko scale constant for a 400-point rating scale
G_SCALE = 173.7178
SQRT3 = sqrt(3.0)

# Floor/cap on rating deviation, in rating points
MIN_RD = 30.0
MAX_RD = 350.0

# Bounds on the volatility (sigma) term
MIN_SIGMA = 0.03
MAX_SIGMA = 0.20


@dataclass
class PuzzleRating:
    """A user's puzzle rating state."""

    rating: float
    rd: float = 350.0  # rating deviation (uncertainty, in rating points)
    volatility: float = 0.06  # sigma
    games: int = 0

    @property
    def phi(self) -> float:
        """Glicko-2 precision parameter derived from RD."""
        return self.rd * SQRT3 / G_SCALE

    @property
    def provisional(self) -> bool:
        """Fewer than 10 games means the rating is still settling."""
        return self.games < 10


def _g(phi: float) -> float:
    """Glicko-2 g(phi): shrinks impact of results for uncertain players."""
    return 1.0 / sqrt(1.0 + 3.0 * (phi / G_SCALE) ** 2 / (pi ** 2))


def _expected_score(phi: float, mu_j: float, mu: float) -> float:
    """Expected score of player (mu) against opponent (mu_j)."""
    return 1.0 / (1.0 + exp(-_g(phi) * (mu - mu_j) / G_SCALE))


def expected_score(user_rating: float, puzzle_rating: float) -> float:
    """Plain Elo-style expectation, useful for tests and previews."""
    return 1.0 / (1.0 + 10.0 ** ((puzzle_rating - user_rating) / 400.0))


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _update_volatility(phi_star: float, sigma: float, v: float, delta: float) -> float:
    """
    Glicko-2 Step 5: iterate to find the new volatility sigma.

    v is the rating-period information, delta is the score surprise.
    """
    phi_sq = phi_star * phi_star
    denom = phi_sq - phi_sq * phi_sq / (2.0 * v) if v > 0 else 1.0
    if denom == 0:
        return _clamp(sigma, MIN_SIGMA, MAX_SIGMA)

    # Solve for A from the volatility function
    a = log(sigma * sigma) if sigma > 0 else log(0.06 ** 2)
    for _ in range(64):
        numerator = exp(a) * (phi_sq * phi_sq - phi_star ** 4) / (2.0 * denom ** 2)
        denominator = 1.0
        # f(a) and f'(a) for the Glicko-2 volatility equation
        f = (
            exp(a) * (phi_sq - phi_star ** 4) / (2.0 * denom)
            - delta * delta
        )
        df_da = (
            exp(a) * (phi_sq - phi_star ** 4) / (2.0 * denom) * 0
            + exp(a) * (-2.0 * phi_star ** 4) / (2.0 * denom)
            + exp(a) * (phi_sq - phi_star ** 4) * (2.0 * phi_star ** 2) / (2.0 * denom ** 2)
        )
        if df_da == 0:
            break
        a -= f / df_da
        a = _clamp(a, log(MIN_SIGMA ** 2), log(MAX_SIGMA ** 2))

    return _clamp(exp(a / 2.0), MIN_SIGMA, MAX_SIGMA)


def update_puzzle_rating(
    user: PuzzleRating,
    puzzle_rating: float,
    solved: bool,
    time_taken_seconds: int = 0,
    hints_used: int = 0,
    max_time_seconds: int = 120,
) -> PuzzleRating:
    """
    Update a user's puzzle rating after one attempt.

    Speed and hint usage modulate the score: a fast solve with no hints is
    worth more than a slow solve with hints, matching how puzzle ladders
    normally feel.
    """
    phi = user.phi
    mu = float(user.rating)
    sigma = user.volatility

    # Observed score, modulated by how the user performed.
    if solved:
        s = 1.0
        time_bonus = 0.0
        if time_taken_seconds > 0:
            if time_taken_seconds <= max_time_seconds:
                time_bonus = 0.5  # solved comfortably inside the limit
            else:
                over = (time_taken_seconds - max_time_seconds) / float(max_time_seconds)
                time_bonus = -0.3 * min(over, 1.0)  # dragged it out
        hint_penalty = -0.2 * min(hints_used, 5)
        s = _clamp(s + time_bonus + hint_penalty, 0.0, 1.0)
    else:
        s = 0.0

    g = _g(phi)
    e_score = 1.0 / (1.0 + 10.0 ** ((puzzle_rating - mu) / 400.0))

    # Rating-period information and score surprise
    e_var = e_score * (1.0 - e_score)
    v = 1.0 / (g * g * e_var) if e_var > 0 else 1.0 / (g * g * 1e-6)
    delta = v * g * (s - e_score)

    # Step 3: pre-rating period
    phi_star = sqrt(phi * phi + sigma * sigma)

    # Step 4: new rating and deviation
    new_phi = 1.0 / sqrt(1.0 / (phi_star * phi_star) + 1.0 / v)
    new_mu = mu + new_phi * new_phi * g * (s - e_score)

    # Step 5: new volatility
    new_sigma = _update_volatility(phi_star, sigma, v, delta)

    # Provisional players move more aggressively toward the truth.
    if user.provisional:
        new_mu = mu + (new_mu - mu) * 1.5

    new_rd = _clamp(new_phi * G_SCALE / SQRT3, MIN_RD, MAX_RD)

    return PuzzleRating(
        rating=int(round(new_mu)),
        rd=new_rd,
        volatility=new_sigma,
        games=user.games + 1,
    )


def select_puzzle_rating(user: PuzzleRating, is_beginner: bool = False) -> int:
    """
    Suggest a puzzle rating close to the user's current level.

    New players are pulled toward easier material so they build confidence
    before the ladder ramps up.
    """
    if user.provisional or is_beginner:
        # Cap the target so beginners get approachable puzzles
        return int(min(user.rating, 1400)) - 100
    return int(user.rating)
