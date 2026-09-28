import copy
from .models import Tournament, TournamentPlayer, TournamentRound, TournamentMatch


def pair_round_robin_round(tournament_id):
    tournament = Tournament.objects.get(id=tournament_id)
    active_players = list(
        TournamentPlayer.objects.filter(
            tournament_id=tournament_id, is_active=True
        ).order_by("seed")
    )

    n = len(active_players)
    if n < 2:
        return []

    round_number = tournament.current_round + 1

    existing_rounds = list(
        TournamentRound.objects.filter(tournament_id=tournament_id)
        .order_by("round_number")
        .select_related()
    )
    existing_matches = TournamentMatch.objects.filter(
        tournament_id=tournament_id
    ).exclude(result=TournamentMatch.Result.BYE)

    played_pairs = set()
    for m in existing_matches:
        if m.white_player and m.black_player:
            pair = tuple(sorted([str(m.white_player.id), str(m.black_player.id)]))
            played_pairs.add(pair)

    if round_number > n - 1 if _is_even(n) else n:
        return None

    pairs = generate_round_robin_pairs(n, round_number, active_players)
    actual_pairs = []
    for w_idx, b_idx in pairs:
        w = active_players[w_idx]
        b = active_players[b_idx]
        pair_key = tuple(sorted([str(w.id), str(b.id)]))
        if pair_key in played_pairs:
            continue
        actual_pairs.append((w, b))

    if not actual_pairs:
        return None

    round_obj = TournamentRound.objects.create(
        tournament=tournament,
        round_number=round_number,
        status=TournamentRound.Status.ACTIVE,
    )

    board = 1
    for white, black in actual_pairs:
        TournamentMatch.objects.create(
            tournament=tournament,
            round=round_obj,
            white_player=white,
            black_player=black,
            board_number=board,
            status=TournamentMatch.Status.PENDING,
        )
        board += 1

    tournament.current_round = round_number
    tournament.save(update_fields=["current_round"])
    return round_obj


def generate_round_robin_pairs(n, round_num, players):
    if _is_even(n):
        return _generate_even(n, round_num)
    else:
        pairs = _generate_even(n + 1, round_num)
        return [(w, b) for w, b in pairs if w < n and b < n]


def _is_even(n):
    return n % 2 == 0


def _generate_even(n, r):
    r = r % (n - 1)
    if r == 0:
        r = n - 1
    pairs = []
    for i in range(n // 2):
        w = (r + i) % (n - 1)
        b = (n - 1 - i + r) % (n - 1)
        if i == 0:
            b = n - 1
        if r % 2 == 1 and i > 0:
            w, b = b, w
        if i == 0 and r % 2 == 1:
            w, b = b, w
        pairs.append((w, b))
    return pairs


def determine_round_robin_results(tournament_id):
    tournaments = Tournament.objects.filter(id=tournament_id)
    tournament = tournaments.first()
    if not tournament:
        return
    players = TournamentPlayer.objects.filter(
        tournament_id=tournament_id
    ).order_by("-score", "-tiebreak1", "-tiebreak2")
    standings = []
    for i, p in enumerate(players):
        standings.append({"rank": i + 1, "user_id": p.user_id, "score": p.score})
    return standings
