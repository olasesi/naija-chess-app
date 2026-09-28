import pytest
from django.conf import settings

from anticheat.engine import compute_score, evaluate_game
from anticheat.models import CheatSignal, GameFlag


def make_signal(signal_type, value, user="u1", game="g1"):
    return CheatSignal(
        signal_type=signal_type, user_id=user, game_id=game, value=value
    )


class TestComputeScore:
    def test_no_signals_zero_score(self):
        score, reasons = compute_score([])
        assert score == 0.0
        assert reasons == []

    def test_low_accuracy_no_score(self):
        signals = [make_signal("engine_accuracy", v) for v in (60, 70, 62, 65, 68, 71, 66, 70, 69, 72)]
        score, reasons = compute_score(signals)
        assert score == 0.0

    def test_high_accuracy_scores(self):
        signals = [make_signal("engine_accuracy", 97) for _ in range(20)]
        score, reasons = compute_score(signals)
        assert reasons[0].startswith("engine_match_accuracy_high")
        assert score > 0
        assert score < 100

    def test_low_variance_move_times_scores(self):
        signals = [make_signal("move_time_ms", 850) for _ in range(20)]
        score, reasons = compute_score(signals)
        assert "move_time_fingerprint" in reasons[0]

    def test_varied_move_times_no_score(self):
        import random
        random.seed(7)
        signals = [make_signal("move_time_ms", random.randint(400, 4000)) for _ in range(20)]
        score, reasons = compute_score(signals)
        assert "move_time_fingerprint" not in reasons

    def test_instant_reply_pattern(self):
        signals = [make_signal("instant_reply", 1.0) for _ in range(5)]
        score, reasons = compute_score(signals)
        assert any("instant_replies" in r for r in reasons)

    def test_clamped_at_100(self):
        signals = [make_signal("engine_accuracy", 99) for _ in range(40)]
        signals += [make_signal("instant_reply", 1.0) for _ in range(20)]
        score, reasons = compute_score(signals)
        assert score <= 100.0


@pytest.mark.django_db
class TestEvaluate:
    def test_clean_game_not_flagged(self):
        for v in (60, 65, 63, 70, 68):
            CheatSignal.objects.create(
                signal_type="engine_accuracy", user_id="u1", game_id="g1", value=v
            )
        result = evaluate_game("u1", "g1")
        assert result["flagged"] is False
        assert result["suspicion_score"] == 0.0

    def test_suspicious_game_flagged(self):
        for _ in range(20):
            CheatSignal.objects.create(
                signal_type="engine_accuracy", user_id="u1", game_id="g1", value=98
            )
        result = evaluate_game("u1", "g1")
        assert result["flagged"] is True
        assert result["suspicion_score"] >= settings.ANTICHEAT_FLAG_THRESHOLD
        assert result["reasons"]

    def test_flags_high_accuracy_log(self):
        for _ in range(20):
            CheatSignal.objects.create(
                signal_type="engine_accuracy", user_id="u1", game_id="g1", value=98
            )
        result = evaluate_game("u1", "g1")
        assert result["flagged"] is True
        assert result["signals_count"] == 20
        assert any("engine_match_accuracy_high" in r for r in result["reasons"])

    def test_radar_signals_count(self):
        from anticheat.engine import evaluate_game as _unused  # noqa
        CheatSignal.objects.create(
            signal_type="move_time_ms", user_id="u2", game_id="g2", value=100
        )
        assert CheatSignal.objects.filter(user_id="u2").count() == 1