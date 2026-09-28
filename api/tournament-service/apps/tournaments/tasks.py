from celery import shared_task
from .models import Tournament, TournamentPlayer, TournamentMatch, TournamentRound
from .swiss import pair_swiss_round, calculate_tiebreaks
from .round_robin import pair_round_robin_round


@shared_task
def auto_pair_next_round(tournament_id):
    try:
        tournament = Tournament.objects.get(id=tournament_id)
    except Tournament.DoesNotExist:
        return {"error": "Tournament not found"}

    if tournament.status != Tournament.Status.ACTIVE:
        return {"error": "Tournament not active"}

    if tournament.current_round >= tournament.total_rounds:
        tournament.status = Tournament.Status.COMPLETED
        tournament.save(update_fields=["status"])
        return {"status": "completed"}

    current_matches = TournamentMatch.objects.filter(
        tournament=tournament,
        round__status=TournamentRound.Status.ACTIVE,
        status__in=[TournamentMatch.Status.PENDING, TournamentMatch.Status.ACTIVE],
    )
    if current_matches.exists():
        return {"error": "Unfinished matches exist"}

    calculate_tiebreaks(tournament_id)

    if tournament.type == Tournament.Type.SWISS:
        round_obj = pair_swiss_round(tournament_id)
    elif tournament.type == Tournament.Type.ROUND_ROBIN:
        round_obj = pair_round_robin_round(tournament_id)
    else:
        return {"error": "Unsupported tournament type"}

    if round_obj is None:
        return {"error": "Pairing failed"}

    return {"round": str(round_obj.id), "round_number": round_obj.round_number}


@shared_task
def check_tournament_completion(tournament_id):
    try:
        tournament = Tournament.objects.get(id=tournament_id)
    except Tournament.DoesNotExist:
        return {"error": "Tournament not found"}

    if tournament.status != Tournament.Status.ACTIVE:
        return {"status": "not_active", "current": tournament.status}

    if tournament.current_round >= tournament.total_rounds:
        pending = TournamentMatch.objects.filter(
            tournament=tournament,
            status__in=[TournamentMatch.Status.PENDING, TournamentMatch.Status.ACTIVE],
        )
        if not pending.exists():
            tournament.status = Tournament.Status.COMPLETED
            tournament.end_date = None
            tournament.save(update_fields=["status", "end_date"])
            return {"status": "completed"}

    return {"status": "in_progress", "round": tournament.current_round}
