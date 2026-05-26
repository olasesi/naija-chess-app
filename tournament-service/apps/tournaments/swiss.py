import random
from collections import defaultdict
from .models import Tournament, TournamentPlayer, TournamentRound, TournamentMatch


def calculate_tiebreaks(tournament_id):
    players = TournamentPlayer.objects.filter(
        tournament_id=tournament_id, is_active=True
    ).select_related("tournament")

    player_map = {p.user_id: p for p in players}
    user_ids = list(player_map.keys())

    matches = TournamentMatch.objects.filter(
        tournament_id=tournament_id,
        round__status=TournamentRound.Status.COMPLETED,
    ).select_related("round", "white_player", "black_player")

    for uid in user_ids:
        player_map[uid].tiebreak1 = 0.0
        player_map[uid].tiebreak2 = 0.0

    opp_map = defaultdict(list)
    for m in matches:
        if m.result == TournamentMatch.Result.BYE:
            continue
        w_uid = m.white_player.user_id if m.white_player else None
        b_uid = m.black_player.user_id if m.black_player else None
        if w_uid and b_uid:
            opp_map[w_uid].append(b_uid)
            opp_map[b_uid].append(w_uid)

    for uid in user_ids:
        p = player_map[uid]
        if p.score > 0:
            passes = TournamentMatch.objects.filter(
                tournament_id=tournament_id,
                round__status=TournamentRound.Status.COMPLETED,
            ).exclude(result=TournamentMatch.Result.BYE).count()
            p.tiebreak1 = p.score / max(passes, 1)
        opp_scores = sum(player_map.get(opp, player_map[uid]).score for opp in opp_map.get(uid, []))
        p.tiebreak2 = opp_scores

    TournamentPlayer.objects.bulk_update(players, ["tiebreak1", "tiebreak2"])


def pair_swiss_round(tournament_id):
    tournament = Tournament.objects.get(id=tournament_id)
    active_players = list(
        TournamentPlayer.objects.filter(
            tournament_id=tournament_id, is_active=True
        ).order_by("-score", "-tiebreak2", "seed")
    )

    if len(active_players) < 2:
        return []

    round_number = tournament.current_round + 1
    round_obj = TournamentRound.objects.create(
        tournament=tournament,
        round_number=round_number,
        status=TournamentRound.Status.ACTIVE,
    )

    played_pairs = get_played_pairs(tournament_id)

    paired = []
    unpaired = list(active_players)
    random.shuffle(unpaired)
    unpaired.sort(key=lambda p: (-p.score, -p.tiebreak2))

    used = set()
    for i, player in enumerate(unpaired):
        if player.id in used:
            continue
        opponent = find_best_opponent(player, unpaired, used, played_pairs)
        if opponent:
            used.add(player.id)
            used.add(opponent.id)
            white, black = determine_colors(player, opponent, tournament_id)
            paired.append((white, black))
        elif tournament.allow_bye:
            used.add(player.id)
            create_bye_match(tournament, round_obj, player)
        else:
            used.add(player.id)

    remaining = [p for p in unpaired if p.id not in used]
    while len(remaining) >= 2:
        p1 = remaining.pop(0)
        p2 = remaining.pop(0)
        white, black = determine_colors(p1, p2, tournament_id)
        paired.append((white, black))
    for p in remaining:
        if tournament.allow_bye:
            create_bye_match(tournament, round_obj, p)

    board = 1
    for white, black in paired:
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


def find_best_opponent(player, candidates, used, played_pairs):
    best = None
    best_score_diff = None
    for candidate in candidates:
        if candidate.id == player.id or candidate.id in used:
            continue
        pair_key = tuple(sorted([str(player.id), str(candidate.id)]))
        if pair_key in played_pairs:
            continue
        score_diff = abs(player.score - candidate.score)
        if best is None or score_diff < best_score_diff:
            best = candidate
            best_score_diff = score_diff
    return best


def get_played_pairs(tournament_id):
    matches = TournamentMatch.objects.filter(
        tournament_id=tournament_id,
    ).exclude(result=TournamentMatch.Result.BYE)
    pairs = set()
    for m in matches:
        if m.white_player and m.black_player:
            pair = tuple(sorted([str(m.white_player.id), str(m.black_player.id)]))
            pairs.add(pair)
    return pairs


def determine_colors(player_a, player_b, tournament_id):
    """Assign colors trying to balance color history."""
    color_count = get_color_counts(tournament_id)
    count_a_white = color_count.get(player_a.user_id, {}).get("white", 0)
    count_b_white = color_count.get(player_b.user_id, {}).get("white", 0)
    total_a = count_a_white + color_count.get(player_a.user_id, {}).get("black", 0)
    total_b = count_b_white + color_count.get(player_b.user_id, {}).get("black", 0)
    if total_a == 0 and total_b == 0:
        return (player_a, player_b)
    if count_a_white <= count_b_white:
        return (player_a, player_b)
    return (player_b, player_a)


def get_color_counts(tournament_id):
    counts = defaultdict(lambda: {"white": 0, "black": 0})
    matches = TournamentMatch.objects.filter(
        tournament_id=tournament_id,
        round__status=TournamentRound.Status.COMPLETED,
    ).select_related("white_player", "black_player")
    for m in matches:
        if m.white_player:
            counts[m.white_player.user_id]["white"] += 1
        if m.black_player:
            counts[m.black_player.user_id]["black"] += 1
    return counts


def create_bye_match(tournament, round_obj, player):
    TournamentMatch.objects.create(
        tournament=tournament,
        round=round_obj,
        white_player=player,
        result=TournamentMatch.Result.BYE,
        status=TournamentMatch.Status.COMPLETED,
        board_number=999,
    )
    player.score += 1.0
    player.has_bye = True
    player.save(update_fields=["score", "has_bye"])
