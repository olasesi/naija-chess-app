from celery import shared_task
from django.utils import timezone
from .models import PlayerRating, RatingHistory, TimeControl
from .glicko2 import calculate_rating_period, adjust_rd_for_inactivity
from django.db import transaction


@shared_task
def process_game_result(
    game_id: str,
    white_user_id: str,
    black_user_id: str,
    result: str,  # "1-0", "0-1", "1/2-1/2"
    time_control: str,
    played_at: str,
):
    """
    Process a completed game result through Glicko-2.
    Called by the game service when a game ends.
    """
    if time_control not in dict(TimeControl.choices):
        time_control = TimeControl.RAPID

    score_map = {
        "1-0": (1.0, 0.0),
        "0-1": (0.0, 1.0),
        "1/2-1/2": (0.5, 0.5),
    }

    scores = score_map.get(result)
    if not scores:
        return {"error": f"Invalid result: {result}"}

    with transaction.atomic():
        white_rating = _get_or_create_rating(white_user_id, time_control)
        black_rating = _get_or_create_rating(black_user_id, time_control)

        # Adjust RDs for inactivity
        now = timezone.now()
        white_rating.ratingDeviation = _adjust_rd(white_rating, now)
        black_rating.ratingDeviation = _adjust_rd(black_rating, now)

        # Calculate new ratings
        white_new_r, white_new_rd, white_new_sigma = calculate_rating_period(
            white_rating.rating,
            white_rating.ratingDeviation,
            white_rating.volatility,
            opponents=[(black_rating.rating, black_rating.ratingDeviation, scores[0])],
        )

        black_new_r, black_new_rd, black_new_sigma = calculate_rating_period(
            black_rating.rating,
            black_rating.ratingDeviation,
            black_rating.volatility,
            opponents=[(white_rating.rating, white_rating.ratingDeviation, scores[1])],
        )

        # Save white
        _save_rating(white_rating, white_new_r, white_new_rd, white_new_sigma, scores[0], game_id, black_user_id, now)

        # Save black
        _save_rating(black_rating, black_new_r, black_new_rd, black_new_sigma, scores[1], game_id, white_user_id, now)

    return {
        "white": {"rating": round(white_new_r), "rd": round(white_new_rd)},
        "black": {"rating": round(black_new_r), "rd": round(black_new_rd)},
    }


def _get_or_create_rating(user_id: str, time_control: str) -> PlayerRating:
    rating, _ = PlayerRating.objects.get_or_create(
        userId=user_id,
        timeControl=time_control,
    )
    return rating


def _adjust_rd(rating: PlayerRating, now) -> float:
    if rating.lastGameAt:
        days_inactive = (now - rating.lastGameAt).days
        if days_inactive > 0:
            return adjust_rd_for_inactivity(rating.ratingDeviation, days_inactive)
    return rating.ratingDeviation


def _save_rating(
    rating: PlayerRating,
    new_r: float,
    new_rd: float,
    new_sigma: float,
    score: float,
    game_id: str,
    opponent_id: str,
    now,
):
    # Update counters
    rating.rating = round(new_r, 1)
    rating.ratingDeviation = round(new_rd, 1)
    rating.volatility = round(new_sigma, 4)
    rating.gamesPlayed += 1

    if score == 1.0:
        rating.wins += 1
    elif score == 0.5:
        rating.draws += 1
    else:
        rating.losses += 1

    if rating.gamesPlayed >= 20:
        rating.provisional = False

    rating.lastGameAt = now
    rating.save()

    # Save history entry
    result_str = {1.0: "win", 0.5: "draw", 0.0: "loss"}.get(score, "unknown")
    RatingHistory.objects.create(
        userId=rating.userId,
        timeControl=rating.timeControl,
        rating=rating.rating,
        ratingDeviation=rating.ratingDeviation,
        volatility=rating.volatility,
        gameId=game_id,
        opponentId=opponent_id,
        result=result_str,
    )
