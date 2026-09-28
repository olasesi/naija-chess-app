"""
Fair-play heuristic engine.

Consumes telemetry signals per (user, game) and produces a 0-100 suspicion
score plus a list of human-readable reasons. Threshold crossing is handled
by the caller, which persists GameFlag rows.
"""
import statistics

from django.conf import settings

from .models import CheatSignal

ACCURACY_CEILING = settings.ANTICHEAT_ACCURACY_CEILING
ACCURACY_WEIGHT = settings.ANTICHEAT_ACCURACY_WEIGHT
GRID_WEIGHT = settings.ANTICHEAT_GRID_WEIGHT
MOVE_TIME_WEIGHT = settings.ANTICHEAT_MOVE_TIME_WEIGHT
FLAG_THRESHOLD = settings.ANTICHEAT_FLAG_THRESHOLD


def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


def _signal_map(qs):
    grouped = {}
    for sig in qs:
        grouped.setdefault(sig.signal_type, []).append(sig)
    return grouped


def compute_score(signals) -> tuple[float, list[str]]:
    """
    Score a user's signals for one game.

    :param signals: iterable of CheatSignal
    :returns: (suspicion_score 0-100, reasons list)
    """
    grouped = _signal_map(signals)
    reasons = []

    # 1. Engine-match accuracy consistently above the ceiling.
    accuracy = [s.value for s in grouped.get("engine_accuracy", [])]
    if accuracy:
        accurate_moves = sum(1 for a in accuracy if a >= ACCURACY_CEILING)
        ratio = accurate_moves / len(accuracy)
        if ratio >= 0.7:
            avg_acc = statistics.mean(accuracy)
            points = (avg_acc - ACCURACY_CEILING) * ACCURACY_WEIGHT * ratio
            reasons.append(f"engine_match_accuracy_high:{avg_acc:.0f}%")
        else:
            points = 0.0
    else:
        points = 0.0

    # 2. Move-time fingerprint: extremely low variance across many moves.
    move_times = [s.value for s in grouped.get("move_time_ms", [])]
    if len(move_times) >= 15:
        mean = statistics.mean(move_times)
        variance = statistics.pstdev(move_times)
        # ratio low (<0.1) means robotically consistent timing
        ratio = variance / mean if mean > 0 else 1.0
        if ratio < 0.1:
            points += GRID_WEIGHT * 25.0
            reasons.append("move_time_fingerprint:low_variance")

    # 3. "Instant" replies: fast responses to critical positions.
    instant = [s.value for s in grouped.get("instant_reply", [])]
    if instant:
        inst_ratio = sum(1 for v in instant if v >= 1.0) / len(instant)
        if inst_ratio >= 0.5:
            points += MOVE_TIME_WEIGHT * 30.0
            reasons.append("instant_replies:pattern")

    # 4. Mouse-out / tab-switch ratio (engine browsing).
    mouseouts = grouped.get("mouseout_count", [])
    moves = len(accuracy) or len(move_times)
    if moves and mouseouts:
        outs = sum(s.value for s in mouseouts)
        if outs / moves >= 0.8:
            points += 15.0
            reasons.append("excessive_tab_switches")

    points = _clamp(points)
    return round(points, 1), reasons


def evaluate_game(user_id, game_id) -> dict:
    """Score a game for a user and surface recommendations."""
    signals = CheatSignal.objects.filter(user_id=user_id, game_id=game_id)
    score, reasons = compute_score(signals)
    return {
        "user_id": user_id,
        "game_id": game_id,
        "suspicion_score": score,
        "flagged": score >= FLAG_THRESHOLD,
        "threshold": FLAG_THRESHOLD,
        "signals_count": signals.count(),
        "reasons": reasons,
    }