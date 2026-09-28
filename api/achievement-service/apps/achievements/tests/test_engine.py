import pytest
from django.conf import settings

from achievements.engine import level_for_xp, xp_bounds, handle_event
from achievements.models import Achievement, UserAchievement, UserXP


def make_achievement(**kwargs):
    defaults = dict(
        code="test_ach",
        name="Test",
        description="",
        category="game",
        xp_reward=50,
        criteria={"event": "game_won", "operator": "gte", "value": 5, "mode": "count"},
    )
    defaults.update(kwargs)
    return Achievement.objects.create(**defaults)


@pytest.mark.django_db
class TestLevel:
    def test_level_one_at_zero_xp(self):
        assert level_for_xp(0) == 1

    def test_level_boundaries(self):
        per = settings.ACHIEVEMENT_XP_PER_LEVEL
        assert level_for_xp(per - 1) == 1
        assert level_for_xp(per) == 2
        assert level_for_xp(per * 9) == 10

    def test_level_capped(self):
        assert level_for_xp(10 ** 9) == settings.ACHIEVEMENT_MAX_LEVEL

    def test_xp_bounds_floor_and_top(self):
        floor, top = xp_bounds(2)
        assert floor == 100
        assert top == 200

    def test_handle_event_grants_standard_xp(self):
        UserXP.objects.create(user_id="u1", total_xp=0, level=1)
        result = handle_event("u1", {"type": "game_won", "value": 1})
        assert result["xp_gained"] == settings.ACHIEVEMENT_EVENT_XP["game_won"]
        assert result["total_xp"] == settings.ACHIEVEMENT_EVENT_XP["game_won"]

    def test_unknown_event_no_xp(self):
        result = handle_event("u1", {"type": "mystery"})
        assert result["xp_gained"] == 0
        assert result["unlocked"] == []

    def test_missing_type_noop(self):
        assert handle_event("u1", {})["xp_gained"] == 0


@pytest.mark.django_db
class TestUnlocks:
    def test_partial_progress_does_not_unlock(self):
        make_achievement(code="wins_5", criteria={"event": "game_won", "value": 5, "mode": "count"})
        handle_event("u1", {"type": "game_won"})
        handle_event("u1", {"type": "game_won"})
        ua = UserAchievement.objects.get(user_id="u1")
        assert ua.progress == 2
        assert ua.unlocked_at is None

    def test_unlock_at_threshold(self):
        make_achievement(code="wins_5", criteria={"event": "game_won", "value": 5, "mode": "count"})
        for _ in range(5):
            result = handle_event("u1", {"type": "game_won"})
        assert result["unlocked"] == ["wins_5"]
        ua = UserAchievement.objects.get(user_id="u1")
        assert ua.progress == 5
        assert ua.unlocked_at is not None

    def test_no_double_unlock(self):
        make_achievement(code="wins_5", criteria={"event": "game_won", "value": 5, "mode": "count"})
        for _ in range(7):
            handle_event("u1", {"type": "game_won"})
        assert UserAchievement.objects.filter(user_id="u1", unlocked_at__isnull=False).count() == 1
        assert ua_progress("u1") == 5

    def test_set_mode_takes_max(self):
        make_achievement(
            code="streak_10",
            criteria={"event": "daily_streak", "operator": "gte", "value": 10, "mode": "set"},
        )
        handle_event("u1", {"type": "daily_streak", "value": 4})
        handle_event("u1", {"type": "daily_streak", "value": 7})
        assert ua_progress("u1") == 7
        assert UserAchievement.objects.get(user_id="u1").unlocked_at is None
        result = handle_event("u1", {"type": "daily_streak", "value": 10})
        assert result["unlocked"] == ["streak_10"]

    def test_unrelated_event_ignored(self):
        make_achievement(code="wins_5", criteria={"event": "game_won", "value": 5, "mode": "count"})
        handle_event("u1", {"type": "puzzle_solved"})
        assert not UserAchievement.objects.filter(user_id="u1").exists()

    def test_achievement_xp_reward_granted_on_unlock(self):
        make_achievement(code="wins_5", criteria={"event": "game_won", "value": 1, "mode": "set"}, xp_reward=100)
        result = handle_event("u1", {"type": "game_won"})
        # event xp (25) + achievement reward (100)
        assert result["xp_gained"] == 125

    def test_level_updates_after_xp(self):
        make_achievement(code="first_win", criteria={"event": "game_won", "value": 1, "mode": "set"})
        for _ in range(10):
            handle_event("u1", {"type": "game_won"})
        record = UserXP.objects.get(user_id="u1")
        # 10 games x 25xp + 50 reward at first win
        assert record.total_xp == 300
        assert record.level == level_for_xp(record.total_xp)


def ua_progress(user_id):
    return UserAchievement.objects.get(user_id=user_id).progress