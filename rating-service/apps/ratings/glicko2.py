"""
Glicko-2 rating system implementation.

Based on Mark Glickman's paper: http://www.glicko.net/glicko/glicko2.pdf

Key concepts:
  r  = rating (Glicko-1 scale, default 1500)
  RD = rating deviation (default 350)
  σ  = volatility (default 0.06)
  μ  = scaled rating (Glicko-2 scale)
  φ  = scaled rating deviation
  τ  = system constant (constrains volatility over time)
"""

import math
from typing import List, Tuple

# Scale constants
RATING_SCALE = 173.7178
DEFAULT_RATING = 1500.0
DEFAULT_RD = 350.0
DEFAULT_VOLATILITY = 0.06
SYSTEM_CONSTANT = 0.5  # τ
PI_SQUARED = math.pi ** 2


def glicko2_scale(r: float, rd: float, sigma: float) -> Tuple[float, float, float]:
    """Convert from Glicko-1 to Glicko-2 scale."""
    mu = (r - DEFAULT_RATING) / RATING_SCALE
    phi = rd / RATING_SCALE
    return mu, phi, sigma


def glicko1_scale(mu: float, phi: float, sigma: float) -> Tuple[float, float, float]:
    """Convert from Glicko-2 to Glicko-1 scale."""
    r = RATING_SCALE * mu + DEFAULT_RATING
    rd = RATING_SCALE * phi
    return r, rd, sigma


def g(phi: float) -> float:
    """Glicko-2 g(φ) function."""
    return 1.0 / math.sqrt(1.0 + 3.0 * phi ** 2 / PI_SQUARED)


def E(mu: float, mu_j: float, phi_j: float) -> float:
    """Expected score of player with rating μ against opponent with (μ_j, φ_j)."""
    return 1.0 / (1.0 + math.exp(-g(phi_j) * (mu - mu_j)))


def calculate_rating_period(
    player_rating: float,
    player_rd: float,
    player_volatility: float,
    opponents: List[Tuple[float, float, float]],
    tau: float = SYSTEM_CONSTANT,
) -> Tuple[float, float, float]:
    """
    Calculate new (rating, RD, volatility) after a rating period.

    Args:
        player_rating: Current Glicko-1 rating r
        player_rd: Current rating deviation RD
        player_volatility: Current volatility σ
        opponents: List of (opponent_rating, opponent_rd, score)
                   where score = 1.0 (win), 0.5 (draw), 0.0 (loss)
        tau: System constant (default 0.5)

    Returns:
        (new_rating, new_rd, new_volatility) in Glicko-1 scale
    """
    # Step 0: Convert to Glicko-2 scale
    mu, phi, sigma = glicko2_scale(player_rating, player_rd, player_volatility)

    # Precompute opponent values in Glicko-2 scale
    ops = []
    for opp_r, opp_rd, score in opponents:
        opp_mu, opp_phi, _ = glicko2_scale(opp_r, opp_rd, 0.06)
        ops.append((opp_mu, opp_phi, score))

    if not ops:
        # No games — just increase RD over time
        phi_new = math.sqrt(phi ** 2 + sigma ** 2)
        return glicko1_scale(mu, phi_new, sigma)

    # Step 1: Compute φ' (pre-period RD)
    phi_prime = math.sqrt(phi ** 2 + sigma ** 2)

    # Step 2: Compute v (estimated variance) and Δ (improvement)
    v_inv = 0.0
    delta_numerator = 0.0

    for opp_mu, opp_phi, score in ops:
        g_val = g(opp_phi)
        E_val = E(mu, opp_mu, opp_phi)
        v_inv += g_val ** 2 * E_val * (1 - E_val)
        delta_numerator += g_val * (score - E_val)

    v = 1.0 / v_inv if v_inv > 0 else float("inf")
    delta = v * delta_numerator

    # Step 3: Update volatility (σ')
    sigma_new = _update_volatility(delta, phi_prime, v, sigma, tau)

    # Step 4: Update rating deviation
    phi_star = math.sqrt(phi_prime ** 2 + sigma_new ** 2)
    phi_new = 1.0 / math.sqrt(1.0 / phi_star ** 2 + 1.0 / v)

    # Step 5: Update rating
    mu_new = mu + phi_new ** 2 * delta_numerator

    # Step 6: Clamp RD to reasonable bounds
    phi_new = min(phi_new, 8.0)  # Max RD of ~1390 Glicko-1

    # Convert back to Glicko-1 scale
    return glicko1_scale(mu_new, phi_new, sigma_new)


def _update_volatility(
    delta: float,
    phi_prime: float,
    v: float,
    sigma: float,
    tau: float,
) -> float:
    """
    Update volatility σ using the iterative algorithm from Glicko-2.

    Uses Newton-Raphson to find the solution to f(x) = 0 where:
    f(x) = (e^x * (Δ² - φ'² - v - e^x)) / (2(φ'² + v + e^x)²) - (x - ln(σ²)) / τ²

    Where x = ln(σ'²)
    """
    A = math.log(sigma ** 2)
    delta_sq = delta ** 2
    phi_prime_sq = phi_prime ** 2
    v_sq = v ** 2
    tau_sq = tau ** 2

    # Convergence threshold
    epsilon = 0.000001

    def f(x: float) -> float:
        ex = math.exp(x)
        numerator = ex * (delta_sq - phi_prime_sq - v - ex)
        denominator = 2.0 * (phi_prime_sq + v + ex) ** 2
        return numerator / denominator - (x - A) / tau_sq

    def f_prime(x: float) -> float:
        ex = math.exp(x)
        denom = phi_prime_sq + v + ex
        part1_numer = ex * (delta_sq - denom) * (denom - 2 * ex)
        part1_denom = 2 * denom ** 3
        part1 = part1_numer / part1_denom if part1_denom != 0 else 0
        part2 = 1.0 / tau_sq
        return part1 - part2

    # Use the Illinois algorithm for robustness
    # Start with two initial guesses
    if delta_sq > phi_prime_sq + v:
        B = math.log(delta_sq - phi_prime_sq - v)
    else:
        B = A - 1.0

    for _ in range(100):
        fA = f(A)
        fB = f(B)

        if abs(fB) < epsilon:
            return math.exp(B / 2.0)

        if fA * fB > 0:
            # Same sign — adjust B
            A = B
            B = A - 1.0
            continue

        # Newton step
        try:
            C = B - fB / f_prime(B)
        except (ZeroDivisionError, OverflowError):
            C = (A + B) / 2.0

        if abs(f(C)) < epsilon:
            return math.exp(C / 2.0)

        # Update interval
        if f(C) * f(B) < 0:
            A = B
        B = C

    # Fallback
    return sigma


def expected_score_vs_opponent(
    player_rating: float,
    player_rd: float,
    opponent_rating: float,
    opponent_rd: float,
) -> float:
    """Calculate expected score of player against a single opponent."""
    mu, phi, _ = glicko2_scale(player_rating, player_rd, 0.06)
    opp_mu, opp_phi, _ = glicko2_scale(opponent_rating, opponent_rd, 0.06)
    return E(mu, opp_mu, opp_phi)


def adjust_rd_for_inactivity(rd: float, days_inactive: int) -> float:
    """
    Increase RD based on inactivity (rating becomes more uncertain).
    Follows the formula: RD' = sqrt(RD² + c² * days)
    where c is a constant based on the system.
    """
    c = 15.0  # Rating points of uncertainty per day
    new_rd = math.sqrt(rd ** 2 + (c ** 2) * days_inactive)
    return min(new_rd, DEFAULT_RD)  # Cap at default
